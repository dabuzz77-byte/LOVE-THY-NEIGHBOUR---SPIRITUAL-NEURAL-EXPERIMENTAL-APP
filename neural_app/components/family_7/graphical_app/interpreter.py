"""Reviewed command plans backed by real Windows tools and app operations."""
import json
import os
from pathlib import Path
import re
import subprocess
from neural_app import section_threads as threading
import uuid
from ..graphical_app.sources import now, save_json
from ..graphical_app.workbench import filename
SHELL = {'system_info': '[pscustomobject]@{OSVersion=[Environment]::OSVersion.VersionString;Is64BitOS=[Environment]::Is64BitOperatingSystem;ProcessorCount=[Environment]::ProcessorCount;SystemDirectory=[Environment]::SystemDirectory;Source="Windows .NET environment"} | ConvertTo-Json', 'list_processes': 'Get-Process | Sort-Object Id | Select-Object Id,ProcessName,CPU,WorkingSet64,Responding | ConvertTo-Json', 'network_status': '[Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() | Select-Object Name,Description,OperationalStatus,Speed,NetworkInterfaceType | ConvertTo-Json', 'inspect_process': 'Get-Process -Id {pid} | Select-Object Id,ProcessName,CPU,WorkingSet64,Responding,StartTime | ConvertTo-Json'}
ACTIONS = set(SHELL) | {'bus_status', 'list_files', 'read_file', 'write_file', 'run_module', 'set_weight'}

class Interpreter:

    def __init__(self, runtime):
        self.rt = runtime
        self.lock = threading.RLock()
        self.active = False
        self.path = runtime.data / 'commands.json'
        try:
            self.plans = json.loads(self.path.read_text(encoding='utf-8'))[-100:]
        except (OSError, ValueError):
            self.plans = []
        for item in self.plans:
            if item['status'] in ('ready', 'running'):
                item['status'] = 'expired'
        self.rt.node('system-commands', 'Windows command passthrough', 'command')
        self.rt.activate('system-commands', int(self.rt.config['system_passthrough']))

    def view(self):
        with self.lock:
            return {'plans': [dict(item) for item in self.plans], 'busy': self.active, 'actions': sorted(ACTIONS), 'passthrough': {'enabled': self.rt.config['system_passthrough'], 'execution_mode': 'user', 'application_ring': 3, 'direct_ring0': False, 'route': 'Windows protected system calls', 'controlled_actions': sorted(SHELL)}}

    def validate(self, plan):
        if not isinstance(plan, dict) or plan.get('action') not in ACTIONS:
            raise ValueError('Choose a supported system or work-folder command')
        action = plan['action']
        clean = {'action': action}
        if action == 'inspect_process':
            if type(plan.get('pid')) is not int or plan['pid'] <= 0:
                raise ValueError('Use a positive process ID')
            clean['pid'] = plan['pid']
        if action in ('read_file', 'write_file'):
            value = plan.get('file')
            if not isinstance(value, str) or not value.strip():
                raise ValueError('Include a work-folder filename')
            if action == 'write_file':
                clean['file'] = filename(value)
                if not isinstance(plan.get('text'), str) or not 1 <= len(plan['text']) <= 30000:
                    raise ValueError('Include up to 30,000 characters to write')
                clean['text'] = plan['text']
            else:
                self.file_path(value)
                clean['file'] = value
        if action == 'run_module':
            if plan.get('module') not in self.rt.modules:
                raise ValueError('Choose an exact module ID from the module library')
            clean['module'] = plan['module']
        if action == 'set_weight':
            if plan.get('node') not in self.rt.nodes:
                raise ValueError('Choose an existing neural node')
            if type(plan.get('weight')) not in (int, float) or not -3 <= plan['weight'] <= 3:
                raise ValueError('Weight must be between -3 and +3')
            clean.update(node=plan['node'], weight=plan['weight'])
        return clean

    def file_path(self, value):
        root = self.rt.workbench.folder.resolve()
        target = (root / value).resolve()
        if not target.is_relative_to(root) or target == root:
            raise ValueError('Read files from the app work folder only')
        return target

    def prepare(self, text, provider='llama', source_ids=None):
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 5000:
            raise ValueError('Enter a command up to 5,000 characters')
        text = text.strip()
        lower = text.lower()
        aliases = {'system': 'system_info', 'show system': 'system_info', 'processes': 'list_processes', 'show processes': 'list_processes', 'network': 'network_status', 'show network': 'network_status', 'bus': 'bus_status', 'bus status': 'bus_status', 'list files': 'list_files'}
        if lower in aliases:
            plan = {'action': aliases[lower]}
            basis = 'Command grammar'
        elif (match := re.fullmatch('(?:inspect|process)\\s+(\\d+)', lower)):
            plan = {'action': 'inspect_process', 'pid': int(match[1])}
            basis = 'Command grammar'
        elif lower.startswith('read '):
            plan = {'action': 'read_file', 'file': text[5:].strip()}
            basis = 'Command grammar'
        elif lower.startswith('write ') and '\n' in text:
            first, content = text.split('\n', 1)
            plan = {'action': 'write_file', 'file': first[6:].strip(), 'text': content}
            basis = 'Command grammar'
        elif lower.startswith('run module '):
            plan = {'action': 'run_module', 'module': text[11:].strip()}
            basis = 'Command grammar'
        else:
            self.rt.model_hub.reserve(provider, 'interpreting')
            error = None
            try:
                prompt = 'Translate the user request into exactly one JSON object for a REVIEWED command plan. No markdown. Allowed actions: system_info, list_processes, network_status, inspect_process (pid integer), bus_status, list_files, read_file (file relative path), write_file (file simple .md/.txt/.csv/.json name, text), run_module (module exact ID), set_weight (node exact ID, weight -3..3). Unsupported requests return {"action":"unsupported"}. This is a proposal; no command has run. Windows commands run as the current user, and writes stay in the app work folder. Observed process IDs: ' + ','.join((str(p['pid']) for p in self.rt.processes[:30])) + '\nREQUEST: ' + text
                prompt, messages, provenance, reference_chars = self.rt.model_hub.with_sources(provider, prompt, [{'role': 'user', 'content': prompt}], source_ids or [])
                response, coverage = self.rt.model_hub.complete(provider, prompt, messages, max_tokens=700, json_mode=True)
                response = response.strip()
                if response.startswith('```') and response.endswith('```'):
                    response = '\n'.join(response.splitlines()[1:-1])
                try:
                    plan = json.loads(response)
                except ValueError:
                    raise ValueError('The model did not return a valid command plan. Try again or use a direct command such as show processes.') from None
                basis = provider + ' · ' + str(coverage['shared_rules']) + ' rules · ' + str(coverage['module_summaries']) + ' modules'
            except Exception as exc:
                error = str(exc)
                raise
            finally:
                self.rt.model_hub.release(provider, error)
        plan = self.validate(plan)
        preview = SHELL[plan['action']].replace('{pid}', str(plan.get('pid', ''))) if plan['action'] in SHELL else json.dumps(plan, ensure_ascii=False, indent=2)
        item = {'id': uuid.uuid4().hex[:12], 'request': text, 'plan': plan, 'preview': preview, 'basis': basis, 'status': 'ready', 'created': now(), 'output': None, 'error': None}
        item['source_ids'] = source_ids or []
        with self.lock:
            self.plans.append(item)
            self.plans = self.plans[-100:]
            save_json(self.path, self.plans)
        self.rt.binary_bus.feed('command-plan', item)
        return dict(item)

    def execute(self, key):
        with self.lock:
            item = next((i for i in self.plans if i['id'] == key), None)
            if item is None or item['status'] != 'ready':
                raise ValueError('Prepare a new command plan first')
            if self.active:
                raise ValueError('Wait for the current command to finish')
            plan = self.validate(item['plan'])
            if plan['action'] in SHELL and (not self.rt.config['system_passthrough']):
                raise ValueError('Windows command passthrough is off. Enable its caution-labelled toggle to run this plan.')
            self.active = True
            item['status'] = 'running'
            save_json(self.path, self.plans)
        try:
            action = plan['action']
            if action in SHELL:
                powershell = Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
                code = "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[Text.Encoding]::UTF8; " + SHELL[action].replace('{pid}', str(plan.get('pid', '')))
                result = subprocess.run([str(powershell), '-NoProfile', '-NonInteractive', '-Command', code], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                if result.returncode:
                    raise ValueError(result.stderr.strip()[:2000] or 'Windows command failed')
                output = result.stdout.strip() or 'Command completed without text output.'
            elif action == 'bus_status':
                output = json.dumps({'processes': self.rt.processes, 'clients': list(self.rt.clients.values()), 'carrier': self.rt.carrier(), 'chiral': self.rt.binary_bus.state()}, indent=2)
            elif action == 'list_files':
                output = '\n'.join((str(p.relative_to(self.rt.workbench.folder)) for p in self.rt.workbench.folder.rglob('*') if p.is_file() and p.resolve().is_relative_to(self.rt.workbench.folder))) or 'The work folder is empty.'
            elif action == 'read_file':
                path = self.file_path(plan['file'])
                with path.open('rb') as file:
                    raw = file.read(128 * 1024 + 1)
                if len(raw) > 128 * 1024:
                    raise ValueError('File exceeds the 128 KB reading limit')
                output = raw.decode('utf-8')
            elif action == 'write_file':
                path = self.file_path('commands/' + item['id'] + '/' + plan['file'])
                path.parent.mkdir(parents=True, exist_ok=True)
                path = self.file_path('commands/' + item['id'] + '/' + plan['file'])
                if path.suffix.lower() == '.json':
                    json.loads(plan['text'])
                raw = (plan['text'] + '\n').encode('utf-8')
                with path.open('xb') as file:
                    file.write(raw)
                if path.read_bytes() != raw:
                    raise OSError('Written bytes did not match the requested text')
                self.rt.binary_bus.feed('command-file', raw)
                output = 'Saved and verified ' + str(path.relative_to(self.rt.workbench.folder)) + ' (' + str(len(raw)) + ' bytes).'
            elif action == 'run_module':
                output = 'Module scheduled: ' + plan['module'] if self.rt.schedule(plan['module']) else 'Module already running.'
            elif action == 'set_weight':
                with self.rt.lock:
                    node = self.rt.nodes[plan['node']]
                    node['weight'] = plan['weight']
                    self.rt.config['weights'][plan['node']] = plan['weight']
                    if plan['node'] == 'carrier':
                        self.rt.config['carrier_weight'] = plan['weight']
                    self.rt.activate(plan['node'], node['input'])
                    self.rt.save_config()
                output = 'Weight applied: ' + plan['node'] + ' = ' + str(plan['weight'])
            self.rt.binary_bus.feed('command-output', output.encode('utf-8'))
            item.update(status='complete', output=output[:40000], truncated=len(output) > 40000, finished=now())
            self.rt.publish('command', {'id': key, 'action': action, 'status': 'complete'})
        except Exception as exc:
            item.update(status='failed', error=str(exc), finished=now())
            self.rt.publish('command', {'id': key, 'status': 'failed', 'error': str(exc)})
        finally:
            with self.lock:
                self.active = False
                save_json(self.path, self.plans)
        return dict(item)
