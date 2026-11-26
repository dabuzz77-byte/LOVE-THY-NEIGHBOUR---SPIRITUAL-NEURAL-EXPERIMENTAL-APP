"""Actual PCM spectra, time sweeps and isolated-band WAV output."""
import hashlib
import io
import json
import math
import threading
import wave
import numpy as np
from sources import now,save_json

THEORY_SOURCES=[
    ('Cymatics history · practitioner account','https://cymascope.com/cymatics-history/'),
    ('Chladni plates · Smithsonian','https://amhistory.si.edu/science/chladni.htm'),
    ('Sound interference and resonance · OpenStax','https://openstax.org/books/physics/pages/14-4-sound-interference-and-resonance'),
    ('Fourier analysis · SciPy','https://docs.scipy.org/doc/scipy/tutorial/fft.html')]
SEARCH_TERMS=['Hans Jenny cymatics wave phenomena','Chladni figures nodal lines boundary conditions',
              'cymatics standing waves resonance amplitude material geometry','Faraday waves liquid surface vibration',
              'cymatics spiritual interpretation evidence','constructive destructive interference phase sound']


def decode_pcm(raw):
    with wave.open(io.BytesIO(raw),'rb') as stream:
        width=stream.getsampwidth();channels=stream.getnchannels();rate=stream.getframerate();frames=stream.getnframes();pcm=stream.readframes(frames)
    if len(pcm)!=frames*width*channels:raise ValueError('Truncated WAV')
    if width==1:values=(np.frombuffer(pcm,np.uint8).astype(float)-128)/128
    elif width in (2,4):values=np.frombuffer(pcm,'<i'+str(width)).astype(float)/(2**(width*8-1))
    elif width==3:
        values=np.frombuffer(pcm,np.uint8).reshape(-1,3).astype(np.int32)
        values=values[:,0]|values[:,1]<<8|values[:,2]<<16
        values=np.where(values & 0x800000,values-0x1000000,values)/8388608
    else:raise ValueError('PCM bit width is unsupported')
    return values.reshape(-1,channels),rate


class SpectrumInspector:
    def __init__(self,rt):
        self.rt=rt;self.lock=threading.RLock();self.last=None;self.audio=None
        self.folder=rt.data/'work'/'spectrum';self.folder.mkdir(parents=True,exist_ok=True)

    def view(self):
        with self.lock:return {'last':self.last,'sources':THEORY_SOURCES,'search_terms':SEARCH_TERMS,
                              'wav':self.rt.v3.wav.view(),'scope':'PCM measurements and user annotations; no moral classification from frequency.'}

    def inspect(self,body):
        with self.rt.v3.wav.lock:raw=getattr(self.rt.v3.wav,'raw',None);meta=dict(self.rt.v3.wav.meta)
        if not raw:raise ValueError('Insert a PCM WAV first')
        size=body.get('size',32768);start=body.get('start',0);channel=body.get('channel',0);low=body.get('low',0);high=body.get('high',2000)
        if size not in (4096,16384,32768,65536):raise ValueError('Choose a supported FFT window')
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in (start,low,high)) or start<0 or not 0<=low<high<=meta['sample_rate']/2:
            raise ValueError('Use a nonnegative position and a band inside the file’s Nyquist frequency')
        if type(channel) is not int or not 0<=channel<meta['channels']:raise ValueError('Choose an available channel')
        annotation=body.get('annotation','unclassified');notes=body.get('notes','')
        if annotation not in ('unclassified','creative','destructive') or not isinstance(notes,str) or len(notes)>1000:raise ValueError('Invalid annotation')
        data,rate=decode_pcm(raw);samples=data[:,channel];offset=int(start*rate)
        if offset>=len(samples):raise ValueError('Position is beyond the audio duration')
        segment=samples[offset:offset+size];actual=len(segment);n=min(size,actual)
        if n<32:raise ValueError('Choose a position with at least 32 remaining samples')
        window=np.hanning(n);frequency=np.fft.rfftfreq(n,1/rate);transformed=np.fft.rfft(segment*window)
        amplitude=np.abs(transformed)*2/max(window.sum(),1);amplitude[0]/=2
        if n%2==0:amplitude[-1]/=2
        db=20*np.log10(np.maximum(amplitude,1e-9));mask=(frequency>=low)&(frequency<=high)
        if not np.any(mask):raise ValueError('Selected band contains no FFT bin at this resolution')
        raw_fft=np.fft.rfft(segment);isolated=np.fft.irfft(raw_fft*mask,n=n)
        clipped=float(np.mean(np.abs(segment)>=.999));peak=float(np.max(np.abs(segment)));rms=float(np.sqrt(np.mean(segment**2)))
        power=np.abs(transformed)**2
        selected=float(power[mask].sum()/max(power.sum(),1e-30))
        peaks=np.argsort(amplitude[1:])[-8:][::-1]+1 if len(amplitude)>1 else np.array([0])
        # Aggregate display bins by peak; measurement and selected-band sum use every bin.
        groups=np.array_split(np.arange(len(frequency)),min(1024,len(frequency)))
        display=[int(group[np.argmax(amplitude[group])]) for group in groups]
        points=np.linspace(0,n-1,min(n,1024)).astype(int)
        sweep=[]
        for position in np.linspace(0,max(0,len(samples)-size),min(64,max(1,math.ceil(len(samples)/size)))).astype(int):
            frame=samples[position:position+size];w=np.hanning(len(frame));spec=np.abs(np.fft.rfft(frame*w))**2;f=np.fft.rfftfreq(len(frame),1/rate);band=(f>=low)&(f<=high)
            sweep.append({'seconds':round(position/rate,4),'band_fraction':float(spec[band].sum()/max(spec.sum(),1e-30)),
                          'peak_hz':float(f[np.argmax(spec[1:])+1]) if len(spec)>1 and np.any(spec[1:]) else None,
                          'near_full_scale':float(np.mean(np.abs(frame)>=.999))})
        output=io.BytesIO()
        # Fixed attenuation only when the selected-band reconstruction exceeds digital range.
        attenuation=min(1,.98/max(float(np.max(np.abs(isolated))),1e-12))
        with wave.open(output,'wb') as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes((isolated*attenuation*32767).astype('<i2').tobytes())
        result={'time':now(),'file':meta['name'],'source_sha256':meta['sha256'],'sample_rate':rate,'channel':channel,
                'start':start,'seconds':n/rate,'samples':n,'resolution_hz':rate/n,'nyquist_hz':rate/2,'peak':peak,'rms':rms,
                'near_full_scale_fraction':clipped,'near_full_scale_threshold':.999,'clipping_proven':False,
                'band':[low,high],'band_power_fraction':selected,'frequencies':frequency[display].tolist(),'dbfs':db[display].tolist(),
                'waveform':segment[points].tolist(),'isolated_waveform':isolated[points].tolist(),
                'peaks':[{'hz':float(frequency[i]),'dbfs':float(db[i])} for i in peaks if amplitude[i]>1e-9],
                'sweep':sweep,'annotation':annotation,'annotation_basis':'user supplied, not measured morality','notes':notes,
                'isolation':'FFT bin mask of selected window; finite-window edge ringing may occur','playback_attenuation':attenuation,
                'scope':'Relative digital amplitude (dBFS); no calibrated sound pressure, physical damage or good/evil determination.'}
        with self.lock:
            self.last=result;self.audio=output.getvalue();save_json(self.folder/'latest.json',result)
            (self.folder/'isolated.wav').write_bytes(self.audio)
        self.rt.binary_bus.feed('spectrum-measurement',result)
        self.rt.binary_bus.feed('spectrum-isolated-audio',self.audio)
        return result

    def ingest_theory(self):
        existing={s.get('url'):s for s in self.rt.source_hub.view()};items=[]
        for title,url in THEORY_SOURCES:
            items.append(existing[url] if url in existing else self.rt.source_hub.add('website',title=title,url=url,automatic=True))
        return {'sources':[{'id':i['id'],'url':i['url'],'status':i['status']} for i in items],'search_terms':SEARCH_TERMS}
