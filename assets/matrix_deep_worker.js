import {deepSearch} from './matrix_deep_search_core.js';
import {sentenceSearch} from './matrix_sentence_core.js';
self.onmessage=e=>{const {id,mode,sources,options}=e.data;try{const progress=p=>self.postMessage({id,progress:p});const result=mode==='sentences'?sentenceSearch(sources,options,progress):deepSearch(sources,options,progress);self.postMessage({id,result});}catch(error){self.postMessage({id,error:error.message});}};
