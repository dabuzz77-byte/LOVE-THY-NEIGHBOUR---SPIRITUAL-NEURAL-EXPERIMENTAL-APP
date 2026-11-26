import {mountReferenceWaves} from './ambient_reference_waves.js';
import {mountWaveRouting} from './wave_routing.js';
import {mountCmbModulator,mountNoiseModulator} from './ambient_extra_modulators.js';
let service;
export function startAmbientModulators(api){
 if(service)return service;
 const parking=document.createElement('div');parking.hidden=true;document.body.append(parking);
 const host=document.createElement('div');parking.append(host);const listeners=new Set(),frames=new Map();let busy=false;
 function receive(value){frames.set(value.id,value);for(const listener of listeners)listener(value);}
 const disposers=[mountWaveRouting(host,api,receive),mountWaveRouting(host,api,receive,{chant:true}),...['dolphin','whale','cat','dog','bird','ice','rain','beach'].map(kind=>mountWaveRouting(host,api,receive,{kind})),mountNoiseModulator(host,receive)];
 const referenceHost=document.createElement('div');host.append(referenceHost);disposers.push(mountReferenceWaves(referenceHost,api,receive));
 mountCmbModulator(host,receive).then(d=>disposers.push(d)).catch(console.error);
 // Routing starts without audio permission. Playback follows a genuine user gesture.
 async function audio(){await Promise.allSettled([...host.querySelectorAll('[data-play],[data-noise-start]')].map(button=>button.onclick()));}
 for(const box of host.querySelectorAll('[data-audible],[data-noise-audible]'))box.checked=true;
 document.addEventListener('pointerdown',audio,{once:true});
 const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Ambient modulators starting · waveform routing on · low-volume audio starts with your first click';parking.before(status);status.style.cssText='font-size:12px;padding:6px 16px;color:#244b65';
 const timer=setInterval(async()=>{if(busy||!frames.size)return;busy=true;try{const receipt=await api('ambient-bus',{target:'all',kind:'reference',origin:'ambient-modulator-service',payload:{frames:[...frames.values()].filter(v=>v.enabled).map(v=>({...v,samples:v.samples.slice(0,32)})),predefined_text:true,stochastic:false,contains_model_text:false}});status.textContent='Ambient modulators active · '+[...frames.values()].filter(v=>v.enabled).length+' waveform sources · shared bus '+(receipt.accepted?'connected':'pending')+' · audio follows your playback controls';}catch(error){status.textContent='Ambient modulator routing: '+error.message;console.warn('Modulator routing:',error.message);}finally{busy=false;}},1500);
 service={attach(target,listener){target.append(host);listeners.add(listener);for(const value of frames.values())listener(value);return()=>{listeners.delete(listener);parking.append(host);};},frames};
 return service;
}
