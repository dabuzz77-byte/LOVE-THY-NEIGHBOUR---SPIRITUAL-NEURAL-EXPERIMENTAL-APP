"""The humble cup: attributed scene study and shared reflection processing."""
import json
from pathlib import Path
from .matter_spirit import process as reflect

def catalogue():
    return json.loads((Path(__file__).resolve().parents[1]/'references'/'wooden-cup.json').read_text(encoding='utf-8'))

def process(body):
    value=reflect({'lesson':'purifier',**body},catalogue())
    value['model']='Symbolic care practice: interrupt status-seeking harm, practise restraint and repair.'
    value['scope']='Educational reflection and shared numerical learning; no score of a person’s spiritual worth.'
    return value
