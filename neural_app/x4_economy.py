"""Independent, bounded resource-flow model informed by a private game-data import."""
import json,math,time
from .translation import translate_bits
from .gnostic_four import CHECKS,decide

class Economy:
    def __init__(self,runtime):
        self.runtime=runtime;self.folder=runtime.data/'x4-import';self.path=runtime.data/'x4-economy-settings.json'
        self.config={'enabled':True,'output':'medicalsupplies','threat':.12,'defence':.8,'demand':.7}
        if self.path.exists():self.config.update(json.loads(self.path.read_text(encoding='utf-8')))
        self.imported=json.loads((self.folder/'economy.json').read_text(encoding='utf-8')) if (self.folder/'economy.json').exists() else None
        self.wares={w['id']:w for w in self.imported['wares']} if self.imported else {};self.nodes=[];self.edges=[];self.ticks=0;self.last=0;self.next_learn=0;self.pending=None;self.last_receipt=None;self.events=[];self.delivered=0.;self.unmet=0.;self.configured_at=time.time()
        if self.wares:self.rebuild()
    def rebuild(self):
        if self.config['output'] not in self.wares:self.config['output']='energycells'
        self.nodes=[];self.edges=[];seen=set()
        def visit(ident,depth):
            if ident in seen or len(seen)>=28:return
            seen.add(ident);row=self.wares.get(ident)
            if not row:return
            recipe=next((r for r in row['recipes'] if r['method']=='default'),row['recipes'][0] if row['recipes'] else None)
            self.nodes.append({'id':ident,'label':ident.replace('_',' '),'depth':depth,'stock':200.,'recipe':recipe,'role':'producer' if recipe else 'raw resource','availability':1.,'produced':0.,'consumed':0.})
            if recipe and depth<5:
                for dep in recipe['inputs']:
                    self.edges.append({'from':dep['ware'],'to':ident,'amount_per_cycle':dep['amount']});visit(dep['ware'],depth+1)
        visit(self.config['output'],0);self.nodes.sort(key=lambda n:-n['depth'])
    def configure(self,body):
        if not isinstance(body,dict) or set(body)-set(self.config):raise ValueError('Unsupported economy option')
        new={**self.config,**body}
        if type(new['enabled']) is not bool:raise ValueError('Enabled must be boolean')
        if new['output'] not in self.wares:raise ValueError('Choose an imported ware')
        for key in ('threat','defence','demand'):
            if isinstance(new[key],bool) or not isinstance(new[key],(float,int)) or not math.isfinite(new[key]) or not 0<=new[key]<=1:raise ValueError('Use 0–1 for '+key)
        rebuild=new['output']!=self.config['output'];self.config=new
        if rebuild:self.rebuild()
        self.path.write_text(json.dumps(self.config),encoding='utf-8');return self.view()
    def step(self):
        now=time.monotonic()
        if not self.config['enabled'] or not self.wares or now-self.last<2:return
        self.last=now;self.ticks+=1;index={n['id']:n for n in self.nodes};threat=self.config['threat'];defence=self.config['defence'];prob=threat*(1-.8*defence)
        for i,node in enumerate(self.nodes):
            # Reproducible disruption scenario, not an attack on a device or person.
            draw=(math.sin(self.ticks*12.9898+i*78.233)*43758.5453)%1
            node['availability']=0. if draw<prob else 1.
            if not node['availability']:continue
            recipe=node['recipe']
            if recipe:
                cycles=2/max(1,recipe['cycle_seconds']);inputs=recipe['inputs']
                for dep in inputs:
                    if dep['ware'] not in index:cycles=0;break
                    if dep['amount']>0:cycles=min(cycles,index[dep['ware']]['stock']/dep['amount'])
                for dep in inputs:
                    used=cycles*dep['amount'];index[dep['ware']]['stock']=max(0.,index[dep['ware']]['stock']-used);index[dep['ware']]['consumed']+=used
                produced=cycles*recipe['output'];node['stock']=min(1000000.,node['stock']+produced);node['produced']+=produced
            else:node['stock']=min(1000000.,node['stock']+1.6)
        output=index[self.config['output']];demand=self.config['demand']*4
        # Need-first allocation uses explicit illustrative demand; no real people are profiled.
        from .care_plan import plan
        allocation=plan({'budget':min(2.,output['stock']/max(1,demand)),'nodes':[{'label':'Illustrative high-need end-user demand','need':1.,'urgency':.9,'protection':.1},{'label':'Illustrative ordinary end-user demand','need':.6,'urgency':.5,'protection':.4},{'label':'Infrastructure upkeep demand','need':.4,'urgency':.7,'protection':.7}]})
        used=min(output['stock'],demand*allocation['coverage']);output['stock']-=used;self.delivered+=used;self.unmet+=max(0,demand-used)
        self.events=(self.events+[{'tick':self.ticks,'model_allocated':used,'model_unmet':max(0,demand-used),'failures':sum(n['availability']==0 for n in self.nodes),'need_first':allocation['priority_order']}])[-24:]
        if self.pending:
            job=self.runtime.result(self.pending)
            if job['status'] in ('complete','error'):self.last_receipt=job.get('receipt');self.pending=None
        if now>=self.next_learn and not self.pending and self.runtime.settings['learning'] and self.runtime.queue.qsize()<3:
            self.next_learn=now+30
            job=self.runtime.submit('pipeline',{'text':'Resource-flow model: '+self.config['output']+'; choose care and protect availability.','sections':['x4_economy','care','gnostic_four','inference','beacon'],'section_inputs':{'gnostic_four':{'lesson':'truevirtue'}}});self.pending=job['id']
    def measure(self,body=None):
        if not self.wares:return {'status':'AWAITING_IMPORT','required':'Import the owner’s game ware data with the read-only indexer'}
        bits=''.join('1' if n['availability']>0 else '0' for n in self.nodes) or '0'
        policy=decide({'candidates':[{'id':'protect_and_supply','label':'Protect availability, allocate by need, preserve choice and repair','benefit':.8,'need':.9,'confidence':.8,'cost':.2,'checks':dict.fromkeys(CHECKS,True)}]})
        from .infrastructure_lab import process as infrastructure
        protected_resources=infrastructure(self.runtime,{})
        return {'status':'COMPLETE','infrastructure_planning':protected_resources,'service_floor':'Preserve infrastructure reserves and existing protection; remaining capacity supports explicit need-first planning.','ticks':self.ticks,'nodes':self.nodes,'edges':self.edges,'config':self.config,'allocated_model_units':self.delivered,'unmet_model_units':self.unmet,'availability_bits':bits,'transport':translate_bits(bits),'policy':policy,'counterfactual_expected_failure_without_defence':self.config['threat'],'expected_failure_with_defence':self.config['threat']*(1-.8*self.config['defence']),'events':self.events[-8:],'scope':'Independent resource/availability simulation using imported game recipe facts. Demand, disruption and defence coefficients are authored scenarios. No actual network attacks, aid deliveries or device control.'}
    def view(self):
        return {**self.measure(),'import':{k:self.imported[k] for k in ('indexed_entries','ware_count','production_wares','selected_base_library','scope')} if self.imported else None,'choices':[{'id':w['id'],'label':w['id'].replace('_',' '),'recipes':len(w['recipes'])} for w in self.wares.values() if 'economy' in w.get('tags','').split()],'last_learning_receipt':self.last_receipt,'mapping':{'ware':'A finite resource or work item','station':'Processing infrastructure','cargo route':'Configured data/resource route','end-user demand':'Explicit need rather than a provider service','attack scenario':'Simulated interruption, never a real exploit','defence':'Redundancy and protection of availability','price':'A game input, not a person’s worth'},'world_grid':'A local scenario for planning and learning. Real-world allocations require identified resources, participant consent and verified conditions.'}
