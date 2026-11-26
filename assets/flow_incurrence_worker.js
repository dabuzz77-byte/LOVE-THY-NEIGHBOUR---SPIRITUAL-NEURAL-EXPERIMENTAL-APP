import {planIncursion} from './flow_incurrence.js';
self.onmessage=event=>{const {id,nodes,selected,direction,hops}=event.data;try{const paths=planIncursion(nodes,selected,direction,hops,512),offset=paths.length?(id*48)%paths.length:0;self.postMessage({id,paths:paths.slice(offset).concat(paths.slice(0,offset)).slice(0,48)});}catch(error){self.postMessage({id,error:error.message});}};
