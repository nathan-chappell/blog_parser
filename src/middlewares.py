# middlewares.py

from paragraph import Paragraph, Paragraphs, ParagraphsAction
from util import get_log, word_count

from typing import List
import re
from logging import DEBUG, WARN

Middlewares = List[ParagraphsAction]

log = get_log(__file__, stderr=True, mode='a')
log.setLevel(WARN)

def pa_log(paragraphs: Paragraphs) -> Paragraphs:
    log.info("\n".join(map(str,paragraphs)))
    return paragraphs

def pa_sanitize_ws(paragraphs: Paragraphs) -> Paragraphs:
    def sanitize_ws(paragraph: Paragraph):
        paragraph.text = re.sub("\s+",' ',paragraph.text).strip()
    for paragraph in paragraphs: sanitize_ws(paragraph)
    return paragraphs

def pa_chunk_long(paragraphs: Paragraphs) -> Paragraphs:
    max_paragraph_length = 300

    def split_text_at_p_tag(text: str) -> List[str]:
        #return re.split('</?p>',text)
        return re.split('<p>',text)

    def split_paragraph(paragraph: Paragraph) -> Paragraphs:
        log.debug(f'splitting long paragraph: {word_count(paragraph.text)}')
        _paragraphs: Paragraphs = []
        paragraph_title = paragraph.paragraph_title
        texts = split_text_at_p_tag(paragraph.text)
        log.debug(f'total chunks: {len(texts)}')
        for i,text in enumerate(texts):
            p = paragraph.new_paragraph()
            p.paragraph_title = f'{paragraph_title}_{i}'
            p.text = text
            _paragraphs.append(p)
        return _paragraphs

    _paragraphs: Paragraphs = []

    for paragraph in paragraphs:
        if word_count(paragraph.text) < max_paragraph_length:
            _paragraphs.append(paragraph)
        else:
            _paragraphs.extend(split_paragraph(paragraph))

    return _paragraphs

def pa_cat_short(paragraphs: Paragraphs) -> Paragraphs:
    min_paragraph_length = 50
    #
    # modifies l by concatenating it with r
    #
    def cat_paragraph(l: Paragraph, r: Paragraph):
        l.text += ' ' + r.text
        #
        # don't catenate subtitles from chunks
        #
        l_st = l.paragraph_title.rsplit('_',1)[0]
        r_st = r.paragraph_title.rsplit('_',1)[0]
        if not l_st == r_st:
            l.paragraph_title += ' ' + r.paragraph_title

    def long_enough(paragraph: Paragraph) -> bool:
        return word_count(paragraph.text) > min_paragraph_length

    def has_enough(paragraphs: Paragraphs, i: int) -> bool:
        wc = 0
        while i < len(paragraphs):
            wc += word_count(paragraphs[i].text)
            i += 1
            if wc > min_paragraph_length:
                return True
        return False
        
    i: int = 0
    while i < len(paragraphs) - 1:
        if long_enough(paragraphs[i]) and has_enough(paragraphs,i+1):
            i += 1
        else:
            cat_paragraph(paragraphs[i],paragraphs[i+1])
            del paragraphs[i+1]

    return paragraphs

def pa_remove_empty(paragraphs: Paragraphs) -> Paragraphs:
    _paragraphs: Paragraphs = []
    for paragraph in paragraphs:
        if not word_count(paragraph.text) == 0:
            _paragraphs.append(paragraph)
    return _paragraphs

r_ptag = re.compile('</?p>')
def pa_remove_ptag(paragraphs: Paragraphs) -> Paragraphs:
    for paragraph in paragraphs:
        paragraph.text = r_ptag.sub(' ', paragraph.text)
    return paragraphs


