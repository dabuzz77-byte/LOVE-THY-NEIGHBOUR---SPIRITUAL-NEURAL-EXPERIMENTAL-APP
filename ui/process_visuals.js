(()=>{
 const cards=[
  ['feedback','process-feedback-v1.jpg','Feedback circuit','Completed results → explicit review → learned update.'],
  ['growth','process-growth-v1.jpg','Growth and renewal','Track result diversity and research freshness; repetition is visible.'],
  ['bridge','process-bridge-v1.jpg','Checked binary bridge','Trace checked encoding, job completion and receipt creation.'],
  ['core','process-core-v1.jpg','Shared processing core','Observe the queue, field ticks and actual processing latency.']
 ];
 const root=document.querySelector('#processVisuals');if(!root)return;
 root.innerHTML='<summary>Four active process views · feedback / renewal / bridge / core <span id="processVisualSummary"></span></summary><div class="process-art-grid">'+cards.map(([id,image,title,caption])=>'<section class="process-art-card"><a href="/assets/'+image+'" target="_blank" rel="noopener"><img loading="lazy" src="/assets/'+image+'" alt="'+title+' · supplied conceptual artwork"></a><div><h3>'+title+'</h3><p>'+caption+'</p><svg viewBox="0 0 260 45" role="img" aria-label="'+title+' session activity"><path d="M15 22H245" stroke="#57737b" stroke-width="2"/><circle cx="15" cy="22" r="8" fill="#7ed8cf"/><circle cx="130" cy="22" r="8" fill="#e3ce92"/><circle cx="245" cy="22" r="8" fill="#7ed8cf"/><rect id="processBar-'+id+'" x="15" y="36" width="0" height="5" fill="#e3ce92"/></svg><p id="processMetric-'+id+'">Waiting for measured events…</p></div></section>').join('')+'</div><p class="muted pad">These images inspire the four process views. Their indicators show recorded results, explicit reviews, source freshness, queue occupancy and processing latency.</p>';
 const text=(id,value)=>{const e=document.querySelector('#processMetric-'+id);if(e)e.textContent=value};
 const bar=(id,value)=>document.querySelector('#processBar-'+id)?.setAttribute('width',String(Math.max(0,Math.min(1,value))*230));
 document.addEventListener('neural-runtime-snapshot',event=>{
  const s=event.detail,o=s.observatory||{},r=s.research||{},latest=Object.values(r.topics||{}).map(t=>t.checked_at).filter(Boolean);
  const age=latest.length?Math.max(0,Date.now()/1000-Math.max(...latest)):null;
  const f=o.result_diversity,latency=o.latency_ewma_ms;
  document.querySelector('#processVisualSummary').textContent='· '+(o.completed||0)+' results · '+(o.reviews||0)+' reviews';
  text('feedback',(o.completed||0)+' completed results · '+(o.reviews||0)+' explicit reviews · '+s.learning.reviewed_updates+' saved preference updates');
  text('growth',(f===null||f===undefined?'No result window':(100*f).toFixed(1)+'% distinct result digests / '+o.diversity_window+' samples')+' · latest research check '+(age===null?'pending':Math.round(age)+'s ago'));
  text('bridge',(o.completed||0)+' checked results recorded · '+(o.failed||0)+' failed jobs · delivery only through configured transports');
  text('core',s.queue+'/16 queued · '+s.field.ticks+' field ticks · '+(latency===null||latency===undefined?'latency pending':latency.toFixed(1)+'ms smoothed result latency'));
  bar('feedback',o.completed?o.reviews/o.completed:0);bar('growth',f||0);bar('bridge',o.success_fraction||0);bar('core',s.queue/16);
 });
})();
