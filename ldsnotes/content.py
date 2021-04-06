import requests
import re
import dpath.util
from bs4 import BeautifulSoup
import os
from tqdm import tqdm
CONTENT = "https://www.churchofjesuschrist.org/study/api/v3/language-pages/type/content?lang=eng"

def clean_uri(uri):
    if "study" in uri:
        uri = uri[7:]
    
    if uri[0] != '/':
        uri = '/' + uri

    return uri

def fetch(uri):
    uri = clean_uri(uri)
        
    resp = requests.get(url=CONTENT, params={"uri": uri})
    if resp.status_code == 200:
        resp = resp.json()
        types = {'chapter': Chapter,
                'general-conference-talk': Talk,
                'book': TableOfContent,
                'general-conference': TableOfContent,
                'topic': Chapter}

        # have corresponding class clean things out
        type = dpath.util.values(resp, "**/data-content-type")[0]
        c = types.get(type)
        if c is None:
            print(f"Not configured for type {type}")
        else:
            c = c(resp)

        return c

class StandardWorks:
    def __init__(self, pkl=None):
        self.uris = ['scriptures/dc-testament/',
                        'scriptures/bofm/',
                        'scriptures/ot/',
                        'scriptures/nt/',
                        'scriptures/pgp/',]
                        # 'scriptures/tg/']
        # self.uris = ['scriptures/ot/']
        self.works = []

        if pkl is None:
            for w in self.uris:
                self.works.append(fetch(w))
        else:
            something_something = self.load_pkl(pkl)

    def save_md(self, folder, seperate_verses=False):
        finder = re.compile('\[.*?\](\([^#]*?\))')

        if seperate_verses:
            pass
        else:
            replacements = dict()
            filenames = []
            pages = []
            for w in self.works:
                replacements.update(w.get_name_replacements(seperate_verses))
                filename, page = w.get_files(seperate_verses)
                filenames.extend(filename)
                pages.extend(page)

            # replace references as needed
            for f, p in zip(filenames, pages):
                for m in finder.finditer(p):
                    match = m[1][1:-1]

                    # remove verse if it has it
                    if '.' in match:
                        match, verse = match.split('.')
                    else:
                        verse = None

                    new = replacements.get(match)

                    # add things in as needed
                    if verse is not None:
                        verse = f".{verse}?lang=eng#p{verse}" if new is None else f"#^{verse}"
                    if new is None:
                        new = "https://www.churchofjesuschrist.org/study" + match
                        print("No match for ", match)
                    if verse is not None:
                        new += verse

                    new = f"({new})".replace(" ", "%20")
                    p = p.replace(m[1], new)

                # save everything
                file = os.path.join(folder, f)
                print(file)
                os.makedirs(os.path.dirname(file), exist_ok=True)
                with open(file, 'w') as t:
                    t.write(p)
                    

    def save_pkl(self, filename):
        pass

    def load_pkl(self, filename):
        pass

class TableOfContent:
    def __init__(self, resp):
        self.resp = resp

        body = dpath.util.values(resp, "**/body")[0]
        body = BeautifulSoup(body, 'html.parser')

        elements = [b['href'] for b in body.find_all('a', href=True)]
        # clean uris
        elements = [clean_uri(e) for e in elements]

        self._uri = clean_uri(resp['uri'])

        self.chapters = self.get_all(elements)

        # TODO Make dictionary mapping URIs to filenames for parsing later
        # TODO When doing this, have it change to lds.org link if it doesn't exist

    def get_name_replacements(self, seperate_verses=False):
        if seperate_verses:
            pass
        else:
            replacements = dict()
            for c in self.chapters:
                uri, filename, page = c.full_page
                replacements[uri] = filename
                
            return replacements

    def get_files(self, seperate_verses=False):
        if seperate_verses:
            pass
        else:
            filenames = []
            pages     = []
            folders   = []
            for c in self.chapters:
                uri, filename, page = c.full_page
                filename = os.path.join(c.folder, filename)
                
                filenames.append(filename)
                pages.append(page)
                folders.append(c.folder)

            return filenames, pages


    def save_md(self, folder, seperate_verses=False):
        if seperate_verses:
            pass
        else:
            for c in self.chapters:
                uri, filename, page = c.full_page
                file = os.path.join(folder, os.path.join(c.folder, filename))
                os.makedirs(os.path.dirname(file), exist_ok=True)
                with open(file, 'w') as f:
                    f.write(page)

    @staticmethod
    def get_all(elements):
        results = []

        # iterate through all elements in TOC
        loop = tqdm(leave=False)
        for e in elements:  
            c = 1
            while c is not None:
                # get it
                loop.update()
                loop.set_description(e)
                c = fetch(e)

                # if it was good, save it
                if c is not None:
                    results.append(c)
                    
                    # if it's a chapter, try to get the next one
                    if e.split('/')[-1].isdigit():
                        parts = e.split('/')
                        num = int(parts[-1])+1
                        new_link = "/".join(parts[:-1]) + "/" + str(num)
                        if new_link not in elements:
                            e = new_link
                        else:
                            c = None
                    # otherwise, end while loop
                    else:
                        c = None
        
        return results

class Content:
    def __init__(self, resp):
        self.resp = resp

        body = dpath.util.values(resp, "**/body")[0]
        body = BeautifulSoup(body, 'html.parser')
        self._header = body.header

        # get all the paragraphs/verses
        verses = body.find_all(id=re.compile("p."))
        self._verses = self.clean_verses(verses)

        # get footnotes
        footnotes = dpath.util.values(resp, "**/footnotes")
        self._fn_id, self._footnotes = self.clean_footnotes(footnotes)

        # get pdf link
        try:
            self._pdf = dpath.util.values(resp, "**/pdf/source")[0]
        except:
            self._pdf = None

        # get uri
        self._uri = clean_uri(resp['uri'])
        self._toc = resp['tableOfContentsUri']

        # get title of chapter/page
        self.title = dpath.util.values(resp, "**/title")[0]

        # get save location
        self.folder = self._uri[::-1].split('/',1)[1][::-1][1:]
        self.filename = self.title

    @staticmethod
    def clean_footnotes(footnotes):

        fn_id = dpath.util.values(footnotes, '**/id')
        textss = dpath.util.values(footnotes, '*/*/text')
        textss = [BeautifulSoup(t, 'html.parser') for t in textss]

        # note doing anything with type here.. be warned it may come up
        # only seen ref['type'] = 'scripture-ref'

        footnotes = []
        # iterate over each footnote
        for id, refs in zip(fn_id, textss):
            # there can be multiple references in a footnote
            for ref in refs.find_all('a'):

                # get info from notes
                chap_name = ref.get_text().split(':')[0]
                link = re.split('[.?]', ref['href'])

                # check if it's verses, or just a normal link
                if len(link) == 3:
                    chap_link, verses, _ = link
                    chap_link = clean_uri(chap_link)

                    # get list of all verses
                    verses = verses.split(',')
                    all_verses = []
                    for v in verses:
                        if "-" in v:
                            start, end = v.split('-')
                            if start.isdigit():
                                all_verses += list(range(int(start), int(end)+1))
                        
                        if "-" not in v or not start.isdigit():
                            all_verses.append( v )

                    # put together all verses
                    links = [f"[{v}]({chap_link}.{v})" for v in all_verses]
                    link = f"[{chap_name}]({chap_link}):"
                    link = link + ",".join(links)

                else:
                    link = f"[{chap_name}]({link[0]})"

                # replace HTML link with a wikilink
                ref.replace_with(link)

            footnotes.append(refs)

        return fn_id, footnotes        

    @property
    def verses(self):
        return [v.get_text() + f" ^{i+1}" for i, v in enumerate(self._verses)]

    @property
    def verse_pages(self):
        return list(zip(*[self._verse_to_page(i) for i in range(len(self._verses))]))

    @property
    def footnotes(self):
        return [f"#### {id[4:]}: {fn.get_text()} ^{id}" for id, fn in zip(self._fn_id, self._footnotes)]

    @property
    def full_page(self):
        # add in header (title, author, etc)
        page = f"# {self._header.get_text().strip()}\n\n"

        # page content
        page += "\n\n".join(self.verses) + "\n\n"

        # footnotes
        page += "\n".join(self.footnotes)

        return self._uri, self.filename+".md", page

    @property
    def link_page(self):
        # add in header (title, author, etc)
        page = f"# {self._header.get_text().strip()}\n\n"

        # page content
        for i in range(1, len(self._verses)+1):
            page += f"![[{self._uri}.{i}#^1]]\n"

        return self._uri, self.filename+".md", page

    def _verse_to_page(self, val):
        # get verse and footnotes in that verse
        verse = self._verses[val-1].get_text()
        fn_name = re.findall("\(#\^(note.*?)\)", verse)
        fn_id = [self._fn_id.index(name) for name in fn_name]

        # header
        result = f"# {self.title}:{val}\n"

        # navigation
        if val != 1:
            result += f"[<-- Previous]({self._uri}.{val-1}) "
        if val != len(self._verses):
            result += f"| [Next -->]({self._uri}.{val+1})"

        # verse
        result += "\n\n\n" + verse + " ^1\n\n"

        # footnotes
        for id in fn_id:
            result += "\n" + self.footnotes[id]
        return f"{self._uri}.{val}", f"{self.filename}.{val}.md", result

class Chapter(Content):
    @staticmethod
    def clean_verses(verses):
        for i, v in enumerate(verses):
            # turn footnotes into wikilinks
            fns = v.find_all(class_="study-note-ref")
            for fn in fns:
                letter = fn.contents[0].string
                word = fn.contents[1]

                fn.contents[0].replace_with("")
                fn.contents[1].replace_with(f"[{word}](#^note{i+1}{letter})")

        return verses


class Talk(Content):
    @staticmethod
    def clean_verses(verses):
        for i, v in enumerate(verses):
            # turn footnotes into wikilinks
            fns = v.find_all(class_="note-ref")
            for fn in fns:
                letter = fn.contents[0].string
                fn.contents[0].replace_with(f" [\[{letter}\]](#^note{letter})")

        return verses