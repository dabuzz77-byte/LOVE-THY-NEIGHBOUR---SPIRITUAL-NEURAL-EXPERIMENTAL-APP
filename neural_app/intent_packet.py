"""Explicit compact intent preparation; no semantic claims or silent truncation."""
import hashlib


def prepare_intent(text):
    if not isinstance(text, str):raise ValueError('Intent must be text')
    compact=' '.join(text.split())
    raw=compact.encode('utf-8')
    if not 1 <= len(raw) <= 512:raise ValueError('Edit your intent to 1–512 UTF-8 bytes')
    return {'format':'neural-intent-v1','text':compact,'bytes':len(raw),
            'sha256':hashlib.sha256(raw).hexdigest(),
            'method':'Whitespace normalization only; meaning is reviewed by the sender, not automatically certified.'}
