import requests
from time import sleep
from content import Content

#basic selenium imports
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
#used for waiting for pages to load
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pprint import pprint
TAGS        = "https://www.churchofjesuschrist.org/notes/api/v2/tags"
ANNOTATIONS = "https://www.churchofjesuschrist.org/notes/api/v2/annotations"

class Annotation(Content):
    def __init__(self, json, content_json):
        super().__init__(content_json)
        hl = json['highlight']['content'][0]
        self.color = hl['color']
        start = int(hl['startOffset']) if int(hl['startOffset']) != -1 else None 
        stop = int(hl['endOffset']) if int(hl['endOffset']) != -1 else None
        self.highlight = " ".join( self.content.split(" ")[start:stop] )
        self.tags = json['tags']
        self.folders = json['folders']
        
        if "note" in json:
            self.note = json['note']['content']
        else:
            self.note = ""

    def __print__(self):
        return self.highlight
    __repr__ = __print__

    @staticmethod
    def fetch(json):
        uris = [f"/{i['locale']}{i['highlight']['content'][0]['uri']}" for i in json]
        content_jsons = Content.fetch(uris, json=True)
        return [Annotation(a, c) for a,c in zip(json, content_jsons)]

class Tag:
    def __init__(self, name, count):
        self.name = name
        self.count = count
    
    def __len__(self):
        return self.count

    def __str__(self):
        return self.name
    __repr__ = __str__


class Notes:
    def __init__(self, username=None, password=None, token=None, headless=True):
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
        return Annotation.fetch(self.session.get(url=ANNOTATIONS, params=params).json())