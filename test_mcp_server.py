"""Minimal protocol check: python test_mcp_server.py"""
import json, os, subprocess, sys

SERVER = os.path.join('src', 'fusion360_mcp', 'server.py')

REQS = [
    {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}},
    {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
    {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
    {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call',
     'params': {'name': 'fusion_eval', 'arguments': {'code': 'result = 1'}}},
]

out = subprocess.run(
    [sys.executable, SERVER],
    input='\n'.join(json.dumps(r) for r in REQS),
    capture_output=True, text=True, timeout=90,
).stdout
lines = [json.loads(l) for l in out.splitlines() if l.strip()]

assert len(lines) == 3, f'expected 3 replies (notification unanswered), got {len(lines)}: {lines}'
assert [l['id'] for l in lines] == [1, 2, 3], lines
assert lines[0]['result']['serverInfo']['name'] == 'fusion360', lines[0]
assert lines[1]['result']['tools'][0]['name'] == 'fusion_eval', lines[1]
block = lines[2]['result']['content'][0]
assert block['type'] == 'text', block
text = block['text']
assert text == '1' or 'Cannot reach Fusion' in text, text
live = text == '1'

# Image blocks must come back as MCP image content, not a JSON blob of base64.
if live:
    out = subprocess.run(
        [sys.executable, SERVER],
        input=json.dumps({'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call',
                          'params': {'name': 'fusion_eval',
                                     'arguments': {'code': 'result = screenshot(200, 150)'}}}),
        capture_output=True, text=True, timeout=90,
    ).stdout
    img = json.loads(out.splitlines()[0])['result']['content'][0]
    assert img['type'] == 'image', img
    assert img['mimeType'] == 'image/png', img
    assert len(img['data']) > 100, 'empty image payload'

def call(code, _id=[10]):
    """Run one code string through the server, return the first content block."""
    _id[0] += 1
    out = subprocess.run(
        [sys.executable, SERVER],
        input=json.dumps({'jsonrpc': '2.0', 'id': _id[0], 'method': 'tools/call',
                          'params': {'name': 'fusion_eval', 'arguments': {'code': code}}}),
        capture_output=True, text=True, timeout=90,
    ).stdout
    return json.loads(out.splitlines()[0])['result']['content'][0]

# undo(): a failed call rolls itself back, and a good call is undoable once.
if live:
    before = call('result = snapshot()')['text']

    build = ("import adsk.core, adsk.fusion\n"
             "sk = root.sketches.add(root.xYConstructionPlane)\n"
             "sk.sketchCurves.sketchCircles.addByCenterRadius("
             "adsk.core.Point3D.create(0,0,0), 1.0)\n"
             "ext = root.features.extrudeFeatures\n"
             "inp = ext.createInput(sk.profiles.item(0),"
             " adsk.fusion.FeatureOperations.NewBodyFeatureOperation)\n"
             "inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(0.5))\n"
             "ext.add(inp).bodies.item(0).name = %r\n")

    # A call that raises after building must leave nothing behind.
    crashed = call(build % 'TEST_CRASH' + "raise RuntimeError('boom')")['text']
    assert 'Rolled back' in crashed, crashed
    assert call('result = snapshot()')['text'] == before, 'crash left geometry behind'

    # A call that succeeds is undoable, exactly once.
    call(build % 'TEST_UNDO')
    assert call('result = snapshot()')['text'] != before, 'build did nothing'
    assert 'undone' in call('result = undo()')['text']
    assert call('result = snapshot()')['text'] == before, 'undo did not restore state'
    assert 'nothing to undo' in call('result = undo()')['text'], 'undo went too far'

print('ok — protocol fine.',
      'Fusion connected, image + undo ok.' if live else 'Fusion not running (expected if closed).')
