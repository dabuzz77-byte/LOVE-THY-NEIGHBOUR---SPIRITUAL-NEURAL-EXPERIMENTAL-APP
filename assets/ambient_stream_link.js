// Source-only bridge: generated characters stay separate from model/authored text.
export function generatedStreams(payload) {
 const rows=Array.isArray(payload?.sources)?payload.sources:[payload];
 return rows.filter(s=>s&&s.stochastic===true&&s.predefined_text===false&&s.contains_model_text===false&&typeof s.text==='string')
  .map(s=>({...s,name:String(s.name||'generated stream').slice(0,100),text:s.text.slice(0,4096)}));
}
export function createAmbientStreamLink(api) {
 const sent=new Map();let sequence=0;
 return async sources=>{
  let captures=0,receipt=null;
  for(const source of generatedStreams({sources})) {
   if(!source.text||sent.get(source.name)===source.text)continue;
   // One bounded source per envelope, so Unicode cannot overflow the bus limit.
   receipt=await api('ambient-bus',{target:'all',kind:'stage-output',origin:'ambient-source-stream',payload:{...source,source_sequence:++sequence,provenance:'captured-generated-characters'}});
   if(!receipt.accepted)throw Error(receipt.error||'Source stream was not accepted');
   sent.set(source.name,source.text);captures++;
  }
  while(sent.size>64)sent.delete(sent.keys().next().value);
  return {captures,sequence,receipt:receipt?.event?.sequence};
 };
}
