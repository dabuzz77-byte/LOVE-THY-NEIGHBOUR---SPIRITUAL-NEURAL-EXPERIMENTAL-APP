"""Source-backed coin casts and a separately identified ethical app adaptation."""
import hashlib,json,secrets,time
from pathlib import Path
from .gnostic_four import decide
from .translation import translate_bits

ROOT=Path(__file__).resolve().parents[1]
COUNTERS={
 'truthful':'Replace misleading claims with a clear account of capabilities, sources and limitations.',
 'non_harm':'Pause the harmful proposal; redesign around protection, de-escalation and repair.',
 'consent':'Offer an understandable invitation through an authorised channel and wait for an informed choice.',
 'privacy':'Minimise collection, keep private material local and use only explicitly configured recipients.',
 'fairness':'Listen to affected people, remove unjust barriers and direct appropriate help toward greater need.',
 'repairable':'Make the next step reversible or define a practical recovery path before proceeding.',
 'reviewed':'Obtain a meaningful review of the proposal and its likely consequences before selecting it.'}

class Changes:
    def __init__(self,runtime):
        self.runtime=runtime;self.rows=json.loads((ROOT/'references/iching/hexagrams.json').read_text(encoding='utf-8'))
        self.by_bits={r['bits_bottom_to_top']:r for r in self.rows};self.path=runtime.data/'iching-settings.json'
        self.enabled=self.path.exists() and json.loads(self.path.read_text(encoding='utf-8')).get('enabled') is True
        self.next_at=0;self.pending=None;self.last=None;self.cycles=0;self.error=None;self.mode_index=0;self.pair=None;self.by_mode={}
    def configure(self,enabled):
        if type(enabled) is not bool:raise ValueError('Enabled must be boolean')
        self.enabled=enabled;self.path.write_text(json.dumps({'enabled':enabled}),encoding='utf-8');return self.view()
    def view(self):
        return {'enabled':self.enabled,'cycles':self.cycles,'pending':self.pending,'last':self.last,'error':self.error,
            'interval_seconds':30,'per_mode_interval_seconds':60,'latest_by_mode':self.by_mode,'feed':'Hydrogen → stellar → biosphere model, mixed with fresh OS entropy; the two modes share each sampled cast.','hexagrams':len(self.rows),'source':json.loads((ROOT/'references/iching/source.json').read_text(encoding='utf-8')),
            'scope':'Traditional three-coin consultation plus separate rule-based Neural App reflection; casts are not guaranteed predictions.'}
    def process(self,body):
        question=body.get('question','How can this app make its next step more truthful and caring?')
        if not isinstance(question,str) or not 1<=len(question)<=1200:raise ValueError('Use a question of 1–1200 characters')
        mode=body.get('mode','adapted')
        if mode not in ('traditional','adapted'):raise ValueError('Choose traditional or adapted')
        lines=body.get('lines')
        if lines is None:lines=[sum(2+secrets.randbelow(2) for _ in range(3)) for _ in range(6)]
        if not isinstance(lines,list) or len(lines)!=6 or any(type(n) is not int or n not in (6,7,8,9) for n in lines):raise ValueError('Six line values must each be 6, 7, 8 or 9, bottom to top')
        bits=''.join('1' if n in (7,9) else '0' for n in lines);changed=''.join('1' if n in (6,7) else '0' for n in lines)
        primary=self.by_bits[bits];related=self.by_bits[changed];changing=[i+1 for i,n in enumerate(lines) if n in (6,9)]
        def brief(row):return {k:row[k] for k in ('number','title','glyph','bits_bottom_to_top')}|{'judgment':row['judgment'][:900]}
        value={'status':'COMPLETE','question':question,'mode':mode,'method':'Three fair coins per line; tails=2, heads=3. Six lines cast bottom to top. 6/9 change; 7/8 remain.',
            'lines':lines,'primary':brief(primary),'related':brief(related),'changing_lines':changing,
            'changing_passages':[{'line':r['line'],'text':r['text'][:500]} for r in primary['lines'] if r['line'] in changing],
            'interpretation_method':'Read primary judgment, each changing line in ascending order, then related judgment. This is one disclosed reading convention, not the only traditional method.',
            'binary':translate_bits(bits),'source_url':'https://tianmu.org/good-work-library/confucian/general-texts/the-i-ching-james-legge',
            'reflection_questions':['What in this situation is changing?','What demands patience, clarity or restraint?','What action protects life while allowing correction?'],
            'scope':'Source passages and reflective questions, not a guaranteed forecast or instructions to harm.'}
        if 'model_feed' in body:
            value['model_feed']=body['model_feed']
            value['method']='Model-conditioned stochastic three-coin equivalent; see recorded model feed, entropy and exact sampling rule.'
        if mode=='adapted':
            decision=decide(body);counters=[]
            for action in decision['actions']:
                if not action['eligible']:
                    repairs=[COUNTERS[k] for i,k in enumerate(decision['checks']) if action['check_bits'][i]=='0']
                    if action['cost']>decision['budget']:repairs.append('Reduce scope or secure resources without taking them from someone else.')
                    if action['confidence']<.5:repairs.append('Study impact and listen before increasing confidence.')
                    if action['benefit']<=0:repairs.append('Identify a concrete life-serving benefit before selecting the action.')
                    counters.append({'action':action['id'],'blocked_reasons':action['reasons'],'constructive_counters':repairs})
            value['app_adaptation']={'decision':decision,'harm_analysis':counters,
                'neural_context':{'learned_updates':self.runtime.model.updates if self.runtime.model else 0,'field_ticks':self.runtime.field.ticks,
                    'public_research_topics':list(self.runtime.research.view()['topics'])},
                'principle':'Analyse harmful possibilities, select only proposals satisfying the declared good-action criteria, and propose constructive repairs.',
                'distinction':'This policy adaptation and runtime context are modern additions. The coin cast is not determined by neural weights, and its result does not overrule failed safety/care checks.'}
        return value
    def sample_model(self):
        source=self.runtime.engine('sovereign',{'text':'I Ching: hydrogen to star to Earth; choose care.'})
        model={k:source[k] for k in ('occupancy','matrix_score','stellar_flux_model_wm2','biosphere_carrier_hz','conditioned_hz')}
        model['carrier']=source['carrier'];model['field_ticks']=self.runtime.field.ticks
        canonical=json.dumps(model,sort_keys=True,allow_nan=False).encode('utf-8');digest=hashlib.sha256(canonical).digest()
        entropy=secrets.token_bytes(3)
        mixed=bytes(a^b for a,b in zip(entropy,digest[:3]))
        bits=''.join(f'{n:08b}' for n in mixed)[:18]
        lines=[6+sum(int(c) for c in bits[i:i+3]) for i in range(0,18,3)]
        return {'lines':lines,'model':model,'model_sha256':hashlib.sha256(canonical).hexdigest(),'entropy_hex':entropy.hex(),'sampled_coin_bits':bits,
            'method':'First 18 bits of three fresh OS-random bytes XOR the first three SHA-256 model-digest bytes; three bits per line, bottom to top. The fair-coin distribution is retained.',
            'scope':'Stochastic software coupling to the app model, not an astronomical sensor or a forecast certification.'}
    def tick(self):
        if not self.enabled:return
        if self.pending:
            result=self.runtime.result(self.pending)
            if result['status']=='complete':
                reading=result['result']['stages']['iching'];self.last={'receipt':result['receipt'],'at':time.time(),'mode':reading['mode'],'primary':reading['primary']['number'],'related':reading['related']['number'],'model_feed':reading.get('model_feed')};self.by_mode[reading['mode']]=self.last;self.pending=None;self.error=None
            elif result['status']=='error':self.error=result.get('error');self.pending=None
        now=time.monotonic()
        if now<self.next_at or self.pending or not self.runtime.settings['learning'] or self.runtime.queue.qsize()>3:return
        self.next_at=now+30
        mode=('traditional','adapted')[self.mode_index%2]
        if mode=='traditional' or self.pair is None:self.pair=self.sample_model()
        question='How can the shared app choose a truthful, respectful and life-serving next step?'
        job=self.runtime.submit('pipeline',{'text':question,'sections':['iching','gnostic_four','inference'],
            'section_inputs':{'iching':{'question':question,'mode':mode,'lines':self.pair['lines'],'model_feed':self.pair},'gnostic_four':{'lesson':'engine'}}})
        self.pending=job['id'];self.cycles+=1;self.mode_index+=1
