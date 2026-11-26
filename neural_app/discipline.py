"""Authored cross-tradition study, exact trigram encoding and reflection."""
import json
from pathlib import Path
from .matter_spirit import process as reflect
from .translation import translate_bits

ROOT=Path(__file__).resolve().parents[1]
TRIGRAMS={
 '111':('Qian','☰','Heaven','Initiative with responsibility'),
 '000':('Kun','☷','Earth','Receptivity without surrendering judgment'),
 '100':('Zhen','☳','Thunder','Awakening and a considered first step'),
 '011':('Xun','☴','Wind','Patient, gentle persistence'),
 '010':('Kan','☵','Water','Attention within difficulty'),
 '101':('Li','☲','Fire','Clarity joined to care'),
 '001':('Gen','☶','Mountain','Stillness and a useful boundary'),
 '110':('Dui','☱','Lake','Joy, exchange and truthful speech')}

def catalogue():
    value=json.loads((ROOT/'references/discipline.json').read_text(encoding='utf-8'))
    value['trigrams']={bits:dict(zip(('name','glyph','image','practice'),row)) for bits,row in TRIGRAMS.items()}
    return value

def process(body):
    bits=body.get('trigram','010')
    if bits not in TRIGRAMS:raise ValueError('Use exactly three 0/1 line bits, bottom to top')
    centre=body.get('centre',3)
    if type(centre) is not int or not 0<=centre<=6:raise ValueError('Choose a centre from 0 to 6')
    intent=body.get('intent','Let strength serve truthful care.')
    if not isinstance(intent,str) or len(intent.encode('utf-8'))>480:raise ValueError('Use at most 480 UTF-8 bytes of intent')
    value=reflect({'lesson':'combined',**body},catalogue())
    value['trigram']={'line_order':'bottom to top; solid=1, broken=0','bits':bits,
        **dict(zip(('name','glyph','image','practice'),TRIGRAMS[bits])),
        'complement':''.join('0' if b=='1' else '1' for b in bits),'transport':translate_bits(bits)}
    value['practice']={'intent':intent,'selected_centre':centre,'attention_vector':[int(i==centre) for i in range(7)],
        'scope':'Declared attention and spiritual reflection; no measurement of chakras, nonlocal force or another person.'}
    value['model']='Embodied reflection, ethical responsibility and exact symbolic line encoding'
    return value
