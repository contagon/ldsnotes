import requests
from time import sleep
from content import Content, clean_html
import re
from datetime import datetime

#basic selenium imports
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
#used for waiting for pages to load
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TAGS        = "https://www.churchofjesuschrist.org/notes/api/v2/tags"
ANNOTATIONS = "https://www.churchofjesuschrist.org/notes/api/v2/annotations"
FOLDERS     = "https://www.churchofjesuschrist.org/notes/api/v2/folders"

class Annotation:
    def __init__(self, json, content_jsons):
        # get highlight color
        self.color = json['highlight']['content'][0]['color']
        # Some notes don't actually have style
        # self.style = json['highlight']['content'][0]['style']

        #pull out content
        sep_content = []
        for j in content_jsons:
            sep_content.append( clean_html(j['content'][0]['markup']) )
        self.content = "\n".join(sep_content)

        # pull out highlight
        sep_hl = []
        for i, (c, hl) in enumerate(zip(sep_content, json['highlight']['content'])):
            # convert start/end word offset into string index
            if int(hl['startOffset']) != -1:
                start = int(hl['startOffset'])-1
                # this ugly regex gets the nth match of of either — or a space
                start = re.search(rf"(?:.*?[\s—]+){{{start-1}}}.*?([\s—]+)",c).end()
            else:
                start = None
            if int(hl['endOffset']) != -1:
                stop = int(hl['endOffset'])
                stop = re.search(rf"(?:.*?[\s—]+){{{stop-1}}}.*?([\s—]+)", c).end()-1
            else:
                stop = None
            sep_hl.append( c[start:stop] )
        self.hl = "\n".join(sep_hl)

        # pull out other info
        self.tags = json['tags']
        self.folders_id = [i['id'] for i in json['folders']]

        #pull out note if there is one
        if "note" in json and 'content' in json['note']:
            self.note = json['note']['content']
        else:
            self.note = ""

        # pull title of note
        if "note" in json and 'title' in json['note']:
            self.title = json['note']['title']
        else:
            self.title = ""

        # pull out last updated date
        self.last_update = datetime.fromisoformat(json["lastUpdated"])

        # pull out id
        self.id = json['id']

        # pull out url to highlight
        lang = json['locale']
        end_p = json['highlight']['content'][-1]['uri'].split('.')[-1]
        self.url = "https://www.churchofjesuschrist.org" + json['highlight']['content'][0]['uri'] + "-" + end_p + "?lang=" + lang

        #name of article ie name of conference talk or Helaman 3
        self.headline = content_jsons[0]['headline']

        #full reference for scriptures like Helaman 3:29
        self.reference = content_jsons[0]['referenceURIDisplayText']

        #refers to book (ie GC 2020, or BOM)
        self.publication = content_jsons[0]['publication']

    def __print__(self):
        return self.hl
    __repr__ = __print__

    def markdown(self, syntax="=="):
        return self.content.replace(self.hl, syntax+self.hl+syntax)

    @staticmethod
    def make(json):
        # fetch all context stuff (do it all at once to be faster)
        uris = [f"/{j['locale']}{i['uri']}" for j in json for i in j['highlight']['content']]
        content_jsons = Content.fetch(uris, json=True)
        #resort uris
        uris = [j['uri'] for j in content_jsons]

        #put it back together
        sorted_content_jsons = []
        #iterate through each note
        for j in json:
            temp = []
            #iterate through each content in note
            for i in j['highlight']['content']:
                #get the content for that note
                temp.append(content_jsons[ uris.index(f"/{j['locale']}{i['uri']}") ])
            sorted_content_jsons.append(temp)

        if len(json) == 1:
            return Annotation(json[0], sorted_content_jsons[0])
        else:
            return [Annotation(a, c) for a,c in zip(json, sorted_content_jsons)]

class Tag:
    def __init__(self, name, count):
        self.name = name
        self.count = count
    
    def __len__(self):
        return self.count

    def __str__(self):
        return self.name
    __repr__ = __str__

class Folder:
    def __init__(self, name, count, id):
        self.name = name
        self.count = count
        self.id = id
    
    def __len__(self):
        return self.count

    def __str__(self):
        return self.name
    __repr__ = __str__

class Notes:
    def __init__(self, username=None, password=None, token=None, headless=True, json=False):
        self.json = json
        self.session = requests.Session()
        
        if token is None:
            self.username = username
            self.password = password
            self._login(headless)
        else:
            self.token = token
            self.session.cookies.set("Church-auth-jwt-prod", self.token)
            
    def _login(self, headless):
        #run headless
        options = Options()
        if headless:
            options.add_argument("--headless")
            options.add_argument("--window-size=1920x1080")
        browser = webdriver.Chrome(options=options)

        #login using selenium
        browser.get("https://churchofjesuschrist.org/notes")

        #username page
        login = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
        login.clear()
        login.send_keys(self.username)
        login.send_keys(Keys.RETURN)

        #password page
        auth = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
        auth.clear()
        auth.send_keys(self.password)
        auth.send_keys(Keys.RETURN)
        sleep(3)

        #copy over cookies into our request session
        self.token = [c['value'] for c in browser.get_cookies() if c['name'] == "Church-auth-jwt-prod"][0]
        self.session.cookies.set("Church-auth-jwt-prod", self.token)

        return self.token

    @property
    def tags(self):
        return [Tag(t['name'], t['annotationCount']) for t in self.session.get(url=TAGS).json()]

    @property
    def folders(self):
        return [Folder(f['name'], f['annotationCount'], f['id']) for f in self.session.get(url=FOLDERS).json()]

    def __getitem__(self, val):
        if isinstance(val, slice):
            if val.start is None:
                start = 0
            else:
                start = val.start
            num = val.stop - start
            #api indexes at 1
            start += 1

        elif isinstance(val, int):
            start = val+1
            num = 1

        params = {"start": start, "numberToReturn": num}
        if self.json:
            return self.session.get(url=ANNOTATIONS, params=params).json()
        else:
            return Annotation.make(self.session.get(url=ANNOTATIONS, params=params).json())

    def search(self, keyword=None, tag=None, folder=None, start=1, num=50):
        # setup request
        params = {"start": start, "numberToReturn": num}
        if tag is not None:
            params['tags'] = tag
        if folder is not None:
            folderid = [f.id for f in self.folders if f.name == folder][0]
            params['folderId'] = folderid
        if keyword is not None:
            params['searchPhrase'] = keyword

        # send request
        if self.json:
            return self.session.get(url=ANNOTATIONS, params=params).json()
        else:
            return Annotation.make(self.session.get(url=ANNOTATIONS, params=params).json())