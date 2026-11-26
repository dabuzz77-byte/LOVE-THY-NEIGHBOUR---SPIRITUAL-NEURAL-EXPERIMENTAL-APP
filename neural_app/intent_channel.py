"""Prayer-led reflection with an inspectable software event, not hardware control."""
import json, hashlib
from pathlib import Path
from .matter_spirit import process as reflect
from .gnostic_four import decide
from .translation import translate_bits

ROOT=Path(__file__).resolve().parents[1]
def catalogue():
    return json.loads((ROOT/'references/intent-channel.json').read_text(encoding='utf-8'))

def process(body):
    intention=body.get('intention','Let this intention serve care, peace and daily bread.')
    if not isinstance(intention,str) or not 1<=len(intention.encode('utf-8'))<=480:
        raise ValueError('Use an intention of 1–480 UTF-8 bytes')
    openness=body.get('open',True)
    if type(openness) is not bool:raise ValueError('Open must be boolean')
    value=reflect({'lesson':'overview',**body},catalogue())
    decision=decide(body)
    value['channel']={'intention':intention,'open':openness,
        'stages':['receive declared intention','recall prayer orientation','evaluate caring proposals','record shared learning','return inspectable result'],
        'state':'LOCAL_REFLECTION_RECORDED' if openness else 'PAUSED',
        'intention_sha256':hashlib.sha256(intention.encode('utf-8')).hexdigest(),
        'software_bits':translate_bits(('1' if openness else '0')+decision['selection_bits']),
        'decision':decision,'hardware_connection':'not configured','physical_measurements':[],
        'external_delivery':False,
        'scope':'Authored spiritual interpretation and actual local computation. No remote physical effect or device connection is reported by this event.'}
    return value
