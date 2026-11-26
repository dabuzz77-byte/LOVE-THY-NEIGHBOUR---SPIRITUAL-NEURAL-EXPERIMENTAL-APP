(()=>{
 let bits='',weighted=0,trajectory=0,previous=null,history=[],phase=0,snapshotBytes=0;
 document.addEventListener('neural-runtime-snapshot',event=>{
  const s=event.detail,r=s.research||{},values=s.field.values||[];
  const energy=values.reduce((a,v)=>a+Math.min(1,Math.abs(v)),0)/Math.max(1,values.length);
  const queue=Math.min(1,s.queue/16),coverage=Math.min(1,(r.completed_topics||0)/Math.max(1,Object.keys(r.queries||{}).length));
  const readiness=s.latest.pipeline?1:0;
  weighted=.35*energy+.25*queue+.2*coverage+.2*readiness;
  trajectory=previous===null?weighted:.8*trajectory+.2*weighted;
  previous=weighted;history.push(trajectory);if(history.length>90)history.shift();
  const projection={field_ticks:s.field.ticks,field_energy:energy,queue:s.queue,learning_updates:s.learning.updates,completed_research_topics:r.completed_topics||0,last_pipeline_receipt:s.latest.pipeline?.receipt||null,processing_weight:weighted};
  const raw=new TextEncoder().encode(JSON.stringify(projection));snapshotBytes=raw.length;
  bits=[...raw].map(b=>b.toString(2).padStart(8,'0')).join('');
  const label=document.querySelector('#titleFluxStatus');
  if(label)label.textContent=snapshotBytes+' snapshot bytes · '+bits.length+' encoded bits · processing index '+weighted.toFixed(3)+' · smoothed activity trajectory '+trajectory.toFixed(3);
 });
 function draw(){if(document.hidden||!document.querySelector("#titleFluxCanvas")?.getClientRects().length)return;
  const canvas=document.querySelector('#titleFluxCanvas');if(!canvas||document.hidden)return;
  const width=canvas.clientWidth,height=canvas.clientHeight,dpr=window.devicePixelRatio||1;
  if(canvas.width!==Math.round(width*dpr)||canvas.height!==Math.round(height*dpr)){canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr)}
  const c=canvas.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);c.fillStyle='#090e08';c.fillRect(0,0,width,height);
  const columns=Math.max(1,Math.floor(width/13)),rows=7;
  if(!bits){c.fillStyle='#c8c095';c.font='12px Consolas';c.fillText('Waiting for runtime snapshot…',15,28);return}
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(!reduced)phase=(phase+1)%Math.max(1,bits.length);
  c.font='12px Consolas';
  for(let row=0;row<rows;row++)for(let col=0;col<columns;col++){
   const i=(row*columns+col+phase)%bits.length,bit=bits[i],highlight=(col+row+phase)%17===0;
   c.fillStyle=highlight?'#ffe7a2':bit==='1'?'#87d78b':'#325b38';c.fillText(bit,8+col*13,17+row*16);
  }
  c.beginPath();history.forEach((v,i)=>{const x=i/89*width,y=height-8-v*32;if(i)c.lineTo(x,y);else c.moveTo(x,y)});c.strokeStyle='#f4d58a';c.lineWidth=2;c.stroke();
 }
 setInterval(draw,250);window.addEventListener('resize',draw);
})();
