#!/usr/bin/env python3
"""MCP server exposing Fusion 360 to Claude Code.

Speaks JSON-RPC over stdio, forwards code to the bridge running inside Fusion.
ponytail: no mcp SDK, the protocol is ~60 lines of stdlib json.
"""

import http.client
import json
import os
import sys
import urllib.error
import urllib.request

FUSION_URL = 'http://127.0.0.1:8766'
SECRET_FILE = os.path.join(os.path.expanduser('~'), '.claude-fusion-secret')


def _secret():
    """Token shared with the add-in, which creates it on first run."""
    try:
        with open(SECRET_FILE, encoding='utf-8') as fh:
            return fh.read().strip()
    except OSError:
        return ''

TOOL = {
    'name': 'fusion_eval',
    'description': (
        "Execute Python inside the running Fusion 360 session. "
        "Pre-bound globals: adsk, app, ui, design (active Design), root "
        "(rootComponent). Assign to `result` to return a value; it must be "
        "JSON-serializable or it comes back as repr(). Runs on Fusion's main "
        "thread, so the API is fully usable. 60s timeout.\n\n"
        "Example: result = [b.name for b in root.bRepBodies]\n\n"
        "Also pre-bound:\n"
        "- snapshot() -> compact text state of the design (bodies, volumes, "
        "bounding boxes, params). Cheap; prefer it over a screenshot to check "
        "your work.\n"
        "- screenshot(width, height, view) -> renders the viewport and returns "
        "the image inline. view is a ViewOrientations name like 'IsoTopRight' "
        "or 'Front', or omit to keep the current camera. Costs ~10k tokens, "
        "so use it when shape matters and snapshot() when numbers do.\n"
        "- api(obj, filter=None) -> lists the object's real methods with "
        "signatures and its properties, read from the installed API. Use it "
        "instead of guessing a method name, and after any AttributeError; it "
        "is far cheaper than a failed call. Example: result = api(root.features"
        ".revolveFeatures) -> createInput(profile, axis, operation)\n"
        "- undo() -> reverts the last call that changed the model, deleting the "
        "timeline entries it added. One level deep. A call that raises is rolled "
        "back automatically, so undo() is for taking back work that succeeded.\n"
        "  Assign any of them to `result`: result = snapshot()"
    ),
    'inputSchema': {
        'type': 'object',
        'properties': {
            'code': {'type': 'string', 'description': 'Python source to execute.'}
        },
        'required': ['code'],
    },
}


def _text(msg: str) -> list:
    return [{'type': 'text', 'text': msg}]


def call_fusion(code: str) -> list:
    """Run code in Fusion; return MCP content blocks (text, or an image)."""
    req = urllib.request.Request(
        FUSION_URL,
        data=json.dumps({'code': code}).encode(),
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + _secret(),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=65) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return _text(
                'Unauthorized: token mismatch. The add-in creates '
                f'{SECRET_FILE} on start; restart the Fusion add-in if the '
                'file was deleted or changed.'
            )
        return _text(f'Fusion returned HTTP {exc.code}: {exc.reason}')
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        return _text(
            f'Cannot reach Fusion 360 ({exc}). Is Fusion open with the '
            '"Claude MCP" add-in running? (Utilities > ADD-INS > Add-Ins)'
        )
    if not payload.get('ok'):
        return _text(f"Error in Fusion:\n{payload.get('error')}")

    value = payload.get('result')
    # screenshot() returns its PNG inline rather than as a path on disk.
    if isinstance(value, dict) and value.get('mime') == 'image/png':
        if not value.get('ok'):
            return _text(f"Screenshot failed: {value.get('error')}")
        return [{'type': 'image', 'data': value['image'], 'mimeType': 'image/png'}]
    # snapshot() is already formatted text; don't re-quote it as a JSON string.
    if isinstance(value, str):
        body = value
    else:
        body = json.dumps(value, indent=2, ensure_ascii=False)
    # A build that returns nothing comes back as null; the delta line is what
    # tells the caller it worked, without spending a snapshot() to find out.
    changed = payload.get('changed')
    if changed:
        body = body + '\n[' + changed + ']'
    return _text(body)


def handle(req: dict):
    method = req.get('method')
    if method == 'initialize':
        return {
            'protocolVersion': '2024-11-05',
            'capabilities': {'tools': {}},
            'serverInfo': {'name': 'fusion360', 'version': '1.0.0'},
        }
    if method == 'tools/list':
        return {'tools': [TOOL]}
    if method == 'tools/call':
        params = req.get('params', {})
        if params.get('name') != TOOL['name']:
            return {'content': _text('Unknown tool'), 'isError': True}
        return {'content': call_fusion(params.get('arguments', {}).get('code', ''))}
    return None  # notifications (e.g. notifications/initialized) get no reply


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        result = handle(req)
        if 'id' not in req:  # notification
            continue
        resp = {'jsonrpc': '2.0', 'id': req['id']}
        if result is None:
            resp['error'] = {'code': -32601, 'message': 'Method not found'}
        else:
            resp['result'] = result
        sys.stdout.write(json.dumps(resp) + '\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
