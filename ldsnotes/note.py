import requests
from time import sleep
from ldsnotes.annotations import make_annotation, Annotation
from addict import Dict
from datetime import datetime

#install chrome driver
import chromedriver_autoinstaller
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


class Tag(Dict):
    """Object that holds all Tag info

    Attributes
    -----------
    annotationCount : string
        Number of annotations assigned to tag
    name : string
        Name of tag
    id : string
        Seems to always be the same as name...
    lastUsed : datetime
        Last time that tag was edited"""
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.lastUsed = datetime.fromisoformat(self.lastUsed)

    def __str__(self):
        return "(Tag) " + self.name
    __repr__ = __str__

class Folder(Dict):
    """Object that holds all Tag info

    Attributes
    -----------
    annotationCount : string
        Number of annotations in folder
    name : string
        Name of folder
    id : string
        Special id of folder
    lastUsed : datetime
        Last time that the folder was changed
    order.id : list
        List of note ids in order that they were put in."""
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    def __str__(self):
        return "(Folder) " + self.name
    __repr__ = __str__

class Notes:
    """Wrapper to pull any annotations from lds.org.

    The API is rather complex to use to login. We take the lazy route and login
    with selenium (basically a fake browser). To avoid doing this everytime you can 
    save the necessary token.

    The object also supports indexing, so you can get the first note with n[0], or the first 
    10 doing n[:10]. When doing this it'll return the most recently edited objects. 
    Whenever querying, it'll always return the most recently edited objects.

    Parameters
    -----------
    username : string
        Your username
    password : string
        Your password
    token : string
        Instead of inputting your username/password, you can save your token and just input it
    headless : bool
        Whether to run selenium headless or not
        
    Attributes
    -----------
    tags : list
        List of Tag objects of all your tags
    folders : list
        List of Folder objects of all your folders"""
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
        #install chromedriver
        chromedriver_autoinstaller.install()

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
        return [Tag(t) for t in self.session.get(url=TAGS).json()]

    @property
    def folders(self):
        return [Folder(f) for f in self.session.get(url=FOLDERS).json()]

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

        params = {"start": start, "numberToReturn": num, "notesAsHtml": False}
        return make_annotation( self.session.get(url=ANNOTATIONS, params=params).json() )

    def search(self, keyword=None, tag=None, folder=None, annot_type=["bookmark", "highlight", "journal", "reference"], start=1, stop=51, as_html=False, json=False):
        """Searches for annotations.

        Parameters
        -----------
        keyword : string
            Keyword to search for. Defaults to None.
        tag : string
            Name of tag you want to search for. Defaults to None.
        folder : string
            Name of folder you want to search for. Defaults to None.
        annot_type : list/string
            Type of annotation to pull. Can be a list/one of bookmark, highlight, journal, reference. Defaults to all of them.
        start : int
            How deep in to start search (must be > 1). Defaults to 1.
        stop : int
            Where to stop search. Defaults to 51.
        as_html : bool
            If True, returns notes with html tags. If False, returns as markdown (I think). Defaults to False.
        json : bool
            If True, returns raw data from lds.org. If False, returns our cleaned objects. 

        Returns
        --------
        List of strings or Bookmark/Highlight/Journal/Reference objects
        """
        #clean out requested annotation type
        if isinstance(annot_type, str):
            annot_type = [annot_type]

        types = ["highlight", "journal", "reference", "bookmark"]
        bad = [t for t in annot_type if t not in types]
        if len(bad) != 0:
            raise ValueError("You tried to search for type that doesn't exist")

        # setup request
        params = {"start": start, "numberToReturn": stop-start, "notesAsHtml": as_html}
        params['type'] = ",".join(annot_type)
        if tag is not None:
            params['tags'] = tag
        if folder is not None:
            folderid = [f.id for f in self.folders if f.name == folder][0]
            params['folderId'] = folderid
        if keyword is not None:
            params['searchPhrase'] = keyword

        # send request
        if json:
            return self.session.get(url=ANNOTATIONS, params=params).json()
        else:
            return make_annotation(self.session.get(url=ANNOTATIONS, params=params).json())