async function captureVisible(selectionOnly){
 if(document.querySelector('input[type="password"]'))return {error:'Password-entry page excluded.'};
 const selection=String(window.getSelection()||'').trim();
 if(selectionOnly&&!selection)return {error:'Select the work you want to send first.'};
 let text=selection;
 if(!text){
  const root=document.querySelector('main,article,[role="main"]')||document.body;const parts=[];let bytes=0;
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode(node){const p=node.parentElement;if(!p||!p.getClientRects().length||p.closest('script,style,noscript,nav,header,footer,input,textarea,select,[contenteditable],[hidden],[aria-hidden="true"]'))return NodeFilter.FILTER_REJECT;const style=getComputedStyle(p);return style.display==='none'||style.visibility==='hidden'?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT;}});
  while(walker.nextNode()){const t=walker.currentNode.textContent.trim();if(!t)continue;bytes+=new TextEncoder().encode(t).length+1;if(bytes>24000)return {error:'This page exceeds 24,000 bytes. Select a smaller part to send; nothing was silently truncated.'};parts.push(t)}text=parts.join('\n');
 }
 if(!text)return {error:'No visible work found.'};if(new TextEncoder().encode(text).length>24000)return {error:'Selection exceeds 24,000 bytes.'};
 return {text,url:location.origin+location.pathname,source_hint:new URL(location.href).searchParams.get('udm')==='50'?'ai_mode':''};
}
let working=false;
async function capture(tab,selectionOnly=false){
 if(working)return {error:'A capture is already running.'};working=true;
 try{
  if(!tab?.id||tab.incognito||!tab.url?.startsWith('https://'))throw Error('Use a normal HTTPS page outside private browsing.');
  const settings=await chrome.storage.local.get(['key','endpoint','fingerprints','account']);
  if(!settings.key)throw Error('Pair the extension with Neural App first.');
  const endpoint=new URL(settings.endpoint||'http://127.0.0.1:8797/api/automatic-flow/browser');
  if(endpoint.protocol!=='http:'||endpoint.hostname!=='127.0.0.1'||endpoint.pathname!=='/api/automatic-flow/browser')throw Error('Use the local Neural App bridge endpoint.');
  const result=(await chrome.scripting.executeScript({target:{tabId:tab.id},func:captureVisible,args:[selectionOnly]}))[0]?.result;
  if(result?.error)throw Error(result.error);if(!result?.text)throw Error('No visible text returned.');
  const fingerprint=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(result.url+'\n'+result.text)))].map(n=>n.toString(16).padStart(2,'0')).join('');
  const previous=settings.fingerprints||{};if(previous[tab.id]===fingerprint)return {status:'Unchanged work already queued.'};
  const response=await fetch(endpoint.href,{method:'POST',headers:{'Content-Type':'application/json','X-Neural-Work-Key':settings.key,'X-Neural-Extension-Id':chrome.runtime.id},body:JSON.stringify({...result,account:settings.account||''}),signal:AbortSignal.timeout(15000)});
  const value=await response.json();if(!response.ok)throw Error(value.error||'App connection failed');
  const fingerprints=Object.fromEntries(Object.entries(previous).slice(-127));fingerprints[tab.id]=fingerprint;
  const status=`${value.accepted_chunks} new chunks accepted locally · ${new Date().toLocaleTimeString()}`;
  await chrome.storage.local.set({fingerprints,lastStatus:status});return {status};
 }catch(e){await chrome.storage.local.set({lastStatus:e.message});return {error:e.message}}finally{working=false}
}
chrome.runtime.onMessage.addListener((message,sender,reply)=>{
 if(sender.id!==chrome.runtime.id)return false;
 if(message.op==='capture'){chrome.tabs.query({active:true,currentWindow:true}).then(tabs=>capture(tabs[0],message.selectionOnly)).then(reply);return true}
 return false;
});
async function automaticCapture(){const settings=await chrome.storage.local.get(['enabled','sites','allPermittedTabs','allSites']);if(!settings.enabled)return;const tabs=await chrome.tabs.query(settings.allPermittedTabs?{}:{active:true});for(const tab of tabs){try{const origin=new URL(tab.url).origin;if(settings.allSites||(settings.sites||[]).includes(origin))await capture(tab,false)}catch{}}}
chrome.alarms.onAlarm.addListener(alarm=>{if(alarm.name==='neural-work')automaticCapture()});
chrome.runtime.onInstalled.addListener(()=>{chrome.alarms.create('neural-work',{periodInMinutes:5});chrome.storage.local.setAccessLevel?.({accessLevel:'TRUSTED_CONTEXTS'})});
chrome.runtime.onStartup.addListener(()=>chrome.alarms.create('neural-work',{periodInMinutes:5}));
let syncing=false;
async function syncBridge(){
 if(syncing)return;syncing=true;
 try{
  const s=await chrome.storage.local.get(['key','endpoint','inventory','bridgeCursor','bridgeInbox']);if(!s.key)return;
  const u=new URL(s.endpoint||'http://127.0.0.1:8797/api/automatic-flow/browser');if(u.protocol!=='http:'||u.hostname!=='127.0.0.1'||u.pathname!=='/api/automatic-flow/browser')throw Error('Use the local bridge endpoint.');
  let tabs=[],omitted=0;if(s.inventory&&await chrome.permissions.contains({permissions:['tabs']})){const all=(await chrome.tabs.query({})).filter(t=>!t.incognito&&t.url?.startsWith('https://'));omitted=Math.max(0,all.length-128);tabs=all.slice(0,128).map(t=>{const x=new URL(t.url);return {url:x.origin+x.pathname,title:t.title,active:t.active,audible:t.audible,pinned:t.pinned,status:t.status};});}
  const response=await fetch(u.href,{method:'POST',headers:{'Content-Type':'application/json','X-Neural-Work-Key':s.key,'X-Neural-Extension-Id':chrome.runtime.id},body:JSON.stringify({bridge_action:'sync',after:s.bridgeCursor||0,tabs,inventory_enabled:!!s.inventory,omitted_tabs:omitted}),signal:AbortSignal.timeout(15000)});const r=await response.json();if(!response.ok)throw Error(r.error||'Bridge connection failed');
  const inbox=[...(s.bridgeInbox||[]),...(r.messages||[])];const unique=[...new Map(inbox.map(x=>[x.id,x])).values()].slice(-64);await chrome.storage.local.set({bridgeCursor:r.cursor,bridgeInbox:unique,bridgeState:r.app,bridgeTime:r.time,bridgeStatus:r.history_gap?'Connected; older return messages expired.':'Connected in both directions.'});return r;
 }catch(e){await chrome.storage.local.set({bridgeStatus:e.message});return {error:e.message};}finally{syncing=false;}
}
chrome.runtime.onMessage.addListener((message,sender,reply)=>{if(sender.id!==chrome.runtime.id)return false;if(message.op==='bridge-sync'){syncBridge().then(reply);return true;}return false;});
chrome.alarms.onAlarm.addListener(a=>{if(a.name==='neural-bridge-sync')syncBridge();});
chrome.runtime.onInstalled.addListener(()=>chrome.alarms.create('neural-bridge-sync',{periodInMinutes:1}));
chrome.runtime.onStartup.addListener(()=>chrome.alarms.create('neural-bridge-sync',{periodInMinutes:1}));
