"""Unicode properties and explicit boundaries between symbols, meaning and execution."""
import unicodedata
SCRIPTS=[(0x41,0x24f,'Latin'),(0x370,0x3ff,'Greek'),(0x400,0x52f,'Cyrillic'),(0x590,0x5ff,'Hebrew'),(0x600,0x6ff,'Arabic'),(0x900,0x97f,'Devanagari'),(0x980,0x9ff,'Bengali'),(0xa00,0xa7f,'Gurmukhi'),(0xb80,0xbff,'Tamil'),(0xc00,0xc7f,'Telugu'),(0xe00,0xe7f,'Thai'),(0x3040,0x309f,'Hiragana'),(0x30a0,0x30ff,'Katakana'),(0x3400,0x9fff,'Han range'),(0xac00,0xd7af,'Hangul')]
APPLICATIONS={
 'conversation':'Interpret words and context; ask when ambiguous. Character properties help segmentation and display, not mind reading.',
 'tasks':'Map an expressed goal to typed inputs, operations, completion conditions and dependencies.',
 'work':'Separate requests, source evidence, proposed actions, actual results and recovery steps.',
 'commands':'Parse according to the chosen shell/API grammar. Quote data, validate arguments and retain actual execution review.',
 'code':'Recognise encoding, tokens, syntax and types; use the correct parser and task tests. Text is not executable merely because it resembles code.',
 'roots':'Study phonology, morphology, lexical history and language contact using source-labelled linguistic references. Script names and visual similarity alone do not establish etymology.'}

def describe(code):
 if type(code)is not int or not 0<=code<=0x10ffff or 0xD800<=code<=0xDFFF:raise ValueError('Provide a Unicode scalar value')
 c=chr(code);name=unicodedata.name(c,'UNASSIGNED OR CONTROL');script=next((n for lo,hi,n in SCRIPTS if lo<=code<=hi),'Other/common/unknown; consult Unicode Script property')
 return {'code':code,'hex':f'U+{code:04X}','character':c,'name':name,'category':unicodedata.category(c),'bidirectional_class':unicodedata.bidirectional(c),'combining_class':unicodedata.combining(c),'script_hint':script,'script_hint_scope':'rough block range, not an authoritative script or language identification','normalisation':{form:unicodedata.normalize(form,c) for form in ('NFC','NFD','NFKC','NFKD')},'casefold':c.casefold(),'unicode_database_version':unicodedata.unidata_version,'graphemes':'One visible grapheme can contain several code points; words and meaning require context.','applications':APPLICATIONS,'sources':['https://www.unicode.org/glossary/','https://www.unicode.org/reports/tr15/','https://universaldependencies.org/','https://docs.python.org/3/library/unicodedata.html']}
