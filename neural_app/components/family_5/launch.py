import pathlib
import subprocess
import sys
import time
import urllib.request
import webbrowser
import os
root = pathlib.Path(__file__).resolve().parent
url = 'http://127.0.0.1:7865'

def alive():
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            return b'Inference Observatory' in r.read()
    except Exception:
        return False
if '--independent' in sys.argv and alive():
    import json
    with urllib.request.urlopen(url + '/api/session', timeout=3) as response:
        session_key = json.load(response)['key']
    request = urllib.request.Request(url + '/api/shutdown', data=b'{}', headers={'X-Observatory-Key': session_key, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=5) as response:
        response.read()
    for _ in range(40):
        if not alive():
            break
        time.sleep(0.25)
    if alive():
        raise SystemExit('Existing runtime did not stop; independent launch cancelled.')
if not alive():
    with (root / 'data/runtime.log').open('ab') as out, (root / 'data/runtime-errors.log').open('ab') as err:
        subprocess.Popen([sys.executable, str(root / 'server.py'), '--port', '7865'], cwd=root, stdout=out, stderr=err, creationflags=getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0), close_fds=True)
    for _ in range(25):
        if alive():
            break
        time.sleep(0.4)
if alive():
    if '--background' not in sys.argv:
        webbrowser.open(url + '/#federation')
else:
    raise SystemExit('Runtime did not respond. Read data/runtime-errors.log.')
