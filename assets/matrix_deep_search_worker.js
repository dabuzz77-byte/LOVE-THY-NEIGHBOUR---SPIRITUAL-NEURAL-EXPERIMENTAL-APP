import {deepSearch} from './matrix_deep_search_core.js';
self.onmessage=e=>{try{const result=deepSearch(e.data.sources,e.data.options,p=>self.postMessage({id:e.data.id,progress:p}));self.postMessage({id:e.data.id,result});}catch(error){self.postMessage({id:e.data.id,error:error.message});}};
