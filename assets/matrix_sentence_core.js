import {fingerprint} from './matrix_deep_search_core.js';
export function sentenceSearch(sources,options={},progress=()=>{}){
 const selected=sources.filter(s=>String(s.text||'').length),budget=Math.max(65536,Math.min(16*1048576,Number(options.budget)||1048576)),share=Math.floor(budget/Math.max(1,selected.length)),minimum=Math.max(2,Math.min(20,Number(options.minWords)||3)),limit=Math.max(100,Math.min(20000,Number(options.results)||5000));
 const sentences=[],phrases=new Map(),stageReports=[],unique=new Set();let total=0,candidates=0;
 const wordPattern=/[\p{L}\p{M}][\p{L}\p{M}'’\d-]*/gu;
 function inspect(text,source,layout,base=0){
  function* windows(){for(const m of text.matchAll(/[^\n.!?。！？]+[.!?。！？]*/gu)){for(let offset=0;offset<m[0].length;offset+=436){yield {0:m[0].slice(offset,offset+500),index:m.index+offset};if(offset+500>=m[0].length)break;}}}
  const segments=windows();
  for(const match of segments){const raw=match[0],candidate=raw.trim(),tokens=[...candidate.matchAll(wordPattern)],cjk=/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]/u.test(candidate),letters=(candidate.match(/[\p{L}\p{M}]/gu)||[]).length,ratio=letters/Math.max(1,Array.from(candidate).length),terminated=/[.!?。！？]$/.test(candidate);
   if(tokens.length>=minimum||(cjk&&letters>=8&&terminated)){
    if(ratio>=.45){const key=source+'|'+layout+'|'+(base+match.index);if(!unique.has(key)){unique.add(key);candidates++;if(sentences.length<limit)sentences.push({source,layout,offset:base+match.index,string:candidate,words:tokens.length,letters,letter_ratio:ratio,terminated,kind:terminated?'punctuated sentence candidate':'unpunctuated phrase candidate',score:Math.round(100*(.4*ratio+.3*Math.min(1,tokens.length/8)+.3*Number(terminated)))});}}
   }
   for(let n=2;n<=Math.min(6,tokens.length);n++)for(let i=0;i+n<=tokens.length;i++){const first=tokens[i],last=tokens[i+n-1],part=candidate.slice(first.index,last.index+last[0].length);if(part.length>160||/[{}\[\]<>_=]/.test(part))continue;const key=part.toLocaleLowerCase();if(!phrases.has(key)){if(phrases.size>=50000)continue;phrases.set(key,{string:part,count:0,stages:new Set(),first:{source,layout,offset:base+match.index+first.index},words:n});}const r=phrases.get(key);r.count++;r.stages.add(source);}
  }
 }
 for(let i=0;i<selected.length;i++){
  const source=selected[i],all=Array.from(String(source.text)),cap=Math.min(share,1048576),start=all.length>cap?((Number(options.pass)||0)*Math.max(1,cap-512))%all.length:0,text=all.slice(start,start+cap).join('');total+=Array.from(text).length;const before=candidates;inspect(text,source.name,'literal source text',start);
  if(options.directional){const width=Math.max(8,Math.min(256,Number(options.width)||64)),chars=Array.from(text.replace(/[\r\n]/g,'')),height=Math.ceil(chars.length/width),at=(x,y)=>chars[y*width+x]||'';
   // Each ray is visited once. Text is not assembled from disconnected word hits.
   const ray=(x,y,dx,dy,label)=>{let line='';while(x>=0&&x<width&&y>=0&&y<height){line+=at(x,y);x+=dx;y+=dy;}if(line.length>2){inspect(line,source.name,label);if(options.reverse)inspect(Array.from(line).reverse().join(''),source.name,label+' reversed');}};
   for(let x=0;x<width;x++){ray(x,0,0,1,'column '+(x+1));ray(x,0,1,1,'diagonal SE top '+(x+1));ray(x,0,-1,1,'diagonal SW top '+(x+1));}for(let y=1;y<height;y++){ray(0,y,1,1,'diagonal SE left '+(y+1));ray(width-1,y,-1,1,'diagonal SW right '+(y+1));}for(let y=0;y<height;y++)ray(0,y,1,0,'reflow row '+(y+1));
  }
  stageReports.push({source:source.name,characters:all.length,start,end:start+Array.from(text).length,complete:all.length<=cap,hash:fingerprint(text),candidates:candidates-before});progress({stage:i+1,stages:selected.length,source:source.name,characters:total});
 }
 const allPhrases=[...phrases.values()].sort((a,b)=>b.count-a.count).map(r=>({...r,stages:[...r.stages]}));
 return {time:new Date().toISOString(),total,candidates,sentences:sentences.sort((a,b)=>b.score-a.score),phrases:allPhrases.slice(0,limit),repeated:allPhrases.filter(r=>r.count>1).slice(0,limit),crossStage:allPhrases.filter(r=>r.stages.length>1).slice(0,limit),stages:stageReports,limits:{budget,retained_rows:limit,phrase_candidates:phrases.size,phrase_cap:50000},scope:'Literal or explicitly labelled directional strings. Scores describe punctuation, length and letter density; they are not a truth, intention or authorship score.'};
}
