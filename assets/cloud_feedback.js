// Exact serialization of the displayed cloud's rounded coordinates and source text.
export function encodeCloudFeedback(capture){
 const source=new TextEncoder().encode(capture.source_text||''),glyphs=capture.glyphs||[];
 const bytes=new Uint8Array(20+source.length+glyphs.length*20),view=new DataView(bytes.buffer);
 bytes.set([77,80,67,49]);view.setUint32(4,glyphs.length,true);view.setUint32(8,capture.frame>>>0,true);view.setUint32(12,Array.from(capture.source_text||'').length,true);view.setUint32(16,source.length,true);bytes.set(source,20);
 glyphs.forEach((g,i)=>{const offset=20+source.length+i*20;view.setUint32(offset,g.char.codePointAt(0),true);view.setInt32(offset+4,g.x,true);view.setInt32(offset+8,g.y,true);view.setFloat64(offset+12,g.probability||0,true);});return bytes;
}
export function createCloudFeedback(capture){return {ascii:Array.from(capture.rendered_text||''),bytes:encodeCloudFeedback(capture),asciiCursor:0,bitCursor:0,frame:capture.frame};}
export function takeCloudFeedback(state,asciiOn,binaryOn,limit=256){
 const chars=[];if(asciiOn){chars.push(...state.ascii.slice(state.asciiCursor,state.asciiCursor+limit));state.asciiCursor=Math.min(state.ascii.length,state.asciiCursor+limit);}
 if(binaryOn){const end=Math.min(state.bytes.length*8,state.bitCursor+limit);for(;state.bitCursor<end;state.bitCursor++)chars.push(String((state.bytes[state.bitCursor>>3]>>(7-(state.bitCursor&7)))&1));}
 return {chars,complete:(!asciiOn||state.asciiCursor>=state.ascii.length)&&(!binaryOn||state.bitCursor>=state.bytes.length*8),asciiProcessed:state.asciiCursor,bitsProcessed:state.bitCursor,totalBits:state.bytes.length*8,frame:state.frame};
}
