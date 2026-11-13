#!/usr/bin/env python3
"""Reconcile monotonic scope events, controls and rollback diagnostics after seal."""
from pathlib import Path
import collections,hashlib,json,re,sys
B=Path(sys.argv[1]);reg=json.loads((B/'registration.json').read_text())
assert json.loads((B/'input_seal.json').read_text())['passed']
results={}
for circuit in reg['circuits']:
 results[circuit]={}
 for arm in reg['arms']:
  rd=B/'runs'/f'{circuit}_{arm}';m=json.loads((rd/'manifest.json').read_text())
  if m['status']!='completed':results[circuit][arm]=dict(status=m['status']);continue
  assert m['metrics']['native_full_check_passed']
  assert json.loads((rd/'independent_audit.json').read_text())['audit']['passed']
  if arm not in ['A','A2']:assert json.loads((rd/'final_guide_audit.json').read_text())['passed']
  enabled=m['environment'].get('VPR_H3D_LAYER_BB_FEEDBACK')=='1'
  lines=(rd/'stdout.log').read_text().splitlines()
  parse=lambda l:{k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',l)}
  initial=[parse(l) for l in lines if l.startswith('H3D_LAYER_BB ')];assert len(initial)==1 and initial[0]['expanded_nets']==0 and initial[0]['enabled']==0
  events=[parse(l) for l in lines if l.startswith('H3D_LAYER_BB_REFRESH ')];assert enabled or not events
  assert len({x['net'] for x in events})==len(events),'No net may oscillate or re-expand'
  assert len(events)<=initial[0]['restricted_nets']
  for e in events:
   assert e['iter']>=2 and e['occ']>e['cap']>=0
   assert 0<=e['old_min']<=e['old_max']<initial[0]['layers']
   assert e['new_min']==0 and e['new_max']==initial[0]['layers']-1
   assert (e['old_min'],e['old_max'])!=(e['new_min'],e['new_max'])
  if arm in ['A','F','U']:assert json.loads((rd/'default_off_equivalence.json').read_text())['passed']
  if arm=='X2':assert json.loads((rd/'rollback_exercised.json').read_text())['rollbacks']==1
  results[circuit][arm]=dict(status='legal',enabled=enabled,expanded_nets=len(events),initially_restricted=initial[0]['restricted_nets'],
    by_iteration=dict(collections.Counter(e['iter'] for e in events)),events=events,metrics=m['metrics'],
    input_sha256={f:hashlib.sha256((rd/f).read_bytes()).hexdigest() for f in ['manifest.json','stdout.log','routed.route','independent_audit.json']})
result=dict(passed=True,scope='Trace consistency and unique monotonic expansion, alongside independently audited final legality and exact disabled controls. Overuse witness numbers are runtime instrumentation, not independently reconstructed per-iteration occupancy. X2 tests one forced transaction and is not a quality-benefit arm.',circuits=results,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(B/'selective_layer_mechanisms.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({c:{a:{k:v for k,v in r.items() if k not in ['events','input_sha256']} for a,r in arms.items()} for c,arms in results.items()},indent=2))
