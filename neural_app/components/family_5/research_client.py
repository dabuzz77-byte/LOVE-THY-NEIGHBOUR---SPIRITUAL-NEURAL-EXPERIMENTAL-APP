"""Local journal helper for the recurring, user-authorized Google AI Mode browser task."""
import argparse
import json
import pathlib
import urllib.request
BASE = 'http://127.0.0.1:7865'

def request(path, data=None):
    with urllib.request.urlopen(BASE + '/api/session', timeout=5) as r:
        key = json.load(r)['key']
    req = urllib.request.Request(BASE + '/api/' + path, data=json.dumps(data).encode() if data is not None else None, headers={'X-Observatory-Key': key, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)
