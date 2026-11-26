/** Observable chat requests; reconnect retries preserve the same request ID. */
export async function runChat(api,payload,options={}){
 const id=options.id||globalThis.crypto?.randomUUID?.()||('chat-'+Date.now()+'-'+Math.random().toString(36).slice(2));
 const sleep=options.sleep||(ms=>new Promise(resolve=>setTimeout(resolve,ms))),now=options.now||Date.now,start=now();let stopSent=false;
 const cancel=()=>{if(!stopSent){stopSent=true;api('reasoning/chat-cancel',{id}).catch(()=>{});}};
 const check=()=>{if(options.signal?.aborted){cancel();throw new DOMException('Reply stopped. Check the work panel for operations that already completed.','AbortError');}if(now()-start>(options.timeout||(payload.response_detail==='detailed'||String(payload.text||'').length>8192?960000:210000))){cancel();throw Error('The response timed out. Your message is retained; check the local model and retry.');}};
 const bounded=promise=>Promise.race([promise,new Promise((_,reject)=>{const timer=setTimeout(()=>reject(Error('The app did not answer the connection check. Retry reconnects to the same request.')),10000);promise.finally(()=>clearTimeout(timer)).catch(()=>{});})]);
 try{
  check();let state=await bounded(api('reasoning/chat-start',{...payload,request_id:id}));
  while(true){
   check();options.onState?.(state);
   if(state.status==='complete')return {id,...state.result};
   if(state.status==='failed'){const error=Error(state.error||'The assistant could not finish this request.');error.serverFailed=true;throw error;}
   if(state.status==='cancelled')throw new DOMException('Reply stopped.','AbortError');
   await sleep(500);check();state=await bounded(api('reasoning/chat-status?id='+encodeURIComponent(id)));
  }
 }catch(error){error.requestId=id;throw error;}
}
