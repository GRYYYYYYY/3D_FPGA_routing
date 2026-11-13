#!/usr/bin/env python3
"""Fixed four-circuit target-feedback transfer; keep all declared statuses and tails."""
from pathlib import Path
import json,math,collections,hashlib
D=Path(__file__).resolve().parent
population={'spmv':'target_feedback_expansion_dev_01','eltwise_layer':'target_feedback_dev_01','softmax':'target_feedback_expansion_dev_01','bnn':'target_feedback_expansion_dev_01'}
rows=[];bindings={};environments={};binaries=set()
for c,b in population.items():
 B=D/b;assert json.loads((B/'input_seal.json').read_text())['passed']
 refs=json.loads((B/f'{c}_references.json').read_text())
 for a in ['A0','R1','U','V','Tf']:
  rd=Path(refs[a]['path']) if a in refs else B/'runs'/f'{c}_{a}'
  if not (rd/'manifest.json').exists():
   rows.append(dict(circuit=c,arm=a,status='missing',metrics={},physical_metrics=None,path=str(rd)));continue
  m=json.loads((rd/'manifest.json').read_text());bindings[str(rd/'manifest.json')]=hashlib.sha256((rd/'manifest.json').read_bytes()).hexdigest()
  audit=json.loads((rd/'independent_audit.json').read_text()) if (rd/'independent_audit.json').exists() else None
  legal=m['status']=='completed' and m['metrics']['native_full_check_passed'] and audit and audit['audit']['passed']
  if a in ['V','Tf']:
   assert json.loads((rd/'final_guide_audit.json').read_text())['passed'] if legal else True
   env=m['environment'];previous=environments.setdefault(a,env);assert env==previous
   binary=m['command'][0];binaries.add(m['shared_inputs'][binary]['sha256'])
  rows.append(dict(circuit=c,arm=a,status='legal' if legal else m['status'],metrics=m['metrics'],process_seconds=m.get('wall_seconds'),physical_metrics=audit['physical_metrics'] if audit else None,path=str(rd)))
assert len(binaries)==1
idx={(r['circuit'],r['arm']):r for r in rows};paired={}
for left,right in [('A0','V'),('R1','V'),('U','Tf'),('V','Tf'),('A0','Tf'),('R1','Tf')]:
 ratios=[];cases=[]
 for c in population:
  a,b=idx[c,left],idx[c,right]
  if a['status']!='legal' or b['status']!='legal':continue
  ac,bc=a['metrics']['critical_path_ns'],b['metrics']['critical_path_ns'];ratio=bc/ac;ratios.append(ratio);cases.append(dict(circuit=c,reference_cpd_ns=ac,new_cpd_ns=bc,improvement_pct=100*(1-ratio)))
 paired[left+'->'+right]=dict(both_legal=len(ratios),declared_circuits=len(population),improve=sum(r<1 for r in ratios),tie=sum(r==1 for r in ratios),regress=sum(r>1 for r in ratios),circuit_geomean_improvement_pct=100*(1-math.exp(sum(map(math.log,ratios))/len(ratios))) if ratios else None,worst_improvement_pct=100*(1-max(ratios)) if ratios else None,cases=cases)
out=dict(scope='Four fixed seen circuits, seed11HybridO/P0/W100, samebinary and per-arm environment; no per-case best choice, no blind test or formal timing claim. Conditional both-legal CPD and total declared count reported separately. Native/independent audits+seals required.',circuits=list(population),status_counts={a:dict(collections.Counter(r['status'] for r in rows if r['arm']==a)) for a in ['A0','R1','U','V','Tf']},paired=paired,observations=rows,bindings=bindings)
(D/'target_feedback_circuit_summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(status=out['status_counts'],paired=paired),indent=2))
