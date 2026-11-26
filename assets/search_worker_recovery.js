// Worker-compatible bounded recovery. Never execute two copies of a capture.
export function createSearchWorker(url, fallback, {timeout=12000,WorkerClass=globalThis.Worker,schedule=setTimeout,cancel=clearTimeout}={}) {
 let native=null,timer=null,closed=false,generation=0;
 const proxy={onmessage:null,onerror:null,mode:'worker',postMessage(payload){
  const job=++generation;let recovering=false;
  if(timer!==null)cancel(timer);
  const recover=()=>{
   if(closed||job!==generation||recovering)return;
   recovering=true;native?.terminate();native=null;proxy.mode='bounded-fallback';
   timer=schedule(()=>{
    if(closed||job!==generation)return;
    try{
     let remaining=4096;const sources=(payload.sources||[]).slice(0,32).map(source=>{const text=Array.from(String(source.text||'').slice(0,remaining*2)).slice(0,remaining).join('');remaining-=Array.from(text).length;return {...source,text};}).filter(s=>s.text);
     const bounded={...payload,sources,options:{...payload.options,budget:4096,keep:200,results:200,maxLength:Math.min(8,payload.options?.maxLength||8),pathMode:'straight'}};
     const result=fallback(bounded);
     if(!closed&&job===generation)proxy.onmessage?.({data:{id:payload.id,result,execution_mode:proxy.mode}});
    }catch(error){if(!closed&&job===generation)proxy.onerror?.({message:error.message});}
   },0);
  };
  if(!native){recover();return;}
  native.onmessage=e=>{if(closed||job!==generation||recovering)return;if(e.data.progress){proxy.onmessage?.(e);return;}cancel(timer);timer=null;proxy.onmessage?.(e);};
  native.onerror=recover;native.onmessageerror=recover;
  timer=schedule(recover,timeout);
  try{native.postMessage(payload);}catch{recover();}
 },terminate(){closed=true;generation++;if(timer!==null)cancel(timer);native?.terminate();native=null;}};
 try{native=new WorkerClass(url,{type:'module'});}catch{proxy.mode='bounded-fallback';}
 return proxy;
}
