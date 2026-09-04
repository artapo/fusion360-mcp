"""Fusion 360 side of the Claude MCP bridge.

Runs an HTTP server on a background thread. Fusion's API is main-thread-only,
so requests are handed to Fusion via a CustomEvent and the HTTP thread blocks
on an Event until the main thread posts the result back.

Must be an ADD-IN, not a script: a script's run() returns and Fusion tears
down its context, so the custom event stops being serviced and every
request hangs until timeout.

Install: Utilities > ADD-INS > Add-Ins tab, or copy this folder into
%APPDATA%/Autodesk/Autodesk Fusion 360/API/AddIns/.

Auth: requests must carry 'Authorization: Bearer <token>' matching
~/.claude-fusion-secret. Without it any local process could execute
arbitrary Python in this Fusion session.
"""

import http.server
import json
import os
import queue
import secrets
import threading
import time
import traceback

import adsk.core
import adsk.fusion  # noqa: F401  (available to eval'd code)

PORT = 8766  # ponytail: 8765 is taken by jlceda-bridge
EVENT_ID = 'claude_mcp_exec'

app = adsk.core.Application.get()
ui = app.userInterface

# Module-level so Fusion's GC doesn't eat the handlers/server mid-session.
_handlers = []
_server = None
_thread = None
_custom_event = None
_pending = queue.Queue()

TRACE = os.path.join(os.path.dirname(__file__), 'bridge_trace.log')
SECRET_FILE = os.path.join(os.path.expanduser('~'), '.claude-fusion-secret')
_secret = ''


def _load_secret():
    """Read the shared token, creating one on first run."""
    try:
        with open(SECRET_FILE, encoding='utf-8') as fh:
            token = fh.read().strip()
        if token:
            return token
    except OSError:
        pass
    token = secrets.token_urlsafe(32)
    with open(SECRET_FILE, 'w', encoding='utf-8') as fh:
        fh.write(token)
    return token


def _trace(msg):
    """Thread-safe trace; app.log() is main-thread-only and silently drops."""
    try:
        with open(TRACE, 'a', encoding='utf-8') as fh:
            fh.write(time.strftime('%H:%M:%S') + ' ' + threading.current_thread().name + ' ' + str(msg) + chr(10))
    except Exception:  # noqa: BLE001
        pass


class _ExecHandler(adsk.core.CustomEventHandler):
    """Runs on Fusion's main thread. Pops one job, executes it, unblocks HTTP."""

    def notify(self, args):
        try:
            job = _pending.get_nowait()
        except queue.Empty:
            return
        try:
            # Docs require terminating the active command before an event
            # handler modifies the model, else Fusion can crash.
            if ui.activeCommand != 'SelectCommand':
                ui.commandDefinitions.itemById('SelectCommand').execute()
            job['result'] = _run_code(job['code'])
        except Exception:  # noqa: BLE001 - report everything back to the client
            job['result'] = {'ok': False, 'error': traceback.format_exc()}
        finally:
            job['done'].set()


def _run_code(code: str) -> dict:
    """Exec user code with Fusion globals; return whatever it puts in `result`."""
    scope = {
        'adsk': adsk,
        'app': app,
        'ui': ui,
        'design': adsk.fusion.Design.cast(app.activeProduct),
        'root': None,
        'result': None,
    }
    if scope['design']:
        scope['root'] = scope['design'].rootComponent
    exec(code, scope)  # noqa: S102 - arbitrary execution is the whole point
    value = scope.get('result')
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        value = repr(value)
    return {'ok': True, 'result': value}


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 - stdlib naming
        try:
            self._post()
        except Exception:  # noqa: BLE001
            _trace('do_POST crashed: ' + traceback.format_exc())
            raise

    def _post(self):
        # compare_digest: constant-time, so a wrong token leaks no timing info.
        got = self.headers.get('Authorization', '')
        if not secrets.compare_digest(got, 'Bearer ' + _secret):
            self._reply(401, {'ok': False, 'error': 'Unauthorized'})
            return

        length = int(self.headers.get('Content-Length', 0))
        code = json.loads(self.rfile.read(length) or b'{}').get('code', '')

        job = {'code': code, 'result': None, 'done': threading.Event()}
        _pending.put(job)
        # fireCustomEvent requires the additionalInfo payload; the 1-arg
        # form raises and kills the handler thread.
        app.fireCustomEvent(EVENT_ID, '{}')  # wake the main thread

        if not job['done'].wait(timeout=60):
            job['result'] = {'ok': False, 'error': 'timed out after 60s'}

        self._reply(200, job['result'])

    def _reply(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass  # ponytail: silence stdlib's stderr logging, Fusion has no console


def run(_context):
    global _server, _thread, _custom_event, _secret  # noqa: PLW0603

    try:
        _secret = _load_secret()
        # Re-running the script stops a previous instance. The old server
        # owns the port, so it must be shut down or the bind below fails and
        # the stale (possibly outdated) instance keeps serving.
        if _server:
            _server.shutdown()
            _server.server_close()
            _server = None
        try:
            app.unregisterCustomEvent(EVENT_ID)
        except Exception:  # noqa: BLE001
            pass

        _custom_event = app.registerCustomEvent(EVENT_ID)
        handler = _ExecHandler()
        _custom_event.add(handler)
        _handlers.append(handler)

        _server = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), _Handler)
        _thread = threading.Thread(target=_server.serve_forever, daemon=True)
        _thread.start()

        # Add-in: no autoTerminate needed, Fusion keeps the module alive
        # until stop(). A script's run() returns and tears down the
        # context, which is why the custom event was never serviced.
        _trace('bridge listening on 127.0.0.1:' + str(PORT))
        ui.messageBox('Claude MCP bridge listening on 127.0.0.1:' + str(PORT))
    except Exception:  # noqa: BLE001
        # app.log() is main-thread-only and silently drops; trace to file
        # and surface the failure instead of dying quietly.
        _trace('run() failed: ' + traceback.format_exc())
        ui.messageBox('Claude MCP failed to start: ' + traceback.format_exc())


def stop(_context):
    if _server:
        _server.shutdown()
        _server.server_close()
    try:
        app.unregisterCustomEvent(EVENT_ID)
    except Exception:  # noqa: BLE001
        pass
