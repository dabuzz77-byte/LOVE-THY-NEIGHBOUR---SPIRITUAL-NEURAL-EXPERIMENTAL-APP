"""Decode the two legacy mono WAVE ADPCM formats in the BuddhaNet samples.
RIFF / Microsoft ADPCM and DVI IMA ADPCM block layout; output PCM16 WAVE.
No external executable, recording synthesis or sample-rate change.
"""
import io,struct,wave
STEPS=(7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552,1707,1878,2066,2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,15289,16818,18500,20350,22385,24623,27086,29794,32767)
INDEX=(-1,-1,-1,-1,2,4,6,8,-1,-1,-1,-1,2,4,6,8)
ADAPT=(230,230,230,230,307,409,512,614,768,614,512,409,307,230,230,230)
def clamp(v):return max(-32768,min(32767,v))
def browser_wav(raw):
 if raw[:4]!=b'RIFF' or raw[8:12]!=b'WAVE':return raw
 chunks={};pos=12
 while pos+8<=len(raw):
  name=raw[pos:pos+4];size=struct.unpack_from('<I',raw,pos+4)[0]
  if pos+8+size>len(raw):raise ValueError('Truncated WAVE chunk')
  chunks[name]=raw[pos+8:pos+8+size];pos+=8+size+(size&1)
 fmt=chunks.get(b'fmt ',b'');data=chunks.get(b'data',b'')
 if len(fmt)<16:raise ValueError('Missing WAVE format')
 tag,channels,rate,_,align,bits=struct.unpack_from('<HHIIHH',fmt)
 if tag not in (2,17):return raw
 if channels!=1 or bits!=4 or align<8 or len(fmt)<20:raise ValueError('Only mono 4-bit ADPCM recordings are supported')
 samples_per_block=struct.unpack_from('<H',fmt,18)[0]
 coefficients=[]
 if tag==2:
  if len(fmt)<22:raise ValueError('Missing ADPCM coefficients')
  count=struct.unpack_from('<H',fmt,20)[0]
  if not 1<=count<=32 or len(fmt)<22+count*4:raise ValueError('Invalid coefficient count')
  coefficients=[struct.unpack_from('<hh',fmt,22+i*4) for i in range(count)]
 decoded=[]
 for start in range(0,len(data),align):
  block=data[start:start+align];out=[]
  if tag==17:
   if len(block)<4:continue
   predictor,index=struct.unpack_from('<hB',block);index=max(0,min(88,index));out=[predictor]
   for byte in block[4:]:
    for nibble in (byte&15,byte>>4):
     step=STEPS[index];delta=step>>3
     if nibble&1:delta+=step>>2
     if nibble&2:delta+=step>>1
     if nibble&4:delta+=step
     predictor=clamp(predictor+(-delta if nibble&8 else delta));index=max(0,min(88,index+INDEX[nibble]));out.append(predictor)
  else:
   if len(block)<7:continue
   pred=block[0]
   if pred>=len(coefficients):raise ValueError('Invalid ADPCM predictor')
   delta,s1,s2=struct.unpack_from('<hhh',block,1);delta=max(16,delta);c1,c2=coefficients[pred];out=[s2,s1]
   for byte in block[7:]:
    for nibble in (byte>>4,byte&15):
     signed=nibble-16 if nibble&8 else nibble
     sample=clamp(int((s1*c1+s2*c2)/256)+signed*delta);s2,s1=s1,sample;delta=max(16,ADAPT[nibble]*delta//256);out.append(sample)
  decoded.extend(out[:samples_per_block])
 if b'fact' in chunks and len(chunks[b'fact'])>=4:decoded=decoded[:struct.unpack_from('<I',chunks[b'fact'])[0]]
 if not decoded:raise ValueError('No decoded samples')
 output=io.BytesIO()
 with wave.open(output,'wb') as wav:
  wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes(struct.pack('<'+'h'*len(decoded),*decoded))
 return output.getvalue()
