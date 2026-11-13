#!/usr/bin/env python3
"""Independently reconstruct sparse timing preferences from sealed P traces and exact oracle."""
from pathlib import Path
import csv,json,math,re,hashlib,sys
B=Path(sys.argv[1]).resolve();D=B.parent;O=D/'estimate_oracle_01'
assert json.loads((B/'input_seal.json').read_text())['passed']
assert json.loads((O/'input_seal.json').read_text())['passed']
reg=json.loads((B/'registration.json').read_text());exact={(int(r['endpoint']),int(r['reverse']),int(r['target'])):float(r['seconds']) for r in csv.DictReader((O/'exact.csv').open())}
traces={}
for r in csv.DictReader((O/'estimates.csv').open()):
 if r['run'].endswith('_P') and r['phase'] in ['table','selected']:
  traces[(r['run'],int(r['net']),int(r['pin']),int(r['candidate']))]=r
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={}
for c in reg['circuits']:
 control=B/'runs'/f'{c}_P';rows={}
 assert json.loads((control/'timing_control_equivalence.json').read_text())['passed']
 guides={(int(r['net']),int(r['pin'])):r for r in csv.DictReader((control/'h3d_final_guides.csv').open())}
 selected={key:int(g['preferred'].strip(';')) for key,g in guides.items()}
 expected={}
 for (run,net,pin,cand),r in traces.items():
  if run!=c+'_P' or cand==selected[net,pin] or r['source_known']!='1' or r['sink_known']!='1':continue
  chosen=traces[run,net,pin,selected[net,pin]]
  if chosen['source_known']!='1' or chosen['sink_known']!='1':continue
  source,sink=int(r['source']),int(r['sink']);unit=float(r['unit'])
  prior=exact[source,0,selected[net,pin]]+exact[sink,1,selected[net,pin]]
  alt=exact[source,0,cand]+exact[sink,1,cand]
  penalty=.25*min(unit,max(0.,alt-prior-.02*unit))
  if penalty>0.:expected[net,pin,cand]=(prior,alt,unit,penalty)
 for arm in reg['arms']:
  rd=B/'runs'/f'{c}_{arm}';m=json.loads((rd/'manifest.json').read_text())
  if m['status']!='completed':rows[arm]=dict(status=m['status']);continue
  assert m['metrics']['native_full_check_passed']
  audit=json.loads((rd/'independent_audit.json').read_text());assert audit['audit']['passed']
  assert json.loads((rd/'final_guide_audit.json').read_text())['passed']
  if arm!='P':assert json.loads((rd/'same_planning_gate.json').read_text())['passed']
  env=m['environment'];assert env['VPR_H3D_DELAY_BUDGET']=='4096' and env['VPR_H3D_TARGET_QUOTA']=='256'
  assert env['VPR_H3D_TIMING_GUIDE_MODE']==('regret' if arm=='Tg' else 'coverage')
  assert float(env['VPR_H3D_TIMING_GUIDE'])==(0. if arm=='P' else .25)
  actual_guides=list(csv.DictReader((rd/'h3d_final_guides.csv').open()))
  assert {(int(r['net']),int(r['pin'])):r['preferred'] for r in actual_guides}=={k:r['preferred'] for k,r in guides.items()}
  lines=(rd/'stdout.log').read_text().splitlines();records=[dict(x.split('=') for x in l.split()[1:]) for l in lines if l.startswith('H3D_TIMING_REGRET ')]
  actual={}
  for r in records:
   key=int(r['net']),int(r['pin']),int(r['alternative']);assert key not in actual;actual[key]=r
  if arm=='Tg':
   assert actual.keys()==expected.keys(),(c,len(actual),len(expected))
   for key,r in actual.items():
    assert int(r['chosen'])==selected[key[:2]] and float(r['weight'])==.25
    for field,value in zip(['chosen_seconds','alternative_seconds','unit','penalty'],expected[key]):
     assert math.isclose(float(r[field]),value,rel_tol=1e-10,abs_tol=1e-18),(key,field,r[field],value)
    assert 0.<float(r['penalty'])<=.25*float(r['unit'])
  else:assert not actual
  final_penalized=sum(any((int(g['net']),int(g['pin']),int(x)) in actual for x in g['actual_crossings'].split(';') if x) for g in actual_guides)
  rows[arm]=dict(status='legal',metrics=m['metrics'],physical_metrics=audit['physical_metrics'],planning_seconds=float(re.findall(r'planning_seconds=([0-9.]+)','\n'.join(l for l in lines if l.startswith('H3D_PLAN ')))[-1]),process_seconds=m['wall_seconds'],regret_pairs=len(actual),regret_guides=len({k[:2] for k in actual}),final_connections_using_penalized_alternative=final_penalized,log_sha256=sha(rd/'stdout.log'))
 result[c]=rows
out=dict(passed=True,circuits=result,scope='Sparse Tg penalties exactly reconstructed from sealed decision-neutral P tables and independent graph distances; complete source/sink knowledge required for selected and alternative. Bound and deadband verified; same guides/tables/query work, native FULL and independent route audits. Final use is not a counter of search expansions, and graph-proxy regret is not final STA improvement. Development times only.',bindings={str(p):sha(p) for p in [Path(__file__),B/'input_seal.json',O/'input_seal.json',O/'exact.csv',O/'estimates.csv']})
(B/'timing_regret_mechanisms.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(result,indent=2))
