#!/usr/bin/env python3
"""Register engineering equivalence on completed real static-state transactions."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from native_batch_evidence import transaction
stage=D/'native_batch_stage_02';proof=D/'native_batch_tiny_regression_02/completion.json';assert read(proof)['passed'];assert all(sha(p)==h for p,h in read(proof)['source_sha256'].items())
assert sha(stage/'bin/vpr')==read(stage/'binding.json')['binary_sha256']
b=D/'native_batch_equivalence_dev_01';b.mkdir(exist_ok=False);cases={}
for key,old,selected in [('BNN_A0',D/'bnn_strong_release_joint_dev_01',None),('SPMV_failure_success',D/'spmv_adoption_factorial_01',['physical_soft','weighted_capacity','physical_soft','weighted_capacity'])]:
 reg=read(old/'registration.json');assert read(old/'completion.json')['passed']
 if selected is None:selected=[n for n,r in reg['roles'].items() if r['baseline']=='A0']
 source=None;requests={};bound={str(p):sha(p) for p in [Path(__file__).resolve(),stage/'binding.json',proof,D/'run_native_static_batch_analysis.py',D/'native_batch_evidence.py',old/'registration.json',old/'completion.json']}
 for i,name in enumerate(selected):
  role=reg['roles'][name];assert source is None or source==role['source'];source=role['source'];complete=old/name/'completion.json';assert read(complete)['passed'];log=Path(read(complete)['run'])/'joint_native.log';tx=transaction(log)
  assert tx['success']==(name!='physical_soft')
  evaluation=read(old/'completion.json')['roles'][name].get('evaluation')
  requests[str(i)+'_'+name]=dict(request=role['request'],objective=role['objective'],reference_log=str(log),reference_completion=str(complete),reference_evaluation=evaluation,reference_success=tx['success'])
  for path,h in role['source_sha256'].items():
   if path in bound:assert bound[path]==h
   bound[path]=h
  for p in [complete,log]:bound[str(p)]=sha(p)
 path=b/(key+'_registration.json');write(path,dict(source=source,requests=requests,source_sha256=bound,question='Can one native process exactly reproduce independent static-state transactions, including a numerical failure followed by success, without changing original route/delays/native STA?',qualification='Component-equivalence development batch. Final candidate quality remains referenced to its existing individual FULLSTA run. No new policy/commit or fresh complete algorithm runtime is claimed.'))
 cases[key]=str(path)
write(b/'registration.json',dict(status='registered_before_native',cases=cases,after='pending_reservation_dev_02',source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'run_native_static_batch_analysis.py',D/'native_batch_evidence.py',proof,stage/'binding.json',*(Path(p) for p in cases.values())]},limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),question='Amortize static input loading while preserving every independent native result and failure recovery. Existing policies, physical delays, candidate acceptance and current registered cohorts unchanged.',qualification='Extra post-batch fresh STA checks are inside observed component cost. No comparison with historical isolated times as a speedup; cold whole-configuration timing remains unknown.'))
print(dict(cases={k:len(read(Path(p))['requests']) for k,p in cases.items()}))
