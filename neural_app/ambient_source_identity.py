"""Bounded stable learner identity without truncation collisions."""
import hashlib

def source_key(value):
 value=str(value)
 return value if len(value)<=100 else value[:75]+'/'+hashlib.sha256(value.encode('utf-8',errors='replace')).hexdigest()[:24]
