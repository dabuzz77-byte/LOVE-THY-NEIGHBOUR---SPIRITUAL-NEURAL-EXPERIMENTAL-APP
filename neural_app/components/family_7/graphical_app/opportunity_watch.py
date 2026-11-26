"""Paced public research and a local review queue; no external enforcement."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from neural_app import section_threads as threading
import time
import urllib.parse
from pathlib import Path
from ..graphical_app.sources import fetch_page, now, save_json
from ..graphical_app.local_knowledge import redact
API = 'https://www.gov.uk/api/search.json'
DOCUMENTATION = 'https://docs.publishing.service.gov.uk/repos/search-api/using-the-search-api.html'
CATEGORIES = {'documented business-practice concerns': ('consumer protection', 'competition', 'unfair trading', 'enforcement', 'exploitative', 'illegal lending', 'modern slavery'), 'food': ('food', 'hunger', 'meal', 'nutrition'), 'housing': ('housing', 'homeless', 'shelter', 'rent'), 'energy': ('energy', 'heating', 'fuel poverty', 'insulation'), 'repair and reuse': ('repair', 'reuse', 'recycle', 'surplus', 'waste'), 'skills and access': ('training', 'education', 'skills', 'accessibility'), 'safety and exploitation support': ('domestic abuse', 'exploitation', 'modern slavery', 'victim support', 'safeguarding'), 'essential access': ('disability support', 'hardship', 'benefits', 'accessible')}
OPPORTUNITIES = ('grant', 'funding', 'support', 'free', 'surplus', 'donation', 'volunteer', 'redistribution')
REVIEW_TERMS = ('closed', 'expired', 'repay', 'loan', 'interest', 'fee', 'eligibility', 'deadline', 'consultation')

def assess(title, text):
    content = (title + ' ' + text).casefold()
    categories = [name for name, terms in CATEGORIES.items() if any((t in content for t in terms))]
    signals = [term for term in OPPORTUNITIES if term in content]
    reviews = [term for term in REVIEW_TERMS if term in content]
    return {'categories': categories, 'opportunity_terms': signals, 'review_terms': reviews, 'human_need_signal': bool(categories), 'resource_opportunity_signal': bool(signals), 'priority': len(categories) * 2 + len(signals), 'floor_impact_verified': False, 'rightful_earnings_assessed': False, 'external_action_allowed': False, 'basis': 'Transparent keyword triage of source text; not verified eligibility, benefit, wrongdoing or economic impact'}

class OpportunityWatch:

    def __init__(self, rt):
        self.rt = rt
        self.lock = threading.RLock()
        self.busy = False
        self.path = rt.data / 'opportunity-watch.json'
        self.folder = rt.data / 'work' / 'watch'
        self.folder.mkdir(parents=True, exist_ok=True)
        defaults = {'enabled': True, 'public_search': True, 'include_sources': True, 'create_briefs': True, 'read_pages': True, 'interval': 900, 'topics': ['CMA consumer enforcement', 'unfair commercial practices', 'modern slavery business enforcement', 'illegal lending support', 'food hardship support', 'housing tenant rights'], 'next_scan': 0, 'last_scan': None, 'last_success': None, 'attempts': 0, 'error': None, 'findings': [], 'scans': 0, 'last_sources': 0}
        try:
            defaults.update(json.loads(self.path.read_text(encoding='utf-8')))
        except FileNotFoundError:
            pass
        self.state = defaults
        self.rt.node('opportunity-watch', 'Public opportunity watch', 'source')

    def view(self):
        with self.lock:
            result = json.loads(json.dumps(self.state))
            result.update(busy=self.busy, privacy=self.rt.privacy.view(), scope='GOV.UK discovery, up to 12 public pages per scan with four concurrent reads, plus ready sources you added', documentation=DOCUMENTATION, report_exists=(self.folder / 'latest-report.md').is_file(), external_enforcement=False, physical_outcome_verified=False)
            result['findings'] = sorted(result['findings'], key=lambda x: (x['review_status'] == 'new', x['assessment']['priority']), reverse=True)
            return result

    def configure(self, body):
        changed = {}
        for key in ('enabled', 'public_search', 'include_sources', 'create_briefs', 'read_pages'):
            if key in body:
                if type(body[key]) is not bool:
                    raise ValueError(key + ' must be true or false')
                changed[key] = body[key]
        if 'interval' in body:
            value = body['interval']
            if type(value) is not int or not 300 <= value <= 86400:
                raise ValueError('Scan interval must be 300–86,400 seconds')
            changed['interval'] = value
        if 'topics' in body:
            topics = body['topics']
            if not isinstance(topics, list) or not 1 <= len(topics) <= 6 or any((not isinstance(t, str) or not 1 <= len(t.strip()) <= 120 for t in topics)):
                raise ValueError('Enter 1–6 topics, each up to 120 characters')
            changed['topics'] = list(dict.fromkeys((t.strip() for t in topics)))
        with self.lock:
            self.state.update(changed)
            self.state['next_scan'] = 0
            save_json(self.path, self.state)
        return self.view()

    def review(self, body):
        status = body.get('status')
        if status not in ('new', 'reviewed', 'dismissed'):
            raise ValueError('Choose new, reviewed or dismissed')
        with self.lock:
            item = next((f for f in self.state['findings'] if f['id'] == body.get('id')), None)
            if item is None:
                raise ValueError('Unknown finding')
            item.update(review_status=status, reviewed_at=now())
            save_json(self.path, self.state)
        return self.view()

    def scan(self):
        with self.lock:
            if self.busy:
                raise ValueError('A scan is already running')
            self.busy = True
            config = json.loads(json.dumps(self.state))
        rows = []
        errors = []
        requests = []
        try:
            if config['public_search'] and (not self.rt.privacy.ready()):
                errors.append({'privacy': 'Public web research is paused until Tor is verified'})
            if config['public_search'] and self.rt.privacy.ready():
                for topic in config['topics']:
                    if self.rt.stop.is_set():
                        break
                    url = API + '?' + urllib.parse.urlencode({'q': topic, 'count': 5, 'fields': 'title,description,link,public_timestamp'})
                    try:
                        page = fetch_page(url)
                        payload = json.loads(page['text'])
                        if not isinstance(payload, dict) or not isinstance(payload.get('results'), list):
                            raise ValueError('Unexpected search response')
                        requests.append({'url': url, 'retrieved': page['retrieved'], 'sha256': hashlib.sha256(page['text'].encode()).hexdigest()})
                        for result in payload['results']:
                            link = result.get('link', '')
                            if not isinstance(link, str) or not link.startswith('/') or link.startswith('//'):
                                continue
                            rows.append({'url': 'https://www.gov.uk' + link, 'title': str(result.get('title', 'Untitled'))[:200], 'text': redact(str(result.get('description', '')))[:2000], 'retrieved': page['retrieved'], 'published': result.get('public_timestamp'), 'topic': topic, 'source_kind': 'GOV.UK search description'})
                    except Exception as exc:
                        errors.append({'topic': topic, 'error': str(exc)[:1000]})
                    if self.rt.stop.wait(0.5):
                        break
            if config.get('read_pages') and rows and self.rt.privacy.ready():
                unique = list({row['url']: row for row in rows}.values())[:12]

                def read(row):
                    page = fetch_page(row['url'])
                    return {**row, **page, 'text': redact(page['text'])[:6000], 'source_kind': 'Public page discovered through GOV.UK search'}
                with ThreadPoolExecutor(max_workers=4, thread_name_prefix='public-read') as pool:
                    jobs = {pool.submit(read, row): row for row in unique}
                    full = {}
                    for future in as_completed(jobs):
                        original = jobs[future]
                        try:
                            full[original['url']] = future.result()
                        except Exception as exc:
                            errors.append({'url': original['url'], 'error': str(exc)[:500]})
                rows = [full.get(row['url'], row) for row in rows]
                for row in full.values():
                    source_id = 'public-' + hashlib.sha256(row['url'].encode()).hexdigest()[:16]
                    source = {**row, 'id': source_id, 'kind': 'public-research', 'targets': list(self.rt.modules), 'status': 'ready', 'automatic': False, 'created': now(), 'next_fetch': 1e+30, 'attempts': 0, 'error': None}
                    with self.rt.source_hub.lock:
                        self.rt.source_hub.items[source_id] = source
                        older = [k for k, v in self.rt.source_hub.items.items() if v.get('kind') == 'public-research']
                        for k in older[:-60]:
                            self.rt.source_hub.items.pop(k)
                        self.rt.source_hub.save()
                    self.rt.source_hub.attach(source_id, source)
                    self.rt.binary_bus.feed('public-page:' + source_id, source['text'])
            if config['include_sources']:
                for source in self.rt.source_hub.view():
                    if source.get('status') != 'ready' or not source.get('text') or source.get('kind') in ('watch', 'pathway', 'public-research', 'manuscript'):
                        continue
                    rows.append({'url': source.get('url', ''), 'title': source.get('title', 'Selected source'), 'text': redact(source['text'])[:6000], 'retrieved': source.get('retrieved'), 'source_id': source['id'], 'source_kind': source.get('kind'), 'topic': 'Selected source', 'published': None})
            with self.lock:
                found = {f['id']: f for f in self.state['findings']}
                for row in rows:
                    analysis = assess(row['title'], row['text'])
                    if not analysis['human_need_signal'] and (not analysis['resource_opportunity_signal']):
                        continue
                    key = hashlib.sha256((row.get('source_id') or row['url']).encode()).hexdigest()[:20]
                    fingerprint = hashlib.sha256(row['text'].encode()).hexdigest()
                    old = found.get(key, {})
                    found[key] = {**row, 'id': key, 'sha256': fingerprint, 'assessment': analysis, 'first_seen': old.get('first_seen', now()), 'last_seen': now(), 'review_status': old.get('review_status', 'new') if old.get('sha256') == fingerprint else 'new', 'reviewed_at': old.get('reviewed_at') if old.get('sha256') == fingerprint else None, 'work_brief': old.get('work_brief'), 'next_step': 'Check current availability, location, eligibility, costs and the published request. Prepare a useful resource brief; do not infer a person’s circumstances or contact anyone automatically.'}
                    if config.get('create_briefs', True) and (not old.get('work_brief') or old.get('sha256') != fingerprint):
                        brief = self.folder / (key + '-brief.md')
                        content = '\n'.join(['# Work brief: ' + row['title'], '', 'Status: research lead; human review needed.', '', 'Source: ' + (row['url'] or row['source_kind']), 'Retrieved: ' + str(row['retrieved']), 'Source hash: ' + fingerprint, '', row['text'][:2000], '', 'Work to do:', '- Check the original source for current availability and eligibility.', '- Identify the public need or resource offer without creating personal vulnerability profiles.', '- Summarise the practical help, location, access steps, costs and missing information.', '- Compare any proposed allocation with actual inventory and protected reserves.', '- Keep contact, applications, accusations and external actions for explicit human review.', '', 'No personal need, wrongdoing, delivery or benefit has been independently established.'])
                        tmp = brief.with_suffix('.tmp')
                        tmp.write_text(content, encoding='utf-8')
                        tmp.replace(brief)
                        found[key]['work_brief'] = brief.name
                self.state['findings'] = sorted(found.values(), key=lambda x: x['last_seen'], reverse=True)[:300]
                success = bool(requests or rows)
                attempts = 0 if success else self.state['attempts'] + 1
                delay = self.state['interval'] if success else min(86400, self.state['interval'] * 2 ** min(attempts, 5))
                self.state.update(last_scan=now(), scans=self.state['scans'] + 1, last_sources=len(rows), attempts=attempts, last_success=now() if success else self.state['last_success'], error=errors or (None if success else 'No source data available'), next_scan=time.time() + delay, last_requests=requests)
                save_json(self.path, self.state)
                report = self.make_report()
            report_path = self.folder / 'latest-report.md'
            temporary = report_path.with_suffix('.tmp')
            temporary.write_text(report, encoding='utf-8')
            temporary.replace(report_path)
            source = {'id': 'opportunity-watch', 'title': 'Opportunity watch evidence queue', 'kind': 'watch', 'url': '', 'text': report[:30000], 'status': 'ready', 'automatic': False, 'retrieved': now(), 'created': now(), 'targets': [], 'next_fetch': 1e+30, 'attempts': 0, 'error': None}
            with self.rt.source_hub.lock:
                self.rt.source_hub.items[source['id']] = source
                self.rt.source_hub.save()
            self.rt.source_hub.attach(source['id'], source)
            self.rt.binary_bus.feed('opportunity-watch', report)
            self.rt.activate('opportunity-watch', 1 if success else 0)
            self.rt.publish('opportunity-watch', {'sources': len(rows), 'findings': len(found), 'errors': errors})
            if success and hasattr(self.rt, 'pathway'):
                self.rt.pathway.enqueue(report, [{k: f.get(k) for k in ('url', 'title', 'retrieved', 'sha256')} for f in self.state['findings']])
            return self.view()
        finally:
            with self.lock:
                self.busy = False

    def make_report(self):
        lines = ['# Public opportunity watch', '', 'Generated: ' + now(), '', 'Public pages and search descriptions are leads for human review. Check whether a concern is an allegation, an ongoing case or a final official finding. Ranking is keyword triage; no measured benefit, eligibility, wrongdoing or delivery is inferred.', '', 'Rules: protect the human/ecological floor, preserve rightful earnings and beneficial reserves, conserve real resources, record evidence and keep legal decisions with humans.', '']
        for item in sorted(self.state['findings'], key=lambda f: f['assessment']['priority'], reverse=True)[:100]:
            lines += ['## ' + item['title'], '', 'Source: ' + (item['url'] or item['source_kind']), 'Retrieved: ' + str(item['retrieved']) + ' | Review: ' + item['review_status'], 'Categories: ' + ', '.join(item['assessment']['categories']), 'Check: ' + ', '.join(item['assessment']['review_terms']), '', item['text'][:1500], '', item['next_step'], '']
        return '\n'.join(lines)

    def loop(self):
        for _shared_tick in range(1):
            with self.lock:
                due = self.state['enabled'] and time.time() >= self.state['next_scan'] and (not self.busy)
            if due and self.rt.config['ingestion'] and (self.rt.privacy.ready() or not self.state['public_search']):
                try:
                    self.scan()
                except Exception as exc:
                    with self.lock:
                        self.state.update(error=str(exc)[:1000], next_scan=time.time() + 900)
                        save_json(self.path, self.state)
