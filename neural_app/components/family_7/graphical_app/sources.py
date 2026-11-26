"""User-selected website and pasted-text ingestion, with attributed snapshots."""
from html.parser import HTMLParser
import http.client
import ipaddress
import json
import re
import socket
from neural_app import section_threads as threading
import time
import urllib.parse
import uuid
from ..graphical_app.privacy_network import public_host, connection as private_connection

def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

def save_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=True, indent=2), encoding='utf-8')
    temp.replace(path)

class PageText(HTMLParser):

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.title_parts, self.hidden = ([], [], [])
        self.in_title = False
        self.stack, self.main_parts = ([], [])
        self.main_depth, self.main_priority = (None, 0)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append(tag)
        priority = 2 if attrs.get('id') == 'mw-content-text' else 1 if tag in {'main', 'article'} or attrs.get('role') == 'main' else 0
        if priority > self.main_priority:
            self.main_priority = priority
            self.main_depth = len(self.stack)
            self.main_parts = []
        excluded_classes = {'sidebar', 'navbox', 'infobox', 'metadata', 'mw-editsection', 'toc'}
        if tag in {'script', 'style', 'noscript', 'svg', 'template', 'nav', 'aside'} or attrs.get('role') == 'navigation' or excluded_classes.intersection(attrs.get('class', '').split()):
            self.hidden.append((tag, len(self.stack)))
        if tag == 'title':
            self.in_title = True
        if tag in {'p', 'div', 'section', 'article', 'br', 'li', 'h1', 'h2', 'h3', 'tr'}:
            self.parts.append('\n')
        if self.main_depth and tag in {'p', 'div', 'section', 'article', 'br', 'li', 'h1', 'h2', 'h3', 'tr'}:
            self.main_parts.append('\n')

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag in {'p', 'div', 'section', 'article', 'li', 'h1', 'h2', 'h3', 'tr'}:
            self.parts.append('\n')
        if self.main_depth and tag in {'p', 'div', 'section', 'article', 'li', 'h1', 'h2', 'h3', 'tr'}:
            self.main_parts.append('\n')
        if tag in self.stack:
            depth = len(self.stack) - self.stack[::-1].index(tag) - 1
            self.stack = self.stack[:depth]
            if self.main_depth and len(self.stack) < self.main_depth:
                self.main_depth = None
            while self.hidden and self.hidden[-1][1] > len(self.stack):
                self.hidden.pop()

    def handle_data(self, text):
        if not self.hidden:
            self.parts.append(text + ' ')
            if self.main_depth:
                self.main_parts.append(text + ' ')
            if self.in_title:
                self.title_parts.append(text)

    def result(self):
        parts = self.main_parts if len(''.join(self.main_parts).strip()) >= 20 else self.parts
        text = '\n'.join((' '.join(line.split()) for line in ''.join(parts).splitlines()))
        return (re.sub('\\n{3,}', '\n\n', text).strip(), ' '.join(self.title_parts).strip()[:160])

def validate_url(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 2048 or any((ord(c) < 33 for c in value)):
        raise ValueError('Enter a complete http:// or https:// website address')
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username is not None or (parsed.password is not None):
        raise ValueError('Use a public HTTP or HTTPS page without embedded sign-in details')
    if parsed.port not in (None, 80, 443):
        raise ValueError('Website ingestion supports ports 80 and 443')
    hostname = parsed.hostname.encode('idna').decode('ascii')
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    public_host(hostname)
    if parsed.scheme != 'https':
        raise ValueError('Public sources require HTTPS with Tor privacy')
    return (parsed, hostname, port, hostname)

def fetch_page(url):
    """Pin each request to its validated public address, including redirect destinations."""
    for _ in range(6):
        parsed, hostname, port, address = validate_url(url)
        connection = private_connection(hostname, port, timeout=45)
        try:
            target = urllib.parse.urlunsplit(('', '', urllib.parse.quote(parsed.path or '/', safe="/%:@!$&'()*+,;=-._~"), parsed.query, ''))
            connection.request('GET', target, headers={'User-Agent': 'PostscarcityObservatory/2.0 (user-selected reading)', 'Accept': 'text/html,text/plain,application/xhtml+xml,application/json', 'Accept-Encoding': 'identity'})
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader('Location')
                if not location:
                    raise ValueError('Website redirect did not include a destination')
                url = urllib.parse.urljoin(url, location)
                continue
            if response.status != 200:
                raise ValueError(f'Website returned HTTP {response.status}')
            content_type = response.getheader('Content-Type', 'text/html').split(';')[0].lower()
            if content_type not in {'text/html', 'text/plain', 'text/markdown', 'text/csv', 'application/xhtml+xml', 'application/json', 'application/xml', 'text/xml', 'application/rss+xml', 'application/atom+xml'}:
                raise ValueError('This address is not a readable text page. Paste its text instead.')
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError('Page exceeds the 2 MB reading limit')
            if response.getheader('Content-Encoding', 'identity') != 'identity':
                raise ValueError('This page requires unsupported compression. Paste its text instead.')
            charset = re.search('charset=([\\w-]+)', response.getheader('Content-Type', ''), re.I)
            try:
                text = raw.decode(charset.group(1) if charset else 'utf-8', errors='replace')
            except LookupError:
                text = raw.decode('utf-8', errors='replace')
            title = hostname
            if content_type in {'text/html', 'application/xhtml+xml'}:
                parser = PageText()
                parser.feed(text)
                text, title = parser.result()
                title = title or hostname
            if len(text.strip()) < 20:
                raise ValueError('No readable page text found. For script-rendered pages, paste the visible text.')
            return {'url': url, 'title': title, 'text': text[:30000], 'truncated': len(text) > 30000, 'retrieved': now(), 'content_type': content_type}
        finally:
            connection.close()
    raise ValueError('Website redirected too many times')

class SourceHub:

    def __init__(self, runtime):
        self.rt, self.lock = (runtime, threading.RLock())
        self.path = runtime.data / 'sources.json'
        try:
            self.items = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.items = {}
        for key, item in self.items.items():
            if item['status'] == 'fetching':
                item['status'] = 'pending'
            self.attach(key, item)

    def attach(self, key, item):
        with self.rt.lock:
            self.rt.node('source:' + key, item['title'], 'source')
            self.rt.edges.setdefault('carrier|source:' + key, 0.1)
            module = '2/ingest_live_web_definitions'
            targets = item.get('targets') or ([module] if module in self.rt.modules else [])
            for target in targets:
                if target in self.rt.modules:
                    self.rt.edges.setdefault('source:' + key + '|module:' + target, 0.1)
        self.rt.activate('source:' + key, 1 if item.get('text') else 0)

    def view(self):
        with self.lock:
            return [dict(item) for item in self.items.values()]

    def save(self):
        save_json(self.path, self.items)

    def add(self, kind, title='', url='', text='', automatic=True):
        if kind not in ('website', 'text'):
            raise ValueError('Choose website or pasted text')
        if type(automatic) is not bool:
            raise ValueError('Automatic refresh must be true or false')
        if not isinstance(title, str) or len(title) > 160:
            raise ValueError('Title must be 160 characters or fewer')
        if kind == 'website':
            validate_url(url)
            text = ''
            title = title.strip() or urllib.parse.urlsplit(url).hostname
        else:
            if not isinstance(text, str) or not 1 <= len(text.strip()) <= 30000:
                raise ValueError('Paste 1–30,000 characters')
            text = text.strip()
            url = ''
            title = title.strip() or 'Pasted text'
        with self.lock:
            if len(self.items) >= 100:
                raise ValueError('The source library currently supports 100 entries')
            key = uuid.uuid4().hex[:12]
            item = {'id': key, 'kind': kind, 'title': title, 'url': url, 'requested_url': url, 'text': text, 'status': 'pending' if kind == 'website' else 'ready', 'automatic': automatic if kind == 'website' else False, 'created': now(), 'retrieved': now() if text else None, 'next_fetch': 0, 'attempts': 0, 'error': None}
            self.items[key] = item
            self.save()
        self.attach(key, item)
        if text:
            self.rt.binary_bus.feed('source-text:' + key, text.encode('utf-8'))
        self.rt.publish('source', {'id': key, 'title': title, 'status': item['status']})
        return dict(item)

    def control(self, key, action):
        with self.lock:
            if key not in self.items:
                raise ValueError('Unknown source')
            item = self.items[key]
            if item['kind'] != 'website':
                raise ValueError('Pasted text does not need web refresh')
            if action == 'refresh':
                item.update(next_fetch=0, status='pending', error=None)
            elif action == 'toggle':
                item['automatic'] = not item['automatic']
            else:
                raise ValueError('Choose refresh or toggle')
            self.save()
            return dict(item)

    def selected_context(self, ids, limit=4000):
        if not isinstance(ids, list) or len(ids) > 3 or any((not isinstance(x, str) for x in ids)):
            raise ValueError('Choose up to three sources')
        chosen = []
        with self.lock:
            for key in dict.fromkeys(ids):
                if key not in self.items:
                    raise ValueError('Unknown selected source')
                item = self.items[key]
                if not item.get('text'):
                    raise ValueError('Wait for the selected source to finish ingestion')
                chosen.append(dict(item))
        if not chosen:
            return ('', [])
        budget = max(200, limit // len(chosen))
        blocks = []
        for item in chosen:
            origin = item['url'] or ('User-selected Windows app/tab capture' if item['kind'] == 'screen' else 'User-pasted text')
            blocks.append(f"SOURCE: {item['title']}\nOrigin: {origin}\nRetrieved: {item['retrieved']}\n" + item['text'][:budget] + ('\n[Excerpt shortened for context]' if len(item['text']) > budget else ''))
        return ('\n\n'.join(blocks), [{key: i.get(key) for key in ('id', 'title', 'url', 'retrieved', 'kind', 'screen_origin', 'targets')} for i in chosen])

    def loop(self):
        for _shared_tick in range(1):
            if not self.rt.config['ingestion'] or not self.rt.privacy.ready():
                self.rt.stop.wait(1)
                continue
            with self.lock:
                item = next((i for i in self.items.values() if i['kind'] == 'website' and i['next_fetch'] <= time.time() and (i['status'] == 'pending' or i['automatic'])), None)
                if item:
                    item['status'] = 'fetching'
                    key = item['id']
                    url = item['requested_url']
            if not item:
                self.rt.stop.wait(1)
                continue
            try:
                result = fetch_page(url)
                with self.lock:
                    item.update(result, status='ready', error=None, next_fetch=time.time() + 1800, attempts=0)
                self.rt.activate('source:' + key, 1)
                self.rt.binary_bus.feed('source-text:' + key, result['text'].encode('utf-8'))
            except Exception as exc:
                with self.lock:
                    item['attempts'] += 1
                    item.update(status='retry', error=str(exc), next_fetch=time.time() + min(1800, 30 * 2 ** min(item['attempts'], 6)))
            with self.lock:
                self.save()
            self.rt.publish('source', {'id': key, 'title': item['title'], 'status': item['status']})
            self.rt.stop.wait(3)
