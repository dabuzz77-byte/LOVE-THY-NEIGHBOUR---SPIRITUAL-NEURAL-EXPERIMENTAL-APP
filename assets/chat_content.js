/** Small safe text/Markdown renderer. User/model HTML is never interpreted. */
function inline(host,text){
 const regex=/(\*\*([^*]+)\*\*|`([^`]+)`|\[([^\]]+)\]\((https?:\/\/[^\s)]+)\))/g;let previous=0,match;
 while((match=regex.exec(text))){host.append(document.createTextNode(text.slice(previous,match.index)));let el;if(match[2]){el=document.createElement('strong');el.textContent=match[2];}else if(match[3]){el=document.createElement('code');el.textContent=match[3];}else{el=document.createElement('a');el.href=match[5];el.textContent=match[4];el.target='_blank';el.rel='noopener noreferrer';}host.append(el);previous=regex.lastIndex;}host.append(document.createTextNode(text.slice(previous)));
}
export function renderChatContent(host,text,copy){
 host.replaceChildren();const blocks=String(text).split(/```([^\n`]*)\n([\s\S]*?)```/g);
 for(let i=0;i<blocks.length;i+=3){
  const lines=blocks[i].split('\n');let list=null,table=null;
  for(let j=0;j<lines.length;j++){const line=lines[j];if(!line.trim()){list=table=null;continue;}
   if(/^\s*\|/.test(line)&&line.includes('|')){if(/^\s*\|?[\s:|\-]+\|?\s*$/.test(line))continue;if(!table){table=document.createElement('table');table.style.cssText='border-collapse:collapse;width:100%;margin:10px 0';host.append(table);}const row=document.createElement('tr');for(const value of line.trim().replace(/^\||\|$/g,'').split('|')){const cell=document.createElement(table.children.length?'td':'th');cell.style.cssText='padding:7px;border-bottom:1px solid #cbd5dc;text-align:left';inline(cell,value.trim());row.append(cell);}table.append(row);continue;}table=null;
   const heading=/^(#{1,4})\s+(.+)$/.exec(line),item=/^\s*(?:[-*]|\d+\.)\s+(.+)$/.exec(line);
   if(item){if(!list){list=document.createElement('ul');host.append(list);}const el=document.createElement('li');inline(el,item[1]);list.append(el);continue;}list=null;
   const el=document.createElement(heading?'h'+Math.min(5,heading[1].length+2):'p');inline(el,heading?heading[2]:line);host.append(el);
  }
  if(i+2<blocks.length){const box=document.createElement('section'),bar=document.createElement('div'),label=document.createElement('span'),button=document.createElement('button'),pre=document.createElement('pre'),code=document.createElement('code');box.className='n-code';bar.className='n-code-bar';label.textContent=blocks[i+1].trim()||'Code';button.textContent='Copy code';button.onclick=()=>copy(blocks[i+2]);code.textContent=blocks[i+2];pre.append(code);bar.append(label,button);box.append(bar,pre);host.append(box);}
 }
}
