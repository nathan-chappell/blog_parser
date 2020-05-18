# paragraph.py

from util import bannerfy

from typing import Dict, Callable, FrozenSet, List
import json

#
# unit of information eaten by BlogParser
#
class Paragraph:
    metadata: Dict[str,str]
    text: str

    attrs: FrozenSet[str] = frozenset([
        "author",
        "date",
        "article_title",
        "paragraph_title",
        "filename",
    ])

    metadata_access_err_msg = bannerfy("""
Please access Paragraph.metadata by assigning metadata directly, e.g:
>>> p = Paragraph()
>>> p.author = Kurt Vonnegut
""")

    def __init__(self):
        metadata = {k:"" for k in Paragraph.attrs}
        object.__setattr__(self,'metadata',metadata)
        object.__setattr__(self,'text',"")

    def __setattr__(self,k,v):
        if k in Paragraph.attrs: 
            object.__getattribute__(self,'metadata')[k]= v
        elif k == 'text': 
            object.__setattr__(self,k,v)
        elif k == 'metadata': 
            raise AttributeError(Paragraph.metadata_access_err_msg)
        else: 
            raise AttributeError(f"{k} not a recognized Paragraph attribute")

    def __getattr__(self,k):
        raise AttributeError(f"{k} not a recognized attribute")

    def __getattribute__(self,k):
        if k == 'text' or k in Paragraph.__dict__:
            return object.__getattribute__(self,k)
        elif k in Paragraph.attrs:
            return object.__getattribute__(self,'metadata')[k]
        else:
            raise AttributeError

    def __repr__(self) -> str:
        metadata = object.__getattribute__(self,'metadata')
        return json.dumps({"metadata":metadata.copy(),"text":self.text})

    def __str__(self) -> str:
        metadata = object.__getattribute__(self,'metadata')
        word_count = len(self.text.split())
        text = f'{self.text[0:20]}...{self.text[-20:]}'
        text += f' [length: {word_count} words]'
        return json.dumps({"metadata":metadata.copy(),"text":text},indent=2)

    #
    # returns a new paragraph with copied metadata except paragraph_title
    # and blank text field
    #
    def new_paragraph(self) -> 'Paragraph':
        metadata = object.__getattribute__(self,'metadata')
        p = Paragraph()
        object.__setattr__(p,'metadata',metadata)
        p.paragraph_title = ""
        return p

#
# a ParagraphsAction takes a list of paragraphs, performs some action,
# then returns the (potentially modified) paragraph for further
# processing.  The functions are called with reduce (similar to redux)
#
# The parameter is a list of paragraphs in case the action splits up
# the paragraph into multiple chunks, or perhaps removes empty
# paragraphs
#

Paragraphs = List[Paragraph]
ParagraphsAction = Callable[[Paragraphs],Paragraphs]

