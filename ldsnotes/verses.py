import requests
import html.parser
import re

H = html.parser.HTMLParser()
CONTENT = "https://www.churchofjesuschrist.org/content/api/v2"


def clean_html(text):
    """Takes in html code and cleans it. Note that footnotes
    are replaced with # for word counting later.

    Parameters
    -----------
        text : string
            html to clean

    Returns
    --------
        text : string
            cleaned text"""

    # convert all html characters
    text = html.unescape(text)
    # footnotes followed by punctuation make the punctuation be counted as a
    # word... sigh.
    punc_footnotes = re.compile(
        r'<sup class=\"marker\">\w</sup>(\w*)</a>([!?.,])')
    text = re.sub(punc_footnotes, r'#\1#\2', text)
    # remove footnotes (also counts as words)
    no_footnotes = re.compile(r'<sup class=\"marker\">\w</sup>')
    text = re.sub(no_footnotes, '#', text)
    # remove rest of html tags
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    # remove peksy leftover
    return text.replace(u'\xa0', u' ')


class Content:
    """Class that pulls/represents content from anywhere
        on churchofjesuschrist.org/study (theoretically)


    Parameters
    ----------
    json : dict
        Dictionary made from json pull from lds.org's API.

    Attributes
    -----------
    content : string
        Book, talk, or section of content.

    headline : string
        The content (see above) with verse number in case of scriptures.

    publication : string
        Overarching publication. Think BoM, DoC, General Conference 2020, etc.

    url : string
        URL of where the content is located (including the paragraph/verse).

    uri : string
        URI that it was pulled with.

    p_start : string
        First verse/paragraph pulled.

    p_end : string
        Last verse/paragraph pulled.
    """

    def __init__(self, json):
        # actual text
        self.sep_content = []
        for j in json['content']:
            self.sep_content.append(clean_html(j['markup']))
        self.content = "\n".join(self.sep_content).replace("#", "")

        # name of article ie name of conference talk or Helaman 3
        self.headline = json['headline']

        # full reference for scriptures like Helaman 3:29
        self.reference = json['referenceURIDisplayText']

        # refers to book (ie GC 2020, or BOM)
        self.publication = json['publication']

        # uri it was pulled with
        self.uri = json['uri']

        # paragraph or verse #'s
        self.p_start = int(json['content'][0]['id'][1:])
        self.p_end = int(json['content'][-1]['id'][1:])

        lang = json['uri'].split('/')[1]
        self.url = "https://www.churchofjesuschrist.org/study/" + \
            "/".join(json['uri'].split('/')[2:]) + "?lang=" + lang

    def __print__(self):
        return self.content
    __repr__ = __print__

    @staticmethod
    def fetch(uris, json=False):
        """Method to actually make content. This is where the magic happens.
            Requires a proper URI to fetch content.

        Parameters
        ----------
        uris : list
            List of URIs to pull from lds.org. See below for example.
        json : bool
            Whether to return as list of Content objects or the raw dictionaries. Most useful in debugging. Defaults to False.

        Returns
        --------
        Either a list of Content objects, or a list of strings.


        Examples
        ---------
        >>> Content.fetch(["/eng/scriptures/bofm/hel/3.p29"])
        [29 Yea, we see that whosoever will may lay hold upon the word of God, which is quick and powerful, which shall divide asunder all the cunning and the snares and the wiles of the devil, and lead the man of Christ in a strait and narrow course across that everlasting gulf of misery which is prepared to engulf the wicked—]
        >>> Content.fetch(["/eng/scriptures/bofm/hel/3.p29"], json=True)
        [{'content': [{'displayId': '29',
                    'id': 'p29',
                    'markup': '<p class="verse" data-aid="128356897" id="p29"><span '
                                'class="verse-number">29 </span>Yea, we see that '
                                'whosoever will may lay hold upon the <a '
                                'class="study-note-ref" href="#note29a"><sup '
                                'class="marker">a</sup>word</a> of God, which is <a '
                                'class="study-note-ref" href="#note29b"><sup '
                                'class="marker">b</sup>quick</a> and powerful, which '
                                'shall <a class="study-note-ref" href="#note29c"><sup '
                                'class="marker">c</sup>divide</a> asunder all the '
                                'cunning and the snares and the wiles of the devil, '
                                'and lead the man of Christ in a strait and <a '
                                'class="study-note-ref" href="#note29d"><sup '
                                'class="marker">d</sup>narrow</a> course across that '
                                'everlasting <a class="study-note-ref" '
                                'href="#note29e"><sup class="marker">e</sup>gulf</a> '
                                'of misery which is prepared to engulf the '
                                'wicked&#x2014;</p>'}],
        'headline': 'Helaman 3',
        'image': {},
        'publication': 'Book of Mormon',
        'referenceURI': '/eng/scriptures/bofm/hel/3.p29?lang=eng#p29',
        'referenceURIDisplayText': 'Helaman 3:29',
        'type': 'chapter',
        'uri': '/eng/scriptures/bofm/hel/3.p29'}]
        """  # noqa: E501

        resp = requests.post(url=CONTENT,
                             data={"uris": uris}).json()

        if json:
            return [resp[u] for u in uris]
        else:
            return [Content(resp[u]) for u in uris]
