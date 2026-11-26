import {searchAscii} from './ascii_wordsearch_core.js';
export function fingerprint(text){let h=2166136261;for(const c of text)h=Math.imul(h^c.codePointAt(0),16777619);return (h>>>0).toString(16).padStart(8,'0');}
function decodeText(bytes){try{const text=new TextDecoder('utf-8',{fatal:true}).decode(new Uint8Array(bytes));return text&&!/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/.test(text)?text:null;}catch{return null;}}
export function deepSearch(sources,options={},progress=()=>{}){
 const budget=Math.max(65536,Math.min(16*1048576,Number(options.budget)||4*1048576)),perSource=Math.max(32768,Math.min(4*1048576,Number(options.perSource)||1048576)),maxRows=Math.max(100,Math.min(20000,Number(options.results)||5000));
 const selected=sources.filter(s=>s&&String(s.text||'').length),share=Math.floor(budget/Math.max(1,selected.length)),words=new Map(),numbers=new Map(),grams=new Map(),dictionary=[],decoded=[],stages=[],sentence_inputs=[],characters=new Map();let total=0,dictionaryCount=0,tokenCount=0,numberCount=0;
 const add=(map,key,stage,position,extra={})=>{if(!map.has(key)){if(map.size>=100000)return;map.set(key,{string:key,count:0,stages:new Set(),first:{stage,position},...extra});}const r=map.get(key);r.count++;r.stages.add(stage);};
 const widths=[...new Set(String(options.widths||'32,64,128').split(',').map(Number).filter(n=>Number.isInteger(n)&&n>=4&&n<=256))].slice(0,4);if(!widths.length)widths.push(64);
 for(let index=0;index<selected.length;index++){
  const source=selected[index],original=Array.from(String(source.text)),limit=Math.min(perSource,share),chunkStart=original.length>limit?((Number(options.pass)||0)*Math.max(1,limit-127))%original.length:0,chars=original.slice(chunkStart,chunkStart+limit),text=chars.join(''),name=source.name;total+=chars.length;
  const utf16Offsets=[];let utf16=0;chars.forEach((c,i)=>{utf16Offsets[utf16]=i;utf16+=c.length;});utf16Offsets[utf16]=chars.length;
  const counts=new Map();for(const c of chars){counts.set(c,(counts.get(c)||0)+1);characters.set(c,(characters.get(c)||0)+1);}let entropy=0;for(const n of counts.values()){const p=n/Math.max(1,chars.length);entropy-=p*Math.log2(p);}
  const stage={source:name,kind:source.kind||'captured ASCII',characters:original.length,scanned:chars.length,start:chunkStart,end:chunkStart+chars.length,complete:chars.length===original.length,hash:fingerprint(text),unique_characters:counts.size,entropy_bits_per_character:entropy,word_tokens:0,number_tokens:0,dictionary_matches:0};
  for(const m of text.matchAll(/[\p{L}\p{M}][\p{L}\p{M}\p{N}'’_-]{1,63}/gu)){stage.word_tokens++;tokenCount++;add(words,options.caseSensitive?m[0]:m[0].toLocaleLowerCase(),name,utf16Offsets[m.index]+chunkStart,{original:m[0]});}
  for(const m of text.matchAll(/[-+]?(?:0x[\da-fA-F]+|0b[01]+|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)/g)){
   const raw=m[0],numeric=/^[-+]?0[xb]/i.test(raw)?Number(raw):Number(raw),digits=raw.replace(/\D/g,'');stage.number_tokens++;numberCount++;
   add(numbers,raw,name,utf16Offsets[m.index]+chunkStart,{value:Number.isFinite(numeric)?numeric:null,palindrome:digits.length>2&&digits===[...digits].reverse().join(''),repeated_digit:digits.length>2&&new Set(digits).size===1,binary_candidate:/^[01]{8,}$/.test(raw),hex_candidate:/^0x[\da-f]+$/i.test(raw)});
  }
  // Fixed-size n-grams are counted once at every position, including overlaps.
  if(options.ngrams!==false)for(const size of [2,3,4,5,6,8])for(let i=0;i+size<=chars.length;i++){const key=chars.slice(i,i+size).join('');if(!/^\s+$/.test(key))add(grams,key,name,i+chunkStart,{size});}
  for(const m of text.matchAll(/(?:\b[01]{8,4096}\b)|(?:\b0x[\da-fA-F]{2,4096}\b)/g)){
   if(decoded.length>=maxRows)break;const isHex=m[0].startsWith('0x'),raw=isHex?m[0].slice(2):m[0],step=isHex?2:8;if(raw.length%step)continue;const bytes=[];for(let i=0;i<raw.length;i+=step)bytes.push(parseInt(raw.slice(i,i+step),isHex?16:2));const value=decodeText(bytes);if(value)decoded.push({source:name,offset:utf16Offsets[m.index]+chunkStart,encoding:isHex?'hex → UTF-8':'8-bit binary → UTF-8',original:m[0],string:value});
  }
  if(options.dictionary!==false){
   const originalLayout={label:'original lines',chars,positions:chars.map((_,i)=>i),width:widths[0]},reflow=chars.map((c,i)=>({c,i})).filter(r=>r.c!=='\r'&&r.c!=='\n');
   const layouts=options.multiWidth===false?[originalLayout]:[originalLayout,...widths.map(width=>({label:width+'-column reflow',chars:reflow.map(r=>r.c),positions:reflow.map(r=>r.i),width}))],seenDictionary=new Set();
   for(const layout of layouts)for(let offset=0;offset<layout.chars.length;offset+=32640){const part=layout.chars.slice(offset,offset+32768).join(''),r=searchAscii([{name,text:part}],{...options,width:layout.width,pass:0});for(const m of r.matches){const source_character_path=m.path.map(i=>chunkStart+layout.positions[offset+i]),identity=JSON.stringify([m.lang,m.word,source_character_path]);if(seenDictionary.has(identity))continue;seenDictionary.add(identity);stage.dictionary_matches++;dictionaryCount++;if(dictionary.length<maxRows)dictionary.push({...m,layout:layout.label,chunk_offset:chunkStart+offset,source_character_path});}}
  }
  sentence_inputs.push({name,text,kind:'wordsearch pinned character / token stream',start:chunkStart,hash:stage.hash});
  stages.push(stage);progress({stage:index+1,stages:selected.length,source:name,characters:total});
 }
 const rows=map=>[...map.values()].sort((a,b)=>b.count-a.count||a.string.localeCompare(b.string)).map(r=>({...r,stages:[...r.stages]}));
 const wordRows=rows(words),numberRows=rows(numbers),gramRows=rows(grams).filter(r=>r.count>1),concordance=[...wordRows,...numberRows].filter(r=>r.stages.length>1).sort((a,b)=>b.stages.length-a.stages.length||b.count-a.count);
 return {time:new Date().toISOString(),stages,total,source_count:selected.length,word_tokens:tokenCount,number_tokens:numberCount,dictionary_count:dictionaryCount,dictionary,sentence_inputs,words:wordRows.slice(0,maxRows),numbers:numberRows.slice(0,maxRows),repeats:gramRows.slice(0,maxRows),concordance:concordance.slice(0,maxRows),decoded,characters:[...characters].sort((a,b)=>b[1]-a[1]).slice(0,1024),limits:{budget,perSource,retained_rows:maxRows,word_candidates:words.size,number_candidates:numbers.size,ngram_candidates:grams.size,candidate_cap:100000},scope:'Pinned snapshots of available Matrix / Flux ASCII. Reflow layouts are explicit analytical arrangements; matches are observed strings, not a consciousness measurement.'};
}
