from ldsnotes.content import Content, clean_html
import re
from datetime import datetime

def make_annotation(json):
    # fetch all context stuff (do it all at once to be faster) # TODO: Reparse this, this is unreadable
    uris = [f"/{j['locale']}{i['uri']}" for j in json  if 'highlight' in j for i in j['highlight']['content']]
    uris += [f"/{j['locale']}{i['uri']}" for j in json  if 'refs' in j for i in j['refs']]
    content_jsons = Content.fetch(uris, json=True) if len(uris) != 0 else []
    #re-sort uris
    uris = [j['uri'] for j in content_jsons]

    #put it back together
    annotations = []
    for j in json:
        if j['type'] == "bookmark":
            annotations.append( Bookmark(j) )

        elif j['type'] == "journal":
            annotations.append( Journal(j) )

        elif j['type'] == 'highlight':
            content = []
            for i in j['highlight']['content']:
                content.append(content_jsons[ uris.index(f"/{j['locale']}{i['uri']}") ])
            annotations.append( Highlight(j, content) ) 

        elif j['type'] == 'reference':
            content = []
            for i in j['highlight']['content']:
                content.append(content_jsons[ uris.index(f"/{j['locale']}{i['uri']}") ])
            ref_content = []
            for i in j['refs']:
                ref_content.append(content_jsons[ uris.index(f"/{j['locale']}{i['uri']}") ])
            annotations.append( Reference(j, content, ref_content) ) 

        else:
            raise ValueError("Unknown Type of note")

    if len(annotations) == 1:
        return annotations[0]
    else:
        return annotations

class Annotation:
    """Base class for all annotations.

    Attributes
    -----------
    tags : list
        List of strings of tag names.
    folders_id : list
        List of strings of folder ids. 
    last_update : datetime
        Last time annotation was edited.
    id : string
        Id of annotation."""
    def __init__(self, json):
        # pull out other info
        self.tags = json['tags']
        self.folders_id = [i['id'] for i in json['folders']]

         # pull out last updated date
        self.last_update = datetime.fromisoformat(json["lastUpdated"])

        # pull out id
        self.id = json['id']

class Bookmark(Annotation):
    """A bookmark annotation. Inherits from annotation.

    Attributes
    -----------
    tags : list
        List of strings of tag names.
    folders_id : list
        List of strings of folder ids. 
    last_update : datetime
        Last time annotation was edited.
    id : string
        Id of annotation.
    headline : string
        Name of article ie name of conference talk or Helaman 3.
    reference : string
        Full reference for scriptures like Helaman 3:29.
    publication : string
        Refers to book (ie GC 2020 or BoM).
    url : string
        Url to bookmark location.
    """
    def __init__(self, json):
        super().__init__(json)

        #name of article ie name of conference talk or Helaman 3
        self.headline = json['bookmark']['name']

        #full reference for scriptures like Helaman 3:29
        self.reference = json['bookmark']['reference']

        #refers to book (ie GC 2020, or BOM)
        self.publication = json['bookmark']['publication']

        # pull out url to highlight
        lang = json['locale']
        self.url = "https://www.churchofjesuschrist.org" + json['bookmark']['uri'] + "?lang=" + lang
    
    def __print__(self):
        return "(Bookmark) " + self.reference
    __repr__ = __print__

class Journal(Annotation):
    """A journal entry. Inherits from Annotation.

    Attributes
    -----------
    tags : list
        List of strings of tag names.
    folders_id : list
        List of strings of folder ids. 
    last_update : datetime
        Last time annotation was edited.
    id : string
        Id of annotation.
    title : string
        Title of journal entry.
    note : string
        Actual note taken."""
    def __init__(self, json):
        super().__init__(json)

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
        
    def __print__(self):
        more = self.note
        if self.title != "":
            more = self.title
        return "(Journal) " + self.title
    __repr__ = __print__

split_reg = "[— ()#¶]"

class Highlight(Journal):
    """A scripture highlight. Inherits from Journal.

    Attributes
    -----------
    tags : list
        List of strings of tag names.
    folders_id : list
        List of strings of folder ids. 
    last_update : datetime
        Last time annotation was edited.
    id : string
        Id of annotation.
    title : string
        Title of journal entry.
    note : string
        Actual note taken.
    color : string
        Color of annotation.
    content : string
        Content of verse/paragraph(s) being highlighted.
    hl : string
        Portion of verse that's been highlighted.
    url : string
        Url to verse/paragraph(s)
    headline : string
        Name of article ie name of conference talk or Helaman 3.
    reference : string
        Full reference for scriptures like Helaman 3:29.
    publication : string
        Refers to book (ie GC 2020 or BoM)."""
    def __init__(self, json, content_jsons):
        super().__init__(json)

        # get highlight color
        self.color = json['highlight']['content'][0]['color']
        # Some notes don't actually have style
        # self.style = json['highlight']['content'][0]['style']

        #pull out content
        sep_content = []
        for j in content_jsons:
            sep_content.append( clean_html(j['content'][0]['markup']) )
        self.content = "\n".join(sep_content).replace("#", "")

        # pull out highlight
        sep_hl = []
        # iterate through each paragraph/verse included
        for i, (c, hl) in enumerate(zip(sep_content, json['highlight']['content'])):
            # convert start/end word offset into string index
            if int(hl['startOffset']) != -1:
                start = int(hl['startOffset'])-1
                hl_and_end = re.split(split_reg, c, maxsplit=start)[-1]
            else:
                hl_and_end = c

            if int(hl['endOffset']) != -1:
                stop = int(hl['endOffset'])
                len_end = -len(re.split(split_reg, c, maxsplit=stop)[-1])
            else:
                len_end = None

            # Put into note altogether
            sep_hl.append( hl_and_end[:len_end].strip() )

        # join all together. Remove # used for word counting
        self.hl = "\n".join(sep_hl).replace("#", "")

        # pull out url to highlight
        lang = json['locale']
        self.url = "https://www.churchofjesuschrist.org/study" + json['highlight']['content'][0]['uri']
        # if multiple verses, make url reflect that
        if len(json['highlight']['content']) > 1:
            end_p = json['highlight']['content'][-1]['uri'].split('.')[-1]
            self.url += "-" + end_p 
        self.url += "?lang=" + lang

        #name of article ie name of conference talk or Helaman 3
        self.headline = clean_html( content_jsons[0]['headline'] )

        #full reference for scriptures like Helaman 3:29
        self.reference = clean_html( content_jsons[0]['referenceURIDisplayText'] )

        #refers to book (ie GC 2020, or BOM)
        self.publication = clean_html( content_jsons[0]['publication'] )

    def __print__(self):
        return "(Highlight) " + self.hl
    __repr__ = __print__

    def markdown(self, syntax="=="):
        """Returns content with the highlight wrapped in markdown syntax.

        Parameters
        -----------
        syntax : string
            String to wrap highlight in. Defaults to ==

        Returns
        --------
        Content with wrapped highlight."""
        return self.content.replace(self.hl, syntax+self.hl+syntax)

class Reference(Highlight):
    """A scripture link/reference. Inherits from Highlight.

    Attributes
    -----------
    tags : list
        List of strings of tag names.
    folders_id : list
        List of strings of folder ids. 
    last_update : datetime
        Last time annotation was edited.
    id : string
        Id of annotation.
    title : string
        Title of journal entry.
    note : string
        Actual note taken.
    color : string
        Color of annotation.
    content : string
        Content of verse/paragraph(s) being highlighted.
    hl : string
        Portion of verse that's been highlighted.
    url : string
        Url to verse/paragraph(s)
    headline : string
        Name of article ie name of conference talk or Helaman 3.
    reference : string
        Full reference for scriptures like Helaman 3:29.
    publication : string
        Refers to book (ie GC 2020 or BoM).
    ref_content : string
        Content of verse/paragraph(s) that are linked to
    ref_headline : string
        Headline of reference. See headline for examples.
    ref_reference : string
        Reference of reference. See reference for examples.
    ref_publication : string
        Publication of reference. See publication for examples."""
    def __init__(self, json, hl_json, ref_json):
        super().__init__(json, hl_json)

        # pull out reference content
        #pull out content
        sep_content = []
        for j in ref_json:
            sep_content.append( clean_html(j['content'][0]['markup']) )
        self.ref_content = "\n".join(sep_content).replace("#", "")

        # pull out url to reference
        lang = json['locale']
        self.ref_url = "https://www.churchofjesuschrist.org/study" + json['refs'][0]['uri']
        if len(json['highlight']['content']) > 1:
            end_p = json['refs'][-1]['uri'].split('.')[-1]
            self.ref_url += "-" + end_p 
        self.ref_url += "?lang=" + lang

        #name of article ie name of conference talk or Helaman 3
        self.ref_headline = clean_html( ref_json[0]['headline'] )

        #full reference for scriptures like Helaman 3:29
        self.ref_reference = clean_html( ref_json[0]['referenceURIDisplayText'] )

        #refers to book (ie GC 2020, or BOM)
        self.ref_publication = clean_html( ref_json[0]['publication'] )

    def __print__(self):
        return "(Reference) " + self.hl
    __repr__ = __print__