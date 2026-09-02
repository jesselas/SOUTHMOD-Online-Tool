"""Headless probe of the run-simulation callback on a running Dash app.

Usage: probe_dash.py BASE_URL CHOICE [--excel] [--reform]
"""
import json
import re
import sys
import urllib.request

BASE = sys.argv[1].rstrip('/')
CHOICE = sys.argv[2]
EXCEL = '--excel' in sys.argv
REFORM = '--reform' in sys.argv

# Demo reform overrides (DV_2023_reform)
REFORM_VALUES = {
    'bsa_2_person': '300', 'bsa_3_plus_person': '450',
    'senior_grant_amount': '90', 'school_meal_value': '110', 'school_meal_age': '16',
    'pit_bracket2_rate': '0.03', 'pit_bracket3_thresh': '800', 'pit_bracket5_rate': '0.30',
    'pit_yse_turnover_threshold': '4000', 'presumptive_rate_4': '0.04',
}


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=300) as r:
        return json.loads(r.read())


layout = get('/_dash-layout')
deps = get('/_dash-dependencies')

comps = {}


def walk(node):
    if isinstance(node, dict):
        props = node.get('props', {})
        cid = props.get('id')
        if cid is not None:
            key = json.dumps(cid, sort_keys=True) if isinstance(cid, dict) else cid
            comps[key] = props
        for v in props.values():
            walk(v)
    elif isinstance(node, list):
        for v in node:
            walk(v)


walk(layout)

dep = next(d for d in deps if any(i['id'] == 'run-button' for i in d['inputs']))
param_keys = sorted(k for k in comps if k.startswith('{') and '"param-input"' in k)

state = []
for s in dep['state']:
    sid = s['id']
    if isinstance(sid, dict) or (isinstance(sid, str) and sid.startswith('{')):
        items = []
        for k in param_keys:
            cid = json.loads(k)
            v = cid if s['property'] == 'id' else comps[k].get(s['property'])
            if REFORM and s['property'] == 'value' and cid.get('index') in REFORM_VALUES:
                v = REFORM_VALUES[cid['index']]
            items.append({'id': cid, 'property': s['property'], 'value': v})
        state.append(items)
    else:
        v = comps.get(sid, {}).get(s['property'])
        if sid == 'analysis-choice':
            v = CHOICE
        if sid == 'generate-excel-switch':
            v = EXCEL
        state.append({**s, 'value': v})

outs = []
for part in dep['output'].strip('.').split('...'):
    i, p = part.rsplit('.', 1)
    outs.append({'id': i, 'property': p})
body = {'output': dep['output'], 'outputs': outs,
        'inputs': [{'id': 'run-button', 'property': 'n_clicks', 'value': 1}],
        'changedPropIds': ['run-button.n_clicks'], 'state': state}
req = urllib.request.Request(BASE + '/_dash-update-component',
                             data=json.dumps(body).encode(),
                             headers={'Content-Type': 'application/json'})
r = urllib.request.urlopen(req, timeout=600)
resp = json.loads(r.read())['response']
txt = json.dumps(resp)
tabs = [k for k in resp if k.startswith('tab-')]
empty_tabs = [k for k in tabs if not resp[k].get('children')]
placeholder_tabs = [k for k in tabs if 'Run a simulation to see results' in json.dumps(resp[k])
                    or 'under development' in json.dumps(resp[k])]
dl = resp.get('download-simulation-output', {}).get('data')
excel_ok = bool(dl and dl.get('content'))
print(f"choice={CHOICE} reform={REFORM} excel={EXCEL}: HTTP {r.status}, {len(txt)} bytes, "
      f"{len(tabs)} tabs")
print("  loading-output:", json.dumps(resp.get('loading-output', {}).get('children'))[:80])
print("  results-title:", json.dumps(resp.get('results-title', {}).get('children'))[:80])
print("  error alert:", 'error occurred during simulation' in txt.lower())
print("  empty/placeholder tabs:", empty_tabs + placeholder_tabs or 'none')
if EXCEL:
    print("  excel download:", 'yes, %d KB (%s)' % (len(dl['content']) * 3 // 4096, dl.get('filename'))
          if excel_ok else 'MISSING')
