const $ = id => document.getElementById(id);
const state = { snapshot:null, online:false, session:null, filter:'all', focus:null, paused:matchMedia('(prefers-reduced-motion: reduce)').matches, gain:1.3, job:null, commandPending:false, history:[], historyIndex:0, draft:'', chartCpu:[], chartNetwork:[], chartRuntime:[], lastEvent:0, lastSnapshot:0 };
let toastTimer;
function toast(message) { $('toast').textContent=message; $('toast').hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('toast').hidden=true,4000); }
function bytes(value, rate=false) {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—';
  const units=rate?['B/s','KB/s','MB/s','GB/s']:['B','KB','MB','GB','TB'];
  let n=Math.max(0,value),i=0; while(n>=1024 && i<units.length-1){n/=1024;i++;}
  return `${n.toFixed(i===0?0:n>=100?0:1)} ${units[i]}`;
}
function number(value, digits=1) { return value == null ? '—' : value.toFixed(digits); }
function duration(seconds) { if(seconds==null)return '—';const d=Math.floor(seconds/86400),h=Math.floor(seconds/3600)%24,m=Math.floor(seconds/60)%60;return d?`${d}d ${h}h`:`${h}h ${m}m`; }
function updateSizeStat(prefix,value,isRate) { const [n,u]=bytes(value,isRate).split(' ');$(prefix).textContent=n;$(prefix+'-unit').textContent=u||''; }
function appendConsole(text, kind='') {
  const out=$('console-output'), nearBottom=out.scrollHeight-out.scrollTop-out.clientHeight<45;
  const line=document.createElement('div'); line.className=`console-line ${kind}`;line.textContent=text;out.append(line);
  while(out.children.length>180 || (out.textContent.length>150000 && out.children.length>1))out.firstElementChild.remove();
  if(nearBottom)out.scrollTop=out.scrollHeight;
}
function setOnline(online) {
  state.online=online;
  const el=$('connection');el.className=`connection ${online?'online':'offline'}`;el.replaceChildren(Object.assign(document.createElement('i'),{}),document.createTextNode(online?'SYSTEM LIVE':'SIGNAL OFFLINE'));
  $('telemetry-status').textContent=online?'LIVE':'OFFLINE';
  $('sample-age').textContent=online?'1 s sampling':'Last sample · offline';
  updateStage();
}
function selectedProcesses() {return (state.snapshot?.processes||[]).filter(p=>(state.filter==='all'||p.runtime===state.filter)&&(!state.focus||p.pid===state.focus));}
function updateStage() {
  const rows=selectedProcesses();
  $('stage-state').textContent=state.paused?'VISUALIZATION PAUSED':!state.online?'SIGNAL OFFLINE · AWAITING DATA':rows.length?`${rows.length} SIGNAL${rows.length===1?'':'S'} IN THE STREAM`:'AMBIENT · WAITING FOR RUNTIMES';
  $('rain-empty').hidden=state.online&&rows.length>0;
  const emptyTitle=$('rain-empty').querySelector('strong'),emptyText=$('rain-empty').lastElementChild;
  emptyTitle.textContent=state.online?'Listening for a heartbeat':'Connecting to your machine';
  emptyText.textContent=state.online?`Start a ${state.filter==='all'?'Python or Java':state.filter==='python'?'Python':'Java'} app to bring the matrix to life.`:'Waiting for live process telemetry. Last values may be out of date.';
  const focused=state.snapshot?.processes.find(p=>p.pid===state.focus);
  $('focus-label').hidden=!focused;$('reset-focus').hidden=!focused;
  if(focused)$('focus-label').textContent=`FOCUS / ${focused.label} · ${focused.pid}`;
}
function drawChart(canvas, values, color, ceiling, fill=true, grid=true) {
  const rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return;
  const ratio=Math.min(devicePixelRatio||1,2),w=rect.width,h=rect.height;
  if(canvas.width!==Math.round(w*ratio)||canvas.height!==Math.round(h*ratio)){canvas.width=Math.round(w*ratio);canvas.height=Math.round(h*ratio);}
  const ctx=canvas.getContext('2d');ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,w,h);
  if(grid){ctx.strokeStyle='#253627';ctx.lineWidth=.5;for(let y=0;y<3;y++){ctx.beginPath();ctx.moveTo(0,2+y*(h-4)/2);ctx.lineTo(w,2+y*(h-4)/2);ctx.stroke();}}
  const data=values.slice(-60),max=ceiling||Math.max(1024,...data.map(v=>v||0))*1.1;
  if(!data.length)return;
  const points=data.map((v,i)=>({x:(60-data.length+i)/59*w,y:h-3-(Math.max(0,v||0)/max)*(h-6)}));
  ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.lineWidth=1.4;ctx.strokeStyle=color;ctx.stroke();
  if(fill){ctx.lineTo(points.at(-1).x,h);ctx.lineTo(points[0].x,h);ctx.closePath();const gradient=ctx.createLinearGradient(0,0,0,h);gradient.addColorStop(0,color+'3a');gradient.addColorStop(1,color+'02');ctx.fillStyle=gradient;ctx.fill();}
}
function renderCharts(){drawChart($('system-cpu-chart'),state.chartCpu,'#a5dc8b',100);drawChart($('network-chart'),state.chartNetwork,'#8eb8c5',null,true,false);drawChart($('cpu-spark'),state.chartRuntime,'#a5d884',Math.max(1,...state.chartRuntime.map(v=>v||0))*1.15,false,false);}
const rowsByPid=new Map();
function renderProcesses(processes) {
  const list=$('process-list'),present=new Set(processes.map(p=>p.pid));
  for(const [pid,row] of rowsByPid)if(!present.has(pid)){row.remove();rowsByPid.delete(pid);}
  for(const p of processes){
    let row=rowsByPid.get(p.pid);
    if(!row){row=document.createElement('tr');row.className='process-row';row.tabIndex=0;row.setAttribute('role','button');row.innerHTML='<td><div class="process-name"><span class="runtime-icon"></span><div class="process-details"><strong></strong><small></small></div></div></td><td></td><td></td><td></td><td><span class="signal-bars"><i></i><i></i><i></i><i></i><i></i></span></td>';row.addEventListener('click',()=>setFocus(state.focus===p.pid?null:p.pid));row.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();row.click();}});rowsByPid.set(p.pid,row);}
    row.classList.toggle('selected',state.focus===p.pid);row.setAttribute('aria-pressed',String(state.focus===p.pid));row.setAttribute('aria-label',`Focus ${p.label}, PID ${p.pid}`);
    row.title=`${p.label} · PID ${p.pid} · ${p.threads??'Unknown'} threads · Running ${duration(p.ageSeconds)}`;
    const icon=row.querySelector('.runtime-icon');icon.className=`runtime-icon ${p.runtime}`;icon.textContent=p.runtime==='python'?'PY':'JV';
    row.querySelector('strong').textContent=p.label;row.querySelector('small').textContent=`${p.runtime==='python'?'Python':'Java'} / ${p.pid}`;
    row.cells[1].textContent=p.cpu==null?'—':`${number(p.cpu)}%`;row.cells[2].textContent=bytes(p.memoryBytes);row.cells[3].textContent=bytes(p.ioRate,true);
    const bars=row.querySelector('.signal-bars');bars.className=`signal-bars ${p.runtime}`;const strength=Math.min(5,1+Math.ceil((p.cpu||0)*.55+Math.log10(1+(p.ioRate||0))*.25));
    Array.from(bars.children).forEach((bar,i)=>bar.classList.toggle('lit',i<strength));
    // Reorder only when needed, preserving keyboard focus and scroll position.
    const index=processes.indexOf(p);if(list.children[index]!==row)list.insertBefore(row,list.children[index]||null);
  }
  $('process-empty').hidden=processes.length>0;
  $('process-empty').textContent=state.filter==='all'?'No Python or Java processes running. Start an app to connect it.':`No ${state.filter} processes match this filter.`;
  $('process-count').textContent=String(processes.length);
}
function renderSnapshot(snapshot) {
  state.snapshot=snapshot;state.lastSnapshot=Date.now();setOnline(true);
  if(state.focus&&!snapshot.processes.some(p=>p.pid===state.focus)){state.focus=null;toast('Focused process exited. Showing all signals.');}
  const {totals,system}=snapshot;
  $('stat-count').textContent=snapshot.processes.length;
  $('runtime-count').textContent=`${totals.python} PY / ${totals.java} JV`;
  $('stat-cpu').textContent=number(totals.cpu);
  updateSizeStat('stat-memory',totals.memory,false);updateSizeStat('stat-io',totals.io,true);
  $('system-cpu').replaceChildren(document.createTextNode(number(system.cpu)),Object.assign(document.createElement('small'),{textContent:'%'}));
  const percent=system.memoryUsed/system.memoryTotal*100;
  $('system-memory-percent').replaceChildren(document.createTextNode(number(percent,0)),Object.assign(document.createElement('small'),{textContent:'%'}));
  $('memory-bar').style.width=`${percent}%`;$('memory-detail').textContent=`${bytes(system.memoryUsed)} / ${bytes(system.memoryTotal)}`;
  $('network-rx').textContent=bytes(system.networkRx,true);$('network-tx').textContent=bytes(system.networkTx,true);
  $('host').textContent=system.hostname;$('host').title=`${system.platform} · ${system.cpuModel} · ${system.cores} logical cores`;
  $('uptime').textContent=duration(system.uptime);$('system-processes').textContent=system.totalProcesses;
  $('disk-free').textContent=bytes(system.disk?.freeBytes);$('disk-label').textContent=`Disk free${system.disk?' · '+system.disk.name:''}`;
  state.chartCpu.push(system.cpu);state.chartNetwork.push((system.networkRx||0)+(system.networkTx||0));state.chartRuntime.push(totals.cpu);
  for(const values of [state.chartCpu,state.chartNetwork,state.chartRuntime])if(values.length>60)values.shift();
  document.querySelectorAll('.mini-bars i').forEach((el,i)=>{el.style.height=`${5+Math.min(23,Math.log2(1+totals.io)*1.2)*(0.5+(i%3)/4)}px`;el.style.opacity=totals.io>0?'.8':'.25';});
  renderProcesses(snapshot.processes.filter(p=>state.filter==='all'||p.runtime===state.filter));renderCharts();updateStage();
}
function setFocus(pid) {state.focus=pid;renderProcesses((state.snapshot?.processes||[]).filter(p=>state.filter==='all'||p.runtime===state.filter));updateStage();}
function setFilter(filter){state.filter=filter;state.focus=null;document.querySelectorAll('[data-filter]').forEach(el=>{el.classList.toggle('selected',el.dataset.filter===filter);el.setAttribute('aria-pressed',String(el.dataset.filter===filter));});renderProcesses((state.snapshot?.processes||[]).filter(p=>filter==='all'||p.runtime===filter));updateStage();}
function setPaused(paused){state.paused=paused;$('pause').setAttribute('aria-label',paused?'Resume rain':'Pause rain');$('pause').title=paused?'Resume rain':'Pause rain';$('pause').innerHTML=paused?'<svg viewBox="0 0 24 24"><path d="m8 5 11 7-11 7z"/></svg>':'<svg viewBox="0 0 24 24"><path d="M8 5v14M16 5v14"/></svg>';updateStage();}
document.querySelectorAll('[data-filter]').forEach(el=>el.addEventListener('click',()=>setFilter(el.dataset.filter)));
$('reset-focus').addEventListener('click',()=>setFocus(null));
$('pause').addEventListener('click',()=>setPaused(!state.paused));
$('gain').addEventListener('input',()=>{state.gain=Number($('gain').value);$('gain-value').textContent=state.gain.toFixed(1)+'×';});
async function fullscreen(el){try{if(document.fullscreenElement)await document.exitFullscreen();else await el.requestFullscreen();}catch{toast('Fullscreen is unavailable in this window.');}}
$('fullscreen').addEventListener('click',()=>fullscreen(document.documentElement));$('expand-rain').addEventListener('click',()=>fullscreen($('rain-panel')));
$('help-button').addEventListener('click',()=>$('help-dialog').showModal());$('close-help').addEventListener('click',()=>$('help-dialog').close());$('help-done').addEventListener('click',()=>$('help-dialog').close());
$('clear-console').addEventListener('click',()=>$('console-output').replaceChildren());
document.querySelectorAll('.rail-link[href]').forEach(el=>el.addEventListener('click',()=>{document.querySelectorAll('.rail-link').forEach(x=>x.classList.remove('active'));el.classList.add('active');}));

async function post(endpoint,data){
  if(!state.session)throw new Error('Local command session is not connected.');
  const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-Matrix-Token':state.session.token},body:JSON.stringify(data)});
  const result=await response.json();if(!response.ok)throw new Error(result.error||'Request failed');return result;
}
function localCommand(command){
  const [name,...args]=command.trim().split(/\s+/);const value=args.join(' ');
  switch(name.toLowerCase()){
    case '/help':appendConsole('/ps                 List connected Python and Java processes\n/focus PID          Isolate one process in the rain\n/focus all          Restore the full stream\n/filter all|python|java\n/gain 0.5–3         Adjust visual sensitivity\n/pause  /resume     Pause or resume the animation\n/clear              Clear the console\n\nOther commands execute in Windows PowerShell. A new shell is created each time.\nFor a long-running app, use Start-Process. Stop cancels the current command tree.','system');return;
    case '/ps':appendConsole((state.snapshot?.processes||[]).map(p=>`${String(p.pid).padEnd(7)} ${p.runtime.padEnd(7)} ${number(p.cpu).padStart(5)}%  ${bytes(p.memoryBytes).padStart(9)}  ${p.label}`).join('\n')||'No matching runtimes are running.','system');return;
    case '/focus':if(value==='all'){setFocus(null);appendConsole('Focus cleared.','system');return;}if(state.snapshot?.processes.some(p=>p.pid===Number(value))){setFilter('all');setFocus(Number(value));appendConsole(`Focused PID ${value}.`,'system');}else appendConsole('That PID is not connected. Use /ps to list processes.','error');return;
    case '/filter':if(['all','python','java'].includes(value)){setFilter(value);appendConsole(`Filter: ${value}`,'system');}else appendConsole('Usage: /filter all|python|java','error');return;
    case '/gain':if(Number(value)>=.5&&Number(value)<=3){$('gain').value=String(Number(value));$('gain').dispatchEvent(new Event('input'));appendConsole(`Sensitivity: ${state.gain}×`,'system');}else appendConsole('Usage: /gain 0.5–3','error');return;
    case '/pause':setPaused(true);appendConsole('Rain paused. Telemetry continues.','system');return;
    case '/resume':setPaused(false);appendConsole('Rain resumed.','system');return;
    case '/clear':$('console-output').replaceChildren();return;
    default:appendConsole('Unknown control. Type /help to see available controls.','error');
  }
}
function commandUI(running){$('cancel-command').hidden=!running;$('run-command').hidden=running;$('run-command').disabled=state.commandPending;$('command-state').textContent=running?'● Command running':state.commandPending?'● Starting…':'● Ready';}
$('command-form').addEventListener('submit',async e=>{
  e.preventDefault();const command=$('command-input').value.trim();if(!command)return;
  if(state.history.at(-1)!==command)state.history.push(command);if(state.history.length>100)state.history.shift();state.historyIndex=state.history.length;state.draft='';
  if(command.startsWith('/')){appendConsole(`❯ ${command}`,'command');$('command-input').value='';localCommand(command);return;}
  if(state.job||state.commandPending){toast('Stop the running command before starting another.');return;}
  state.commandPending=true;commandUI(false);
  try{await post('/api/command',{command});$('command-input').value='';}catch(error){appendConsole(error.message,'error');}
  finally{state.commandPending=false;commandUI(Boolean(state.job));}
});
$('command-input').addEventListener('keydown',e=>{
  if(e.key==='ArrowUp'){e.preventDefault();if(state.historyIndex===state.history.length)state.draft=e.target.value;state.historyIndex=Math.max(0,state.historyIndex-1);e.target.value=state.history[state.historyIndex]||'';}
  if(e.key==='ArrowDown'){e.preventDefault();state.historyIndex=Math.min(state.history.length,state.historyIndex+1);e.target.value=state.historyIndex===state.history.length?state.draft:state.history[state.historyIndex];}
  if(e.key==='Escape')e.target.blur();
});
$('cancel-command').addEventListener('click',async()=>{if(!state.job)return;try{await post('/api/cancel',{id:state.job});}catch(error){appendConsole(error.message,'error');}});
$('shutdown').addEventListener('click',async()=>{try{await post('/api/shutdown',{});events?.close();setOnline(false);setPaused(true);state.session=null;document.body.classList.add('shutdown');$('stage-state').textContent='SESSION ENDED';appendConsole('Matrix Bus stopped. Relaunch with Launch.cmd to reconnect.','system');toast('Matrix Bus stopped. You can close this window.');}catch(error){toast(error.message);}});
document.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement.tagName!=='INPUT'&&!$('help-dialog').open){e.preventDefault();$('command-input').focus();}});

// A stream is assigned a process. Every frame interpolates measured activity.
// Ambient streams are deliberately dim and are labeled as ambient in the interface.
const canvas=$('rain'),ctx=canvas.getContext('2d',{alpha:false});
const glyphs='アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン012345789:<>+=*/';
let width=0,height=0,streams=[],lastFrame=0,frameCount=0,lastFps=performance.now(),elapsed=0;
function resizeRain(){const r=canvas.getBoundingClientRect(),ratio=Math.min(devicePixelRatio||1,2);width=r.width;height=r.height;canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);ctx.setTransform(ratio,0,0,ratio,0,0);const count=Math.ceil(width/16);streams=Array.from({length:count},(_,i)=>streams[i]||{y:Math.random()*height*1.7-height*.4,seed:Math.random()*9999,speed:15,energy:0});renderRain(0);renderCharts();}
function renderRain(dt){
  elapsed+=dt;ctx.fillStyle='#030b07';ctx.fillRect(0,0,width,height);ctx.font='12px "Cascadia Code",Consolas,monospace';ctx.textAlign='center';
  const procs=state.online?selectedProcesses():[];const active=procs.length>0;const coreCount=state.snapshot?.system.cores||1;
  // When there are more processes than screen columns, combine their signals
  // into channels so every running process still contributes to the field.
  let channels=procs;
  if(streams.length>0&&procs.length>streams.length){
    channels=streams.map(()=>({cpu:0,ioRate:0,memoryBytes:0,runtimes:[]}));
    procs.forEach((p,i)=>{const channel=channels[i%channels.length];channel.cpu+=p.cpu||0;channel.ioRate+=p.ioRate||0;channel.memoryBytes+=p.memoryBytes||0;channel.runtimes.push(p.runtime);});
    channels.forEach((channel,i)=>{channel.runtime=channel.runtimes[(Math.floor(elapsed/2)+i)%channel.runtimes.length];});
  }
  const globalCpu=procs.reduce((n,p)=>n+(p.cpu||0),0);
  streams.forEach((stream,i)=>{
    const p=active?channels[i%channels.length]:null;
    const cpu=Math.min(2,((p?.cpu||0)*coreCount/100));
    const io=Math.min(1,Math.log2(1+(p?.ioRate||0))/21);
    const mem=Math.min(1,Math.log2(1+(p?.memoryBytes||0)/1048576)/11);
    const speed=active?(24+cpu*135+Math.sqrt(globalCpu)*3+io*45)*state.gain:9;
    stream.speed+=(speed-stream.speed)*Math.min(1,dt*3);stream.energy+=(io-stream.energy)*Math.min(1,dt*4);
    const spacing=17,tail=active?Math.floor(8+mem*23):8;
    stream.y+=dt*stream.speed*(.7+(stream.seed%100)/100);
    if(stream.y-tail*spacing>height+20)stream.y=-Math.random()*170;
    // Staggered gaps and varied trails make the field readable, not a solid wall.
    const presence=active?(i%9===0?.42:1):(i%3===0?1:.15);
    const rgb=p?.runtime==='java'?[225,188,102]:[116,236,145];
    const head=Math.floor(stream.y/spacing);
    for(let j=tail;j>=0;j--){
      const y=stream.y-j*spacing;if(y<12||y>height+15)continue;
      const hash=Math.abs(Math.floor(Math.sin((head-j)*17.32+stream.seed+i*91.7+Math.floor(elapsed*(j===0?9:.9)))*99999));
      const character=glyphs[hash%glyphs.length];const fade=Math.pow(1-j/tail,1.5);
      let alpha=(active?.22+fade*.55:.035+fade*.095)*presence;
      if(j===0&&active){ctx.fillStyle=p.runtime==='java'?`rgba(255,244,187,${.64+stream.energy*.36})`:`rgba(207,255,216,${.64+stream.energy*.36})`;ctx.shadowBlur=stream.energy>0.1?5+stream.energy*8:0;ctx.shadowColor=`rgba(${rgb.join(',')},.8)`;}
      else{alpha=Math.min(.95,alpha+stream.energy*fade*.22);ctx.fillStyle=`rgba(${rgb.join(',')},${alpha})`;ctx.shadowBlur=0;}
      ctx.fillText(character,8+i*16,y);
    }
  });ctx.shadowBlur=0;
}
function animate(now){const dt=Math.min(.05,(now-(lastFrame||now))/1000);lastFrame=now;if(!document.hidden&&!state.paused){renderRain(dt);frameCount++;}if(now-lastFps>1000){$('fps').textContent=state.paused?'PAUSED':`${Math.round(frameCount*1000/(now-lastFps))} FPS`;lastFps=now;frameCount=0;}requestAnimationFrame(animate);}
new ResizeObserver(resizeRain).observe($('rain-stage'));requestAnimationFrame(animate);setPaused(state.paused);
setInterval(()=>{$('clock').textContent=new Date().toLocaleTimeString('en-GB',{hour12:false});if(state.online&&Date.now()-state.lastSnapshot>5000)setOnline(false);},1000);

let events;
async function connect(){
  try{const response=await fetch('/api/session');if(!response.ok)throw new Error('Session unavailable');state.session=await response.json();$('command-input').title=`Working folder: ${state.session.cwd}`;}
  catch{appendConsole('Unable to connect to the local server. Relaunch Matrix Bus.','error');setOnline(false);return;}
  events=new EventSource('/api/events');
  events.addEventListener('session',e=>{const session=JSON.parse(e.data);state.session=session;state.job=session.activeCommand?.id||null;commandUI(Boolean(state.job));});
  events.addEventListener('snapshot',e=>renderSnapshot(JSON.parse(e.data)));
  events.addEventListener('status',e=>{const status=JSON.parse(e.data);setOnline(status.connected);});
  events.addEventListener('activity',e=>{const item=JSON.parse(e.data);if(item.id<=state.lastEvent)return;state.lastEvent=item.id;appendConsole(`[${new Date(item.at).toLocaleTimeString('en-GB',{hour12:false})}] ${item.message}`,'system');});
  events.addEventListener('command',e=>{const message=JSON.parse(e.data);if(message.state==='start'){state.job=message.id;appendConsole(`❯ ${message.command}`,'command');commandUI(true);}if(message.state==='output')appendConsole(message.text,message.type==='stderr'?'error':'');if(message.state==='end'){state.job=null;commandUI(false);appendConsole(`Process exited · code ${message.code??'unknown'}`,message.code===0?'system':'error');}});
  events.onerror=()=>setOnline(false);
}
connect();
