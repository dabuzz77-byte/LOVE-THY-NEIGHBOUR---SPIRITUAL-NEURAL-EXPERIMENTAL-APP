"""Evidence-scoped boolean capability imprint; read-only, no probing side effects."""
import time
from ..graphical_app.sources import now

def imprint(rt):
    rows = []

    def add(key, title, enabled, active, verified, scope, needs='', control=None, implemented=True):
        rows.append({'id': key, 'title': title, 'implemented': bool(implemented), 'enabled': bool(enabled), 'active': bool(active), 'verified': bool(verified), 'scope': scope, 'additional_logic_or_setup': needs, 'control': control})
    live = bool(rt.http and (not rt.stop.is_set()))
    recent = bool(rt.pulse_times and time.monotonic() - rt.pulse_times[-1] < 2)
    config = dict(rt.config)
    sources = rt.source_hub.view()
    models = rt.model_hub.view()
    watch = rt.watch.view()
    ledger = rt.resources.view()
    agent = rt.agent.view()
    bus = rt.binary_bus.state()
    with rt.v3.lock:
        connections = [dict(c) for c in rt.v3.saved['connections']]
        revisions = list(rt.v3.saved['revisions'])
    add('module_workers', '16 module workers', config['running'], live and config['running'], any((r.get('ok') for r in rt.results.values())), 'Actual child-process calculations. Completion alone does not verify a physical outcome.', control='running')
    add('definition_ingestion', 'Continuous definitions', config['ingestion'], live and config['ingestion'] and rt.privacy.ready(), any((d['status'] == 'ready' for d in rt.definitions.values())), 'Retrieved reference text and local definitions. Dynamic calls can remain unresolved.', 'A definition is documentation; missing integrations still require implementation.', control='ingestion')
    add('opportunity_watch', 'Public opportunity watch', watch['enabled'] and config['ingestion'], watch['busy'], bool(watch['last_success']), 'GOV.UK public search and selected source snapshots; keyword triage and local reports.', 'Confirm location, eligibility, availability and actual outcomes. This does not search the entire internet.', control='watch')
    add('carrier', '7.83 Hz software carrier', True, recent, rt.pulses > 0, 'Timed software events on the local bus.', 'Physical RF needs appropriate external hardware.')
    add('chiral', 'Binary/chiral processing', config['chiral_running'], recent and config['chiral_running'], bus['processed_bytes'] > 0, 'Bytes accepted by the app queue, source snapshots and cooperating bus events.', 'Full private memory/instructions of arbitrary processes are not captured.', control='chiral_running')
    add('learning', 'Adaptive neural weights', config['learning'], live and config['learning'], bool(rt.edges), 'Bounded app-level Hebbian weights. Verified here means weights exist, not improved real-world performance.', 'Llama parameter training needs a separate dataset, training process and evaluation.', control='learning')
    add('bus', 'Local process bus', True, live, bool(rt.clients), 'Local TCP/UDP events; subscriber verification means a client has attached.', 'Each Java/Python process needs the cooperative adapter to exchange its internal events.')
    add('telemetry', 'Host and process readings', True, live, bool(rt.host), 'Accessible CPU, memory and process metadata.')
    add('windows_commands', 'Windows-command passthrough', config['system_passthrough'], rt.interpreter.active, any((p['status'] == 'complete' and p['plan']['action'] in ('system_info', 'list_processes', 'network_status', 'inspect_process') for p in rt.interpreter.plans)), 'Supported Windows queries with current-user permissions; each run needs a reviewed plan.', control='system_passthrough')
    for name, label in (('llama', 'Llama 3'), ('gemini', 'Gemini'), ('chatgpt', 'ChatGPT')):
        m = models[name]
        add(name, label, m['configured'], m['busy'], m['status'] == 'connected' or any((x['role'] == 'assistant' for x in m['messages'])), 'Last successful connection/reply in this runtime; no continuous provider health guarantee.', 'Ollama with the selected model.' if name == 'llama' else 'Provider credentials, available model and account access.')
    add('agent', 'Llama work sessions', models['llama']['configured'], agent['status'] == 'running', any((s['ok'] for s in agent['steps'])), 'Actual allowed tool receipts, code writes and memory.', 'Start a goal; generated code still needs behavior checks.')
    add('files', 'Work-folder files', True, bool(rt.workbench.active), bool(revisions) or bool(rt.workbench.view()['outcomes']['files_verified']), 'Files written to the local work folder, with saved-byte receipts.')
    add('code_run', 'Reviewed Python execution', True, False, any((e['type'] == 'v3-reviewed-code-run' for e in rt.events)), 'Explicitly reviewed Python runs as the current Windows user. Verification reflects a run receipt, not code correctness.', 'Open/save and review the code before Run reviewed Python.')
    wav = rt.v3.wav.current()
    add('wav', 'WAV carrier modulation', bool(rt.v3.wav.view().get('name')), wav['running'], bool(rt.v3.wav.view().get('name')), 'Measured PCM envelope changes software carrier/chiral drive.', 'Load a WAV, choose intensity, then Start modulation.')
    screen = rt.screen_hub.view()
    add('screen', 'Selected window/tab ingestion', bool(screen['selection']), screen['automatic'], bool(screen['source_id']), 'Windows accessibility text from the selected target.', 'Select an accessible window/tab; this does not grant arbitrary UI control.')
    add('sources', 'Website/text ingestion', bool(sources), any((s.get('automatic') for s in sources)), any((s.get('status') == 'ready' for s in sources)), 'Actual page or supplied text snapshots.', 'Add selected websites, text or accessible app content.')
    add('network', 'Configured API reads', bool(connections), live and config['ingestion'] and any((c['automatic'] for c in connections)), any((c['status'] == 'ready' for c in connections)), 'GET requests with response receipts.', 'Device commands, inventory updates and other writes need a service-specific authenticated adapter.')
    add('inventory', 'Resource inventory and reservations', True, bool(ledger['stock']), bool(ledger['revision']), 'Transactional local records, protected reserves, no double booking and attributed delivery records.', 'Import actual observed inventory and needs. Physical fulfilment requires a person or connected service.')
    add('delivery', 'Physical resource delivery', False, False, False, 'A human delivery record is evidence submitted by a person, not independent verification.', 'A fulfilment service or person, identifiers, authenticated receipts and reconciliation.', implemented=False)
    add('ring0', 'Direct Ring 0 access', False, False, False, 'Application runs in Ring 3.', 'A compatible driver and a narrowly defined hardware requirement.', implemented=False)
    add('llama_training', 'Llama parameter retraining', False, False, False, 'App priorities and saved memory do not retrain pretrained model parameters.', 'A separate training pipeline, suitable data and validation.', implemented=False)
    add('enforcement', 'Autonomous legal/moral enforcement', False, False, False, 'Local evidence and proposals; no automatic punishment, public accusations or court decisions.', 'Legal responsibility and consequences remain human decisions.', implemented=False)
    privacy = rt.privacy.view()
    add('ip_privacy', 'Windows / VPN network route', privacy['automatic'], privacy['running'], privacy['verified'], privacy['scope'] + ' VPN protection is not inferred from reachability.', privacy['error'] or 'Use VPN & network. Connect your VPN in Windows or its provider client.')
    pathway = rt.pathway.view()
    add('inference_pathway', 'Inference network pathway', pathway['enabled'], pathway['busy'], bool((pathway.get('last') or {}).get('local_beacon_seq')), 'Source context enters all modules, then optional local Llama inference and a local beacon receipt.', 'Requires source evidence; scheduled work waits for global execution. Public reads follow the Windows/VPN route and network controls.')
    modules = []
    inference = rt.inference.view()
    add('inference_engine', 'Real model inference engine', True, inference['busy'], any((j['status'] == 'complete' for j in inference['jobs'])), 'Actual model answers with provider, duration, context coverage and source receipts.', 'Local Llama needs Ollama; cloud providers need your account configuration and an enabled network route.')
    if hasattr(rt, 'python'):
        p = rt.python.view()
        add('abstract_signals', 'Hydrogen / Earth / Sun abstract streams', p['signals_enabled'], recent and p['signals_enabled'], p['sequence'] > 0, 'Actual generated bytes enter the chiral queue. OS entropy and deterministic patterns retain explicit provenance.', 'These profiles are useful abstract signal sources, not remote physical sensors.')
        add('classifier', 'Trainable 2–12–8–1 model', bool(p['classifier']['dataset']), False, p['classifier']['steps'] > 0, 'Actual supervised training and held-out evaluation on imported labels; separate from Llama.', 'Supply labelled x,y data and evaluate whether its predictions are useful for your chosen task.')
        add('planetary', 'NOAA planetary observation', p['planetary']['status'] != 'not connected', False, p['planetary']['status'] == 'ready', 'Actual geomagnetic K-index feed; unavailable readings remain unavailable.', 'Use Connect NOAA feed in Abstract signal studio. Kp is not a measurement of 7.83 Hz.')
        add('mesh_review', 'Llama + reviewer mesh', True, p['mesh_busy'], any((m.get('status') == 'review completed' for m in p['mesh'])), 'Two actual provider responses and their receipts; agreement is not independent proof.', 'Select a configured reviewer and submit a request.')
    for m in rt.modules.values():
        result = rt.results.get(m['id'], {})
        reports = result.get('reports', {})
        waiting = any((isinstance(value, dict) and str(value.get('status', '')).startswith('awaiting') for value in reports.values()))
        modules.append({'id': m['id'], 'implemented': True, 'scheduled': config['running'], 'running': m['status'] == 'running', 'execution_verified': bool(result.get('ok')), 'awaiting_input': waiting, 'physical_outcome_verified': False, 'input_basis': m['input_basis'], 'last_run': m['last_run'], 'error': m['error']})
    return {'generated_at': now(), 'runtime_running': live, 'port': config['port'], 'worker_limit': 16, 'meaning': {'implemented': 'A code path exists for the stated scope.', 'enabled': 'Its gate or required configuration is present.', 'active': 'Running, scheduled or currently processing, as stated in scope.', 'verified': 'An observed receipt/state exists for the stated scope; not a general truth or benefit claim.'}, 'capabilities': rows, 'modules': modules, 'global_simulation_to_reality_switch': False, 'additional_logic': 'A physical integration needs observed inputs, a defined action, authority, an adapter, execution receipts and outcome reconciliation.'}
