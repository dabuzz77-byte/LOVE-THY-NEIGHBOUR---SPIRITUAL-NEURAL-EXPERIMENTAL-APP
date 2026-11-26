// Bounded visual particles: input bytes remain inspectable throughout the lifecycle.
export function makeCharge(text, order=10) {
  const bytes=new TextEncoder().encode(text);
  if(!text.trim()||bytes.length>1024)throw Error('Enter 1–1,024 UTF-8 bytes.');
  if(!Number.isFinite(order)||Math.abs(order)>1e6)throw Error('Order must be finite and within ±1,000,000.');
  const mask=Math.trunc(order)&255;
  return {intent:text,order,yield:order*7.83,bytes:Array.from(bytes,b=>b^mask)};
}
export function birthParticles(charge, now) {
  return charge.bytes.slice(0,128).map((byte,i)=>({byte,index:i,born:now,angle:i*2.399963+(byte/255),duration:6400}));
}
export function particlePhase(p,now) {
  const age=Math.max(0,(now-p.born)/p.duration);
  return {age,alive:age<1,alpha:Math.max(0,Math.min(1,age*6,(1-age)*5)),stage:age<.18?'materializing':age<.75?'transmitting':age<1?'dematerializing':'complete'};
}
