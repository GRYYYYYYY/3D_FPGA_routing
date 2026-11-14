#!/usr/bin/env python3
"""Evaluate matched successor opportunities and journal each branch's current STA."""
import os,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from endpoint_timing_policy import decide
from current_sta_selector import select

b=D/'plateau_successor_evaluation_01';b.mkdir(exist_ok=False);started=time.monotonic();study=read(D/'current_sta_policy_R1_near_01/completion.json');rows=[];costs=[]
write(b/'registration.json',dict(status='registered_before_native',question='Same successor mechanism from each policy currentstate after the plateau-only experiment.',
 source_sha256={str(p):sha(p) for p in [Path(__file__),D/'current_sta_plateau_successor_experiment_01.json',D/'plateau_successor_potential_01/completion.json',D/'current_sta_policy_R1_near_01/completion.json']},
 guards=dict(process_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3)))
for role,policy in [('strict','strict'),('endpoint','endpoint_vector')]:
 initial=Path(study['outcomes'][policy]['state']);source=Path(read(initial/'completion.json')['run']);tx=D/f'plateau_successor_{role}_transaction_01';transaction=read(tx/'analysis.json')
 assert transaction['passed'] and transaction['candidate_route'] and route_body(source/'routed.route')==route_body(Path(transaction['input_run'])/'routed.route')
 state=b/role;command=[sys.executable,str(D/'run_endpoint_state_analysis.py'),'--source',str(source),'--batch',str(state),'--candidate-route',transaction['candidate_route']]
 t=time.monotonic();timed_out=False
 with (b/(role+'.log')).open('w') as f:
  proc=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=proc.wait(timeout=1800)
  except subprocess.TimeoutExpired:
   timed_out=True;os.killpg(proc.pid,signal.SIGTERM)
   try:code=proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
 costs.append(dict(role=role,command=command,returncode=code,timed_out=timed_out,seconds=time.monotonic()-t));write(b/'process_costs.json',costs)
 if code or timed_out:
  rows.append(dict(role=role,status='evaluation_failed_original_retained',current_state=str(initial)));continue
 complete=read(state/'completion.json');assert complete['passed'];before=read(initial/'endpoint_vector.json');after=read(state/'endpoint_vector.json')
 decisions={p:decide(p,before,after,True) for p in ['strict','endpoint_vector']};write(b/(role+'_decisions.json'),decisions)
 current=state if decisions[policy]['accepted'] else initial;rd=Path(read(current/'completion.json')['run'])
 row=dict(role=role,active_policy=policy,status='legal_candidate',before_state=str(initial),evaluated_state=str(state),current_state=str(current),
  cpd_before_ns=before['cpd_s']*1e9,cpd_candidate_ns=after['cpd_s']*1e9,accepted=decisions[policy]['accepted'],
  decisions={p:{k:v for k,v in d.items() if k!='comparison'} for p,d in decisions.items()},
  setup_improved=decisions[policy]['comparison']['setup_improved'],setup_regressed=decisions[policy]['comparison']['setup_regressed'],
  current_selection=select(rd/'native_sta_frontier.jsonl'),current_resources=read(rd/'independent_audit.json')['physical_metrics'])
 rows.append(row);write(b/(role+'_current.json'),row);write(b/'progress.json',rows);print(row,flush=True)
write(b/'completion.json',dict(passed=all(r['status']=='legal_candidate' for r in rows),rows=rows,complete_seconds=time.monotonic()-started,
 source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'process_costs.json',*b.glob('*_decisions.json'),*b.glob('*/completion.json'),*b.glob('*/endpoint_vector.json')]},
 qualification='Each branch keeps its own acceptance rule/current state. Every accepted successor gets fresh STA selection; this batch is not a total research stopping matrix.'))
