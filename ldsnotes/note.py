import requests
from time import sleep
from annotations import make_annotation, Annotation

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

    def search(self, keyword=None, tag=None, folder=None, start=1, stop=51):
        # setup request
        params = {"start": start, "numberToReturn": stop-start}
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