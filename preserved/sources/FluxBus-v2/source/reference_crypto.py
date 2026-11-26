"""Local cryptographic operations. Private keys never enter engine snapshots.
Docs: https://cryptography.io/en/latest/fernet/ and its Ed25519 documentation.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from cryptography.fernet import Fernet
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf8')


def derive_skeleton_key(master_password: str, salt: bytes) -> bytes:
    """The supplied PBKDF2 function, with the base64 encoding Fernet requires."""
    if not isinstance(master_password, str) or not master_password: raise ValueError('Passphrase is empty')
    if not isinstance(salt, bytes) or len(salt) < 16: raise ValueError('Salt needs at least 16 bytes')
    return base64.urlsafe_b64encode(hashlib.pbkdf2_hmac('sha256', master_password.encode(), salt, 600_000, 32))


class KeyDerivationEngine:
    def verify_round_trip(self, text='A local message'):
        salt=secrets.token_bytes(16);password=secrets.token_urlsafe(32)
        cipher=Fernet(derive_skeleton_key(password,salt));encrypted=cipher.encrypt(text.encode('utf8'))
        return {'status':'COMPLETE','algorithm':'PBKDF2-HMAC-SHA256 + Fernet','iterations':600_000,
                'salt_hex':salt.hex(),'key_bytes':32,'ciphertext':encrypted.decode(),
                'verified':cipher.decrypt(encrypted).decode()==text,
                'basis':'Local round-trip verification with a temporary secret; not a saved encrypted vault.'}


class InferenceMeshNode:
    def __init__(self, node_id='local-reference-node'):
        self.node_id=node_id;self._private_key=Ed25519PrivateKey.generate();self._seen=set()

    def get_public_bytes(self): return self._private_key.public_key().public_bytes_raw()

    def sign_inference_payload(self, workload_hash):
        if isinstance(workload_hash,bytes): workload_hash=workload_hash.hex()
        packet={'node_id':self.node_id,'workload_hash':str(workload_hash),'timestamp':time.time(),'nonce':uuid.uuid4().hex}
        return {'packet':packet,'signature':self._private_key.sign(canonical(packet)).hex(),'public_key':self.get_public_bytes().hex()}

    def verify_inference_payload(self,envelope,expected_workload_hash=None,max_age=300):
        try:
            packet=envelope['packet']
            if envelope['public_key']!=self.get_public_bytes().hex(): return False
            Ed25519PublicKey.from_public_bytes(bytes.fromhex(envelope['public_key'])).verify(bytes.fromhex(envelope['signature']),canonical(packet))
            if packet['node_id']!=self.node_id or not 0<=time.time()-packet['timestamp']<=max_age:return False
            if expected_workload_hash is not None and packet['workload_hash']!=str(expected_workload_hash):return False
            if packet['nonce'] in self._seen:return False
            self._seen.add(packet['nonce']);return True
        except (KeyError,ValueError,TypeError,InvalidSignature):return False

    def verify_round_trip(self,text='A signed workload'):
        digest=hashlib.sha256(text.encode()).hexdigest();envelope=self.sign_inference_payload(digest)
        valid=self.verify_inference_payload(envelope,digest)
        return {'status':'COMPLETE','algorithm':'Ed25519','verified':valid,
                'replay_rejected':not self.verify_inference_payload(envelope,digest),'envelope':envelope}


class MeshPrivilegeVerifier:
    def __init__(self,cluster_secret=None):self._secret=cluster_secret or secrets.token_bytes(32);self.revoked_tokens=set()

    def issue_capability_token(self,node_id,capabilities,ttl_seconds=300):
        if ttl_seconds<=0:raise ValueError('Token lifetime must be positive')
        payload={'node':node_id,'caps':sorted(set(capabilities)),'exp':time.time()+ttl_seconds,'nonce':uuid.uuid4().hex}
        raw=base64.urlsafe_b64encode(canonical(payload)).decode()
        return raw+'.'+hmac.new(self._secret,raw.encode(),hashlib.sha256).hexdigest()

    def verify_node_privilege(self,token,expected_node_id,required_capability):
        try:
            if token in self.revoked_tokens:return False
            raw,signature=token.split('.')
            if not hmac.compare_digest(signature,hmac.new(self._secret,raw.encode(),hashlib.sha256).hexdigest()):return False
            p=json.loads(base64.urlsafe_b64decode(raw))
            return p['node']==expected_node_id and p['exp']>time.time() and required_capability in p['caps']
        except (TypeError,ValueError,KeyError):return False

    def revoke(self,token):self.revoked_tokens.add(token);return {'revoked':True}

    def verify_round_trip(self,node_id='local-worker',capability='layer_forward_pass'):
        token=self.issue_capability_token(node_id,[capability]);valid=self.verify_node_privilege(token,node_id,capability)
        wrong=not self.verify_node_privilege(token,node_id+'-other',capability);self.revoke(token)
        return {'status':'COMPLETE','verified':valid,'wrong_node_rejected':wrong,
                'revocation_verified':not self.verify_node_privilege(token,node_id,capability)}


class ClassicalCipherEngine:
    def transform(self,text,shift=3,keyword='',decrypt=False):
        key=[ord(c.upper())-65 for c in keyword if c.isascii() and c.isalpha()]
        if keyword and not key:raise ValueError('Keyword needs ASCII letters')
        output=[];position=0
        for char in text:
            if char.isascii() and char.isalpha():
                offset=key[position%len(key)] if key else int(shift);base=65 if char.isupper() else 97
                output.append(chr(base+(ord(char)-base+(-offset if decrypt else offset))%26));position+=1
            else:output.append(char)
        return {'status':'COMPLETE','output':''.join(output),'letters':position,'algorithm':'Vigenere' if key else 'Caesar',
                'basis':'Classical text transformation; not secure encryption.'}


class FernetEnvelopeEngine:
    def verify_round_trip(self,text='A local encrypted message'):
        cipher=Fernet(Fernet.generate_key());token=cipher.encrypt(text.encode('utf8'))
        return {'status':'COMPLETE','algorithm':'Fernet','ciphertext':token.decode(),'verified':cipher.decrypt(token).decode()==text,
                'plaintext_bytes':len(text.encode()),'basis':'Local authenticated-encryption round trip; temporary key is discarded.'}
