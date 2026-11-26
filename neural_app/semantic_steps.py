"""Finite semantic slots for compositional data requests; no dropped qualifiers."""
import json,math,re
FIELD=r'[a-zA-Z_][\w-]{0,63}'
REL=r'greater than|less than|no more than|no less than|at least|at most|equal to|equals|above|below|over|under'
RELATIONS={'greater than':'greater','above':'greater','over':'greater','less than':'less','below':'less','under':'less','no more than':'at_most','at most':'at_most','no less than':'at_least','at least':'at_least','equal to':'equal','equals':'equal'}

def parse(text):
    key=text.casefold().strip()
    aliases={'remove repeated values':'unique','remove repeated items':'unique','remove duplicate entries':'unique',
             'arrange in increasing order':'sort','arrange in ascending order':'sort','arrange in decreasing order':'sort-desc',
             'arrange in descending order':'sort-desc','add up all values':'sum','add up the values':'sum','count the items':'count',
             'count the values':'count','calculate the average':'mean','find the middle value':'median','find the largest value':'maximum','find the smallest value':'minimum'}
    if key in aliases:
        op=aliases[key];return {'op':'sort','descending':True} if op=='sort-desc' else {'op':op}
    first=re.fullmatch(r'keep the first (\d{1,3}) (?:items|values|rows|characters)',key)
    if first:return {'op':'take','count':int(first[1])}
    column=re.fullmatch(r'(?:pick|select|extract) the ('+FIELD+r') column',text,re.I)
    if column:return {'op':'field','name':column[1]}
    sort=re.fullmatch(r'sort (?:rows|items|values) by ('+FIELD+r') from (lowest to highest|highest to lowest)',text,re.I)
    if sort:return {'op':'sort','field':sort[1],'descending':sort[2].casefold()=='highest to lowest'}
    aggregate=re.fullmatch(r'(total|average|minimum|maximum) ('+FIELD+r') for each ('+FIELD+r')',text,re.I)
    if aggregate:return {'op':'group','field':aggregate[3],'aggregate':{'total':'sum','average':'mean','minimum':'minimum','maximum':'maximum'}[aggregate[1].casefold()],'value_field':aggregate[2]}
    filtered=re.fullmatch(r'(?:keep|retain)(?: only)? (?:(?:rows|items) where ('+FIELD+r')(?: is)?|(?:numbers|values)) ('+REL+r') (.+)',text,re.I)
    if not filtered:return None
    field,relation,literal=filtered.groups()
    try:value=json.loads(literal)
    except ValueError:return None
    relation=RELATIONS[relation.casefold()]
    if type(value) not in (str,int,float,bool,type(None)):return None
    if type(value) in (int,float) and (not math.isfinite(value) or abs(value)>1e100):return None
    if relation!='equal' and type(value) not in (int,float):return None
    return {'op':'filter','relation':relation,'value':value,**({'field':field} if field is not None else {})}
