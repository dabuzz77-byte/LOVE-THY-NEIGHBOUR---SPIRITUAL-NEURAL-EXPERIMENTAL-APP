import {searchAscii} from './ascii_wordsearch_core.js';
self.onmessage=e=>{try{self.postMessage({id:e.data.id,result:searchAscii(e.data.sources,e.data.options)});}catch(error){self.postMessage({id:e.data.id,error:error.message});}};
