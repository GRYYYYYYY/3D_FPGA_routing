#!/usr/bin/env python3
"""Observe pristine SpMV inputs and reuse only exact physical/analysis aliases."""
import json,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v3 import input_identity,native_config

started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));b=D/'native_endpoint_spmv_dev_01';b.mkdir(exist_ok=False);spec=read(D/'current_sta_cross_circuit_spmv_experiment_01.json');assert all(sha(p)==h for p,h in spec['source_sha256'].items())
bindings={str(p):sha(p) for p in [Path(__file__),D/'current_sta_cross_circuit_spmv_experiment_01.json',D/'run_endpoint_state_analysis.py',D/'run_native_scope_policy_v3.py',D/'native_endpoint_vector_stage_01/binding.json']};rows={};seen={};costs=[]
write(b/'registration.json',dict(status='registered_before_observation',pid=os.getpid(),source_sha256=bindings,question='Capture exact endpoint/clock-domain vectors for pristine SpMV A0/R1/Tf without rerouting; reuse identical R1/Tf analysis inputs.'))
for arm in ['R1','Tf','A0']:
 assert shutil.disk_usage(D).free>=80*1024**3
 source=Path(spec['inputs'][arm]['source']);identity=json.dumps([route_body(source/'routed.route'),input_identity(source),native_config(source)],sort_keys=True)
 if identity in seen:
  state=seen[identity];rows[arm]=dict(state=str(state),source=str(source),reused=True,reuse_from=next(k for k,v in rows.items() if v['state']==str(state)),completion_sha256=sha(state/'completion.json'))
 else:
  state=b/arm;cmd=[sys.executable,str(D/'run_endpoint_state_analysis.py'),'--source',str(source),'--batch',str(state)];t=time.monotonic()
  with (b/(arm+'.log')).open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   try:code=proc.wait(timeout=1800)
   except subprocess.TimeoutExpired:
    os.killpg(proc.pid,signal.SIGTERM)
    try:code=proc.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
  costs.append(dict(arm=arm,command=cmd,returncode=code,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs);assert code==0 and read(state/'completion.json')['passed']
  assert route_body(Path(read(state/'completion.json')['run'])/'routed.route')==route_body(source/'routed.route');seen[identity]=state;rows[arm]=dict(state=str(state),source=str(source),reused=False,completion_sha256=sha(state/'completion.json'))
 rows[arm]['cpd_s']=read(state/'endpoint_vector.json')['cpd_s'];write(b/'progress.json',rows)
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=True,roles=rows,new_native_observations=len(costs),route_search_calls=0,complete_orchestrator_seconds=time.monotonic()-started,source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'progress.json',b/'process_costs.json']},qualification='Initial legal-route observations, not new routing or repair quality. Exact R1/Tf alias is one physical input, not independent samples.'))
print(rows,flush=True)
