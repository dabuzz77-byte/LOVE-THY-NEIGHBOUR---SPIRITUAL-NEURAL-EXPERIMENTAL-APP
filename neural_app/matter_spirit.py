"""Authored spiritual study and a bounded, explicitly symbolic repair model."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def catalogue():
    return json.loads((ROOT/'references'/'matter-spirit.json').read_text(encoding='utf-8'))

def number(body, key, default):
    value = body.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(key+' must be a finite number from 0 to 1')
    return float(value)

def process(body, data=None):
    if data is None: data = catalogue()
    ident = body.get('lesson', 'purifier')
    chapter = next((x for x in data['chapters'] if x['id'] == ident), None)
    if chapter is None: raise ValueError('Choose a listed lesson')
    care = number(body, 'care', .7)
    restraint = number(body, 'restraint', .7)
    repair = number(body, 'repair', .7)
    pressure = number(body, 'pressure', .6)
    steps = body.get('steps', 12)
    if type(steps) is not int or not 1 <= steps <= 60: raise ValueError('steps must be an integer from 1 to 60')
    # A teaching model, with declared coefficients and conserved symbolic units.
    # Outputs cannot measure a person's karma, faith, morality or physical matter.
    protected = 0.; unresolved = pressure; trace = []
    for tick in range(steps):
        interrupted = unresolved * restraint * .2
        restored = (unresolved-interrupted) * care * repair * .15
        transformed = interrupted+restored
        unresolved -= transformed; protected += transformed
        trace.append({'step':tick+1, 'unresolved':unresolved, 'restored':protected,
                      'interrupted_this_step':interrupted, 'repaired_this_step':restored})
    return {'status':'COMPLETE','lesson':ident,'title':chapter['title'],
            'teaching':chapter['paragraphs'], 'source_ids':chapter.get('sources', []),
            'supplied_passage':chapter.get('quote'), 'attribution':chapter.get('attribution'),
            'author_notes':data['author_notes'] if ident in ('faith','chaos','lamb','choice','cross') else [],
            'content_digest':hashlib.sha256(json.dumps(chapter,sort_keys=True).encode()).hexdigest(),
            'model':'Symbolic shadow-side purification: interrupt harm, apply care, repair, review.',
            'scope':'Educational state transitions; not a measurement of souls, karma or antimatter. No device or external system is altered.',
            'inputs':{'care':care,'restraint':restraint,'repair':repair,'pressure':pressure,'steps':steps},
            'equations':['interrupted = unresolved × restraint × 0.2',
                         'repaired = (unresolved − interrupted) × care × repair × 0.15',
                         'unresolved_next = unresolved − interrupted − repaired'],
            'trajectory':trace,'restored':protected,'unresolved':unresolved,
            'conservation_error':abs(pressure-protected-unresolved),
            'routing_features':[care,restraint,repair,pressure],
            'counterfactual_without_care_or_restraint':{'unresolved':pressure,'restored':0.},
            'review_prompt':'What concrete act of protection or repair follows this reflection?'}
