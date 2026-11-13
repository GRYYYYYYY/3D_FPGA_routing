#!/usr/bin/env python3
"""Verify decision-neutral prior-coverage diagnostics against refresh receipts."""
from pathlib import Path
import json,re,sys,math,struct,hashlib,collections
D=Path(__file__).resolve().parent;B=Path(sys.argv[1]) if len(sys.argv)>1 else D/'eligibility_trigger_dev_01'
rd=B/'runs/eltwise_layer_B';m=json.loads((rd/'manifest.json').read_text());assert m['status']=='completed'
assert json.loads((rd/'independent_audit.json').read_text())['audit']['passed']
assert json.loads((rd/'final_guide_audit.json').read_text())['passed']
assert json.loads((B/'input_seal.json').read_text())['passed']
f32=lambda x:struct.unpack('f',struct.pack('f',float(x)))[0]
threshold=f32(m['environment']['VPR_H3D_MIN_CRITICALITY']);reasons={};pins=collections.defaultdict(list);refresh={}
for line in (rd/'stdout.log').read_text().splitlines():
 prefix=line.split(' ',1)[0]
 if prefix not in ['H3D_PRIOR_PIN','H3D_PRIOR_REASON','H3D_REFRESH']:continue
 r=dict(re.findall(r'(\w+)=([^ ]+)',line));key=(int(r['net']),int(r['iter']))
 if prefix=='H3D_PRIOR_PIN':
  p={k:int(v) if k in ['net','iter','pin','newly_eligible'] else f32(v) if k in ['old_criticality','new_criticality'] else v for k,v in r.items()}
  assert p['reason']=='empty' and p['new_criticality']>=threshold
  assert bool(p['newly_eligible'])==(p['old_criticality']<threshold)
  pins[key].append(p)
 elif prefix=='H3D_PRIOR_REASON':
  assert key not in reasons;reasons[key]={k:float(v) if k.endswith('_cost') else int(v) for k,v in r.items()}
 else:
  assert key not in refresh;refresh[key]=r
assert reasons.keys()==refresh.keys() and set(pins)<=reasons.keys()
rows=[]
for key,r in reasons.items():
 other=sum(r[k] for k in ['multiple','outside','branch_missing','branch_nonfinite','opening_nonfinite'])
 assert r['empty']==r['empty_newly_eligible']+r['empty_previously_eligible']==len(pins[key])
 assert sum(p['newly_eligible'] for p in pins[key])==r['empty_newly_eligible']
 assert r['accepted']==int(refresh[key]['accepted'])
 assert r['old_cost']==float(refresh[key]['old_cost']) and r['new_cost']==float(refresh[key]['new_cost'])
 if r['table']:
  assert r['leaves']==r['pairs']+r['empty']+r['multiple']+r['outside']
  assert r['branch_missing']+r['branch_nonfinite']<=r['pairs'] and r['opening_nonfinite']<=r['pairs']
  assert (not math.isfinite(r['old_cost']))==bool(r['empty']+other),r
  assert not r['clear']
 if r['clear']:assert r['table']==0 and r['leaves']==0
 r['only_new_eligible_empty']=bool(r['empty_newly_eligible']) and r['empty_previously_eligible']==0 and other==0
 r['missing_pins']=pins[key];rows.append(r)
accepted=[r for r in rows if r['accepted'] and not r['clear'] and not math.isfinite(r['old_cost'])]
clear=[r for r in rows if r['accepted'] and r['clear']]
summary=dict(attempts=len(rows),table_attempts=sum(r['table'] for r in rows),accepted_nonfinite_prior=len(accepted),accepted_nonfinite_explained_only_by_new_eligibility=sum(r['only_new_eligible_empty'] for r in accepted),accepted_nonfinite_other_causes=sum(not r['only_new_eligible_empty'] for r in accepted),accepted_empty_pin_events=sum(r['empty'] for r in accepted),accepted_newly_eligible_pin_events=sum(r['empty_newly_eligible'] for r in accepted),unique_accepted_newly_eligible_pins=len({(r['net'],p['pin']) for r in accepted for p in r['missing_pins'] if p['newly_eligible']}),accepted_clear=len(clear),accepted_clear_previously_nonempty=sum(r['old_guided']>0 for r in clear),accepted_clear_already_empty=sum(r['old_guided']==0 for r in clear))
files=[rd/f for f in ['stdout.log','manifest.json','independent_audit.json','final_guide_audit.json']]+[B/'input_seal.json',Path(__file__)]
result=dict(scope='Eligibility-trigger variant is independently audited; equality to the old trajectory is not required. Criticality is current planner timing state, not final STA or proof that a given event caused the CPD gain. Empty guide classifications use last accepted feedback-state criticality, float32-roundtripped from nine significant digits.',threshold_float32=threshold,summary=summary,rows=rows,input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
(B/'eligibility_reason_analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summary,indent=2))
