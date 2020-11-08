import requests
import html.parser

H = html.parser.HTMLParser()
CONTENT = "https://www.churchofjesuschrist.org/content/api/v2"

def remove_html_tags(text):
    """Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

class Content:
    def __init__(self, json):
        #actual text
        self.content = H.unescape(json['content'][0]['markup'])
        #name of article ie name of conference talk or Helaman 3
        self.headline = json['headline']
        #full reference for scriptures like Helaman 3:29
        self.reference = json['referenceURIDisplayText']
        #refers to book (ie GC 2020, or BOM)
        self.publication = json['publication']
        lang = json['uri'].split('/')[1] 
        self.url = "https://www.churchofjesuschrist.org/" + "/".join( json['uri'].split('/')[2:] ) + "?lang=" + lang

    def __print__(self):
        return self.content
    __repr__ = __print__

    @staticmethod
    def fetch(uris, json=False):
        resp = requests.post(url=CONTENT,
                            data={"uris": uris}).json()

        if json:
            return [resp[u] for u in uris]
        else:
            return [Content(resp[u]) for u in uris]

if __name__ == "__main__":
    from pprint import pprint
    c = Content.fetch(["/eng/scriptures/bofm/hel/3.p29", "/eng/general-conference/2020/10/34franco.p28"])
    pprint(c)
