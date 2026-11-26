"""Conservative request framing; preserve quoted data and explicit task boundaries."""
import re

def normalize(text):
    value=text.strip()
    for _ in range(5):
        updated=re.sub(r"^(?:please\s+|(?:can|could|would) you\s+|(?:i would|i'd|i’d) like you to\s+|i need you to\s+)",'',value,flags=re.I)
        if updated==value:break
        value=updated
    if value.casefold().rstrip('?.!') in ('tell me what you can do','tell me your capabilities','explain your capabilities'):return 'what are your capabilities'
    return value

def arithmetic(text):
    match=re.fullmatch(r"(?:what is|what's|work out)\s+(.+?)[?]?",text.strip(),re.I)
    if not match:return None
    expression=match[1].rstrip('?').strip().casefold()
    for word,op in [('multiplied by','*'),('divided by','/'),('plus','+'),('minus','-'),('times','*')]:expression=re.sub(r'\b'+word+r'\b',op,expression)
    if not re.fullmatch(r'[0-9.()+*/%\s-]+',expression):return None
    from .exact_numbers import calculate
    result=calculate(expression)
    value=int(result['numerator']) if result['denominator']=='1' else result['exact_result']
    return {**result,'status':'complete','answer':result['exact_result'],'value':value}

def questions(text):
    """Only explicit '? Also' boundaries outside quoted/structured data.

    Documents, code and labelled evidence keep their content opaque.
    """
    text=normalize(text)
    if re.match(r'^(?:read this|summari[sz]e this|research brief|conversation facts|study|analyse study|analyze study|write|create|generate|teach|learn|work request|preview|remember)\b',text,re.I):return None
    quote=None;escaped=False;stack=[];cuts=[];i=0
    while i<len(text):
        c=text[i]
        if quote:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c==quote:quote=None
        elif c in ('"',"'",'`'):
            if c!="'" or not (i and i+1<len(text) and text[i-1].isalnum() and text[i+1].isalnum()):quote=c
        elif c in '[{(':stack.append(c)
        elif c in ']})':
            if not stack or '[{('.index(stack.pop())!=']})'.index(c):return None
        elif c=='?' and not stack:
            m=re.match(r'\s+also(?:,|\s)\s*',text[i+1:],re.I)
            if m:cuts.append((i+1,i+1+m.end()));i+=m.end()
        i+=1
    if quote or stack or not cuts:return None
    parts=[];start=0
    for end,next_start in cuts:parts.append(normalize(text[start:end]));start=next_start
    parts.append(normalize(text[start:]))
    if not 2<=len(parts)<=8 or any(not p for p in parts):return None
    return parts
