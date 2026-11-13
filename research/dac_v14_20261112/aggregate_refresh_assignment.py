#!/usr/bin/env python3
"""Fixed four-circuit feedback-only solver ablation with matched reused controls."""
from pathlib import Path
import collections,hashlib,json,math
D=Path(__file__).resolve().parent
population={'eltwise_layer':'refresh_assignment_dev_01','spmv':'refresh_assignment_expansion_dev_01','softmax':'refresh_assignment_expansion_dev_01','bnn':'refresh_assignment_expansion_dev_01'}
rows=[];bindings={};envs={};ri_binaries=set()
def read(p):
 data=p.read_bytes();bindings[str(p)]=hashlib.sha256(data).hexdigest();return json.loads(data)
assert read(D/'target_membership_dev_02/target_membership_mechanisms.json')['passed']
assert read(D/'refresh_assignment_dev_01/runs/eltwise_layer_C/refresh_assignment_control_equivalence.json')['passed']
for c,batch in population.items():
 B=D/batch;assert read(B/'input_seal.json')['passed'];refs=read(B/f'{c}_references.json');assert read(B/'refresh_assignment_mechanisms.json')['passed']
 for arm in ['A0','R1','Tf','Ri']:
  rd=B/'runs'/f'{c}_C' if arm=='Tf' and c=='eltwise_layer' else B/'runs'/f'{c}_Ri' if arm=='Ri' else Path(refs[arm]['path'])
  if not (rd/'manifest.json').exists():rows.append(dict(circuit=c,arm=arm,status='missing',metrics={},path=str(rd)));continue
  m=read(rd/'manifest.json');audit=read(rd/'independent_audit.json') if (rd/'independent_audit.json').exists() else None
  legal=m['status']=='completed' and m['metrics']['native_full_check_passed'] and audit and audit['audit']['passed']
  if arm in ['Tf','Ri']:
   assert read(rd.parent.parent/'input_seal.json')['passed']
   if legal:assert read(rd/'final_guide_audit.json')['passed']
   env=dict(m['environment']);env.setdefault('VPR_H3D_TARGET_DRIFT','0');env.setdefault('VPR_H3D_TRACE_TARGET_GATE','0');env.setdefault('VPR_H3D_REFRESH_ASSIGNMENT','inherit')
   assert env['VPR_H3D_REFRESH_ASSIGNMENT']==('independent' if arm=='Ri' else 'inherit') and env['VPR_H3D_TARGET_FEEDBACK']=='1' and env['VPR_H3D_ASSIGNMENT']=='shared'
   if arm in envs:assert env==envs[arm],(c,arm)
   else:envs[arm]=env
   if arm=='Ri':ri_binaries.add(m['shared_inputs'][m['command'][0]]['sha256'])
  rows.append(dict(circuit=c,arm=arm,status='legal' if legal else m['status'],metrics=m.get('metrics') or {},physical_metrics=audit.get('physical_metrics') if audit else None,process_seconds=m.get('wall_seconds'),path=str(rd),reference_semantics='CexactTf' if arm=='Tf' and c=='eltwise_layer' else arm))
assert len(ri_binaries)==1;idx={(r['circuit'],r['arm']):r for r in rows};comparisons={}
for left,right in [('Tf','Ri'),('A0','Ri'),('R1','Ri')]:
 cases=[]
 for c in population:
  a,b=idx[c,left],idx[c,right]
  if a['status']!=b['status'] or a['status']!='legal':continue
  ratio=b['metrics']['critical_path_ns']/a['metrics']['critical_path_ns'];cases.append(dict(circuit=c,reference_ns=a['metrics']['critical_path_ns'],new_ns=b['metrics']['critical_path_ns'],ratio=ratio,improvement_pct=100*(1-ratio)))
 comparisons[left+'->'+right]=dict(declared_circuits=len(population),both_legal=len(cases),improve=sum(r['ratio']<1 for r in cases),tie=sum(r['ratio']==1 for r in cases),regress=sum(r['ratio']>1 for r in cases),circuit_geomean_improvement_pct=100*(1-math.exp(sum(math.log(r['ratio']) for r in cases)/len(cases))) if cases else None,worst_improvement_pct=min((r['improvement_pct'] for r in cases),default=None),cases=cases)
out=dict(scope='Four seen seed11HybridO/P0/W100 cases, fixed per-arm environment after explicitly normalizing absent default-off flags. Same Ri binary, paired C exactTf pilot plus strict matched sealed Tf controls reused for transfer; NOT all-row samebinary formal timing. Initial sharedplanning preserved; refresh solver/objective isolated. Later routing contexts may differ.',statuses={a:dict(collections.Counter(r['status'] for r in rows if r['arm']==a)) for a in ['A0','R1','Tf','Ri']},comparisons=comparisons,observations=rows,input_sha256=bindings)
(D/'refresh_assignment_circuit_summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(comparisons,indent=2))
