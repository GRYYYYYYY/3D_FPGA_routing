#!/usr/bin/env python3
"""Reconstruct original and actual-target drift gates on a reproduced sealed Tf trajectory."""
from pathlib import Path
import json,re,sys,hashlib
B=Path(sys.argv[1]);assert json.loads((B/'input_seal.json').read_text())['passed'];reg=json.loads((B/'registration.json').read_text());out={}
for c in reg['circuits']:
 rd=B/'runs'/f'{c}_T';m=json.loads((rd/'manifest.json').read_text());assert m['status']=='completed' and m['metrics']['native_full_check_passed']
 for f in ['final_guide_audit.json','target_gate_trace_equivalence.json']:assert json.loads((rd/f).read_text())['passed']
 assert json.loads((rd/'independent_audit.json').read_text())['audit']['passed']
 env=m['environment'];assert env['VPR_H3D_TRACE_TARGET_GATE']==env['VPR_H3D_TARGET_FEEDBACK']=='1'
 for key in ['VPR_H3D_PLANAR_FEEDBACK','VPR_H3D_EXIT_PRICE']:assert float(env[key])==0
 records=[];current=None
 for l in (rd/'stdout.log').read_text().splitlines():
  if l.startswith('H3D_TARGET_GATE '):
   r=dict(re.findall(r'(\w+)=(\S+)',l));r={k:float(v) if k in ['drift','target_drift','change'] else int(v) for k,v in r.items()}
   cooled=r['iter']-r['last_attempt']>=r['cooldown'];due=lambda d:cooled and (bool(r['crossing_overuse']) or d>=.15 or r['change']>=.25)
   assert r['original_due']==due(r['drift']) and r['target_original_due']==due(r['target_drift']) and r['due']==r['original_due']
   assert 0<=r['target_drift']<=r['drift'] and 0<=r['target_missing']<=r['missing'] and 0<=r['eligible']<=r['targets'] and 0<=r['guided']<=r['targets']
   assert r['target_original_due']<=r['original_due']
   r.update(refresh=None,changed_pins=0);records.append(r);current=r
  elif l.startswith('H3D_REFRESH '):
   r=dict(re.findall(r'(\w+)=(\S+)',l));assert current and current['due'] and int(r['net'])==current['net'] and int(r['iter'])==current['iter'] and current['refresh'] is None;current['refresh']=r
  elif l.startswith('H3D_UPDATE_PIN '):
   r=dict(x.split('=',1) for x in l.split()[1:]);assert current and current['refresh'] and current['refresh']['accepted']=='1' and int(r['net'])==current['net'] and int(r['iter'])==current['iter'];current['changed_pins']+=1
  elif l.startswith('H3D_FEEDBACK '):feedback=dict(re.findall(r'(\w+)=(\S+)',l))
 assert len(records)==int(feedback['checks']) and sum(r['due'] for r in records)==int(feedback['attempts'])
 assert all((r['refresh'] is not None)==bool(r['due']) for r in records)
 extra=[r for r in records if r['original_due'] and not r['target_original_due']]
 def describe(rs):
  return dict(contexts=len(rs),unique_nets=len({r['net'] for r in rs}),accepted=sum(r['refresh'] and r['refresh']['accepted']=='1' for r in rs),changed_preferences=sum(r['changed_pins'] for r in rs),accepted_without_changed_preferences=sum(r['refresh'] and r['refresh']['accepted']=='1' and r['changed_pins']==0 for r in rs),no_eligible_targets=sum(r['eligible']==0 for r in rs),no_previously_guided_targets=sum(r['guided']==0 for r in rs))
 out[c]=dict(metrics=m['metrics'],feedback=feedback,all_attempts=describe([r for r in records if r['due']]),non_target_drift_only_attempts=describe(extra),records=extra)
result=dict(passed=True,circuits=out,scope='Exact route/table/refresh/guide/query/pinchange reproduction; independent final route/guide audit and input seal. Repeated observed contexts, not independent samples. Original trajectory counterfactual gate counts do not predict the trajectory after changing cooldown/decisions. No cost reduction or QoR claim.',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(B/'target_gate_mechanisms.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({c:{k:v for k,v in r.items() if k!='records'} for c,r in out.items()},indent=2))
