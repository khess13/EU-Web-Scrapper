import re, os, json
import urllib.request, urllib.error, urllib.parse
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from pathlib import Path

def get_files_from_dir(filepath, ext = '.html') -> list:
    filesindir = os.listdir(filepath)
    #tilda indicates open temp file, excluding these
    xlsxfiles = [f for f in filesindir if ext in f and not 'Procurement Services' in f]
    if len(xlsxfiles) == 0:
        print('No files found, try checking the extension.')
    else:
        return xlsxfiles

def souper(filepath) -> 'soup':
    with open(filepath, 'r', encoding='utf8') as page:
        soup = BeautifulSoup(page, 'html.parser')
        return soup

def text_extract(soupCommand, reCompile) -> list:
    listName = []
    for v in soupCommand:
        extract = v.get_text()
        search = re.search(reCompile, extract)
        if search:
            listName.append(search.group())
    return listName

def webpage_to_file(key, url):
    response = urllib.request.urlopen(url)
    responseRead = response.read()
    with open(key+'.html', 'wb') as file:
        file.write(responseRead)

root = os.getcwd()
root_parent = str(Path(os.getcwd()).parents[0]) + "\\"
target = root_parent + '\\PO-Plan\\vendorListByBrand.json'
target2 = root_parent + '\\PO-Plan\\vendorNameByBrand.json'
mainPage = root + '\\Procurement Services.html'

links = {}
domain = 'https://procurement.sc.gov'
#parent page
pPage = 'https://procurement.sc.gov/contracts/search?b=9918-0-0'

#soup = BeautifulSoup(mainPage.content, 'html.parser')
refresh = input('Refresh webpages? Y/N')
if refresh.lower() == 'y':
    webpage_to_file('Procurement Services', pPage)
    print('Retrieved new main page')
    soup = souper(mainPage)
    #retrieve links
    text = re.compile('PCs, Servers, Storage, Peripherals')
    paratext = re.compile('\((.+)\)')
    print('Finding links')
    for a in soup.find_all('a', text=text):
        extract = a.get_text()
        search = re.search(paratext, extract)
        if search:
            key = search.group(1)
        else:
            key = extract
        links[key] = (a['href'])
    print('Loading new child pages')
    #spider the links
    for key, url in links.items():
        webpage_to_file(key, domain + url)
else:
    print('Skipped refresh')

#rebuild
filesindir = get_files_from_dir(root)
print('Processing new pages')
vendorNoList = []
vendorNameList = []
vendorNameDict = {}
vendorNoDict = {}
#TODO - may be make this a regex for () acronyms
stopwords = ['.',',','LLC','US','Corporation','Incorporated','Corp','Inc']
for file in filesindir:
    soup = souper(file)
    brandPattern = re.compile('.+(?=\.html)')
    brandSearch = re.search(brandPattern, file)
    if brandSearch:
        brandSelect = brandSearch.group().upper()
    vendorNameSearch = re.compile('(?<=Vendor:\s).+')
    vendorName = soup.find_all('td', class_='dta100 gry spc3a')
    vendorNoSearch = re.compile('7[0-9]{9}')
    vendorNo = soup.find_all('td', class_='dta100 spc3')
    #Contract#: no
    vendorNoList = text_extract(vendorNo, vendorNoSearch)
    vendorNameList = text_extract(vendorName, vendorNameSearch)

    #remove stop words
    cleanedVendorNameList = []
    for ven in vendorNameList:
        text_tokens = word_tokenize(ven)
        tokens_cleaned = [w for w in text_tokens if not w in stopwords]
        cleanedVendorNameList.append(' '.join(tokens_cleaned))

    vendorNameDict[brandSelect] = cleanedVendorNameList
    vendorNoDict[brandSelect] = vendorNoList

with open(target,'w') as file:
    json.dump(vendorNoDict, file)
with open(target2,'w') as file:
    json.dump(vendorNameDict, file)
print('Processing Complete!')
