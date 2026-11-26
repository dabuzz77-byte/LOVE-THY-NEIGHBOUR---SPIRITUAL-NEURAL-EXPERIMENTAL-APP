import sys,json,pathlib,contextlib,io,typing,os,hmac,hashlib,time,uuid,math,base64,secrets,collections,random
from typing import *
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
ROOT=pathlib.Path(__file__).resolve().parent
# Only retained definitions selected by catalog ID can be executed by this runner.
def encode(x):
    if isinstance(x,bytes): return {'hex':x.hex(),'encoding':'bytes'}
    if isinstance(x,set): return sorted(x)
    return str(x)
def decode(x):
    if isinstance(x,dict) and set(x)=={'$bytes'}: return bytes.fromhex(x['$bytes'])
    if isinstance(x,dict) and set(x)=={'$set'}: return set(x['$set'])
    if isinstance(x,dict): return {k:decode(v) for k,v in x.items()}
    if isinstance(x,list): return [decode(v) for v in x]
    return x
if __name__=='__main__':
    req=json.load(sys.stdin); out=io.StringIO(); result=[]
    try:
        module=next(m for m in json.loads((ROOT/'catalog.json').read_text(encoding='utf8'))['modules'] if m['id']==req['id'])
        with contextlib.redirect_stdout(out):
            exec(compile(module['source'],f"manuscript:{module['line']}",'exec'),globals())
            target=globals()[module['name']]
            if module['kind']=='class':
                target=target(**decode(req.get('init',{})))
                for call in req.get('calls',[]):
                    if call['method'].startswith('_'): raise ValueError('Choose a public method')
                    result.append({'method':call['method'],'result':getattr(target,call['method'])(**decode(call.get('args',{})))})
                state={k:v for k,v in vars(target).items() if not any(s in k.lower() for s in ['secret','key','password'])}
            else: result=target(**decode(req.get('init',{}))); state={}
        print(json.dumps({'ok':True,'results':result,'state':state,'stdout':out.getvalue(),'basis':'Executed retained source; values describe local software state'},default=encode,allow_nan=False))
    except Exception as e: print(json.dumps({'ok':False,'error':f'{type(e).__name__}: {e}','results':result,'stdout':out.getvalue()},default=encode))
