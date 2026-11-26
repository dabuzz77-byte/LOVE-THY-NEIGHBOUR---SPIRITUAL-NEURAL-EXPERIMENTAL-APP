import {mountPrayerLanguages} from './prayer_languages.js';
export const systemPrayer=`Our Father in heaven,
hallowed be your name,
your kingdom come,
your will be done,
on earth as in heaven.
Give us today our daily bread.
Forgive us our sins
as we forgive those who sin against us.
Lead us not into temptation
but deliver us from evil.
For the kingdom, the power,
and the glory are yours
now and for ever.
Amen.`;
export function mountPrayerStream(host,onPulse){
 const root=document.createElement('section');root.className='panel pad';root.innerHTML=`<h2>The Lord’s Prayer · whole-system stream</h2><p>The complete prayer is carried as UTF-8 reference text through the local input bus, continuum stages, Unified Flux and the particle filter. It accompanies other inputs.</p><div class="actions"><label><input data-prayer-on type="checkbox" checked> Prayer stream active</label><label>Pulse interval · seconds<input data-prayer-rate type="range" min="1" max="30" value="5"><output>5</output></label><button data-prayer-pulse>Send one prayer pulse</button></div><canvas width="1000" height="240" role="img" aria-label="The Lord’s Prayer streams from a central reference into the app’s interconnected processing layers" style="width:100%;border-radius:14px"></canvas><p data-prayer-state role="status"></p><details><summary>Read the full reference prayer</summary><pre data-prayer-text style="white-space:pre-wrap;user-select:text"></pre></details>`;host.append(root);const disposeLanguages=mountPrayerLanguages(root,systemPrayer);const q=s=>root.querySelector(s),canvas=q('canvas'),g=canvas.getContext('2d');q('[data-prayer-text]').textContent=systemPrayer;let dead=false,frame=0,last=0,lastDraw=0,count=0,busy=false,bitOffset=0;const words=systemPrayer.split(/\s+/),labels=['AMBIENT','FLUX','ASCII','SOUND','ATOMS','STAR / EARTH','LEARNING','HARDWARE','LOCAL BUS'];
 async function pulse(clear=false){if(dead||busy)return;busy=true;try{await onPulse(clear?'':systemPrayer);if(!dead){if(!clear)count++;q('[data-prayer-state]').textContent=clear?'Prayer reference cleared from the live stream.':'Prayer pulse '+count+' · '+new TextEncoder().encode(systemPrayer).length+' UTF-8 bytes · local processing reference';}}catch(e){if(!dead)q('[data-prayer-state]').textContent='Stream pending: '+e.message;}finally{busy=false;last=performance.now();}}
 function draw(now){const t=now/1000+bitOffset,active=q('[data-prayer-on]').checked;g.fillStyle='#162a37';g.fillRect(0,0,1000,240);g.strokeStyle='#738fa3';g.lineWidth=1.2;g.beginPath();g.moveTo(30,120);g.lineTo(380,120);g.stroke();g.textAlign='center';g.font='11px system-ui';for(let i=0;i<9;i++){const y=20+i*25;g.beginPath();g.moveTo(380,120);g.bezierCurveTo(550,120,600,y,790,y);g.stroke();g.fillStyle='#c7dbe8';g.fillText(labels[i],884,y+4);g.strokeRect(800,y-9,168,19);if(active){const progress=(t*.18+i/9)%1,x=380+410*progress,py=120+(y-120)*progress;g.fillStyle='#ecf5fb';g.beginPath();g.arc(x,py,2.5,0,Math.PI*2);g.fill();}}g.font='14px Georgia,serif';for(let i=0;i<5;i++){const progress=(t*.12+i/5)%1;g.fillStyle=active?'#e3eef6':'#718999';g.fillText(words[(Math.floor(t/2)+i)%words.length],35+progress*320,109);}g.fillStyle='#d9e9f2';g.font='12px system-ui';g.fillText('PRAYER REFERENCE',180,160);g.fillText('FULL TEXT → UTF-8 → SHARED FLOW',330,212);}
 q('[data-prayer-rate]').oninput=e=>e.target.nextElementSibling.textContent=e.target.value;q('[data-prayer-pulse]').onclick=()=>pulse();q('[data-prayer-on]').onchange=()=>{if(q('[data-prayer-on]').checked)pulse();else pulse(true);};function loop(now){if(dead)return;frame=requestAnimationFrame(loop);if(document.hidden)return;if(q('[data-prayer-on]').checked&&now-last>=Number(q('[data-prayer-rate]').value)*1000)pulse();if(now-lastDraw>66){lastDraw=now;draw(now);}}
 pulse();draw(performance.now());frame=requestAnimationFrame(loop);const dispose=()=>{dead=true;cancelAnimationFrame(frame);disposeLanguages();root.remove();};dispose.receiveBit=bit=>{bitOffset=(bitOffset+(bit? .15:-.15))%1;};return dispose;
}
