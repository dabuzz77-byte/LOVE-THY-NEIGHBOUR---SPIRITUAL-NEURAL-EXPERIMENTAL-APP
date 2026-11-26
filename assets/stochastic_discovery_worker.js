import {discoverStreams} from './stochastic_discovery_core.js';
self.onmessage=e=>{try{self.postMessage({id:e.data.id,result:discoverStreams(e.data.sources,e.data.options)});}catch(error){self.postMessage({id:e.data.id,error:error.message});}};
