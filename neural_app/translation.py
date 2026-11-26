"""Lossless shared transport; Fourier qutrits ported from the Beacon translator.

Qutrit states are classical complex amplitudes, not quantum hardware.
Values use bounded 256-byte blocks, retaining exact lengths and leading zeros.
"""
import hashlib, json, math

MAX_BYTES = 16384
BLOCK_BYTES = 256

def base3(value):
    if value == 0: return '0'
    out=[]
    while value:
        value,r=divmod(value,3);out.append(str(r))
    return ''.join(reversed(out))

def balanced(value):
    if value == 0:return '0'
    out=[]
    while value:
        value,r=divmod(value,3)
        if r==2:r=-1;value+=1
        out.append({-1:'-',0:'0',1:'+'}[r])
    return ''.join(reversed(out))

def fourier(trit):
    if type(trit) is not int or trit not in (0,1,2):raise ValueError('Trit must be 0, 1 or 2')
    return [{'real':math.cos(math.tau*trit*j/3)/math.sqrt(3),
             'imag':math.sin(math.tau*trit*j/3)/math.sqrt(3)} for j in range(3)]

def inverse_fourier(amplitudes):
    if not isinstance(amplitudes,list) or len(amplitudes)!=3:raise ValueError('Three amplitudes required')
    values=[complex(a['real'],a['imag']) for a in amplitudes]
    if not all(math.isfinite(z.real) and math.isfinite(z.imag) for z in values):raise ValueError('Nonfinite qutrit')
    norm=sum(abs(z)**2 for z in values)
    if not math.isclose(norm,1,abs_tol=1e-8):raise ValueError('Unnormalized qutrit')
    overlaps=[abs(sum(complex(a['real'],-a['imag'])*z for a,z in zip(fourier(k),values)))**2 for k in range(3)]
    k=max(range(3),key=overlaps.__getitem__)
    if overlaps[k]<1-1e-8:raise ValueError('Qutrit is not one of the encoded Fourier basis states')
    return k

def translate_bits(raw):
    if not isinstance(raw,str):raise ValueError('Binary input must be text')
    bits=''.join(c for c in raw if not c.isspace() and c!='_')
    if not bits or len(bits)>4096 or set(bits)-{'0','1'}:raise ValueError('Use 1–4096 binary digits')
    value=int(bits,2);ternary=base3(value)
    recovered=format(int(ternary,3),f'0{len(bits)}b')
    states=[{'index':i,'trit':int(t),'amplitudes':fourier(int(t)),'probabilities':[1/3]*3} for i,t in enumerate(ternary)]
    return dict(binary=bits,bit_width=len(bits),decimal=str(value),ternary=ternary,balanced_ternary=balanced(value),
                qutrits=states,recovered_binary=recovered,round_trip=bits==recovered,
                basis='Orthonormal Fourier states; trit identity is encoded in phase, not computational-basis probability.')

def encode(raw):
    if not isinstance(raw,bytes) or len(raw)>MAX_BYTES:raise ValueError('Use at most 16 KiB')
    blocks=[]
    for start in range(0,len(raw),BLOCK_BYTES):
        block=raw[start:start+BLOCK_BYTES];value=int.from_bytes(block,'big')
        blocks.append({'bytes':len(block),'ternary':base3(value),'balanced':balanced(value)})
    return {'format':'neural-btq-v1','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
            'blocks':blocks,'qutrit_basis':[fourier(i) for i in range(3)],'encoding':'Each ternary digit selects a Fourier basis state.'}

def decode(packet):
    if packet.get('format')!='neural-btq-v1':raise ValueError('Unknown transport')
    size=packet.get('bytes')
    if type(size) is not int or not 0<=size<=MAX_BYTES:raise ValueError('Invalid byte count')
    blocks=packet.get('blocks')
    if not isinstance(blocks,list) or len(blocks)>math.ceil(MAX_BYTES/BLOCK_BYTES):raise ValueError('Invalid blocks')
    decoded=[]
    for i,b in enumerate(blocks):
        count=b.get('bytes');digits=b.get('ternary');bt=b.get('balanced')
        if type(count) is not int or not 1<=count<=BLOCK_BYTES or (i<len(blocks)-1 and count!=BLOCK_BYTES):raise ValueError('Invalid block length')
        if not isinstance(digits,str) or not 1<=len(digits)<=1300 or set(digits)-{'0','1','2'}:raise ValueError('Invalid ternary digits')
        n=int(digits,3)
        if bt!=balanced(n):raise ValueError('Balanced ternary mismatch')
        try:decoded.append(n.to_bytes(count,'big'))
        except OverflowError:raise ValueError('Value does not fit block')
    raw=b''.join(decoded)
    if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=packet.get('sha256'):raise ValueError('Transport integrity check failed')
    basis=packet.get('qutrit_basis')
    if not isinstance(basis,list) or [inverse_fourier(s) for s in basis]!=[0,1,2]:raise ValueError('Qutrit basis mismatch')
    return raw

def envelope(value):
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')
    packet=encode(raw)
    if decode(packet)!=raw:raise RuntimeError('Internal transport mismatch')
    return packet
