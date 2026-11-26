"""Example real service: answer map-summary tasks using the shared text corpus."""
import argparse
import time
import uuid
from .backbone import BASE, Client

def summarize(client, task):
    if task.get('action') != 'map-summary':
        return {'task_id': task.get('task_id'), 'state': 'unsupported', 'error': 'Supported action: map-summary'}
    graph = client.graph()
    texts = {n['id']: n for n in graph['nodes'] if n['type'] == 'passage'}
    shared = {}
    for edge in graph['edges']:
        shared.setdefault(edge['to'].removeprefix('theme:'), []).append({'passage_id': edge['from'], 'title': texts[edge['from']]['title'], 'reference': texts[edge['from']]['reference'], 'source': texts[edge['from']]['source'], 'basis': edge['basis']})
    return {'task_id': task.get('task_id'), 'state': 'completed', 'passage_count': len(texts), 'themes': {theme: {'passage_count': len(refs), 'examples': refs[:3]} for theme, refs in shared.items()}, 'note': graph['note']}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=17830)
    parser.add_argument('--token', default=str(BASE / 'data' / 'token.txt'))
    args = parser.parse_args()
    service = 'text-map-worker-' + uuid.uuid4().hex[:8]
    while True:
        try:
            with Client(args.port, args.token, service, ['workflow.request', 'pulse']) as client:
                client.publish('service.status', {'role': 'map-summary', 'state': 'ready'})
                print('Text-map worker connected; waiting for map-summary tasks.', flush=True)
                last_status = time.monotonic()
                while True:
                    message = client.receive()
                    if message.get('topic') == 'workflow.request':
                        try:
                            result = summarize(client, message['data'])
                        except ValueError as exc:
                            result = {'task_id': message['data'].get('task_id'), 'state': 'failed', 'error': str(exc)}
                        client.publish('workflow.result', result)
                    if time.monotonic() - last_status > 30:
                        client.request('status')
                        last_status = time.monotonic()
        except KeyboardInterrupt:
            break
        except (OSError, EOFError, ValueError) as exc:
            print(f'Waiting for backbone: {exc}', flush=True)
            time.sleep(3)
