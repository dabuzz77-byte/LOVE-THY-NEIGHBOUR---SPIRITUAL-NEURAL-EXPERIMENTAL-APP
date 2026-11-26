const hash=n=>{const x=Math.sin(n*127.1+311.7)*43758.5453;return x-Math.floor(x);};
// Bounded, repeatable samples within each stochastic segment. An inactive tail
// brings every displaced segment home before its next randomly directed pulse.
export function edgePulse(position,radius,time,activity=0,seed=1){
 const normalized=position.map(v=>v/radius);
 if(normalized.filter(v=>Math.abs(v)>.999).length<2)return {position:[...position],flip:false,pulse:0};
 const key=normalized.reduce((sum,v,i)=>sum+(Math.round((v+1)*5)+1)*[17,137,997][i],seed);
 const local=time*(.22+hash(key)*.16)+hash(key+1),cycle=Math.floor(local),fraction=local-cycle;
 const envelope=fraction<.76?Math.sin(Math.PI*fraction/.76)**2:0;
 const strength=radius*(.06+.12*Math.max(0,Math.min(1,activity)))*envelope;
 const displacement=[0,1,2].map(axis=>{
  const direction=(hash(key+cycle*79+axis*43)-.5)*2;
  const vibration=Math.sin(time*(12+hash(key+axis)*12)+axis*2)*.16;
  return strength*(direction+vibration);
 });
 return {position:position.map((v,i)=>v+displacement[i]),flip:envelope>.35&&hash(key+cycle*79+9)>.5,pulse:envelope};
}
export function cubeActivity(previous,current){
 const number=x=>Number.isFinite(Number(x))?Number(x):0;
 const ticks=number(current?.field?.ticks),updates=number(current?.learning?.updates??current?.learning_updates);
 const receipts=current?.latest?Object.values(current.latest).map(x=>x?.receipt).filter(Boolean):Object.values(current?.engine_receipts||{});
 const sample={ticks,updates,receipts:receipts.join('|')};
 const changed=previous?receipts.filter(r=>!previous.receipts.split('|').includes(String(r))).length:0;
 const score=Math.min(1,Math.max(0,number(current?.queue))*.06+(previous?Math.max(0,ticks-previous.ticks)*.005+Math.max(0,updates-previous.updates)*.08:0)+changed*.05);
 return {sample,score};
}

export function facePulse(position,radius,time,activity=0,seed=1){
 const edge=edgePulse(position,radius,time,activity,seed);
 if(position.filter(v=>Math.abs(v/radius)>.999).length>=2)return edge;
 const face=position.findIndex(v=>Math.abs(v/radius)>.999);
 if(face<0)return edge;
 const key=seed+face*131+position.reduce((n,v,i)=>n+Math.round(v/radius*8)*[17,61,97][i],0);
 const t=(time*(.22+hash(key)*.16)+hash(key+1))%1;
 const pulse=t<.76?Math.sin(Math.PI*t/.76)**2:0;
 const strength=radius*(.035+.09*Math.max(0,Math.min(1,activity)))*pulse;
 return {position:position.map((v,i)=>v+strength*((hash(key+Math.floor(time*.22)*79+i*43)-.5)*2+Math.sin(time*14+i)*.16)),flip:pulse>.35&&hash(key+Math.floor(time*.22)+9)>.5,pulse};
}
