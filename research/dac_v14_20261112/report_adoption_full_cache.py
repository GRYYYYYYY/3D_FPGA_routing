#!/usr/bin/env python3
"""Bind plateau policy, matched factorial and complete physical-audit cache."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
names=['native_scope_spmv_near_physical_summary_01.json','spmv_adoption_factorial_01/completion.json','full_route_graph_cache_validation_01/completion.json','full_route_graph_cache_e695_01/completion.json','spmv_timing_cone_sensitivity_experiment_01.json']
bindings={};objects={}
for n in names:
 o=read(D/n);assert o.get('passed',True)
 for p,h in o.get('source_sha256',{}).items():
  if p not in bindings:bindings[p]=sha(p)
  assert bindings[p]==h,p
 bindings[str(D/n)]=sha(D/n);objects[n]=o
b=objects[names[0]]['batches'][0];masked=[]
for d in b['decisions']:
 before=read(Path(d['source_state'])/'endpoint_vector.json');after=read(Path(d['evaluated_state'])/'endpoint_vector.json')
 if d['policy']=='endpoint_vector' and not d['decision']['accepted']:
  assert before['setup']==after['setup'] and before['hold']==after['hold'] and before['cpd_s']==after['cpd_s']
  source=Path(read(Path(d['source_state'])/'completion.json')['run']);candidate=Path(read(Path(d['evaluated_state'])/'completion.json')['run'])
  rows={}
  for label,run in [('before',source),('after',candidate)]:
   import json
   rows[label]={}
   for line in (run/'native_sta_frontier.jsonl').open():
    p=json.loads(line)
    if p.get('type')=='pin' and (p.get('net'),p.get('pin'))==(6997,1):rows[label]=p
   bindings[str(run/'native_sta_frontier.jsonl')]=sha(run/'native_sta_frontier.jsonl')
  assert rows['after']['native_net_delay_s']<rows['before']['native_net_delay_s']
  assert rows['after']['setup_slack_s']>rows['before']['setup_slack_s']
  masked.append(dict(attempt=d['attempt'],all_endpoint_setup_hold_and_CPD_equal=True,net6997pin1_native_delay_before_after_s=[rows[k]['native_net_delay_s'] for k in ['before','after']],net6997pin1_native_slack_before_after_s=[rows[k]['setup_slack_s'] for k in ['before','after']],qualification='Actual local change with endpoint masking; specific downstream reconvergence remains unproven until graph/arrival/required tags are traced.'))
for n in ['report_adoption_full_cache.py','full_route_graph_cache.py','validate_full_route_graph_cache.py','run_endpoint_state_analysis_cached.py','run_spmv_adoption_factorial.py']:bindings[str(D/n)]=sha(D/n)
write(D/'adoption_full_cache_summary_01.json',dict(passed=True,research_complete=False,quality_promoted=False,physical_policy=b,factorial=objects[names[1]],full_cache_validation=objects[names[2]],full_cache_build=objects[names[3]],masked_endpoint_cases=masked,source_sha256=bindings,next_registered=names[-1],new_work_pushed=False,qualification='Strict-versus-endpoint policy divergence and component data-access optimization. No demonstrated CPD improvement over A0, no overall routing speedup, and no identified reconvergent fanin yet. Cached FULL/STA wrapper prepared but not yet exercised on a fresh native candidate.'))
print(dict(passed=True,sources=len(bindings),endpoint_accepts=b['policies']['endpoint_vector']['accepted_steps'],masked_endpoint_cases=len(masked)))
