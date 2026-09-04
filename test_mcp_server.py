"""Minimal protocol check: python test_mcp_server.py"""
import json, subprocess, sys

REQS = [
    {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}},
    {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
    {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
    {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call',
     'params': {'name': 'fusion_eval', 'arguments': {'code': 'result = 1'}}},
]

out = subprocess.run(
    [sys.executable, 'mcp_server.py'],
    input='\n'.join(json.dumps(r) for r in REQS),
    capture_output=True, text=True, timeout=90,
).stdout
lines = [json.loads(l) for l in out.splitlines() if l.strip()]

assert len(lines) == 3, f'expected 3 replies (notification unanswered), got {len(lines)}: {lines}'
assert [l['id'] for l in lines] == [1, 2, 3], lines
assert lines[0]['result']['serverInfo']['name'] == 'fusion360', lines[0]
assert lines[1]['result']['tools'][0]['name'] == 'fusion_eval', lines[1]
text = lines[2]['result']['content'][0]['text']
assert text == '1' or 'Cannot reach Fusion' in text, text
print('ok — protocol fine.', 'Fusion connected.' if text == '1' else 'Fusion not running (expected if closed).')
