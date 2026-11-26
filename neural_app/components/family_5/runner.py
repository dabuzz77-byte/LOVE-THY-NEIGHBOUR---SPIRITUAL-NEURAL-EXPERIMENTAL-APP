import sys
import json
import pathlib
from neural_app import capture_output as contextlib
import io
import typing
import os
import hmac
import hashlib
import time
import uuid
import math
import base64
import secrets
import collections
import random
from typing import *
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
ROOT = pathlib.Path(__file__).resolve().parent

def encode(x):
    if isinstance(x, bytes):
        return {'hex': x.hex(), 'encoding': 'bytes'}
    if isinstance(x, set):
        return sorted(x)
    return str(x)

def decode(x):
    if isinstance(x, dict) and set(x) == {'$bytes'}:
        return bytes.fromhex(x['$bytes'])
    if isinstance(x, dict) and set(x) == {'$set'}:
        return set(x['$set'])
    if isinstance(x, dict):
        return {k: decode(v) for k, v in x.items()}
    if isinstance(x, list):
        return [decode(v) for v in x]
    return x
