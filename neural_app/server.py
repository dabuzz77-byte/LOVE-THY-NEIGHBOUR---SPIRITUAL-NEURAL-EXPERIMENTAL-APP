"""Local desktop UI and authenticated API; a separate bus handles optional LAN use."""
import io,json,mimetypes,secrets,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs,unquote
from pathlib import Path
from .runtime import ROOT

def create_server(runtime,port=8797,bus=None):
    token=secrets.token_urlsafe(32);scene_lock=threading.Lock();scene_cache={};chat_instance=[];component_instance=[];component_lock=threading.RLock()
    def components():
        with component_lock:
            if not component_instance:
                from .component_host import ComponentHost
                component_instance.append(runtime.component_host if hasattr(runtime,'component_host') else ComponentHost(runtime))
                runtime.component_host=component_instance[0]
            return component_instance[0]
    from .ambient_bus import AmbientBus
    ambient_bus=AmbientBus();runtime.ambient_cube_bus=ambient_bus
    from .control_bus import ControlBus
    control_bus=ControlBus();runtime.engine_control_bus=control_bus;ambient_bus.control_handler=control_bus.command
    from .flow_backbone import FlowBackbone
    backbone=FlowBackbone(ambient_bus,start=False)
    from .omni_cube import OmniCube
    omni_cube=OmniCube(runtime,ambient_bus,start=False)
    from .tesseract_flow import TesseractFlow
    tesseracts=TesseractFlow(runtime,ambient_bus,omni_cube,start=False)
    from .potential_sphere import PotentialSphere
    potential_sphere=PotentialSphere(ambient_bus,start=False)
    from .bit_command import BitCommand
    bit_command=BitCommand(ambient_bus);potential_sphere.bit_command=bit_command;runtime.bit_command=bit_command
    from .language_learning import LearningCore
    learning_core=LearningCore(runtime.data);runtime.language_learning_core=learning_core;ambient_bus.on_event=lambda event:(learning_core.observe_bus(event),backbone.observe(event),omni_cube.observe(event),tesseracts.observe(event),potential_sphere.observe(event),bit_command.observe(event))
    def backbone_runtime_event(event):
        backbone.observe({'origin':'runtime-stage','target':event.get('section','all'),'payload':event})
        for core in getattr(runtime,'recursive_cores',{}).values():core.observe({'origin':'runtime-stage/'+str(event.get('section','all')),'target':event.get('section','all'),'payload':event})
    runtime.listeners.append(backbone_runtime_event)
    learning_core.on_prediction=lambda result:ambient_bus.publish({'target':'all','kind':'stage-output','origin':'language-learning-core','payload':{'provenance':'model-explanation','prediction':result['continuation'],'host_action':False}})
    from .learning_intake import KnowledgeIntake
    knowledge_intake=KnowledgeIntake(learning_core,runtime.data);runtime.learning_knowledge=knowledge_intake
    def intake_cycle(states):
        public=[{'source':r['name'],'items':r.get('items',0)} for r in states if r.get('status')=='received']
        if public:
            ambient_bus.publish({'target':'all','kind':'stage-output','origin':'public-learning-rails','payload':{'rails':knowledge_intake.rails(),'sources':knowledge_intake.balanced()[:12],'provenance':'retrieved-public-source-excerpts','stochastic':False,'bridge_direction':'all','scope':'Retrieved statements retain sources; correctness requires task-specific checks; no external instructions executed'}})
            learning_core.ingest({'source':'public-feed-cycle','provenance':'observed','kind':'reference-intake','outcome':json.dumps(public)[:400]})
            text=json.dumps(public,ensure_ascii=True).encode()[:400].decode('ascii',errors='ignore')
            try:runtime.submit('pipeline',{'text':text,'sections':['signals','translation','inference']})
            except ValueError as error:learning_core.worker_error='Public intake pipeline: '+str(error)
    knowledge_intake.on_cycle=intake_cycle
    from .llama_flow import LlamaFlow
    llama_flow=LlamaFlow(runtime,ambient_bus)
    from .grounded_reasoner import GroundedReasoner
    reasoner=GroundedReasoner(runtime,llama_flow.controller,ambient_bus,start=False)
    from .chat_requests import ChatRequests
    chat_requests=ChatRequests(reasoner)
    def bit_context():
        with reasoner.lock:
            active=next((g for g in reversed(reasoner.workbench.executive.s['goals']) if g['status']=='running'),None)
            return {'goal':active['goal'] if active else reasoner.s.get('current_goal',{}).get('input_summary',llama_flow.goal)}
    def bit_memory(memory):
        with reasoner.lock:reasoner.s['bit_command_policy']=memory
    bit_command.context_provider=bit_context;bit_command.memory_sink=bit_memory;bit_command.restore(reasoner.s.get('bit_command_policy',{}))
    from .native_training import NativeTrainer
    from .system_access import SystemAccess
    system_access=SystemAccess(runtime)
    native_trainer=NativeTrainer(runtime,reasoner,ambient_bus,backbone.stages,start=False);bit_command.training_sink=native_trainer.submit;potential_sphere.trainer=native_trainer
    from .native_matrix import NativeMatrix
    native_matrix=NativeMatrix(reasoner,ambient_bus,start=False)
    from .process_ascii_grids import ProcessAsciiGrid,VectorAsciiGrid
    process_grid=ProcessAsciiGrid(ambient_bus,start=False);vector_grid=VectorAsciiGrid(ambient_bus,process_grid,start=False)
    from .expression_field import ExpressionField
    expression_field=ExpressionField(ambient_bus,reasoner,start=False)
    from .parallel_native_lanes import ParallelNativeLanes
    parallel_lanes=ParallelNativeLanes(runtime,ambient_bus,reasoner,expression_field,start=False)
    from .recursive_core import RecursiveCore
    from .recursive_manifest import RecursiveManifest
    recursive_core=RecursiveCore(ambient_bus,backbone,reasoner,start=False);runtime.recursive_core=recursive_core
    recursive_core_2=RecursiveCore(ambient_bus,backbone,reasoner,start=False,name='recursive-core-2');recursive_core_3=RecursiveCore(ambient_bus,backbone,reasoner,start=False,name='recursive-core-3');recursive_cores={'1':recursive_core,'2':recursive_core_2,'3':recursive_core_3};runtime.recursive_cores=recursive_cores
    recursive_manifest=RecursiveManifest(ambient_bus,recursive_core,start=False);recursive_manifest.cores=list(recursive_cores.values())
    from .thought_expression import ThoughtExpression
    thought_expression=ThoughtExpression(ambient_bus,list(recursive_cores.values()),recursive_manifest,start=False)
    from .generation_cognition import GenerationCognition
    generation_cognition=GenerationCognition(ambient_bus,reasoner,start=False);runtime.generation_cognition=generation_cognition
    from .cognitive_circuit import CognitiveCircuit
    cognitive_circuit=CognitiveCircuit(ambient_bus,reasoner,start=False);runtime.cognitive_circuit=cognitive_circuit
    prediction_emit_at=[0.]
    def emit_source_prediction(source,check):
        if time.monotonic()<prediction_emit_at[0]:return
        prediction_emit_at[0]=time.monotonic()+1
        temporal=check.get('temporal_prediction') or {};adaptive=check.get('adaptive_prediction') or {}
        representation=check.get('representation_prediction') or {}
        gain=temporal.get('relative_error_reduction')
        selected='temporal-readout' if gain is not None and gain>.05 and temporal.get('test_samples',0)>=64 else 'baseline-or-symbolic'
        if representation.get('prior_captures',0)>=2 and (representation.get('selected_gain_over_best_baseline') or 0)>.05:selected='representation/'+representation['next_selected']
        ambient_bus.publish({'target':'all','kind':'stage-output','origin':'ambient-learned-prediction','payload':{'processing_receipt':True,'stochastic':False,'host_action':False,'source':source,'selected_predictor':selected,'representation_prediction':representation,'temporal_prediction':temporal,'symbolic_order':adaptive.get('selected_order'),'symbolic_gain':adaptive.get('gain_over_frequency_bits_per_byte'),'scope':'Measured learning result and forecast, not a command or a new random source'}})
    cognitive_circuit.ascii_chain.emergence.on_update=emit_source_prediction
    from .science_library import ScienceLibrary
    science_library=ScienceLibrary(runtime.data,ambient_bus,knowledge_intake,cognitive_circuit,start=getattr(runtime,'science_background',True));runtime.science_library=science_library
    from .opera_bridge import OperaBridge
    opera_bridge=OperaBridge(runtime,cognitive_circuit)
    cognitive_circuit.world_karma.intake=knowledge_intake
    cognitive_circuit.souls_digits.intake=knowledge_intake
    cognitive_circuit.souls_digits.research=science_library
    cognitive_circuit.software_theory.research=science_library;cognitive_circuit.software_theory.intake=knowledge_intake
    cognitive_circuit.world_knowledge.research=science_library;cognitive_circuit.world_knowledge.intake=knowledge_intake
    def seed_reference_index():
        runtime.reference_seed_status={'status':'running'}
        try:
            from .world_knowledge import SOURCES as world_sources
            for domain,refs in world_sources.items() if hasattr(knowledge_intake,'store') else []:
                for title,url,note in refs:knowledge_intake.store('World knowledge / '+domain,url,title,note)
            from .action_ethics import PRINCIPLES as action_ethics
            if hasattr(knowledge_intake,'store'):knowledge_intake.store('App ethical inquiry framework','app:action-ethics','Four-way action and inaction assessment',json.dumps(action_ethics))
            if hasattr(knowledge_intake,'store'):
                from .periodic_study import FORMULAS
                knowledge_intake.store('Atomic study / CIAAW','https://ciaaw.org/abridged-atomic-weights.htm','Periodic element reference records',json.dumps(cognitive_circuit.periodic_study.elements))
                knowledge_intake.store('Atomic study / model catalogue','app:periodic-models','Atomic equations and explicit applicability',json.dumps(FORMULAS))
            from .free_learning import RESOURCES,resources
            for kind in RESOURCES if hasattr(knowledge_intake,'store') else []:
                for ref in resources(kind):knowledge_intake.store('Free learning / '+kind,ref['url'],ref['title'],ref['summary'])
            from .software_theory import REFERENCES as software_references
            for ref in software_references if hasattr(knowledge_intake,'store') else []:knowledge_intake.store('Software / experiment reference',ref['url'],ref['title'],ref['summary'])
            cognitive_circuit.ethical_projection.intake=knowledge_intake;cognitive_circuit.ethical_projection.research=science_library
            from .ethical_projection import REFERENCES as ethical_references
            for ref in ethical_references if hasattr(knowledge_intake,'store') else []:knowledge_intake.store('Ethical projection / scripture reference',ref['url'],ref['title'],ref['summary'])
            from .souls_digits import SOURCES as welfare_sources
            for title,url,summary in welfare_sources if hasattr(knowledge_intake,'store') else []:
                knowledge_intake.store('Civilisation / welfare reference',url,title,summary)
            from .correction_projection import SOURCES as causal_method_sources
            for source in causal_method_sources if hasattr(knowledge_intake,'store') else []:
                knowledge_intake.store('Causal projection methods',source['url'],source['title'],source['lesson'])
            runtime.reference_seed_status={'status':'complete'}
        except Exception as exc:
            runtime.reference_seed_status={'status':'error','error':type(exc).__name__+': '+str(exc)[:180]}
    threading.Thread(target=seed_reference_index,daemon=True,name='startup-reference-index').start()
    previous_bus_observer=ambient_bus.on_event
    cognition_observers=[('existing-generation-chain',previous_bus_observer),('reasoner',reasoner.observe),('native-matrix',native_matrix.observe),('process-grid',process_grid.observe),('vector-grid',vector_grid.observe),('trainer',native_trainer.observe),('expression-field',expression_field.observe),('recursive-core',recursive_core.observe),('recursive-core-2',recursive_core_2.observe),('recursive-core-3',recursive_core_3.observe),('generation-cognition',generation_cognition.observe)]
    ambient_bus.on_event=lambda event:cognitive_circuit.dispatch(event,cognition_observers)
    for service_name,service in [('adaptive-intelligence-rail',cognitive_circuit.adaptive_rail),('ternary-shadow',cognitive_circuit.ternary_layer),('cognitive-circuit',cognitive_circuit),('generation-cognition',generation_cognition),('thought-expression',thought_expression),('recursive-core-2',recursive_core_2),('recursive-core-3',recursive_core_3),('recursive-core',recursive_core),('recursive-manifest',recursive_manifest),('parallel-native-lanes',parallel_lanes),('expression-field',expression_field),('flow-backbone',backbone),('omni-cube',omni_cube),('tesseracts',tesseracts),('potential-sphere',potential_sphere),('grounded-reasoner',reasoner),('native-matrix',native_matrix),('process-ascii-grid',process_grid),('vector-ascii-grid',vector_grid),('native-trainer',native_trainer)]:
        service.worker=threading.Thread(target=service.loop,daemon=True,name=service_name);service.worker.start()
    cognitive_circuit.sphere_workspace.start()
    from .atmosphere import AtmosphereFeed
    from .dual_rails import DualRails
    from .router_monitor import RouterMonitor
    ambience_rails=DualRails(ambient_bus)
    router_monitor=RouterMonitor(rails=ambience_rails);runtime.router_monitor=router_monitor
    atmosphere=AtmosphereFeed(runtime.data,ambient_bus,learning_core,rails=ambience_rails);runtime.atmosphere_feed=atmosphere
    from .system_fractal import SystemFractal
    system_fractal=SystemFractal(runtime,ambient_bus)
    bus_settings=runtime.data/'ambient-bus-settings.json'
    try:
        configured_port=json.loads(bus_settings.read_text()).get('port',8800) if bus_settings.exists() else 8800
        if configured_port in (port,11434) or (bus and configured_port==bus.port):configured_port=8800
        ambient_bus.start(configured_port,token)
    except (OSError,ValueError,TypeError) as e:ambient_bus.error=str(e)
    def configure_bus(value):
        selected=int(value.get('port',8800))
        if selected==port or (bus and selected==bus.port):raise ValueError('That port belongs to another app listener. Use 8800 for the ambient HTTP bus; Llama uses 11434.')
        if selected==11434:raise ValueError('Port 11434 belongs to Ollama. Use a different ambient bus port, such as 8800.')
        state=ambient_bus.start(selected,token)
        bus_settings.parent.mkdir(parents=True,exist_ok=True)
        bus_settings.write_text(json.dumps({'port':state['port']}),encoding='utf-8')
        return state
    ambient2_instance=[]
    def ambient2():
        with component_lock:
            if not ambient2_instance:
                from .ambient2_service import IntegratedAmbient2
                ambient2_instance.append(IntegratedAmbient2(runtime.data))
            return ambient2_instance[0]
    def chat():
        if not chat_instance:
            from .chat import Chat
            chat_instance.append(Chat(runtime));runtime.conversation_service=chat_instance[0]
        return chat_instance[0]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,value,status=200,kind='application/json'):
            if status==200 and isinstance(value,dict):
                request=urlsplit(self.path)
                if request.path=='/api/intelligence-sphere':
                    lane=parse_qs(request.query).get('lane',['original'])[0]
                    value=cognitive_circuit.sphere_functions.decorate(lane,value)
                elif request.path=='/api/intelligence-spheres' and 'frames' in value:
                    value={**value,'frames':{lane:cognitive_circuit.sphere_functions.decorate(lane,frame) for lane,frame in value['frames'].items()}}
            raw=value if isinstance(value,bytes) else value.encode() if isinstance(value,str) and kind!='application/json' else json.dumps(value,ensure_ascii=False,allow_nan=False).encode()
            try:
                self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
                if urlsplit(self.path).path=='/api/activity/ingest' and runtime.activity.valid_origin(self.headers.get('Origin','')):
                    self.send_header('Access-Control-Allow-Origin',self.headers['Origin']);self.send_header('Vary','Origin')
                    self.send_header('Access-Control-Allow-Methods','POST, OPTIONS');self.send_header('Access-Control-Allow-Headers','Content-Type, X-Neural-Activity-Key, X-Neural-Extension-Id')
                    if self.headers.get('Access-Control-Request-Private-Network')=='true':self.send_header('Access-Control-Allow-Private-Network','true')
                if urlsplit(self.path).path=='/api/automatic-flow/browser' and runtime.automatic_flow().valid_origin(self.headers.get('Origin','')):
                    self.send_header('Access-Control-Allow-Origin',self.headers['Origin']);self.send_header('Vary','Origin')
                    self.send_header('Access-Control-Allow-Methods','POST, OPTIONS');self.send_header('Access-Control-Allow-Headers','Content-Type, X-Neural-Work-Key, X-Neural-Extension-Id')
                    if self.headers.get('Access-Control-Request-Private-Network')=='true':self.send_header('Access-Control-Allow-Private-Network','true')
                self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.end_headers();self.wfile.write(raw)
            except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
        def valid_host(self):
            host=self.headers.get('Host','').split(':')[0]
            return host in ('127.0.0.1','localhost')
        def authorized(self):return secrets.compare_digest(self.headers.get('X-Neural-Token',''),token)
        def do_OPTIONS(self):
            if self.valid_host() and urlsplit(self.path).path=='/api/automatic-flow/browser':
                if not runtime.automatic_flow().valid_origin(self.headers.get('Origin','')):return self.send({'error':'Extension not paired'},403)
                return self.send({'allowed':True})
            if not self.valid_host() or urlsplit(self.path).path!='/api/activity/ingest' or not runtime.activity.valid_origin(self.headers.get('Origin','')):return self.send({'error':'Origin not paired'},403)
            return self.send({'allowed':True})
        def do_GET(self):
            if not self.valid_host():return self.send({'error':'Invalid local host'},403)
            u=urlsplit(self.path);q=parse_qs(u.query)
            try:
                if u.path=='/':return self.send((ROOT/'ui'/'index.html').read_text(encoding='utf8').replace('__TOKEN__',token),kind='text/html; charset=utf-8')
                if u.path in ('/visual_atlas.js','/visual_atlas.css','/logic_cube.js','/original_lessons.js','/app.js','/style.css','/academy.js','/components.js','/section_web.js','/active_lesson.js','/devices.js','/flux_grid.js','/watts_review.js','/care.js','/care_library.js','/golden_bridge.js','/inference_beacon.js','/inference_sources.js','/title_flux.js','/process_visuals.js','/activity.js','/faith_practice.js','/theology.js','/sphere_intent.js','/souls_over_digits.js','/neural_activity.js','/zhuan_falun.js','/google_workspace.js','/model_intersect.js','/source_atlas.js','/matter_spirit.js','/wooden_cup.js','/four_voices.js','/living_circuit.js','/discipline.js','/intent_channel.js','/iching.js','/watts_study.js','/automatic_flow.js','/mesh_monitor.js','/x4_economy.js','/matrix_study.js','/parallel_flux.js','/work_observatory.js','/runinplace.js','/focus_study.js','/faith_alchemy.js'):
                    return self.send((ROOT/'ui'/u.path[1:]).read_bytes(),kind='text/javascript' if u.path.endswith('.js') else 'text/css')
                public_pwa={'/manifest.webmanifest':('manifest.webmanifest','application/manifest+json'),'/sw.js':('sw.js','text/javascript'),'/icon-192.png':('icon-192.png','image/png'),'/icon-512.png':('icon-512.png','image/png')}
                if u.path in public_pwa:
                    file,kind=public_pwa[u.path];return self.send((ROOT/'ui'/'pwa'/file).read_bytes(),kind=kind)
                if u.path=='/cross-platform.zip':return self.send((ROOT/'distributions'/'Neural-Mesh-Cross-Platform-v1.zip').read_bytes(),kind='application/zip')
                if u.path=='/companion.html':return self.send((ROOT/'ui'/'companion.html').read_bytes(),kind='text/html; charset=utf-8')
                if u.path.startswith('/assets/'):
                    name=unquote(u.path[8:]);path=ROOT/'assets'/name
                    if Path(name).name!=name or not path.is_file():return self.send({'error':'Asset not found'},404)
                    return self.send(path.read_bytes(),kind=mimetypes.guess_type(name)[0] or 'application/octet-stream')
                if not self.authorized() and not (u.path=='/api/ambient2/audio' and secrets.compare_digest(q.get('key',[''])[0],token)):return self.send({'error':'Reload the app to reconnect'},403)
                if u.path=='/api/components':return self.send(components().index())
                if u.path=='/api/components/open':return self.send(components().open(q['id'][0]))
                if u.path=='/api/components/background':return self.send(components().original_lane.view())
                if u.path=='/api/components/graphic':
                    raw,kind=components().graphic(q['id'][0],q['control'][0],min(1600,int(q.get('width',['850'])[0])),min(900,int(q.get('height',['360'])[0])))
                    return self.send(raw,kind=kind)
                if u.path.startswith('/api/components/'):
                    tail=u.path[len('/api/components/'):];ident,_,path=tail.partition('/')
                    return components().route(self,ident,'/'+path+('?' +u.query if u.query else ''),'GET')
                if u.path=='/api/rewrite-catalogue':return self.send(json.loads((ROOT/'references'/'rewrite-logic-catalogue.json').read_text(encoding='utf8')))
                if u.path=='/api/activity':return self.send(runtime.activity.view())
                if u.path=='/api/activity/request':
                    file=runtime.data/'google-activity'/'access-request.json'
                    return self.send(json.loads(file.read_text(encoding='utf8')) if file.exists() else {'status':'No account request prepared'})
                if u.path=='/api/theology':return self.send({'latest':runtime.latest.get('theology'),'public_context':runtime.theology_public})
                if u.path=='/api/google-index':return self.send(runtime.google_index.view())
                if u.path=='/api/source-atlas':return self.send(runtime.source_atlas().catalogue())
                if u.path=='/api/source-atlas/source':return self.send(runtime.source_atlas().source(q.get('id',[''])[0]))
                if u.path=='/api/opera-workspace':return self.send(runtime.opera_workspace.view())
                if u.path=='/api/google-index/search':return self.send(runtime.google_index.search(q.get('q',[''])[0],q.get('source',[None])[0]))
                if u.path=='/api/research':return self.send(runtime.research.view())
                if u.path=='/api/four-voices':
                    from .gnostic_four import catalogue
                    return self.send(catalogue())
                if u.path=='/api/four-texts':return self.send(runtime.four_texts().view())
                if u.path=='/api/four-texts/source':return self.send(runtime.four_texts().source(q.get('id',[''])[0],q.get('q',[''])[0]))
                if u.path=='/api/four-texts/presets':
                    from .gnostic_four import presets
                    return self.send(presets())
                if u.path=='/api/living-circuit':return self.send(runtime.living_circuit().view())
                if u.path=='/api/work-observatory':
                    from .work_observatory import view
                    return self.send(view(runtime))
                if u.path=='/api/original-lessons':
                    from .original_lessons import view
                    return self.send(view(ROOT))
                if u.path=='/api/ambient2/geomagnetic':return self.send(ambient2().sources.geomagnetic())
                if u.path=='/api/ambient2/stations':return self.send(ambient2().sources.catalogue())
                if u.path=='/api/ambient2/audio':return ambient2().sources.stream(self,q.get('station',[''])[0])
                if u.path=='/api/ambient2/chant':
                    from .earth_field_sources import chant_recording
                    return self.send(chant_recording(q.get('id',['om'])[0]))
                if u.path=='/api/hardware-profile':
                    from .hardware_profile import snapshot
                    return self.send(snapshot())
                if u.path=='/api/ambience/rails':return self.send(ambience_rails.view(q.get('source',[None])[0]))
                if u.path=='/api/definition-library':return self.send(backbone.ethics_library)
                if u.path=='/api/reasoning/output':return self.send(reasoner.output(q.get('id',[''])[0]))
                if u.path=='/api/native-media':
                    from .media_skills import workspace_view
                    return self.send(workspace_view(reasoner.work_tools()))
                if u.path=='/api/native-media/read':
                    from .media_skills import read_media
                    return self.send(read_media(reasoner.work_tools(),q.get('path',[''])[0]))
                if u.path=='/api/recursive-core':
                    selected=recursive_cores.get(q.get('core',['1'])[0])
                    if selected is None:raise ValueError('Choose core 1, 2 or 3')
                    return self.send({**selected.view(),'cores_summary':[{'id':key,'name':core.name,'sequence':core.sequence,'mode':core.last_mode,'point':core.point,'pending':len(core.pending),'errors':core.errors,'verified_mailboxes':core.delivered} for key,core in recursive_cores.items()]})
                if u.path=='/api/assistant-models':
                    from .assistant_models import view
                    return self.send(view(reasoner))
                if u.path=='/api/ascii-chain':
                    with cognitive_circuit.lock:return self.send(cognitive_circuit.ascii_chain.view())
                if u.path=='/api/ambient-pattern-evidence':return self.send(cognitive_circuit.ascii_chain.emergence.view(detail=True))
                if u.path=='/api/ambient-physics-learning':
                    with cognitive_circuit.sphere_functions.lock:return self.send(cognitive_circuit.sphere_functions.ambient_reasoning.physics_discovery.view())
                if u.path=='/api/ambient-rule-learning':
                    with cognitive_circuit.sphere_functions.lock:
                        study=cognitive_circuit.sphere_functions.ambient_reasoning
                        return self.send({'summary':study.rule_lab.view(),'latest':(study.latest or {}).get('rule_learning')})
                if u.path=='/api/stochastic-structure':return self.send(cognitive_circuit.stochastic_structure.view())
                if u.path=='/api/sphere-workspace':return self.send(cognitive_circuit.sphere_workspace.view())
                if u.path=='/api/sphere-functions':return self.send(cognitive_circuit.sphere_functions.view())
                if u.path=='/api/reasoning-episode':return self.send({'episode':cognitive_circuit.sphere_workspace.view().get('reasoning_episode'),'bus':cognitive_circuit.episode_bus.view()})
                if u.path=='/api/intelligence-spheres':
                    cognitive_circuit.plane_orientations.update(cognitive_circuit);cognitive_circuit.neural_topology_views.update(cognitive_circuit)
                    with cognitive_circuit.lock:return self.send({'ascii_chain':cognitive_circuit.ascii_chain.view(),'frames':{'whole-mind-study':cognitive_circuit.whole_mind_study.view(),'original':cognitive_circuit.expression_sphere.view(),'selected':cognitive_circuit.selection_sphere.view(),'unmodulated':cognitive_circuit.selection_sphere.unmodulated,'combined':cognitive_circuit.system_flux_sphere.view(),'inverse-combined':cognitive_circuit.system_flux_sphere.inverse_view(),'experiment':cognitive_circuit.experiment_sphere.view(),'total-plane':cognitive_circuit.total_plane_sphere.view(),'potential-zero':cognitive_circuit.potential_zero_sphere.view(),'neural-space':cognitive_circuit.neural_space.view(),'synthesis':cognitive_circuit.synthesis_sphere.view(),**cognitive_circuit.plane_orientations.view(),**cognitive_circuit.neural_topology_views.view(),**cognitive_circuit.choice_action_study.view(),'self-analysis':cognitive_circuit.self_analysis.sphere(),'mind-improvement':cognitive_circuit.mind_improvement.sphere(),**{lane:cognitive_circuit.principle_research.sphere(lane) for lane in ('ethical-hacking-research','souls-digits-research','power-influence-research','cosmic-emergence-research')},'spectrum-logic':cognitive_circuit.spectrum_logic.sphere(),'source-study':cognitive_circuit.source_study.sphere(cognitive_circuit),'atomic-theory':cognitive_circuit.periodic_study.sphere(cognitive_circuit),'etiquette-study':cognitive_circuit.email_trainer.sphere(cognitive_circuit),'platform-study':cognitive_circuit.platform_trainer.sphere(cognitive_circuit)}})
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0]=='whole-mind-study':return self.send(cognitive_circuit.whole_mind_study.view())
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0]=='thought-cloud':return self.send(cognitive_circuit.thought_cloud.view())
                if u.path=='/api/net-learning-stream':return self.send(cognitive_circuit.net_learning_stream.view())
                if u.path=='/api/cognition-quality':return self.send(cognitive_circuit.cognition_quality.view())
                if u.path=='/api/self-analysis':return self.send(cognitive_circuit.self_analysis.view())
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0]=='self-analysis':return self.send(cognitive_circuit.self_analysis.sphere())
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0]=='platform-study':return self.send(cognitive_circuit.platform_trainer.sphere(cognitive_circuit))
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0]=='etiquette-study':return self.send(cognitive_circuit.email_trainer.sphere(cognitive_circuit))
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0]=='atomic-theory':return self.send(cognitive_circuit.periodic_study.sphere(cognitive_circuit))
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0] in ('ethical-hacking-research','souls-digits-research','power-influence-research','cosmic-emergence-research'):return self.send(cognitive_circuit.principle_research.sphere(q['lane'][0]))
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0]=='spectrum-logic':return self.send(cognitive_circuit.spectrum_logic.sphere())
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0]=='source-study':return self.send(cognitive_circuit.source_study.sphere(cognitive_circuit))
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0]=='mind-improvement':return self.send(cognitive_circuit.mind_improvement.sphere())
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0] in ('choice-study','action-study','consequence-study','choice-action-consequence'):
                    return self.send(cognitive_circuit.choice_action_study.view(q['lane'][0]))
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0] in ('neural-inverse','neural-combined','neural-overse','neural-all-three'):
                    cognitive_circuit.neural_topology_views.update(cognitive_circuit);return self.send(cognitive_circuit.neural_topology_views.view(q['lane'][0]))
                if u.path=='/api/intelligence-sphere' and q.get('lane',[''])[0] in ('plane-rotated-positive','plane-rotated-inverse','plane-three-combined'):
                    cognitive_circuit.plane_orientations.update(cognitive_circuit);return self.send(cognitive_circuit.plane_orientations.view(q['lane'][0]))
                if u.path=='/api/intelligence-sphere':
                    with cognitive_circuit.lock:return self.send(cognitive_circuit.synthesis_sphere.view() if q.get('lane',['original'])[0]=='synthesis' else cognitive_circuit.potential_zero_sphere.view() if q.get('lane',['original'])[0]=='potential-zero' else cognitive_circuit.neural_space.view() if q.get('lane',['original'])[0]=='neural-space' else cognitive_circuit.total_plane_sphere.view() if q.get('lane',['original'])[0]=='total-plane' else cognitive_circuit.experiment_sphere.view() if q.get('lane',['original'])[0]=='experiment' else cognitive_circuit.system_flux_sphere.inverse_view() if q.get('lane',['original'])[0]=='inverse-combined' else cognitive_circuit.system_flux_sphere.view() if q.get('lane',['original'])[0]=='combined' else cognitive_circuit.selection_sphere.unmodulated if q.get('lane',['original'])[0]=='unmodulated' else (cognitive_circuit.selection_sphere if q.get('lane',['original'])[0]=='selected' else cognitive_circuit.expression_sphere).view())
                if u.path=='/api/knowledge-library':
                    from .knowledge_library import search,stats
                    return self.send({**stats(),'results':search(q.get('q',[''])[0],20)})
                if u.path=='/api/engine-visual-summary':
                    with cognitive_circuit.lock:
                        sphere=cognitive_circuit.synthesis_sphere.latest;resources=cognitive_circuit.adaptive_rail.view();return self.send({'sequence':sphere.get('sequence',0),'sources':len(cognitive_circuit.sources),'experiments':sum(cognitive_circuit.synthesis_sphere.coverage.values()),'points':[{'point':p['point'],'selected':p['selected'],'phase':p['phase']} for p in sphere.get('particles',[])[:32]],'connections':len(cognitive_circuit.neural_space.edges),'resources':resources.get('resource_metrics',{}),'status':'active' if sphere.get('sequence') else 'waiting'})
                if u.path=='/api/character-knowledge':
                    from .character_knowledge import describe
                    return self.send(describe(int(q.get('code',['65'])[0])))
                if u.path=='/api/opera-bridge':return self.send(opera_bridge.view())
                if u.path=='/api/souls-digits':return self.send(cognitive_circuit.souls_digits.view())
                if u.path=='/api/correction-projection':return self.send(cognitive_circuit.correction_projection.view())
                if u.path=='/api/world-karma':return self.send(cognitive_circuit.world_karma.view())
                if u.path=='/api/experimental-thought':return self.send(cognitive_circuit.experimental_thought.view())
                if u.path=='/api/consequence-thought':return self.send(cognitive_circuit.consequence_thought.view())
                if u.path=='/api/science-library':
                    return self.send(science_library.view())
                if u.path=='/api/science-library/search':
                    return self.send(science_library.retrieve(q.get('q',[''])[0]))
                if u.path=='/api/creative-training-streams':
                    from .creative_training_streams import streams
                    return self.send(streams(cognitive_circuit,q.get('kind',['document'])[0]))
                if u.path=='/api/capability-validation':return self.send(cognitive_circuit.capability_validation.view())
                if u.path=='/api/periodic-study':return self.send(cognitive_circuit.periodic_study.view())
                if u.path=='/api/watts-unity':
                    from .watts_unity import lesson
                    return self.send(lesson())
                if u.path=='/api/mustard-seed':
                    from .mustard_seed import lesson
                    return self.send(lesson())
                if u.path=='/api/dinosaur-faith':
                    from .dinosaur_faith import lesson
                    return self.send(lesson())
                if u.path=='/api/animal-kinship':
                    from .animal_kinship import lesson
                    return self.send(lesson())
                if u.path=='/api/world-ai':return self.send(cognitive_circuit.world_ai.view())
                if u.path=='/api/teacher-intake':return self.send(cognitive_circuit.teacher_intake.view())
                if u.path=='/api/engine-performance':return self.send(cognitive_circuit.service_metrics.view())
                if u.path=='/api/deep-decision':return self.send(cognitive_circuit.deep_decision.view())
                if u.path=='/api/decision-ledger':return self.send(cognitive_circuit.decision_ledger.view())
                if u.path=='/api/system-shield':return self.send(cognitive_circuit.system_shield.view())
                if u.path=='/api/model-substrate':return self.send(cognitive_circuit.model_substrate.view())
                if u.path=='/api/native-only-chat':
                    dialogue=cognitive_circuit.whole_mind_study.native_dialogue;dialogue.start_goal_worker()
                    return self.send(dialogue.view())
                if u.path=='/api/deliberation':return self.send(cognitive_circuit.whole_mind_study.deliberation.view())
                if u.path=='/api/whole-mind-study':return self.send(cognitive_circuit.whole_mind_study.view())
                if u.path=='/api/thin-inference':return self.send({'model_data':cognitive_circuit.model_substrate.view(),'node':cognitive_circuit.thin_inference.view(),'native':cognitive_circuit.self_controller.view(),'captured_events':cognitive_circuit.sequence})
                if u.path=='/api/thought-cloud':return self.send(cognitive_circuit.thought_cloud.view())
                if u.path=='/api/expression-canvas':return self.send(cognitive_circuit.expression_canvas.view())
                if u.path=='/api/potential-selection':return self.send(cognitive_circuit.potential_selection.view())
                if u.path=='/api/ethical-refinement':return self.send(cognitive_circuit.ethical_refinement.view())
                if u.path=='/api/ethical-learning':
                    from .action_ethics import PRINCIPLES
                    return self.send(PRINCIPLES)
                if u.path=='/api/interaction-learning':return self.send(cognitive_circuit.interaction_learning.view())
                if u.path=='/api/study-monitor':
                    from .study_monitor import view
                    return self.send(view(cognitive_circuit))
                if u.path=='/api/mind-improvement':return self.send(cognitive_circuit.mind_improvement.view())
                if u.path=='/api/self-improvement-engine':return self.send(cognitive_circuit.self_improvement_engine.view())
                if u.path=='/api/video-ambience':return self.send(cognitive_circuit.video_ambience.view())
                if u.path=='/api/source-study':return self.send(cognitive_circuit.source_study.view())
                if u.path=='/api/native-reasoning-engine':return self.send(reasoner.workbench.reasoning_engine.view())
                if u.path=='/api/active-thought':return self.send(cognitive_circuit.active_thought.view(q.get('stage',[None])[0]))
                if u.path=='/api/world-knowledge':return self.send(cognitive_circuit.world_knowledge.view(q.get('kind',['industry'])[0]))
                if u.path=='/api/game-trainer':return self.send(cognitive_circuit.game_trainer.view())
                if u.path=='/api/music-trainer':return self.send(cognitive_circuit.music_trainer.view())
                if u.path=='/api/finance-industry':return self.send(cognitive_circuit.finance_industry.view())
                if u.path=='/api/tech-industry':return self.send(cognitive_circuit.tech_industry.view())
                if u.path=='/api/platform-trainer':return self.send(cognitive_circuit.platform_trainer.view())
                if u.path=='/api/email-trainer':return self.send(cognitive_circuit.email_trainer.view())
                if u.path=='/api/paint-trainer':return self.send(cognitive_circuit.paint_trainer.view())
                if u.path=='/api/art-trainer':return self.send(cognitive_circuit.art_trainer.view())
                if u.path=='/api/document-trainer':return self.send(cognitive_circuit.document_trainer.view())
                if u.path=='/api/software-theory':return self.send(cognitive_circuit.software_theory.view(q.get('frame',[None])[0]))
                if u.path=='/api/ethical-projection':return self.send(cognitive_circuit.ethical_projection.view())
                if u.path=='/api/ternary-layer':return self.send(cognitive_circuit.ternary_layer.view(q.get('id',[None])[0]))
                if u.path=='/api/creative-thought-sphere':return self.send(cognitive_circuit.creative_thought_sphere.view())
                if u.path=='/api/skill-trainer':return self.send(cognitive_circuit.skill_trainers.view(q.get('mode',['conversation'])[0]))
                if u.path=='/api/parallel-thought-streams':return self.send(cognitive_circuit.parallel_thought_streams.view())
                if u.path=='/api/mind-output':
                    from .mind_output import snapshot
                    with cognitive_circuit.lock:return self.send(snapshot(cognitive_circuit))
                if u.path=='/api/symbol-bus':
                    from .symbol_bus import BUS as symbol_bus
                    return self.send(symbol_bus.view())
                if u.path=='/api/systemic-library':
                    from .systemic_library import view
                    return self.send(view(q.get('q',[''])[0]))
                if u.path=='/api/investigations/get':
                    return self.send(cognitive_circuit.investigations.get(q.get('id',[''])[0]))
                if u.path=='/api/investigations/search':
                    return self.send(cognitive_circuit.investigations.retrieve(q.get('q',[''])[0]))
                if u.path=='/api/investigations/history':
                    return self.send(cognitive_circuit.investigations.revisions(q.get('id',[''])[0]))
                if u.path=='/api/investigations':
                    return self.send(cognitive_circuit.investigations.view())
                if u.path=='/api/action-definitions':
                    from .command_knowledge import view as command_view
                    with cognitive_circuit.lock:return self.send({**cognitive_circuit.action_definitions.view(),'programming_and_commands':command_view()})
                if u.path=='/api/generation-selector':
                    with cognitive_circuit.lock:return self.send(cognitive_circuit.generation_selector.view())
                if u.path=='/api/element-thinking':
                    with cognitive_circuit.lock:
                        element=q.get('element',[None])[0];result=cognitive_circuit.element_thinking.view(element)
                        if element:
                            from .systemic_outcomes import stage_outcomes
                            result['outcome_model']=stage_outcomes(element,result,cognitive_circuit.generation_selector.last.get(element),cognitive_circuit.action_definitions)
                        return self.send(result)
                if u.path=='/api/cognitive-circuit':return self.send(cognitive_circuit.view())
                if u.path=='/api/generation-cognition':return self.send(generation_cognition.view())
                if u.path=='/api/thought-expression':return self.send(thought_expression.view())
                if u.path=='/api/recursive-manifest':return self.send(recursive_manifest.view())
                if u.path=='/api/expression-field':return self.send({**expression_field.view(),'parallel_lanes':parallel_lanes.view()})
                if u.path=='/api/system-access':return self.send(system_access.view())
                if u.path=='/api/native-training':return self.send(native_trainer.view())
                if u.path=='/api/process-ascii-grid':return self.send(process_grid.view())
                if u.path=='/api/vector-ascii-grid':return self.send(vector_grid.view())
                if u.path=='/api/native-matrix':return self.send(native_matrix.view())
                if u.path=='/api/potential-sphere':return self.send(potential_sphere.view())
                if u.path=='/api/reasoning/chat-status':return self.send(chat_requests.view(q.get('id',[''])[0]))
                if u.path=='/api/reasoning':return self.send(reasoner.view())
                if u.path=='/api/tesseracts':return self.send(tesseracts.view())
                if u.path=='/api/omni-cube':return self.send(omni_cube.view())
                if u.path=='/api/flow-backbone':return self.send(backbone.view())
                if u.path=='/api/system-fractal':return self.send(system_fractal.view())
                if u.path=='/api/router-monitor':return self.send(router_monitor.view())
                if u.path=='/api/atmosphere':return self.send(atmosphere.view())
                if u.path=='/api/atmosphere/signal':return self.send(atmosphere.signal())
                if u.path=='/api/ambient-combined':return self.send(llama_flow.combined())
                if u.path=='/api/ambient-flow-summary':return self.send({'backbone':{'recursive_sequence':sum(core.sequence for core in recursive_cores.values()),'generation_cognition_sequence':generation_cognition.sequence,'thought_expression_sequence':thought_expression.sequence,'recursive_manifest_sequence':recursive_manifest.sequence,'expression_sequence':expression_field.sequence,'workbench_events':len(reasoner.workbench.s['events']),'training_sequence':native_trainer.s['sequence'],'bit_command_operations':bit_command.sequence,'process_grid_sequence':process_grid.sequence,'vector_grid_sequence':vector_grid.sequence,'native_matrix_sequence':native_matrix.sequence,'potential_sphere_sequence':potential_sphere.sequence,'reasoning_events':reasoner.s['observed_events'],'pattern_tests':reasoner.s['pattern_tests'],'tesseract_sequence':tesseracts.sequence,'omni_cube_sequence':omni_cube.sequence,'sequence':backbone.sequence,'element_cycle':backbone.element_tick,'layers':backbone.element_layers,'inlets':backbone.view()['inlets']},'stages':llama_flow.context.get('stage_summary',[]),'captured':llama_flow.context.get('updated'),'background':llama_flow.context.get('background',{}),'learning':{k:v for k,v in learning_core.view().items() if k in ('characters_seen','engine_metrics')},'llama':llama_flow.view(),'public_sources':sum(r.get('status')=='received' for r in knowledge_intake.status),'environment':{'weather_sequence':atmosphere.sequence,'router_sequence':router_monitor.sequence,'rail_sequence':ambience_rails.sequence},'bus':{'sequence':ambient_bus.sequence,'activity':ambient_bus.activity(),'scope':'local authenticated bus'}})
                if u.path=='/api/llama-flow':return self.send(llama_flow.view())
                if u.path=='/api/work-orchestrator':return self.send(chat().work_tools.view())
                if u.path=='/api/language-learning/knowledge':return self.send(knowledge_intake.view(q.get('query',[''])[0]))
                if u.path=='/api/language-learning':return self.send(learning_core.view(q.get('query',[''])[0]))
                if u.path=='/api/engine-controls':return self.send(control_bus.view(q.get('offset',[0])[0],q.get('limit',[128])[0]))
                if u.path=='/api/engine-controls/value':return self.send(control_bus.inspect(q.get('id',[''])[0]))
                if u.path=='/api/engine-controls/poll':return self.send(control_bus.poll(q.get('client',[''])[0]))
                if u.path=='/api/engine-controls/settings':return self.send({'ambient_port':ambient_bus.port,'tcp':bus.info() if bus else None,'default_tcp_port':8798})
                if u.path=='/api/ambient-bus':return self.send(ambient_bus.view(max(0,int(q.get('after',['0'])[0]))))
                if u.path=='/api/ambient2/telemetry':return self.send(ambient2().telemetry())
                # PRIVATE-VISION-BEGIN
                if u.path=='/api/private-vision/available':return self.send({'available':(runtime.data/'private-vision/catalog.json').is_file() and (ROOT/'assets/private_vision.js').is_file()})
                if u.path=='/api/private-vision':
                    from .private_vision import view
                    return self.send(view(runtime.data))
                if u.path=='/api/private-vision/workflows':
                    from .private_vision_ops import info
                    return self.send(info(runtime.data))
                if u.path=='/api/private-vision/profile':
                    from .private_vision_ops import load_profile
                    return self.send(load_profile(q.get('name',[''])[0],runtime.data))
                # PRIVATE-VISION-END
                if u.path=='/api/language-formats':
                    from .language_formats import catalog
                    return self.send(catalog())
                if u.path=='/api/logic-cube':return self.send(runtime.logic_cube().view())
                if u.path=='/api/faith-alchemy':return self.send(json.loads((ROOT/'references/faith-alchemy.json').read_text(encoding='utf-8')))
                if u.path=='/api/focus-study':
                    from .focus_study import catalogue
                    return self.send(catalogue())
                if u.path=='/api/focus-study/status':return self.send(runtime.focus_study().view())
                if u.path=='/api/matrix-study':
                    from .matrix_study import catalogue
                    return self.send(catalogue())
                if u.path=='/api/matrix-study/status':return self.send(runtime.matrix_study().view())
                if u.path=='/api/x4-economy':return self.send(runtime.economy().view())
                if u.path=='/api/inference-workers':return self.send(runtime.inference_workers().view())
                if u.path=='/api/runinplace':return self.send(runtime.runinplace().view())
                if u.path=='/api/automatic-flow':return self.send(runtime.automatic_flow().view())
                if u.path=='/api/mesh/pull':return self.send(runtime.automatic_flow().pull(int(q.get('after',['0'])[0])))
                if u.path=='/api/watts-study':
                    from .watts_study import catalogue
                    return self.send(catalogue())
                if u.path=='/api/watts-study/status':return self.send(runtime.watts_study().view())
                if u.path=='/api/watts-study/reading':return self.send(runtime.watts_study().reading(int(q.get('position',['0'])[0])))
                if u.path=='/api/intent-channel':
                    from .intent_channel import catalogue
                    return self.send(catalogue())
                if u.path=='/api/iching':return self.send(runtime.changes().view())
                if u.path=='/api/iching/book':return self.send({'text':(ROOT/'references/iching/legge-complete.txt').read_text(encoding='utf-8')})
                if u.path=='/api/discipline':
                    from .discipline import catalogue
                    return self.send(catalogue())
                if u.path=='/api/wooden-cup':
                    from .wooden_cup import catalogue
                    return self.send(catalogue())
                if u.path=='/api/matter-spirit':
                    from .matter_spirit import catalogue
                    return self.send(catalogue())
                if u.path=='/api/care-library':return self.send(json.loads((ROOT/'references'/'care-comparison.json').read_text(encoding='utf8')))
                if u.path=='/api/watts-review':return self.send(json.loads((ROOT/'references'/'watts-review.json').read_text(encoding='utf8')))
                if u.path=='/api/devices':return self.send(runtime.device_hub.info())
                if u.path=='/api/lesson':return self.send(runtime.causal.view(q.get('source',['0'])[0]=='1'))
                if u.path=='/api/state':return self.send(runtime.snapshot(q.get('visuals',['1'])[0]=='1'))
                if u.path=='/api/job':return self.send(runtime.result(q['id'][0]))
                if u.path=='/api/receipts':return self.send(runtime.receipts(int(q['id'][0]) if 'id' in q else None))
                if u.path=='/api/network':return self.send(bus.info() if bus else {'error':'Bus unavailable'})
                if u.path=='/api/bus-key':return self.send({'key':bus.key} if bus else {})
                if u.path=='/api/migration':return self.send(json.loads((ROOT/'migration-status.json').read_text(encoding='utf8')))
                if u.path=='/api/assets':return self.send(json.loads((ROOT/'original-catalog.json').read_text(encoding='utf8'))['assets'])
                if u.path=='/api/reference':
                    from .engines.flux_library.reference_catalog import examples,FAMILIES
                    return self.send({'families':FAMILIES,'examples':examples()})
                if u.path.startswith('/api/chat/'):return self.send(chat().get(u.path[len('/api/chat/'):],q))
                if u.path=='/api/scene':
                    preset=q.get('preset',['Cosmos'])[0]
                    if preset not in ('Cosmos','Hydrogen','Stellar','Dyson','Earth','Biosphere','Matrix'):raise ValueError('Unknown scene')
                    with scene_lock:
                        if 'renderer' not in scene_cache:
                            from .engines.realistic_scenes import RealisticSceneRenderer as SceneRenderer
                            scene_cache['renderer']=SceneRenderer()
                        frame=int(time.monotonic()*2);key=(preset,frame)
                        if scene_cache.get('key')!=key:
                            bits=''.join(map(str,runtime.field.bits));image=scene_cache['renderer'].render(1600,480,preset,bits=bits)
                            out=io.BytesIO();image.save(out,format='JPEG',quality=85);scene_cache.update(key=key,raw=out.getvalue())
                        return self.send(scene_cache['raw'],kind='image/jpeg')
                return self.send({'error':'Not found'},404)
            except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):return
            except Exception as e:return self.send({'error':str(e)},400)
        def do_POST(self):
            if urlsplit(self.path).path=='/api/automatic-flow/browser':
                if not self.valid_host():return self.send({'error':'Invalid host'},403)
                try:
                    size=int(self.headers.get('Content-Length','0'))
                    if not 0<size<=150000:raise ValueError('Use a compact visible-work snapshot')
                    body=json.loads(self.rfile.read(size))
                    if body.get('bridge_action')=='sync':
                        runtime.automatic_flow().authorize_browser(self.headers.get('X-Neural-Work-Key',''),self.headers.get('Origin',''),self.headers.get('X-Neural-Extension-Id',''))
                        return self.send(opera_bridge.sync(body,self.headers.get('X-Neural-Extension-Id','')))
                    received=runtime.automatic_flow().ingest_browser(self.headers.get('X-Neural-Work-Key',''),self.headers.get('Origin',''),self.headers.get('X-Neural-Extension-Id',''),body)
                    cognitive_circuit.capture({'origin':'opera-visible-work-local','kind':'input','target':'all','payload':{'text':body.get('text',''),'provenance':'paired-visible-page-data','stochastic':False}})
                    return self.send(received)
                except PermissionError as e:return self.send({'error':str(e)},403)
                except (ValueError,TypeError,AttributeError) as e:return self.send({'error':str(e)},400)
            if urlsplit(self.path).path=='/api/activity/ingest':
                if not self.valid_host():return self.send({'error':'Invalid local host'},403)
                try:
                    size=int(self.headers.get('Content-Length','0'))
                    if not 0<size<=512000:raise ValueError('Use a compact activity snapshot under 512 KB')
                    body=json.loads(self.rfile.read(size))
                    return self.send(runtime.activity.ingest(self.headers.get('X-Neural-Activity-Key',''),self.headers.get('Origin',''),self.headers.get('X-Neural-Extension-Id',''),body))
                except PermissionError as e:return self.send({'error':str(e)},403)
                except (ValueError,TypeError,AttributeError) as e:return self.send({'error':str(e)},400)
            if not self.valid_host() or not self.authorized():return self.send({'error':'Reload the app to reconnect'},403)
            try:
                origin=self.headers.get('Origin')
                if origin and origin!='http://'+self.headers.get('Host',''):return self.send({'error':'Origin rejected'},403)
                size=int(self.headers.get('Content-Length',0));path=urlsplit(self.path).path
                binary=path.startswith('/api/components/observatory/') and path.endswith('/wav-upload')
                limit=524288 if path=='/api/llama-flow/context' else 2_000_000 if path in ('/api/chat/send','/api/reasoning/chat-start','/api/reasoning/request') or path.startswith('/api/language-formats/') else 1_000_000 if path=='/api/watts-study/import' else 24*1024*1024 if binary else 16_000_000 if path=='/api/google-index/import' else 2_000_000 if path.startswith('/api/components/') else 65536
                if not 0<=size<=limit:raise ValueError(f'{path.rsplit("/",1)[-1]} request is {size:,} bytes; this operation accepts {limit:,} bytes')
                raw=self.rfile.read(size);b=raw if binary else json.loads(raw or '{}')
                if path.startswith('/api/llama-flow/'):
                    action=path.rsplit('/',1)[-1]
                    if action=='context':
                        result=llama_flow.update(b)
                        for source in llama_flow.context.get('streams',[]):
                            capture={'target':'all','origin':'ambient-stage/'+source['name'],'payload':source};process_grid.observe(capture);expression_field.observe(capture)
                            for core in recursive_cores.values():core.observe(capture)
                        return self.send(result)
                    if action=='configure':return self.send(llama_flow.configure(b))
                    if action=='applied':return self.send(llama_flow.applied(b))
                    raise ValueError('Unknown Llama flow action')
                if path.startswith('/api/language-learning/'):
                    action=path.rsplit('/',1)[-1]
                    handlers={'ingest':learning_core.ingest,'predict':learning_core.predict,'propose':learning_core.propose,'approve':learning_core.approve,'activate':learning_core.activate}
                    if action=='sources':return self.send(knowledge_intake.configure(b))
                    if action=='refresh':return self.send(knowledge_intake.refresh())
                    if action=='restore':return self.send(learning_core.restore())
                    if action not in handlers:raise ValueError('Unknown learning action')
                    result=handlers[action](b)
                    if action=='ingest' and b.get('kind')=='generated-capture' and b.get('provenance') in ('stochastic','influenced-stochastic'):
                        capture={'target':'all','origin':'generated-stage/'+str(b.get('source','unknown'))[:100],'time':time.time(),'payload':{'text':str(b.get('text',''))[:4096],'stochastic':True,'predefined_text':False,'contains_model_text':False,'provenance':b['provenance']}}
                        process_grid.observe(capture);reasoner.observe(capture);native_matrix.observe(capture);vector_grid.observe(capture);expression_field.observe(capture)
                    return self.send(result)
                if path=='/api/sphere-workspace/activity':
                    result=cognitive_circuit.activity_policy.configure(b);cognitive_circuit.wake.set()
                    return self.send(result)
                if path=='/api/native-only-chat/send':
                    dialogue=cognitive_circuit.whole_mind_study.native_dialogue
                    reply=dialogue.send(b);dialogue.start_goal_worker()
                    return self.send(reply)
                if path=='/api/deliberation/submit':return self.send(cognitive_circuit.whole_mind_study.deliberation.submit(b))
                if path=='/api/deliberation/cancel':return self.send(cognitive_circuit.whole_mind_study.deliberation.cancel(str(b.get('id',''))))
                if path=='/api/engine-controls/register':return self.send(control_bus.register(b))
                if path=='/api/engine-controls/mounted':return self.send(control_bus.mounted(str(b.get('client','')),b.get('ids',[])))
                if path=='/api/engine-controls/observe':
                    receipt=control_bus.observe(b)
                    ambient_bus.publish({'origin':'engine-control-state','target':'all','kind':'stage-output','payload':receipt})
                    return self.send(receipt)
                if path=='/api/engine-controls/ack':return self.send(control_bus.acknowledge(b))
                if path=='/api/engine-controls/settings':
                    tcp=int(b.get('tcp_port',bus.port if bus else 8798))
                    if not 1024<=tcp<=65535 or tcp in (port,11434,ambient_bus.port,8799):raise ValueError('Choose an unused TCP port distinct from the UI, ambient bus, discovery and Ollama ports')
                    if 'ambient_port' in b and int(b['ambient_port'])!=ambient_bus.port:configure_bus({'port':int(b['ambient_port'])})
                    pathfile=runtime.data/'engine-control-transport.json';temporary=pathfile.with_suffix('.tmp');temporary.write_text(json.dumps({'tcp_port':tcp}),encoding='utf-8');temporary.replace(pathfile)
                    return self.send({'ambient_port':ambient_bus.port,'tcp_current':bus.port if bus else None,'tcp_saved':tcp,'tcp_apply':'next desktop restart','scope':'Existing listener scope and authentication retained'})
                if path=='/api/ambient-bus/config':return self.send(configure_bus(b))
                if path=='/api/ambient-bus':return self.send(ambient_bus.publish(b))
                if path=='/api/ambient2/preview':return self.send(ambient2().engine.preview_payload(b.get('payload'),b.get('tuning_factor')))
                if path=='/api/ambient2/send':return self.send(ambient2().engine.transmit_payload(b.get('payload'),b.get('tuning_factor'),b.get('endpoint')))
                # PRIVATE-VISION-BEGIN
                if path=='/api/private-vision/run':
                    from .private_vision import run
                    return self.send(run(b,runtime.data))
                if path=='/api/private-vision/execute':
                    from .private_vision_ops import execute
                    return self.send(execute(b,runtime.data))
                if path=='/api/private-vision/profile':
                    from .private_vision_ops import save_profile
                    return self.send(save_profile(b,runtime.data))
                # PRIVATE-VISION-END
                if path=='/api/neural-space/input':
                    return self.send(ambient_bus.publish({'origin':'neural-space-user-input','target':'all','kind':'input','payload':{'text':str(b.get('text',''))[:4000],'thinking_layers':['all'],'stochastic':False}}))
                if path=='/api/capability-validation/read-source':return self.send(cognitive_circuit.capability_validation.read_source(cognitive_circuit,b.get('url',''),b.get('query','')))
                if path=='/api/interaction-learning/observe':return self.send(cognitive_circuit.interaction_learning.observe(b,cognitive_circuit))
                if path=='/api/interaction-learning/clear':return self.send(cognitive_circuit.interaction_learning.clear())
                if path=='/api/interaction-learning/configure':return self.send(cognitive_circuit.interaction_learning.configure(b))
                if path=='/api/net-learning-stream/configure':return self.send(cognitive_circuit.net_learning_stream.configure(b))
                if path=='/api/cognition-quality/run':return self.send(cognitive_circuit.cognition_quality.run(cognitive_circuit))
                if path=='/api/mind-improvement/rollback':return self.send(cognitive_circuit.mind_improvement.rollback(cognitive_circuit))
                if path=='/api/self-improvement-engine':return self.send(cognitive_circuit.self_improvement_engine.command(b))
                if path=='/api/capability-validation/run':return self.send(cognitive_circuit.capability_validation.run())
                if path=='/api/game-trainer/test':
                    from .game_trainer import validate
                    return self.send(validate(b.get('rows')))
                if path=='/api/music-trainer/refresh':return self.send(cognitive_circuit.music_trainer.view(refresh=True))
                if path=='/api/mustard-seed/plan':
                    from .mustard_seed import plan
                    result=plan(b)
                    cognitive_circuit.bus.publish({'origin':'mustard-seed-practice','target':'all','kind':'stage-output','payload':{'plan_complete':True,'provenance':'user-authored-if-then-plan','predefined_text':True,'stochastic':False}})
                    return self.send(result)
                if path=='/api/dinosaur-faith/simulate':
                    from .dinosaur_faith import simulate
                    result=simulate(b.get('action'))
                    cognitive_circuit.bus.publish({'origin':'dinosaur-faith-lesson','target':'all','kind':'stage-output','payload':{'people_sheltered':result['people_sheltered'],'unresolved_exposure':result['unresolved_exposure'],'provenance':'synthetic-parable-contract','stochastic':False,'predefined_text':True}})
                    return self.send(result)
                if path=='/api/animal-kinship/review':
                    from .animal_kinship import review
                    result=review(b.get('case'),b.get('choice'))
                    cognitive_circuit.bus.publish({'origin':'animal-kinship-practice','target':'all','kind':'stage-output','payload':{'passed':result['passed'],'provenance':'explicit-kinship-lesson-practice','stochastic':False,'predefined_text':True}})
                    return self.send(result)
                if path=='/api/teacher-intake/submit':
                    result=cognitive_circuit.teacher_intake.submit(b)
                    cognitive_circuit.bus.publish({'origin':'teacher-intake','target':'all','kind':'stage-output','payload':{'retained':result['retained'],'checks_passed':result['checks_passed'],'checks_total':result['checks_total'],'provenance':'independent-native-teacher-fixtures','stochastic':False,'predefined_text':True}})
                    return self.send(result)
                if path=='/api/teacher-intake/run':
                    result=cognitive_circuit.teacher_intake.run(b.get('skill'),b.get('value'))
                    cognitive_circuit.action_definitions.record('teacher/verified-skill',None,result['result'],True,stage='nativematrix')
                    cognitive_circuit.bus.publish({'origin':'teacher-intake-reuse','target':'all','kind':'stage-output','payload':{'verified':True,'model_calls':0,'provenance':'independently-verified-local-skill','stochastic':False,'predefined_text':True}})
                    return self.send(result)
                if path=='/api/native-reasoning/run':return self.send(cognitive_circuit.native_reasoning.run(str(b.get('action','')),b.get('value','')))
                if path=='/api/thin-inference/student-plan':return self.send(cognitive_circuit.thin_inference.student.predict(b.get('text','')))
                if path=='/api/thin-inference/configure':return self.send(cognitive_circuit.thin_inference.configure(b))
                if path=='/api/platform-trainer/plan':
                    from .platform_trainer import plan
                    return self.send(plan(b.get('platform'),b.get('task'),b.get('choice','later'),b.get('informed',False),b.get('owner',False),b.get('backup',False)))
                if path=='/api/email-trainer/review':
                    from .email_trainer import review
                    return self.send(review(b.get('subject',''),b.get('body','')))
                if path=='/api/art-trainer/check':
                    from .art_trainer import check
                    return self.send(check(b))
                if path=='/api/document-trainer/practice':return self.send(cognitive_circuit.document_trainer.practice(b))
                if path=='/api/software-theory/consider':return self.send(cognitive_circuit.software_theory.update(cognitive_circuit,b.get('question',b.get('intent',''))))
                if path=='/api/software-theory/experiment':return self.send(cognitive_circuit.software_theory.experiment(b.get('model'),b.get('parameters')))
                if path=='/api/ethical-projection/consider':return self.send(cognitive_circuit.ethical_projection.consider(cognitive_circuit,b))
                if path=='/api/ternary-layer/experiment':return self.send(cognitive_circuit.ternary_layer.process(cognitive_circuit))
                if path=='/api/ternary-layer/input':return self.send(cognitive_circuit.ternary_layer.proposal(cognitive_circuit,b.get('value')))
                if path=='/api/creative-thought-sphere/experiment':return self.send(cognitive_circuit.creative_thought_sphere.step(cognitive_circuit,b.get('intent','')))
                if path=='/api/skill-trainer/run':return self.send(cognitive_circuit.skill_trainers.run(cognitive_circuit,b.get('mode','conversation'),b.get('text','')))
                if path=='/api/skill-trainer/feedback':return self.send(cognitive_circuit.skill_trainers.rate(b.get('mode','conversation'),b.get('id'),b.get('rating')))
                if path=='/api/skill-trainer/configure':
                    if type(b.get('enabled')) is not bool:raise ValueError('Enabled must be boolean')
                    cognitive_circuit.skill_trainers.enabled=b['enabled'];return self.send({'enabled':b['enabled']})
                if path=='/api/opera-bridge/message':return self.send(opera_bridge.send(b))
                if path=='/api/souls-digits/experiment':return self.send(cognitive_circuit.souls_digits.calculate(b.get('model')))
                if path=='/api/correction-projection/project':return self.send(cognitive_circuit.correction_projection.calculate(b.get('model')))
                if path=='/api/world-karma/reflect':return self.send(cognitive_circuit.world_karma.reflect(cognitive_circuit,b.get('question','')))
                if path=='/api/experimental-thought/run':return self.send(cognitive_circuit.experimental_thought.calculate(b.get('model'),b.get('parameters')))
                if path=='/api/consequence-thought/consider':return self.send(cognitive_circuit.consequence_thought.consider(b))
                if path=='/api/science-library/research':return self.send(science_library.request(b.get('query','')))
                if path=='/api/science-library/configure':return self.send(science_library.configure(b))
                if path=='/api/symbol-bus/set':
                    from .symbol_bus import BUS as symbol_bus
                    result=symbol_bus.select_set(b.get('source','symbol-potential'),b.get('position','0'),b.get('original',0),b.get('alphabet','unicode'),b.get('groups'),b.get('count'));codes=result['groups'][0]['sample_codes'];receipt=ambient_bus.publish({'origin':'symbol-potential','target':'all','kind':'stage-output','payload':{'text':''.join(map(chr,codes)),'unicode_codes':codes,'ascii_codes':[x for x in codes if x<128],'symbol_sets':result,'stochastic':True,'predefined_text':False,'contains_model_text':False,'provenance':'generated-symbol-subset'}});return self.send({**result,'receipt':receipt})
                if path=='/api/symbol-bus/membership':
                    from .symbol_bus import BUS as symbol_bus
                    return self.send(symbol_bus.membership(b.get('id'),b.get('index')))
                if path=='/api/symbol-bus/select':
                    from .symbol_bus import BUS as symbol_bus
                    result=symbol_bus.select(b.get('source','symbol-potential'),b.get('position','0'),b.get('original',0),b.get('mode','self-select'),b.get('depth',.5),b.get('alphabet','ascii'))
                    receipt=ambient_bus.publish({'origin':'symbol-potential','target':'all','kind':'stage-output','payload':{'text':result['selected'],'ascii_codes':[result['selected_code']] if result['selected_code']<128 else [],'stochastic':True,'predefined_text':False,'contains_model_text':False,'symbol_node':result,'provenance':'generated-character-selection'}})
                    return self.send({'selection':result,'receipt':receipt})
                if path=='/api/investigations/create':
                    return self.send(cognitive_circuit.investigations.create(b.get('question',''),knowledge_intake.retrieve(b.get('question',''))+science_library.retrieve(b.get('question',''))))
                if path=='/api/investigations/evidence':
                    return self.send(cognitive_circuit.investigations.add_evidence(b.get('id',''),b))
                if path=='/api/investigations/assess':
                    return self.send(cognitive_circuit.investigations.assess_scenario(b.get('id',''),b.get('scenario',{})))
                if path=='/api/investigations/spec':
                    return self.send(cognitive_circuit.investigations.set_spec(b.get('id',''),b.get('spec')))
                if path=='/api/investigations/use-procedure':
                    return self.send(cognitive_circuit.investigations.use_procedure(b.get('id',''),b.get('input')))
                if path=='/api/investigations/test':
                    return self.send(cognitive_circuit.investigations.test(b.get('id','')))
                if path.startswith('/api/language-formats/'):
                    from .language_formats import recognize,syntax,scan
                    action=path.rsplit('/',1)[-1]
                    if action=='recognize':return self.send(recognize(b))
                    if action=='syntax':return self.send(syntax(b,runtime.data))
                    if action=='scan':return self.send(scan(b,runtime.data))
                    if action=='restricted-test':
                        from .restricted_test import run_restricted
                        if b.get('language')=='auto':b['language']=recognize(b)['aliases'][0]
                        return self.send(run_restricted(b))
                    raise ValueError('Unknown language-format action')
                if path=='/api/logic-cube/step':return self.send(runtime.logic_cube().step(b.get('global_state','PASS'),record=True))
                if path=='/api/logic-cube/configure':return self.send(runtime.logic_cube().configure(b.get('enabled')))
                if path=='/api/components/action':return self.send(components().action(b))
                if path=='/api/components/background':return self.send(components().original_lane.configure(b.get('enabled')))
                if path=='/api/components/active':return self.send(components().active(b.get('section'),b.get('active')))
                if path.startswith('/api/components/'):
                    tail=path[len('/api/components/'):];ident,_,local=tail.partition('/')
                    return components().route(self,ident,'/'+local,'POST',b)
                if path=='/api/devices':
                    action=b.get('action');hub=runtime.device_hub
                    if action=='start':return self.send(hub.start(b.get('port',8800),b.get('lan',True)))
                    if action=='stop':hub.close();return self.send(hub.info())
                    if action=='invite':return self.send(hub.invite(b.get('name',''),b.get('send',False)))
                    if action=='revoke':hub.revoke(b.get('id'));return self.send(hub.info())
                    raise ValueError('Choose start, stop, invite or revoke')
                if path=='/api/activity':
                    action=b.get('action')
                    if action=='pair':return self.send(runtime.activity.pair(b.get('account'),b.get('extension_id')))
                    if action=='revoke':return self.send(runtime.activity.revoke())
                    if action=='configure':return self.send(runtime.activity.configure(b.get('enabled')))
                    raise ValueError('Choose pair, configure or revoke')
                if path=='/api/google-index/import':return self.send(runtime.google_index.ingest(b))
                if path=='/api/focus-study/configure':return self.send(runtime.focus_study().configure(b.get('enabled')))
                if path=='/api/matrix-study/configure':return self.send(runtime.matrix_study().configure(b.get('enabled')))
                if path=='/api/x4-economy/configure':return self.send(runtime.economy().configure(b))
                if path=='/api/inference-workers/configure':return self.send(runtime.inference_workers().configure(b.get('worker'),b.get('settings',{})))
                if path=='/api/mesh-governance':
                    from .mesh_governance import assess
                    return self.send(assess(b))
                if path=='/api/mesh-governance/apply':
                    from .mesh_governance import apply_counter
                    return self.send(apply_counter(runtime,b))
                if path=='/api/mesh-governance/restore':
                    from .mesh_governance import restore_counter
                    return self.send(restore_counter(runtime,b))
                if path=='/api/runinplace/command':return self.send(runtime.runinplace().command(b.get('text')))
                if path=='/api/automatic-flow/configure':return self.send(runtime.automatic_flow().configure(b))
                if path=='/api/automatic-flow/pair':return self.send(runtime.automatic_flow().pair(b.get('extension_id')))
                if path=='/api/watts-study/configure':return self.send(runtime.watts_study().configure(b.get('enabled')))
                if path=='/api/watts-study/import':return self.send(runtime.watts_study().ingest(b))
                if path=='/api/iching/configure':return self.send(runtime.changes().configure(b.get('enabled')))
                if path=='/api/four-texts/configure':return self.send(runtime.four_texts().configure(b.get('enabled')))
                if path=='/api/living-circuit/configure':return self.send(runtime.living_circuit().configure(b))
                if path=='/api/living-circuit/input':return self.send(runtime.living_circuit().receive(b))
                if path=='/api/living-circuit/drop':return self.send(runtime.living_circuit().drop())
                if path=='/api/source-atlas/run':return self.send(runtime.submit('pipeline',runtime.source_atlas().input(b.get('id'))))
                if path=='/api/source-atlas/batch':return self.send(runtime.source_atlas().start_batch())
                if path=='/api/source-atlas/continuous':return self.send(runtime.source_atlas().configure_continuous(b.get('enabled')))
                if path=='/api/opera-workspace':
                    if b.get('action')=='configure':return self.send(runtime.opera_workspace.configure(b.get('enabled')))
                    if b.get('action')=='open':return self.send(runtime.opera_workspace.open('http://127.0.0.1:'+str(self.server.server_address[1])))
                    raise ValueError('Choose configure or open')
                if path=='/api/google-index/owner':return self.send(runtime.google_index.set_owner(b))
                if path=='/api/google-index/configure':return self.send(runtime.google_index.configure(b.get('enabled')))
                if path=='/api/google-index/infer':return self.send(runtime.google_index.infer(b.get('query','')))
                if path=='/api/falun-research':
                    from .research_intake import fetch_plight,research_input
                    records=fetch_plight()
                    return self.send({'records':records,'job':runtime.submit('pipeline',research_input('falun_plight',records))})
                if path=='/api/design-research':
                    from .research_intake import fetch_metadata,TOPICS
                    topic=b.get('topic')
                    if topic not in ('tesla','fuller','fresco'):raise ValueError('Choose Tesla, Fuller or Fresco')
                    records=fetch_metadata(dict(TOPICS)['design_'+topic]);full='\n'.join(v['title'] for v in records);projection=full.encode('utf-8')[:480].decode('utf-8',errors='ignore')
                    job=runtime.submit('pipeline',{'text':projection or topic,'sections':['suite','unified','platform_alignment','karmic_welfare','virtue_text','reference','inference'],'research':{'topic':'design_'+topic,'records':records,'projection_bytes':len(projection.encode('utf-8'))}})
                    return self.send({'job':job,'records':records,'topic':topic})
                if path=='/api/theology':
                    from .theology import THEMES
                    from .research_intake import fetch_metadata,TOPICS
                    topic=b.get('topic','unity')
                    if topic not in THEMES:raise ValueError('Choose a supported theology topic')
                    query=dict(TOPICS)['theology_'+topic];records=fetch_metadata(query)
                    return self.send(runtime.submit('theology',{'topic':topic,'records':records}))
                if path=='/api/research':return self.send(runtime.research.configure(b.get('enabled')))
                if path=='/api/lesson':return self.send(runtime.lesson_action(b))
                if path=='/api/recursive-core/configure':
                    selected=recursive_cores.get(str(b.get('core','1')))
                    if selected is None:raise ValueError('Choose core 1, 2 or 3')
                    return self.send(selected.configure(b))
                if path=='/api/recursive-core/seed':
                    selected=recursive_cores.get(str(b.get('core','1')))
                    if selected is None:raise ValueError('Choose core 1, 2 or 3')
                    return self.send(selected.seed(b))
                if path=='/api/recursive-core/step':
                    selected=recursive_cores.get(str(b.get('core','1')))
                    if selected is None:raise ValueError('Choose core 1, 2 or 3')
                    return self.send(selected.step())
                if path=='/api/section-calculation':
                    from .section_calculation import run as calculate_section
                    return self.send(calculate_section(b,cognitive_circuit))
                if path=='/api/generation-selector/configure':
                    with cognitive_circuit.lock:return self.send(cognitive_circuit.generation_selector.configure(b))
                if path=='/api/cognitive-circuit/configure':return self.send(cognitive_circuit.configure(b))
                if path=='/api/generation-cognition/configure':return self.send(generation_cognition.configure(b))
                if path=='/api/thought-expression/configure':return self.send(thought_expression.configure(b))
                if path=='/api/recursive-manifest/configure':return self.send(recursive_manifest.configure(b))
                if path=='/api/expression-field/configure':return self.send(expression_field.configure(b))
                if path=='/api/native-training/configure':return self.send(native_trainer.configure(b))
                if path=='/api/native-training/step':return self.send(native_trainer.step())
                if path=='/api/process-ascii-grid/configure':return self.send(process_grid.configure(b))
                if path=='/api/vector-ascii-grid/configure':return self.send(vector_grid.configure(b))
                if path in ('/api/process-ascii-grid/input','/api/vector-ascii-grid/input'):return self.send(ambient_bus.publish({'target':'all','kind':'input','origin':path.split('/')[2]+'-user','payload':{'text':str(b.get('text',''))[:8000],'stochastic':False,'provenance':'user-input'}}))
                if path=='/api/native-matrix/configure':return self.send(native_matrix.configure(b))
                if path=='/api/native-matrix/input':return self.send(ambient_bus.publish({'target':'all','kind':'input','origin':'native-matrix-user','payload':{'text':str(b.get('text',''))[:8000],'stochastic':False,'provenance':'user-input'}}))
                if path=='/api/potential-sphere/configure':return self.send(potential_sphere.configure(b))
                if path=='/api/potential-sphere/input':return self.send(ambient_bus.publish({'origin':'potential-sphere-user','target':'all','kind':'input','payload':{'text':str(b.get('text',''))[:8000],'stochastic':False,'provenance':'user-input'}}))
                if path=='/api/assistant-models/select':
                    from .assistant_models import select
                    return self.send(select(reasoner,b))
                if path=='/api/reasoning/goal-control':return self.send(reasoner.workbench.executive.control(b.get('action')))
                if path=='/api/reasoning/chat-start':return self.send(chat_requests.submit(b))
                if path=='/api/reasoning/chat-cancel':return self.send(chat_requests.cancel(b.get('id','')))
                if path=='/api/reasoning/request':return self.send(reasoner.request(b))
                if path=='/api/reasoning/approve':return self.send(reasoner.approve(b.get('id')))
                if path=='/api/tesseracts/input':
                    channel=str(b.get('channel','combined'))
                    if channel not in ('1','2','3','combined'):raise ValueError('Choose a tesseract channel')
                    return self.send(ambient_bus.publish({'target':'all','kind':'input','origin':'tesseract-user','payload':{'tesseract_channel':channel,'text':str(b.get('text',''))[:8000],'stochastic':False,'provenance':'user-input'}}))
                if path=='/api/omni-cube/configure':return self.send(omni_cube.configure(b))
                if path=='/api/omni-cube/input':return self.send(ambient_bus.publish({'target':'all','kind':'input','origin':'omni-cube-user','payload':{'text':str(b.get('text',''))[:8000],'provenance':'user-input','stochastic':False}}))
                if path=='/api/flow-backbone/input':return self.send(backbone.process({'origin':'manual-backbone','target':b.get('entry','all'),'payload':b}))
                if path=='/api/router-monitor/configure':return self.send(router_monitor.configure(b))
                if path=='/api/atmosphere/configure':return self.send(atmosphere.configure(b))
                if path=='/api/run':return self.send(runtime.submit(b.get('section','pipeline'),b.get('input',{})))
                if path=='/api/settings':return self.send(runtime.configure(b))
                if path=='/api/checkpoint':return self.send(runtime.checkpoint())
                if path=='/api/feedback':return self.send(runtime.feedback(b))
                if path.startswith('/api/chat/'):return self.send(chat().post(path[len('/api/chat/'):],b))
                return self.send({'error':'Not found'},404)
            except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):return
            except Exception as e:return self.send({'error':str(e)},400)
    class LocalHTTPServer(ThreadingHTTPServer):
        request_queue_size=128
    try:server=LocalHTTPServer(('127.0.0.1',port),Handler)
    except Exception:
        chat_requests.close();cognitive_circuit.whole_mind_study.deliberation.close();science_library.close();cognitive_circuit.close();generation_cognition.close();thought_expression.close();recursive_manifest.close();recursive_core_3.close();recursive_core_2.close();recursive_core.close();parallel_lanes.close();expression_field.close();native_trainer.close();bit_command.checkpoint();vector_grid.close();process_grid.close();native_matrix.close();potential_sphere.close();reasoner.close();tesseracts.close();omni_cube.close();backbone.close();
        if backbone_runtime_event in runtime.listeners:runtime.listeners.remove(backbone_runtime_event)
        system_fractal.close();router_monitor.close();atmosphere.close();llama_flow.close();knowledge_intake.close();learning_core.close();ambient_bus.stop();raise
    server.daemon_threads=True
    def start_component_intake():
        try:
            components()
            settings_path=runtime.data/'source-atlas-settings.json'
            if settings_path.exists() and json.loads(settings_path.read_text(encoding='utf-8')).get('continuous'):runtime.source_atlas().configure_continuous(True)
        except Exception as error:runtime.errors.append('Component learning intake: '+str(error))
    threading.Thread(target=start_component_intake,daemon=True,name='shared-component-intake').start()
    original_close=server.server_close
    def close_with_bus():
        chat_requests.close();cognitive_circuit.whole_mind_study.deliberation.close();science_library.close();cognitive_circuit.close();generation_cognition.close();thought_expression.close();recursive_manifest.close();recursive_core_3.close();recursive_core_2.close();recursive_core.close();parallel_lanes.close();expression_field.close();native_trainer.close();bit_command.checkpoint();vector_grid.close();process_grid.close();native_matrix.close();potential_sphere.close();reasoner.close();tesseracts.close();omni_cube.close();backbone.close();
        if backbone_runtime_event in runtime.listeners:runtime.listeners.remove(backbone_runtime_event)
        system_fractal.close();router_monitor.close();atmosphere.close();llama_flow.close();knowledge_intake.close();learning_core.close();ambient_bus.stop();original_close()
    server.server_close=close_with_bus
    return server
