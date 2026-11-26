"""Bind optional language-proposed transformations to actual current user data."""
import hashlib,json

def execute(request,proposal):
 if not isinstance(proposal,str) or len(proposal)>16000:raise ValueError('Use a compact proposed workflow')
 body=json.loads(proposal)
 if not isinstance(body,dict) or set(body)!={'steps'}:raise ValueError('A language workflow may contain only transformation steps; its input must come from the current request')
 instruction,separator,data=request.partition(':')
 if not separator or not data.strip():return {'status':'needs-input','question':'Please supply the data after a colon so the proposed transformation can use your actual input.','executed':False}
 try:value=json.loads(data)
 except ValueError:value=data.lstrip(' \r\n')
 from .reasoning_engine import pipeline
 result=pipeline(value,body['steps'])
 return {**result,'status':'complete','input_sha256':hashlib.sha256(data.encode()).hexdigest(),'input_source':'data supplied in the current request','interpretation':'language-proposed transformations; inspect the steps to confirm the intended meaning','interpretation_verified':False}
