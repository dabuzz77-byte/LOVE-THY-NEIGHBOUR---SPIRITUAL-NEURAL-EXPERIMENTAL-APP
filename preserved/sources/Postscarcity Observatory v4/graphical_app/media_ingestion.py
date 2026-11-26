"""Background public-audio retrieval. No playback, cookies or access bypasses."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np

APP=Path(__file__).resolve().parent


def retrieve_audio(rt,vid,folder,cancelled):
    if not rt.privacy.ready():raise ValueError('Public web access is paused')
    folder.mkdir(parents=True,exist_ok=True)
    used=sum(p.stat().st_size for p in folder.parent.rglob('*') if p.is_file())
    if used>450*1024*1024:raise ValueError('Research media storage reached 450 MB. Archive old media before retrieving more audio.')
    request={'video':vid,'folder':str(folder.resolve()),'privacy':rt.privacy.view()}
    process=subprocess.Popen([sys.executable,str(APP/'media_ingestion.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             text=True,encoding='utf-8',cwd=APP,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    started=time.monotonic();payload=json.dumps(request)
    while True:
        try:
            output,errors=process.communicate(payload,timeout=.5);break
        except subprocess.TimeoutExpired:
            payload=None
            if cancelled() or rt.stop.is_set() or not rt.privacy.ready() or time.monotonic()-started>120:
                process.kill();process.communicate();raise ValueError('Audio retrieval stopped or exceeded two minutes')
    if process.returncode:raise ValueError('Audio retrieval failed: '+errors[-500:])
    result=json.loads(output)
    if not result.get('ok'):raise ValueError(result.get('error','Audio unavailable'))
    path=(folder/'audio.wav').resolve()
    if not path.is_relative_to(folder.resolve()) or not path.is_file():raise ValueError('No decoded audio was produced')
    from spectrum_inspector import decode_pcm
    raw=path.read_bytes();data,rate=decode_pcm(raw);samples=data[:,0]
    size=min(32768,len(samples));window=np.hanning(size);f=np.fft.rfftfreq(size,1/rate)
    spectra=[];frames=[]
    for start in np.linspace(0,max(0,len(samples)-size),min(48,max(1,len(samples)//size))).astype(int):
        frame=samples[start:start+size];power=np.abs(np.fft.rfft(frame*window))**2;spectra.append(power)
        frames.append({'seconds':round(start/rate,3),'rms':float(np.sqrt(np.mean(frame**2))),
                       'dominant_hz':float(f[np.argmax(power[1:])+1]) if np.any(power[1:]) else None,
                       'near_full_scale_fraction':float(np.mean(np.abs(frame)>=.999))})
    mean=np.mean(spectra,axis=0);energy=max(float(mean.sum()),1e-30)
    summary={'status':'measured','basis':'downloaded public audio, mono PCM conversion','sha256':hashlib.sha256(raw).hexdigest(),
             'duration':len(samples)/rate,'sample_rate':rate,'peak':float(np.max(np.abs(samples))),
             'rms':float(np.sqrt(np.mean(samples**2))),'near_full_scale_fraction':float(np.mean(np.abs(samples)>=.999)),
             'spectral_centroid_hz':float(np.sum(f*mean)/energy),'sampled_windows':len(frames),
             'band_power':{name:float(mean[(f>=low)&(f<high)].sum()/energy) for name,low,high in [('low',0,250),('mid',250,2000),('high',2000,rate/2+1)]},
             'time_sweep':frames,'no_playback':True,'visual_frames_analyzed':0,
             'scope':'Audio measurements do not establish emotion, intention, moral status, physical exposure or damage.'}
    (folder/'waveform.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    for offset in range(0,len(raw),65536):
        if cancelled() or rt.stop.is_set():break
        # Avoid blocking inference on a paused/full bus; expose accepted/rejected bytes.
        accepted=rt.binary_bus.feed('youtube-audio:'+vid,raw[offset:offset+65536])
        summary['bus_accepted_bytes' if accepted else 'bus_rejected_bytes']=summary.get('bus_accepted_bytes' if accepted else 'bus_rejected_bytes',0)+len(raw[offset:offset+65536])
    rt.binary_bus.feed('youtube-waveform:'+vid,summary)
    return summary


def worker(request):
    sys.path.insert(0,str(APP/'vendor'))
    from privacy_network import install_worker
    install_worker(request['privacy'])
    import yt_dlp
    import imageio_ffmpeg
    from spiritual_research import video_id
    vid=video_id(request['video']);folder=Path(request['folder']).resolve();folder.mkdir(parents=True,exist_ok=True)
    class Quiet:
        def debug(self,*a):pass
        def warning(self,*a):pass
        def error(self,*a):pass
    def progress(item):
        if item.get('downloaded_bytes',0)>24*1024*1024:raise ValueError('Public audio exceeds 24 MB limit')
    options={'quiet':True,'no_warnings':True,'logger':Quiet(),'noplaylist':True,'cachedir':False,'socket_timeout':20,'retries':0,
             'fragment_retries':0,'max_filesize':24*1024*1024,'outtmpl':str(folder/'source.%(ext)s'),
             'format':'bestaudio[ext=m4a]/bestaudio/best','progress_hooks':[progress],
             'js_runtimes':{},'remote_components':set()}
    with yt_dlp.YoutubeDL(options) as downloader:
        info=downloader.extract_info('https://www.youtube.com/watch?v='+vid,download=False)
        if info.get('is_live') or not info.get('duration') or info['duration']>300:raise ValueError('Audio analysis supports public clips up to five minutes; use a shorter clip or supplied WAV')
        if info.get('has_drm'):raise ValueError('Protected media is unavailable')
        downloader.process_info(info)
        source=Path(downloader.prepare_filename(info)).resolve()
    if not source.is_relative_to(folder) or not source.is_file() or source.stat().st_size>24*1024*1024:raise ValueError('No bounded public audio file was downloaded')
    result=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-v','error','-y','-i',str(source),'-vn','-t','300','-ar','24000','-ac','1','-c:a','pcm_s16le',str(folder/'audio.wav')],
                          capture_output=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:raise ValueError('Audio decoder could not read the downloaded stream')
    return {'ok':True,'title':info.get('title'),'duration':info['duration']}


if __name__=='__main__':
    try:print(json.dumps(worker(json.load(sys.stdin))))
    except Exception as exc:print(json.dumps({'ok':False,'error':str(exc)[:800]}))
