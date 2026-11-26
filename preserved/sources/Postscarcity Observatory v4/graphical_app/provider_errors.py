"""Readable, redacted provider errors; never treat HTML 403 as a confirmed key error."""
import html
import json
import re

def provider_error(code,raw,reason,provider,headers=None):
    text=raw.decode('utf-8',errors='replace')
    try:
        body=json.loads(text);error=body.get('error',{})
        detail=error.get('message',str(error)) if isinstance(error,dict) else str(error)
        status=error.get('status','') if isinstance(error,dict) else ''
        reasons=' '.join(str(d.get('reason','')) for d in error.get('details',[]) if isinstance(d,dict)) if isinstance(error,dict) else ''
        structured=True
    except (ValueError,AttributeError):
        detail=' '.join(html.unescape(re.sub('<[^>]+>',' ',text)).split())[:400] or str(reason)
        status=reasons='';structured=False
    for key,value in (headers or {}).items():
        if key.lower() in ('authorization','x-goog-api-key','x-api-key') and value:
            detail=detail.replace(value,'[redacted]').replace(value.removeprefix('Bearer '),'[redacted]')
    detail=re.sub(r'\b(?:AIza[\w-]+|sk-(?:proj-)?[\w-]+)','[redacted]',detail)
    clue=(detail+' '+reasons).lower();help_text=''
    if provider=='Gemini':
        if code==403 and not structured:help_text='Google returned a non-JSON denial. Check the VPN/network route; this response alone does not identify an API-key permission problem.'
        elif 'referer' in clue or 'referrer' in clue:help_text='This server-side app needs an API key whose application restrictions allow server requests; a browser-referrer restriction will not match.'
        elif 'ip_address' in clue or 'ip address' in clue:help_text='The key has an IP restriction. Check its allowed server/VPN exit address in Google Cloud.'
        elif 'service_disabled' in clue or 'has not been used' in clue:help_text='Enable the Generative Language API for this key’s Google Cloud project.'
        elif 'leaked' in clue or 'unrestricted' in clue or 'expired' in clue:help_text='Create a current restricted Gemini API key in Google AI Studio and save it in this panel.'
        elif code in (401,403):help_text='Check the Gemini API key, its API restrictions and project permissions in Google AI Studio. The model name alone cannot grant access.'
        elif code==404:help_text='Check the model name. Use the Gemini API model ID, optionally prefixed with models/.'
    return f'{provider} HTTP {code}'+(f' ({status})' if status else '')+': '+detail[:1500]+(' '+help_text if help_text else '')
