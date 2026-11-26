"""Launch one desktop and one shared runtime. No nested application processes."""
import argparse,json,os,sys,threading,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'runtime'))
sys.path.insert(0,str(ROOT/'vendor-java'))
temporary=ROOT/'data'/'temp';temporary.mkdir(parents=True,exist_ok=True)
os.environ['TEMP']=str(temporary);os.environ['TMP']=str(temporary)
import tempfile
tempfile.tempdir=str(temporary)
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1')

def existing_service_url(port, attempts=12):
    """Only attach to a responding Neural App on this computer."""
    from urllib.request import urlopen
    url='http://127.0.0.1:'+str(port)
    for attempt in range(attempts):
        try:
            with urlopen(url,timeout=.75) as response:
                page=response.read(131072).decode('utf-8')
            if 'NEURAL_TOKEN' in page and 'Neural App' in page:return url
        except (OSError,ValueError):pass
        if attempt+1<attempts:time.sleep(.25)
    return None

def open_desktop_window(url, connected=False):
    """A second launch is a client window, never another state-writing runtime."""
    import webview
    files=DesktopFiles()
    window=webview.create_window('Neural App · Integrated Neural Studio',url,width=1520,height=980,min_size=(1060,700),background_color='#080d16',js_api=files)
    files._window=window
    profile='desktop-client-profile' if connected else 'desktop-profile'
    webview.start(gui='edgechromium',private_mode=False,storage_path=str(ROOT/'data'/profile),icon=str(ROOT/'nexus.ico'))

class DesktopFiles:
    def __init__(self):self._window=None
    def select_file(self,mode='open'):
        import webview
        if mode not in ('open','save','folder'):raise ValueError('Unknown file selection')
        kind={'open':webview.FileDialog.OPEN,'save':webview.FileDialog.SAVE,'folder':webview.FileDialog.FOLDER}[mode]
        result=self._window.create_file_dialog(kind,directory=str(ROOT/'data'),save_filename='neural-export.json' if mode=='save' else '')
        return result[0] if result else None

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--headless',action='store_true');parser.add_argument('--port',type=int,default=8797);parser.add_argument('--bus-port',type=int,default=None);parser.add_argument('--discovery-port',type=int,default=8799);parser.add_argument('--lan',action='store_true');args=parser.parse_args()
    if args.bus_port is None:
        try:args.bus_port=int(json.loads((ROOT/'data'/'engine-control-transport.json').read_text(encoding='utf-8')).get('tcp_port',8798))
        except (OSError,ValueError,TypeError):args.bus_port=8798
        if not 1024<=args.bus_port<=65535 or args.bus_port in (args.port,args.discovery_port,11434):args.bus_port=8798
    # Only one owner may write the app state at a time, including headless mode.
    lockfile=ROOT/'data'/'instance.lock';lockfile.parent.mkdir(exist_ok=True);lock=lockfile.open('a+b')
    if os.name=='nt':
        import msvcrt
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:
            lock.close()
            url=existing_service_url(args.port)
            if not url:raise RuntimeError('Another Neural App instance holds the data lock, but its local service is not responding. Wait for it to finish starting, or close its existing window and try again.')
            if args.headless:print(json.dumps({'url':url,'already_running':True}),flush=True)
            else:open_desktop_window(url,connected=True)
            return
    from neural_app.runtime import Runtime
    from neural_app.network import Bus
    from neural_app.server import create_server
    runtime=Runtime();bus=server=None
    def close():
        if server:server.shutdown();server.server_close()
        if bus:bus.close()
        runtime.close()
    try:
        from neural_app.java_components import bridge
        bridge()  # Initialize the single embedded JVM on the desktop owner thread.
        if not hasattr(runtime,'component_host'):
            from neural_app.component_host import ComponentHost
            ComponentHost(runtime)
        bus=Bus(runtime,args.bus_port,args.discovery_port,args.lan);server=create_server(runtime,args.port,bus)
        thread=threading.Thread(target=server.serve_forever,name='neural-local-http',daemon=True);thread.start()
        url='http://127.0.0.1:'+str(server.server_address[1])
        (ROOT/'data'/'connection.json').write_text(json.dumps({'app':'Neural App','url':url,**bus.info()}),encoding='utf8')
        runtime.opera_workspace.on_start(url)
        atlas_settings=ROOT/'data'/'source-atlas-settings.json'
        try:
            atlas_config=json.loads(atlas_settings.read_text(encoding='utf-8-sig')) if atlas_settings.exists() else {}
        except (OSError,ValueError):
            atlas_config={}  # A damaged optional preference must not prevent the desktop opening.
        if isinstance(atlas_config,dict) and atlas_config.get('continuous') is True:runtime.source_atlas().configure_continuous(True)
        if args.headless:
            print(json.dumps({'url':url,'bus':bus.info()}),flush=True)
            try:
                while not runtime.halt.wait(1):pass
            except KeyboardInterrupt:pass
        else:
            open_desktop_window(url)
    finally:close();lock.close()

if __name__=='__main__':
    try:main()
    except Exception:
        (ROOT/'data').mkdir(exist_ok=True);(ROOT/'data'/'desktop-error.log').write_text(traceback.format_exc(),encoding='utf8')
        if '--headless' in sys.argv:raise
        import ctypes
        ctypes.windll.user32.MessageBoxW(0,'Neural App could not open.\n\n'+str(sys.exception())[:600]+'\n\nDetails: data/desktop-error.log','Neural App',16)
