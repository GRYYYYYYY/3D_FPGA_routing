#!/usr/bin/env python3
"""Evaluate trigger-only pilot, actual extra accepted proposals and transaction exercise."""
from pathlib import Path
import json,re,sys,hashlib,math
B=Path(sys.argv[1]);assert json.loads((B/'input_seal.json').read_text())['passed'];reg=json.loads((B/'registration.json').read_text());results={}
for c in reg['circuits']:
 results[c]={}
 for arm in reg['arms']:
  rd=B/'runs'/f'{c}_{arm}';m=json.loads((rd/'manifest.json').read_text())
  if m['status']!='completed':results[c][arm]=dict(status=m['status']);continue
  audit=json.loads((rd/'independent_audit.json').read_text());assert m['metrics']['native_full_check_passed'] and audit['audit']['passed'] and json.loads((rd/'final_guide_audit.json').read_text())['passed']
  if arm=='V':assert json.loads((rd/'optimization_equivalence.json').read_text())['passed']
  env=m['environment'];assert env['VPR_H3D_FEEDBACK']=='1' and env['VPR_H3D_PLANAR_FEEDBACK']==('0' if arm=='V' else '1')
  assert env['VPR_H3D_TRACE_PLANAR_FEEDBACK']=='0' and env['VPR_H3D_MIXED_DELAY']==env['VPR_H3D_TIMING_GUIDE']==env['VPR_H3D_EQUIVALENT_GUIDES']=='0'
  for k in ['TARGET_DELAY','TARGET_FRONTIER','LAYER_BB_DELAYED','ALL_LAYER_BB','LAYER_BB_FEEDBACK']:assert env['VPR_H3D_'+k]=='0'
  lines=(rd/'stdout.log').read_text().splitlines();extra=[];pending=None;rollbacks=[]
  for line in lines:
   if line.startswith('H3D_PLANAR_TRIGGER '):
    assert pending is None;r={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)}
    assert r['affected_paths']>0 and r['planar_nodes']>0 and r['iter']-r['last_attempt']>=r['cooldown']==3
    pending=dict(r,clear=False)
   elif line.startswith('H3D_REFRESH_CLEAR ') and pending:
    r=dict(re.findall(r'(\w+)=(\S+)',line));assert int(r['net'])==pending['net'];pending['clear']=True
   elif line.startswith('H3D_REFRESH ') and pending:
    r=dict(re.findall(r'(\w+)=(\S+)',line));assert int(r['net'])==pending['net'] and int(r['iter'])==pending['iter']
    pending.update(accepted=bool(int(r['accepted'])),old_cost=r['old_cost'],new_cost=r['new_cost']);extra.append(pending);pending=None
   elif line.startswith('H3D_GUIDE_ROLLBACK '):
    r=dict(re.findall(r'(\w+)=(\S+)',line));assert r['restored']=='1';rollbacks.append(int(r['net']))
  assert pending is None
  summary=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith('H3D_PLANAR_FEEDBACK ')][-1];assert int(summary['extra_attempts'])==len(extra)
  if arm=='V':assert not extra
  final=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith('H3D_FINAL ')][-1];assert final['success']=='1' and int(final['guide_rollbacks'])==len(rollbacks)
  if arm=='X':assert len(rollbacks)>=1 and env['VPR_H3D_TEST_ROLLBACK_ONCE']=='1'
  feedback=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith('H3D_FEEDBACK ')][-1]
  delay=[dict(re.findall(r'(\w+)=(\S+)',l)) for l in lines if l.startswith('H3D_DELAY ')][-1]
  results[c][arm]=dict(status='legal',diagnostic_only=arm=='X',metrics=m['metrics'],physical_metrics=audit['physical_metrics'],extra_attempts=len(extra),extra_unique_nets=len({e['net'] for e in extra}),extra_accepted=sum(e['accepted'] for e in extra),extra_clear=sum(e['accepted'] and e['clear'] for e in extra),extra_events=extra,feedback=feedback,delay=delay,guide_rollbacks=len(rollbacks),planning_seconds=float(re.findall(r'planning_seconds=([0-9.]+)','\n'.join(l for l in lines if l.startswith('H3D_PLAN ')))[-1]),process_seconds=m['wall_seconds'])
out=dict(passed=True,circuits=results,scope='Additional guided-path ordinary planar-overuse trigger only on native-selected nets, same objective/query/5percent acceptance. Exact off control, independent final legality/adoption audits and sealed inputs. Extra events can change later opportunity population; do not equate with old43counterfactual opportunities. Xtests existing rollback path and final legality, excludedQoRbenefit; not proof that first forced rejection followed an accepted new planar update. Development times only.',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(B/'planar_feedback_mechanisms.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({c:{a:{k:v for k,v in r.items() if k!='extra_events'} for a,r in arms.items()} for c,arms in results.items()},indent=2))
