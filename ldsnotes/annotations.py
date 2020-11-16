from content import Content, clean_html
import re
from datetime import datetime

def make_annotation(json):
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
                hl_and_end = re.split("[— ]", c, maxsplit=start)[-1]
            else:
                hl_and_end = c
            if int(hl['endOffset']) != -1:
                stop = int(hl['endOffset'])
                len_end = -len(re.split("[— ]", c, maxsplit=stop)[-1])
            else:
                len_end = None
            sep_hl.append( hl_and_end[:len_end] )
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