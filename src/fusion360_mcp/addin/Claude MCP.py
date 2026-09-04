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

import base64
import collections
import http.server
import inspect
import json
import os
import queue
import re
import secrets
import tempfile
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


def _snapshot() -> str:
    """Compact text state of the design. The cheap alternative to a screenshot.

    ASCII only: mm3 not mm³. Identical bodies collapse into one line, so a
    50-instance pattern costs the same as one body.
    """
    d = adsk.fusion.Design.cast(app.activeProduct)
    if not d:
        return 'no active design (Manufacture workspace?)'
    r = d.rootComponent

    groups = collections.OrderedDict()
    for b in r.bRepBodies:
        bb = b.boundingBox
        key = (
            round(b.physicalProperties.volume * 1000, 3),
            round((bb.maxPoint.x - bb.minPoint.x) * 10, 3),
            round((bb.maxPoint.y - bb.minPoint.y) * 10, 3),
            round((bb.maxPoint.z - bb.minPoint.z) * 10, 3),
            b.faces.count,
            b.isVisible,
        )
        groups.setdefault(key, []).append(b.name)

    parametric = d.designType == adsk.fusion.DesignTypes.ParametricDesignType
    out = ['doc: %s  [%s]  sketches:%d  timeline:%s' % (
        app.activeDocument.name,
        d.unitsManager.defaultLengthUnits,
        r.sketches.count,
        d.timeline.count if parametric else 'direct',
    )]

    params = [p for p in d.userParameters]
    if params:
        out.append('params: ' + ', '.join(
            '%s=%s' % (p.name, p.expression) for p in params[:12]))

    out.append('bodies: %d' % r.bRepBodies.count)
    for (vol, x, y, z, nf, vis), names in groups.items():
        label = names[0] if len(names) == 1 else '%s x%d' % (names[0], len(names))
        out.append('  %-26s %10.3f mm3  %gx%gx%g  faces:%d%s' % (
            label, vol, x, y, z, nf, '' if vis else '  [hidden]'))

    if not groups:
        out.append('  (nenhum)')
    return chr(10).join(out)


def _screenshot(width=1000, height=750, view=None) -> dict:
    """Viewport as base64 PNG, returned inline. No file left behind.

    view: named ViewOrientations member (e.g. 'IsoTopRight', 'Front'), or
    None to keep the current camera.
    """
    vp = app.activeViewport
    if view:
        orient = getattr(adsk.core.ViewOrientations, view + 'ViewOrientation', None)
        if orient is None:
            return {'ok': False, 'error': 'unknown view %r' % view}
        cam = vp.camera
        cam.viewOrientation = orient
        cam.isFitView = True
        vp.camera = cam
    vp.refresh()

    path = os.path.join(tempfile.gettempdir(), 'claude_fusion_shot.png')
    if not vp.saveAsImageFile(path, width, height):
        return {'ok': False, 'error': 'saveAsImageFile failed'}
    try:
        with open(path, 'rb') as fh:
            data = base64.b64encode(fh.read()).decode('ascii')
    finally:
        try:
            os.remove(path)  # ponytail: temp file is an implementation detail
        except OSError:
            pass
    return {'ok': True, 'image': data, 'mime': 'image/png'}


# createInput(...) and similar take different args per feature type; the
# traceback alone doesn't say which. Pull the real signature from the stubs.
def _signature_hint(exc: BaseException, scope: dict) -> str:
    """On a TypeError/AttributeError, append the real signature if findable."""
    msg = str(exc)
    m = re.search(r'(\w+)\(\) (?:missing|takes)', msg)
    if not m:
        return ''
    fname = m.group(1)
    # Walk the last frame's locals/globals for an object exposing that method.
    tb = exc.__traceback__
    while tb and tb.tb_next:
        tb = tb.tb_next
    candidates = {}
    if tb:
        candidates.update(tb.tb_frame.f_locals)
    candidates.update(scope)
    for obj in list(candidates.values()):
        fn = getattr(obj, fname, None)
        if fn is None or not callable(fn):
            continue
        try:
            sig = str(inspect.signature(fn))
        except (TypeError, ValueError):
            doc = (inspect.getdoc(fn) or '').strip().splitlines()
            if not doc:
                continue
            sig = doc[0]
        return ('\n\nHint: %s.%s%s'
                % (type(obj).__name__, fname, sig))
    return ''


# Timeline position captured before the last call that changed anything.
# None means there is nothing to undo (read-only call, or already undone).
_checkpoint = None


def _timeline():
    """The active parametric timeline, or None (direct modelling has none)."""
    d = adsk.fusion.Design.cast(app.activeProduct)
    if not d or d.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        return None
    return d.timeline


def _rollback_to(mark: int) -> int:
    """Delete every timeline entry after `mark`. Returns how many went.

    Moving the marker alone only suppresses features -- they stay in the
    timeline and come back if anything rolls forward. Deleting is what
    actually undoes the work.
    """
    tl = _timeline()
    if tl is None:
        return 0
    removed = 0
    for i in range(tl.count - 1, mark - 1, -1):
        entry = tl.item(i)
        if entry.isDeletable:
            entry.deleteObject()
            removed += 1
    tl.markerPosition = tl.count  # leave the marker at the end, not mid-history
    return removed


def _undo() -> str:
    """Undo the last state-changing fusion_eval call. The Ctrl+Z of the bridge."""
    global _checkpoint  # noqa: PLW0603
    if _checkpoint is None:
        return 'nothing to undo (last call changed nothing, or already undone)'
    tl = _timeline()
    if tl is None:
        return 'no parametric timeline: direct-modelling designs cannot roll back'
    target = _checkpoint
    _checkpoint = None  # ponytail: single level, matching one saved checkpoint
    removed = _rollback_to(target)
    return 'undone: %d timeline entr%s removed, back to position %d' % (
        removed, 'y' if removed == 1 else 'ies', target)


def _run_code(code: str) -> dict:
    """Exec user code with Fusion globals; return whatever it puts in `result`."""
    global _checkpoint  # noqa: PLW0603

    scope = {
        'adsk': adsk,
        'app': app,
        'ui': ui,
        'design': adsk.fusion.Design.cast(app.activeProduct),
        'root': None,
        'result': None,
        'snapshot': _snapshot,
        'screenshot': _screenshot,
        'undo': _undo,
    }
    if scope['design']:
        scope['root'] = scope['design'].rootComponent

    # Checkpoint on count, not markerPosition: the marker can sit behind the
    # end (user rolled back in the UI), and comparing against it would either
    # miss new features or delete ones that were already there.
    tl = _timeline()
    mark = tl.count if tl else None

    try:
        exec(code, scope)  # noqa: S102 - arbitrary execution is the whole point
    except BaseException as exc:  # noqa: BLE001 - report everything back
        # Roll back whatever the failed call managed to create, so a crash
        # halfway through never leaves half-built geometry behind.
        undone = 0
        if mark is not None and tl.count > mark:
            try:
                undone = _rollback_to(mark)
            except Exception:  # noqa: BLE001 - rollback is best-effort
                _trace('rollback failed: ' + traceback.format_exc())
        _checkpoint = None
        err = traceback.format_exc()
        if isinstance(exc, (TypeError, AttributeError)):
            err += _signature_hint(exc, scope)
        if undone:
            err += ('\n\nRolled back %d timeline entr%s created before the error.'
                    % (undone, 'y' if undone == 1 else 'ies'))
        return {'ok': False, 'error': err}

    # Only remember a checkpoint when the call actually built something;
    # undo() after a read-only call would otherwise clobber earlier work.
    if mark is not None and tl.count > mark:
        _checkpoint = mark

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
        # charset matters: without it accented output comes back as mojibake
        # (mm3 -> mmÂ³) because the client falls back to latin-1.
        self.send_header('Content-Type', 'application/json; charset=utf-8')
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
