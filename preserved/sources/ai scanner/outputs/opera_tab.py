"""Small synchronous CDP reader for ONE newly created Opera tab.

Avoids Playwright's browser-wide target discovery/initialisation. Only the DOM
operations needed by ai_mode_scanner are implemented. Existing tabs are never
enumerated, attached, changed or closed.
"""
from contextlib import contextmanager
import json
import logging
import re
import socket
import time
from urllib.parse import quote, urlsplit
from urllib.request import Request, ProxyHandler, HTTPRedirectHandler, build_opener
from uuid import uuid4


class TabTimeout(TimeoutError):
    pass


class ProtocolError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("Opera connection redirects are disabled.")


def endpoint_url(endpoint):
    endpoint = endpoint.rstrip("/")
    parsed = urlsplit(endpoint)
    if (parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1")
            or not parsed.port or parsed.username or parsed.password
            or parsed.path or parsed.query or parsed.fragment):
        raise ValueError("Opera's connection must be a loopback HTTP address with a port.")
    return endpoint


def local_request(endpoint, path, method="GET", parse_json=True):
    request = Request(endpoint_url(endpoint) + path, method=method)
    with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=10) as reply:
        body = reply.read(100001)
    if len(body) > 100000:
        raise ProtocolError("Unexpectedly large Opera connection reply.")
    return json.loads(body) if parse_json else body


def page_websocket(endpoint, target):
    target_id = target.get("id", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", target_id) or target.get("type") != "page":
        raise ProtocolError("Opera did not create a normal scanner tab.")
    address = target.get("webSocketDebuggerUrl", "")
    parsed, server = urlsplit(address), urlsplit(endpoint_url(endpoint))
    if (parsed.scheme != "ws" or parsed.hostname not in ("127.0.0.1", "localhost")
            or parsed.port != server.port or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path != "/devtools/page/" + target_id):
        raise ProtocolError("Opera returned an unexpected tab connection address.")
    # Use the configured local server rather than following a returned hostname.
    return "ws://" + server.netloc + parsed.path


class CDP:
    def __init__(self, websocket):
        self.ws = websocket
        self.sequence = 0
        self.closed = False

    def call(self, method, params=None, timeout=10):
        if self.closed:
            raise ProtocolError("The scanner's Opera tab connection is closed.")
        self.sequence += 1
        request_id = self.sequence
        deadline = time.monotonic() + timeout
        try:
            self.ws.settimeout(timeout)
            self.ws.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TabTimeout(f"Opera did not answer {method} within {timeout:g} seconds.")
                self.ws.settimeout(remaining)
                packet = self.ws.recv()
                if not packet:
                    self.closed = True
                    raise ProtocolError("Opera closed the scanner's tab connection.")
                message = json.loads(packet)
                # Events and late replies must not be mistaken for this response.
                if message.get("id") != request_id:
                    continue
                if "error" in message:
                    error = message["error"]
                    raise ProtocolError(f"Opera rejected {method}: {error.get('message', 'protocol error')}")
                return message.get("result", {})
        except ProtocolError:
            raise
        except Exception as error:
            self.closed = True
            # A partially received websocket frame cannot safely be reused.
            self.ws.close()
            if isinstance(error, (TimeoutError, socket.timeout)) or type(error).__name__ == "WebSocketTimeoutException":
                raise TabTimeout(f"Opera timed out answering {method}.") from error
            raise ProtocolError(f"Opera connection failed during {method}: {type(error).__name__}") from error

    def close(self):
        self.closed = True
        self.ws.close()


VISIBLE_JS = """e => { const s=getComputedStyle(e); const r=e.getBoundingClientRect();
  return s.visibility!=='hidden' && s.visibility!=='collapse' && s.display!=='none' && r.width>0 && r.height>0; }"""


def text_match(value, exact):
    if isinstance(value, re.Pattern):
        flags = "i" if value.flags & re.I else ""
        return f"s => new RegExp({json.dumps(value.pattern)}, {json.dumps(flags)}).test(s)"
    normalised = " ".join(value.split())
    compare = f"s === {json.dumps(normalised)}" if exact else f"s.includes({json.dumps(normalised)})"
    return f"s => {compare}"


class Locator:
    def __init__(self, page, expression="[document]"):
        self.page, self.expression = page, expression

    def locator(self, selector):
        visible = selector.endswith(":visible")
        css = selector[:-8] if visible else selector
        expression = f"({self.expression}).flatMap(e=>Array.from(e.querySelectorAll({json.dumps(css)})))"
        if visible:
            expression += f".filter({VISIBLE_JS})"
        return Locator(self.page, expression)

    def get_by_role(self, role, name, exact=False):
        if role != "button":
            raise ValueError("The scanner only needs button locators.")
        elements = self.locator('button, [role="button"], input[type="button"], input[type="submit"]')
        match = text_match(name, exact)
        return Locator(self.page, f"({elements.expression}).filter(e=>({match})((e.getAttribute('aria-label') || e.innerText || e.value || '').replace(/\\s+/g,' ').trim()))")

    def get_by_text(self, text, exact=False):
        match = text_match(text, exact)
        # Match leaf-most text containers, not every ancestor of a label.
        elements = self.locator("body *")
        return Locator(self.page, f"({elements.expression}).filter(e=>!['SCRIPT','STYLE','NOSCRIPT'].includes(e.tagName) && ({match})((e.textContent||'').replace(/\\s+/g,' ').trim()) && !Array.from(e.children).some(c=>({match})((c.textContent||'').replace(/\\s+/g,' ').trim())))")

    def nth(self, index):
        return Locator(self.page, f"({self.expression}).slice({index},{index+1})")

    def count(self):
        return self.page.evaluate(f"({self.expression}).length")

    def is_visible(self):
        return self.page.evaluate(f"({self.expression}).some({VISIBLE_JS})")

    def evaluate(self, function):
        return self.page.evaluate(f"(() => {{const els={self.expression}; if(els.length!==1) throw new Error('Expected one scanner element, found '+els.length); return ({function})(els[0]);}})()")

    def get_attribute(self, name):
        return self.evaluate(f"e=>e.getAttribute({json.dumps(name)})")

    def inner_html(self):
        return self.evaluate("e=>e.innerHTML")

    def wait_for(self, state="visible", timeout=None):
        if state not in ("visible", "hidden", "attached", "detached"):
            raise ValueError("Unsupported scanner wait state.")
        def ready():
            if state in ("attached", "detached"):
                attached = bool(self.count())
                return attached if state == "attached" else not attached
            visible = self.is_visible()
            return visible if state == "visible" else not visible
        self.page.wait_until(ready, timeout, f"activity element to become {state}")

    def click(self):
        self.wait_for()
        self.evaluate("e=>{if(e.disabled || e.getAttribute('aria-disabled')==='true') throw new Error('Scanner button is disabled'); e.scrollIntoView({block:'center'}); e.click();}")


class OperaTab(Locator):
    scanner_direct_tab = True

    def __init__(self, cdp):
        super().__init__(self)
        self.cdp = cdp
        self.timeout = 30000

    def set_default_timeout(self, timeout):
        self.timeout = timeout

    def evaluate(self, expression):
        result = self.cdp.call("Runtime.evaluate", {"expression": expression, "returnByValue": True})
        if result.get("exceptionDetails"):
            raise ProtocolError("Opera could not read the activity page; the page layout may have changed.")
        return result.get("result", {}).get("value")

    def wait_until(self, predicate, timeout, description):
        deadline = time.monotonic() + (self.timeout if timeout is None else timeout)/1000
        while time.monotonic() < deadline:
            try:
                if predicate():
                    return
            except ProtocolError as error:
                # A navigation briefly destroys the previous JavaScript context.
                if not any(s in str(error) for s in ("Cannot find context", "Execution context was destroyed")):
                    raise
            time.sleep(0.2)
        raise TabTimeout(f"Timed out waiting for {description}.")

    def goto(self, url, wait_until="domcontentloaded", timeout=None):
        if wait_until != "domcontentloaded":
            raise ValueError("Unsupported scanner navigation wait.")
        marker = "__scanner_navigation_" + uuid4().hex
        self.evaluate(f"window[{json.dumps(marker)}]=true")
        result = self.cdp.call("Page.navigate", {"url": url})
        if result.get("errorText"):
            raise ProtocolError("Opera could not load the activity page: " + result["errorText"])
        self.wait_until(lambda: self.evaluate(f"!window[{json.dumps(marker)}] && ['interactive','complete'].includes(document.readyState)"), timeout, "the activity page to load")

    def wait_for_timeout(self, milliseconds):
        time.sleep(milliseconds/1000)

    def is_closed(self):
        return self.cdp.closed

    @classmethod
    @contextmanager
    def open(cls, endpoint):
        try:
            from websocket import create_connection
        except ImportError:
            raise RuntimeError("The updated Opera connector needs websocket-client. Run Setup.cmd once, then Start Scanner.cmd.") from None
        endpoint = endpoint_url(endpoint)
        target = local_request(endpoint, "/json/new?about:blank", method="PUT")
        target_id = target.get("id", "")
        cdp = None
        try:
            address = page_websocket(endpoint, target)
            ws = create_connection(address, timeout=10, suppress_origin=True,
                                   http_no_proxy=["localhost", "127.0.0.1"], redirect_limit=0)
            cdp = CDP(ws)
            # Deliberately no Target.setAutoAttach or browser-wide initialisation.
            cdp.call("Page.enable")
            page = cls(cdp)
            if page.evaluate("1+1") != 2:
                raise ProtocolError("Opera's scanner tab did not pass the connection check.")
            yield page
        finally:
            if cdp:
                cdp.close()
            # Close only the target returned by OUR create-tab request.
            if re.fullmatch(r"[A-Za-z0-9_-]+", target_id):
                try:
                    local_request(endpoint, "/json/close/" + quote(target_id), parse_json=False)
                except Exception:
                    logging.getLogger("ai-mode").warning("Could not close the scanner's tab; you can close that tab manually.")
