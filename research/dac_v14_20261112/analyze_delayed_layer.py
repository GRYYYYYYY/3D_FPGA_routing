#!/usr/bin/env python3
"""Audit delayed global expansion versus the selective-scope reproduction."""
from pathlib import Path
import hashlib,json,re,sys
B=Path(sys.argv[1]);reg=json.loads((B/'registration.json').read_text());assert json.loads((B/'input_seal.json').read_text())['passed'];result={}
parse=lambda s:{k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',s)}
for c in reg['circuits']:
 result[c]={}
 for a in reg['arms']:
  rd=B/'runs'/f'{c}_{a}';m=json.loads((rd/'manifest.json').read_text())
  if m['status']!='completed':result[c][a]=dict(status=m['status']);continue
  audit=json.loads((rd/'independent_audit.json').read_text());assert m['metrics']['native_full_check_passed'] and audit['audit']['passed']
  if a!='A3':assert json.loads((rd/'final_guide_audit.json').read_text())['passed']
  lines=(rd/'stdout.log').read_text().splitlines();initial=[parse(s) for s in lines if s.startswith('H3D_LAYER_BB ')];assert len(initial)==1
  if a=='F1c':assert initial[0]['enabled']==1 and initial[0]['expanded_nets']==initial[0]['restricted_nets']
  else:assert initial[0]['expanded_nets']==0
  delayed=[parse(s) for s in lines if s.startswith('H3D_LAYER_BB_DELAYED ')];selective=[parse(s) for s in lines if s.startswith('H3D_LAYER_BB_REFRESH ')]
  if a in ['S','F1c']:
   assert not delayed and json.loads((rd/'default_off_equivalence.json').read_text())['passed']
  else:
   assert not selective and len(delayed)==1 and delayed[0]['iter']==2
   assert delayed[0]['new_min']==0 and delayed[0]['new_max']==initial[0]['layers']-1
   assert 0<=delayed[0]['expanded_nets']<=initial[0]['restricted_nets']
  result[c][a]=dict(status='legal',initial=initial[0],delayed=delayed,selective_expansions=len(selective),metrics=m['metrics'],physical_metrics=audit['physical_metrics'],process_seconds=m['wall_seconds'],log_sha256=hashlib.sha256((rd/'stdout.log').read_bytes()).hexdigest())
(B/'delayed_mechanisms.json').write_text(json.dumps(dict(passed=True,scope='Exactly one global expansion at iteration2, no selective events, independently audited final routes; S reproduces selective F2. Does not independently reconstruct per-iteration BB coordinates.',circuits=result,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
print(json.dumps(result,indent=2))
