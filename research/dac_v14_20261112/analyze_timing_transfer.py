#!/usr/bin/env python3
"""Transfer audits and logged formula checks; independent exact-distance reconstruction is pilot-only."""
from pathlib import Path
import json,csv,math,re,hashlib,sys
B=Path(sys.argv[1]);D=B.parent
assert json.loads((B/'input_seal.json').read_text())['passed']
assert json.loads((D/'timing_regret_dev_01/timing_regret_mechanisms.json').read_text())['passed']
reg=json.loads((B/'registration.json').read_text());rows={}
def body(p):
 t=p.read_text();return hashlib.sha256(t[t.index('Net '):].encode()).hexdigest()
for c in reg['circuits']:
 rows[c]={};control=B/'runs'/f'{c}_P'
 if (control/'timing_control_equivalence.json').exists():assert json.loads((control/'timing_control_equivalence.json').read_text())['passed']
 for a in reg['arms']:
  p=B/'runs'/f'{c}_{a}';m=json.loads((p/'manifest.json').read_text())
  if m['status']!='completed':rows[c][a]=dict(status=m['status']);continue
  audit=json.loads((p/'independent_audit.json').read_text());assert audit['audit']['passed'] and m['metrics']['native_full_check_passed']
  assert json.loads((p/'final_guide_audit.json').read_text())['passed']
  if a!='P':assert json.loads((p/'same_planning_gate.json').read_text())['passed']
  env=m['environment'];assert env['VPR_H3D_TIMING_GUIDE_MODE']==('regret' if a=='Tg' else 'coverage')
  assert float(env['VPR_H3D_TIMING_GUIDE'])==(0. if a=='P' else .25)
  for key in ['FEEDBACK','SOURCE_GEOMETRY_FLOOR','REVERSE_RERANK','QUERY_CRITICALITY_ORDER','SOURCE_QUERY_SHARE','BOUND_CLAMP','ALL_LAYER_BB','LAYER_BB_DELAYED','LAYER_BB_FEEDBACK']:assert env['VPR_H3D_'+key]=='0'
  assert env['VPR_H3D_DELAY_BUDGET']=='4096' and env['VPR_H3D_TARGET_QUOTA']=='256'
  guides={(int(g['net']),int(g['pin'])):g for g in csv.DictReader((p/'h3d_final_guides.csv').open())}
  prior={(int(g['net']),int(g['pin'])):g for g in csv.DictReader((control/'h3d_final_guides.csv').open())}
  assert {k:g['preferred'] for k,g in guides.items()}=={k:g['preferred'] for k,g in prior.items()}
  lines=(p/'stdout.log').read_text().splitlines();entries={}
  for line in lines:
   if not line.startswith('H3D_TIMING_REGRET '):continue
   r=dict(x.split('=') for x in line.split()[1:]);key=int(r['net']),int(r['pin']),int(r['alternative']);assert key not in entries;entries[key]=r
   assert a=='Tg' and guides[key[:2]]['preferred']==r['chosen']+';'
   src,alt,u,w,pen=[float(r[k]) for k in ['chosen_seconds','alternative_seconds','unit','weight','penalty']]
   assert all(math.isfinite(v) for v in [src,alt,u,w,pen]) and w==.25 and 0.<pen<=.25*u
   assert math.isclose(pen,.25*min(u,max(0.,alt-src-.02*u)),rel_tol=1e-12,abs_tol=1e-20)
  summaries=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith('H3D_TIMING_REGRET_SUMMARY ')]
  assert summaries and int(summaries[-1]['pairs'])==len(entries)
  assert int(summaries[-1]['guides'])==len({k[:2] for k in entries})
  rows[c][a]=dict(status='legal',metrics=m['metrics'],physical_metrics=audit['physical_metrics'],same_route_as_P=body(p/'routed.route')==body(control/'routed.route'),regret_pairs=len(entries),regret_guides=len({k[:2] for k in entries}),planning_seconds=float(re.findall(r'planning_seconds=([0-9.]+)','\n'.join(l for l in lines if l.startswith('H3D_PLAN ')))[-1]),process_seconds=m['wall_seconds'])
(B/'timing_transfer_mechanisms.json').write_text(json.dumps(dict(passed=True,circuits=rows,scope='Native and independent route/guide legality, controls, identical finite table/query states, original parameters, sparse logged formula/bound checks. Exact graph-distance reconstruction was performed on pilot; transfer formula verification is not a new independent distance oracle. No formal timing claim.'),indent=2)+'\n');print(json.dumps(rows,indent=2))
