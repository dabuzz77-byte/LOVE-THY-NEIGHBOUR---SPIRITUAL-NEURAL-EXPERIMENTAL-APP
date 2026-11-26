(()=>{
 let busy=false;const seen=new Set();
 const delay=ms=>new Promise(r=>setTimeout(r,ms));
 const digest=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
 function details(){const heading=[...document.querySelectorAll('h2')].find(h=>h.textContent.trim()==='Item details');if(!heading)return null;let parent=heading;for(let i=0;i<7&&parent;i++,parent=parent.parentElement)if(parent.innerText.includes('Your prompt:'))return parent;return null}
 async function send(cfg,account,row,origin){const key=await digest(JSON.stringify(row));if(seen.has(key))return;const result=await chrome.runtime.sendMessage({type:'activity-sessions',account,source:origin,sessions:[row]});if(result?.error)throw Error(result.error);seen.add(key);if(seen.size>3000)seen.delete(seen.values().next().value)}
 async function snapshot(){if(busy)return;busy=true;try{
  const cfg=(await chrome.storage.local.get('config')).config;if(!cfg?.enabled)return;
  const accountLabel=[...document.querySelectorAll('[aria-label]')].map(e=>e.getAttribute('aria-label')).find(v=>v.startsWith('Google Account:'))||'';
  const account=accountLabel.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)?.[0];
  if(!account||account.toLowerCase()!==cfg.account.toLowerCase()){await chrome.runtime.sendMessage({type:'activity-state',message:'Waiting for the paired account identity on this page'});return}
  if(location.hostname==='myactivity.google.com'){
   let panel=details(),opened=false,card=null;
   if(!panel&&cfg.scanDetails){
    card=[...document.querySelectorAll('[aria-label="Card showing an activity from AI mode"]')].find(c=>!seen.has('card:'+c.innerText));
    const button=card?.querySelector('button[aria-label^="Open details of activity"]');
    if(button){button.click();opened=true;for(let i=0;i<20&&!panel;i++){await delay(200);panel=details()}}
   }
   if(panel){const text=panel.innerText;const title=(text.match(/Searched for ([^\n]+)/)||[])[1]||'AI Mode session';const stamp=(text.match(/(?:Today|Yesterday|\d+ [A-Za-z]+(?: \d{4})?) at \d+:\d+/)||[])[0]||'';
    await send(cfg,account,{source:'ai_mode',title:title.slice(0,500),date_label:stamp,content:text,url:'https://myactivity.google.com/myactivity?product=83',capture:'visible_page'},'https://myactivity.google.com/myactivity?product=83');
    if(card)seen.add('card:'+card.innerText);
    if(opened)[...document.querySelectorAll('button[aria-label="Close this dialogue"]')].at(-1)?.click();
   }else{
    const cards=[...document.querySelectorAll('[aria-label^="Card showing an activity from "]')].slice(0,50);
    for(const c of cards){const label=c.getAttribute('aria-label'),source=label.includes('YouTube')?'youtube':label.includes('AI mode')?'ai_mode':label.includes('Search')?'search':'google_activity';
     await send(cfg,account,{source,title:c.innerText.slice(0,200),date_label:'',content:c.innerText,url:'https://myactivity.google.com/',capture:'visible_page'},'https://myactivity.google.com/');}
   }
  }else if(['gemini.google.com','labs.google'].includes(location.hostname)){
   const text=(document.querySelector('main')||document.body).innerText;
   if(text.trim())await send(cfg,account,{source:location.hostname==='labs.google'?'flow':'gemini',title:document.title.slice(0,500),date_label:new Date().toISOString(),content:text,url:location.href,capture:'visible_page'},location.hostname==='labs.google'?'https://labs.google/fx/':'https://gemini.google.com/');
  }
 }catch(error){chrome.runtime.sendMessage({type:'activity-state',message:error.message}).catch(()=>{})}finally{busy=false}}
 setInterval(snapshot,15000);setTimeout(snapshot,5000);
})();
