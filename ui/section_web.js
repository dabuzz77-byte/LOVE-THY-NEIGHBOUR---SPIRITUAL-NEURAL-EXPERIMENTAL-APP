/* Built-in section lifecycle: scoped controls, local routing, shared API. No frames. */
export async function mountWebSection(host,id,token,bundle){
 const native=globalThis.window,root=host.attachShadow({mode:'open'}),lifecycle=new AbortController(),timers=[],intervals=[],frames=[],listeners=[],localWindow={},componentCleanups=[];
 let route='#overview';
 host.style.width='100%';host.style.minWidth='0';host.style.containerType='inline-size';
 const base='/api/components/'+encodeURIComponent(id);
 const location={get hash(){return route},set hash(value){route=value.startsWith('#')?value:'#'+value;listeners.filter(x=>x[0]==='hashchange').forEach(x=>x[1](new Event('hashchange')))},origin:native.location.origin,href:native.location.origin+base+'/',hostname:'127.0.0.1',port:native.location.port,protocol:'http:'};
 const history={state:null,replaceState(state,title,url){this.state=state;if(url!==undefined){const hash=String(url).split('#')[1];if(hash!==undefined)route='#'+hash}},pushState(state,title,url){this.replaceState(state,title,url)}};
 const bodyProxy=new Proxy(host,{get(target,key){if(key==='contains')return node=>root.contains(node)||target.contains(node);let value=target[key];return typeof value==='function'?value.bind(target):value},set(target,key,value){target[key]=value;return true}});
 const document=new Proxy(native.document,{get(target,key){
  if(key==='querySelector')return s=>root.querySelector(s);if(key==='querySelectorAll')return s=>root.querySelectorAll(s);if(key==='getElementById')return s=>root.getElementById(s);
  if(key==='body'||key==='documentElement')return bodyProxy;if(key==='activeElement')return root.activeElement||native.document.activeElement;if(key==='hidden')return native.document.hidden||!host.isConnected;
  if(key==='addEventListener')return (name,fn)=>{if(name==='DOMContentLoaded'){native.setTimeout(fn,0);return}root.addEventListener(name,fn,{signal:lifecycle.signal})};
  if(key==='title')return 'Neural App';let value=target[key];return typeof value==='function'?value.bind(target):value;
 },set(target,key,value){if(key==='title')return true;target[key]=value;return true}});
 function targetURL(value){let path=String(value);if(path.startsWith('http:')||path.startsWith('https:')||path.startsWith('data:')||path.startsWith('blob:'))return path;return base+'/'+path.replace(/^\//,'')}
 const fetch=async(url,options={})=>{const target=targetURL(url),local=new URL(target,native.location.href).origin===native.location.origin;const response=await native.fetch(target,{...options,headers:{...(options.headers||{}),...(local?{'X-Neural-Token':token}:{})},signal:options.signal||lifecycle.signal});if(local&&options.method==='POST'&&response.headers.get('Content-Type')?.includes('application/json')){response.clone().json().then(value=>{if(value.navigate&&host.isConnected)host.dispatchEvent(new CustomEvent('neural-section-navigate',{detail:{id:value.navigate},bubbles:true,composed:true}))}).catch(()=>{})}return response};
 const apiProxy=new Proxy({},{get:(target,method)=>(...args)=>fetch('/bridge/'+String(method),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({args})}).then(async r=>{let v=await r.json();if(!r.ok)throw Error(v.error||'Section operation failed');return v})});
 const window=new Proxy(native,{get(target,key){if(key in localWindow)return localWindow[key];if(key==='innerWidth')return host.clientWidth;if(key==='document')return document;if(key==='location')return location;if(key==='history')return history;if(key==='pywebview')return {api:apiProxy};if(key==='addEventListener')return (name,fn)=>{listeners.push([name,fn]);if(name==='hashchange')return;native.addEventListener(name,fn,{signal:lifecycle.signal})};if(key==='removeEventListener')return (name,fn)=>native.removeEventListener(name,fn);if(key==='scrollTo')return ()=>host.scrollIntoView({block:'start'});let value=target[key];return typeof value==='function'?value.bind(target):value},set(target,key,value){localWindow[key]=value;return true}});
 const setTimeout=(fn,ms,...args)=>{let value=native.setTimeout(()=>{if(host.isConnected&&!lifecycle.signal.aborted)fn(...args)},ms);timers.push(value);return value};
 const setInterval=(fn,ms,...args)=>{let value=native.setInterval(()=>{if(!native.document.hidden&&host.isConnected&&!lifecycle.signal.aborted)fn(...args)},Math.max(250,ms));intervals.push(value);return value};
 const clearTimeout=native.clearTimeout.bind(native),clearInterval=native.clearInterval.bind(native);
 let lastFrame=0;
 const requestAnimationFrame=fn=>{let value=native.requestAnimationFrame(ms=>{if(lifecycle.signal.aborted||!host.isConnected)return;if(native.document.hidden||ms-lastFrame<66){setTimeout(()=>requestAnimationFrame(fn),66);return}lastFrame=ms;fn(ms)});frames.push(value);if(frames.length>200)frames.splice(0,100);return value};
 const cancelAnimationFrame=native.cancelAnimationFrame.bind(native);
 class EventSource{
  constructor(url){this.listeners={};this.active=true;this.lastEventId='';this.controller=new AbortController();lifecycle.signal.addEventListener('abort',()=>this.close(),{once:true});this.run(url)}
  addEventListener(name,fn){(this.listeners[name]??=[]).push(fn)}
  close(){this.active=false;this.controller.abort()}
  async run(url){while(this.active&&!lifecycle.signal.aborted){try{let response=await fetch(url,{signal:this.controller.signal,headers:this.lastEventId?{'Last-Event-ID':this.lastEventId}:{}});if(!response.ok)throw Error('Section event connection failed');this.onopen?.({type:'open'});let reader=response.body.getReader(),decoder=new TextDecoder(),buffer='';while(this.active&&!lifecycle.signal.aborted){let chunk=await reader.read();if(chunk.done)break;buffer+=decoder.decode(chunk.value,{stream:true}).replace(/\r\n/g,'\n');let end;while((end=buffer.indexOf('\n\n'))>=0){let block=buffer.slice(0,end);buffer=buffer.slice(end+2);let type=block.match(/^event:\s*(.*)$/m)?.[1]||'message',data=block.split('\n').filter(line=>line.startsWith('data:')).map(line=>line.slice(5).replace(/^ /,'')).join('\n'),eventId=block.match(/^id:\s*(.*)$/m)?.[1];if(eventId!==undefined)this.lastEventId=eventId;if(data){let event={data,lastEventId:this.lastEventId};if(type==='message')this.onmessage?.(event);for(let fn of this.listeners[type]||[])fn(event)}}}await reader.cancel()}catch(error){if(this.active&&!lifecycle.signal.aborted)this.onerror?.(error)}if(this.active&&!lifecycle.signal.aborted)await new Promise(resolve=>native.setTimeout(resolve,1000));}}
 }

 root.innerHTML=bundle.html;
 // Keep the original controls, but give the drawing the full shared-page width.
 const sectionRail=root.querySelector('aside.sidebar,aside,nav.sidebar');
 if(sectionRail&&!sectionRail.querySelector('main')){
  const controls=native.document.createElement('details'),summary=native.document.createElement('summary');
  controls.className='neural-section-controls';summary.textContent='Section controls';
  sectionRail.before(controls);controls.append(summary,sectionRail);sectionRail.classList.add('neural-section-rail');
 }
 for(const style of root.querySelectorAll('style'))style.textContent=style.textContent.replace(/@media\s*(?:screen\s+and\s*)?(\((?:max|min)-width\s*:[^{}]+\))/g,'@container $1');
 const bounds=native.document.createElement('style');bounds.textContent=`
 :host{display:block;max-width:100%;min-width:0;--sidebar:0px}
 img,svg,canvas{max-width:100%}input,textarea,select{box-sizing:border-box;max-width:100%}
 .neural-section-controls{display:block!important;grid-column:1/-1;position:relative;margin:0 0 16px;max-width:100%;border:1px solid #77889655;border-radius:10px}
 .neural-section-controls>summary{padding:12px 16px;cursor:pointer;font:600 14px system-ui;color:#c5d6e4;background:#24313d}
 .neural-section-controls>.neural-section-rail{position:static!important;inset:auto!important;width:auto!important;min-width:0!important;height:auto!important;max-height:320px;overflow:auto;box-sizing:border-box}
 .neural-section-rail nav{display:flex;flex-wrap:wrap;gap:6px}
 .neural-section-rail nav button{width:auto!important;flex:1 1 180px}
 .neural-section-controls~main{margin-left:0!important;margin-inline-start:0!important;width:auto!important;min-width:0!important;padding:16px!important}
 `;root.append(bounds);
 root.addEventListener('click',async event=>{let anchor=event.target.closest('a');if(!anchor)return;let href=anchor.getAttribute('href')||'';if(href.startsWith('#')){event.preventDefault();location.hash=href}else if(href.startsWith('/api/')){event.preventDefault();let response=await fetch(href);let blob=await response.blob();let url=URL.createObjectURL(blob),a=native.document.createElement('a');a.href=url;a.download=response.headers.get('Content-Disposition')?.match(/filename="?([^";]+)/)?.[1]||'neural-section-export';a.click();native.setTimeout(()=>URL.revokeObjectURL(url),2000)}},{signal:lifecycle.signal});
 // Script declarations are local to this component. The object model belongs to
 // this same document and the calculation endpoints belong to the shared server.
 const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
 const evaluate=new AsyncFunction('window','document','location','history','fetch','setTimeout','setInterval','clearTimeout','clearInterval','requestAnimationFrame','cancelAnimationFrame','EventSource','componentRoot','componentCleanups',bundle.script+"\n function __bindOriginalHandlers(){for(const element of componentRoot.querySelectorAll('*')){for(const attr of [...element.attributes]){if(!/^on[a-z]+$/.test(attr.name))continue;const action=eval('(function(event){'+attr.value+'\\n})');element.removeAttribute(attr.name);element.addEventListener(attr.name.slice(2),function(event){if(action.call(this,event)===false)event.preventDefault()});}}}\n __bindOriginalHandlers();const __handlerObserver=new window.MutationObserver(__bindOriginalHandlers);__handlerObserver.observe(componentRoot,{subtree:true,childList:true});componentCleanups.push(()=>__handlerObserver.disconnect());\n");
 await evaluate(window,document,location,history,fetch,setTimeout,setInterval,clearTimeout,clearInterval,requestAnimationFrame,cancelAnimationFrame,EventSource,root,componentCleanups);
 if(id==='ambient'||id==='injector'){
  setInterval(async()=>{try{let response=await fetch('/bridge/__telemetry'),state=await response.json();if(id==='ambient'){localWindow.updateTelemetry?.(state.telemetry);if(state.audio)localWindow.updateAudio?.(state.audio)}else localWindow.updateMachineLogStream?.(state);}catch{}},1000)
 }
 return ()=>{lifecycle.abort();componentCleanups.forEach(fn=>fn());timers.forEach(clearTimeout);intervals.forEach(clearInterval);frames.forEach(cancelAnimationFrame);};
}
