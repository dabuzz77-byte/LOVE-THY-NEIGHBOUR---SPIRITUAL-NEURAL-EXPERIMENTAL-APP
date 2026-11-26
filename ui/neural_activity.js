(()=>{
 const host=document.querySelector('#neuralActivity');if(!host)return;
 host.innerHTML='<div class="neural-activity-head"><div><span class="lesson-overline">SHARED NEURAL ACTIVITY</span><h2>One living process</h2><p>Source → binary / ternary / qutrit → engines → learning → inference output</p></div><button id="neuralMotion">Pause motion</button></div><canvas id="neuralActivityCanvas" role="img" aria-label="Live 96-node recurrent field, measured processing stages and exact snapshot binary grid"></canvas><div id="neuralActivityMetrics" class="neural-activity-metrics" role="status">Waiting for runtime state…</div><ol id="neuralProcessStream" aria-label="Recorded process stream"></ol><small>The nodes represent the shared 96-node field. Light intensity follows field values; paths and moving highlights illustrate the flow. The flux grid encodes the selected counters and field bits exactly. Socket writes report local transport, not remote reading or learning.</small>';
 const canvas=host.querySelector('canvas'),ctx=canvas.getContext('2d'),metrics=host.querySelector('#neuralActivityMetrics'),stream=host.querySelector('ol');
 let state=null,encoded='',moving=!matchMedia('(prefers-reduced-motion: reduce)').matches,visible=true,lastFrame=0,phase=0,pulseAt=0,lastCompleted=0;
 const motion=host.querySelector('button');const label=()=>motion.textContent=moving?'Pause motion':'Resume motion';label();motion.onclick=()=>{moving=!moving;label();draw(performance.now())};
 new IntersectionObserver(entries=>{visible=entries[0].isIntersecting}).observe(host);
 const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 document.addEventListener('neural-runtime-snapshot',event=>{
  state=event.detail;const o=state.observatory||{},l=state.learning||{},d=state.delivery||{};
  if((o.completed||0)>lastCompleted)pulseAt=performance.now();lastCompleted=o.completed||0;
  const payload={queue:state.queue,completed:o.completed||0,learned:l.updates||0,subscribers:d.subscribers||0,writes:d.peer_writes||0,field_bits:state.field.bits||[]};
  encoded=[...new TextEncoder().encode(JSON.stringify(payload))].map(b=>b.toString(2).padStart(8,'0')).join('');
  metrics.textContent=(o.completed||0)+' results · '+(l.updates||0)+' learned updates · '+(l.reviewed_updates||0)+' reviews · '+(state.queue||0)+'/16 queued · '+(d.subscribers||0)+' subscribers · '+(d.peer_writes||0)+' socket writes · '+encoded.length+' selected bits';
  stream.innerHTML=(o.events||[]).slice(-5).reverse().map(e=>'<li><time>'+escape(new Date(e.at*1000).toLocaleTimeString())+'</time><b>'+escape(e.section)+'</b><span>'+escape(e.stage)+(e.receipt?' · receipt '+escape(e.receipt):'')+'</span></li>').join('')||'<li>Ready for a recorded process. Run a section or research query.</li>';
  draw(performance.now());
 });
 function draw(now){
  if(!visible||document.hidden)return;
  const w=Math.max(320,canvas.clientWidth),h=w<650?390:300,dpr=Math.min(devicePixelRatio||1,2);
  if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)){canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr)}
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);
  const bg=ctx.createLinearGradient(0,0,w,h);bg.addColorStop(0,'#061523');bg.addColorStop(.55,'#0c2336');bg.addColorStop(1,'#051722');ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
  const f=state?.field||{},values=f.values||[],cx=w<650?w*.5:w*.34,cy=w<650?125:135,rx=Math.min(w*.3,190),ry=88;
  const halo=ctx.createRadialGradient(cx,cy,5,cx,cy,rx*1.4);halo.addColorStop(0,'#75d9f525');halo.addColorStop(1,'#75d9f500');ctx.fillStyle=halo;ctx.fillRect(0,0,w,h);
  const nodes=Array.from({length:96},(_,i)=>{const y=1-2*(i+.5)/96,a=i*2.399963+phase*.08,z=Math.sqrt(1-y*y)*Math.cos(a),x=Math.sqrt(1-y*y)*Math.sin(a);return {x:cx+x*rx,y:cy+y*ry,z,v:Math.abs(values[i]||0)}});
  nodes.forEach((n,i)=>{[1,11,23].forEach(step=>{const b=nodes[(i+step)%96];ctx.strokeStyle='rgba(119,211,239,'+(.035+Math.min(n.v+b.v,1)*.17)+')';ctx.lineWidth=.5+n.v;ctx.beginPath();ctx.moveTo(n.x,n.y);ctx.lineTo(b.x,b.y);ctx.stroke()})});
  nodes.slice().sort((a,b)=>a.z-b.z).forEach(n=>{ctx.shadowBlur=4+n.v*10;ctx.shadowColor='#a4edff';ctx.fillStyle=n.v>.5?'#ffe3a8':'#acebff';ctx.globalAlpha=.4+(n.z+1)*.2;ctx.beginPath();ctx.arc(n.x,n.y,1.3+n.v*2.2,0,Math.PI*2);ctx.fill()});ctx.globalAlpha=1;ctx.shadowBlur=0;
  ctx.fillStyle='#bce8f6';ctx.font='11px system-ui';ctx.textAlign='center';ctx.fillText('96 SHARED FIELD NODES · '+(f.ticks||0)+' TICKS',cx,cy+ry+24);
  const gx=w<650?20:w*.64,gy=w<650?275:50,gw=w<650?w-40:w*.32,cols=Math.max(16,Math.floor(gw/11));
  ctx.textAlign='left';ctx.fillStyle='#f4dc9f';ctx.fillText('FLUX GRID · EXACT SELECTED SNAPSHOT',gx,gy-17);ctx.font='10px monospace';
  for(let i=0;i<cols*7;i++){const index=(Math.floor(phase*5)*cols+i)%Math.max(1,encoded.length),bit=encoded[index];ctx.fillStyle=bit==='1'?'#b8f5eb':'#536f88';ctx.fillText(bit||'·',gx+(i%cols)*11,gy+Math.floor(i/cols)*13)}
  const stages=['INTAKE','BTQ','ENGINES','LEARN','OUTPUT'],pathY=h-24,start=25,end=w-25,pulse=Math.max(0,1-(now-pulseAt)/2500);
  ctx.strokeStyle='#46768b';ctx.beginPath();ctx.moveTo(start,pathY);ctx.lineTo(end,pathY);ctx.stroke();
  stages.forEach((name,i)=>{const x=start+(end-start)*i/4;ctx.fillStyle=i===4&&!(state?.delivery?.subscribers)?'#607789':'#c8e9ee';ctx.beginPath();ctx.arc(x,pathY,3+pulse*3,0,Math.PI*2);ctx.fill();ctx.font='9px system-ui';ctx.textAlign=i===0?'left':i===4?'right':'center';ctx.fillText(name,x,pathY-10)});
  if(moving&&pulse>0){const x=start+(end-start)*((phase*.4)%1);ctx.shadowBlur=12;ctx.shadowColor='#f8d89b';ctx.fillStyle='#ffe4aa';ctx.beginPath();ctx.arc(x,pathY,4,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0}
 }
 function frame(now){if(now-lastFrame>50){if(moving)phase+=Math.min(.1,(now-lastFrame)/1000);lastFrame=now;if(moving)draw(now)}requestAnimationFrame(frame)}requestAnimationFrame(frame);
})();
