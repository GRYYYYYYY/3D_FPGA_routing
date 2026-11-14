#!/usr/bin/env python3
"""One policy's current-state repair trajectory, with complete process accounting.

Operator termination does not complete the continuing research goal. Development
reuse is recorded separately from an unavailable fresh full-algorithm runtime.
"""
import argparse,fcntl,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from fixed_anchor_acceptance import decisions
from current_group_feedback import commands
from current_native_reuse import match,failed_match
p=argparse.ArgumentParser()
for n in ['initial-state','batch','query-graph','audit-cache']:p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--policy',choices=['strict','endpoint_vector','timing_under_resources','resources_under_timing'],default='strict')
p.add_argument('--fraction',type=float,default=.9);p.add_argument('--reuse-plan',type=Path,action='append',default=[]);p.add_argument('--reuse-native-batch',type=Path,action='append',default=[]);p.add_argument('--reuse-query-batch',type=Path,action='append',default=[])
p.add_argument('--objective',choices=['weighted_soft','weighted_capacity','physical_capacity'],default='weighted_soft');a=p.parse_args()
started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));b=a.batch.resolve();b.mkdir(exist_ok=False)
owner=(b/'owner.lock').open('w');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
initial=a.initial_state.resolve();assert read(initial/'completion.json')['passed'];current=initial
def res(state):
 r=read(run_dir(state)/'independent_audit.json');assert r['audit']['passed'];x=r['physical_metrics']
 return dict(wirelength=x['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=x['sb_pairs_used'],CB_sources=x['cb_crossing_output_sources_used'])
anchor=dict(CPD_s=read(initial/'endpoint_vector.json')['cpd_s'],**res(initial))
files=[Path(__file__).resolve(),D/'current_group_feedback.py',D/'current_native_reuse.py',D/'fixed_anchor_acceptance.py',D/'prepare_native_group_step.py',D/'run_registered_native_transactions_v3.py',D/'plan_current_critical_group.py',D/'critical_group_planner_stage_01/binding.json',initial/'completion.json',initial/'endpoint_vector.json']
bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],initial_state=str(initial),policy=a.policy,objective=a.objective,fraction=a.fraction,anchor=anchor,source_sha256=bindings,
 question='Does a fixed policy automatically advance from its own accepted current route using fresh STA/feedback, without a persistent initial target list or drifting budgets?',
 limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
 qualification='Imported-state development repair workflow. Initial routing and prebuilt graph caches are outside measured elapsed time. Exact historical reuse is explicit; do not claim fresh full-configuration algorithm time. This operator currently proposes strict-CPD winning-path groups, not exhaustive resource-only or near-critical search.'))
costs=[];steps=[];seen={};replays=[];query_history=list(a.reuse_query_batch);native_history=list(a.reuse_native_batch)
def invoke(script,args,tag):
 if shutil.disk_usage(D).free<80*1024**3:
  costs.append(dict(tag=tag,status='disk_guard',complete_process_seconds=0));write(b/'process_costs.json',costs);return False
 cmd=[sys.executable,str(D/script),*map(str,args)];start=time.monotonic();status='completed'
 with (b/(tag+'.log')).open('w') as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);write(b/'active_child.json',dict(pid=proc.pid,tag=tag,command=cmd))
  try:code=proc.wait(timeout=1800)
  except subprocess.TimeoutExpired:
   status='timeout';os.killpg(proc.pid,signal.SIGTERM)
   try:code=proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
 costs.append(dict(tag=tag,command=cmd,status=status if code==0 or status=='timeout' else 'failed',returncode=code,complete_process_seconds=time.monotonic()-start));write(b/'process_costs.json',costs);return code==0
reason=None;step=0
while True:
 s=b/f'step_{step:03d}';s.mkdir();before=read(current/'endpoint_vector.json');state_key=(route_body(run_dir(current)/'routed.route'),before['constraints_sha256']);plan=None
 if state_key in seen:reason='unchanged_or_previously_visited_state';break
 seen[state_key]=step
 for candidate in a.reuse_plan:
  candidate=candidate.resolve();v=read(candidate)
  if Path(v['source_state']).resolve()!=current or v['selection'].get('fraction',a.fraction)!=a.fraction:continue
  assert v['passed'] and all(sha(p)==h for p,h in v['source_sha256'].items());plan=candidate
  replays.append(dict(kind='current_plan',path=str(candidate),sha256=sha(candidate),creation_time_excluded=True));break
 if plan is None:
  feedback=s/'feedback';feedback.mkdir();ok=True
  for script,args,tag in commands(current,feedback,a.query_graph.resolve(),a.audit_cache.resolve(),query_history,a.fraction):
   if not invoke(script,args,f'{step:03d}_{tag}'):ok=False;break
  if not ok:reason='feedback_failed_or_process_guard';break
  plan=feedback/'proposal/plan.json';query_history.append(feedback/'capacity')
 v=read(plan);assert Path(v['source_state']).resolve()==current
 if not v['repair_pins']:
  reason='no_positive_group_in_current_operator';steps.append(dict(step=step,state=str(current),plan=str(plan),accepted=False,reason=reason));break
 transaction=s/'transaction'
 if not invoke('prepare_native_group_step.py',['--plan',plan,'--anchor-state',initial,'--output',transaction,'--objective',a.objective],f'{step:03d}_prepare_transaction'):
  reason='transaction_preparation_failed';break
 role=read(transaction/'registration.json')['roles']['current_group'];reuse=match(role,native_history);evaluation=None
 if not reuse:
  failed=failed_match(role,native_history)
  if failed:
   write(s/'native_failure_reuse.json',failed);replays.append(dict(kind='completed_native_failure',**failed));reason='known_identical_native_failure';break
 if reuse:
  write(s/'native_reuse.json',reuse);replays.append(dict(kind='native_transaction_and_FULL_STA',**reuse));evaluation=Path(reuse['evaluation'])
 else:
  if not invoke('run_registered_native_transactions_v3.py',['--batch',transaction,'--selector','compact'],f'{step:03d}_native_transaction'):
   reason='transaction_failed_or_process_guard';break
  row=read(transaction/'progress.json')['current_group']
  if row['status']!='legal_evaluated':reason='native_transaction_rolled_back';break
  evaluation=Path(row['evaluation']);native_history.append(transaction)
 after=read(evaluation/'endpoint_vector.json');d=decisions(before,after,res(current),res(evaluation),anchor)
 write(s/'policy_decisions.json',d);accepted=d[a.policy]['accepted']
 record=dict(step=step,before_state=str(current),evaluation=str(evaluation),plan=str(plan),accepted=accepted,policy=a.policy,reason=d[a.policy]['reason'],before_CPD_s=before['cpd_s'],after_CPD_s=after['cpd_s'],before_resources=res(current),after_resources=res(evaluation),reused_native=bool(reuse));steps.append(record);write(b/'steps.json',steps)
 if not accepted:reason='selected_proposal_rejected_by_fixed_policy';break
 assert after['constraints_sha256']==before['constraints_sha256'];current=evaluation
 write(b/'current_state.json',dict(state=str(current),anchor_state=str(initial),accepted_steps=sum(r.get('accepted',False) for r in steps),policy=a.policy,source_decision=str(s/'policy_decisions.json')))
 # No fixed net list survives this commit. Next round selects this route's STA.
 step+=1
write(b/'steps.json',steps);write(b/'reuse_receipts.json',replays)
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=reason not in ['feedback_failed_or_process_guard','transaction_preparation_failed','transaction_failed_or_process_guard'],operator_stop=reason,policy=a.policy,initial_state=str(initial),final_state=str(current),accepted_steps=sum(r.get('accepted',False) for r in steps),steps=steps,
 initial_CPD_s=anchor['CPD_s'],final_CPD_s=read(current/'endpoint_vector.json')['cpd_s'],final_resources=res(current),complete_imported_state_workflow_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None,
 source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'steps.json',b/'reuse_receipts.json']},
 qualification='Operator termination only; the research goal remains active. Rejected/failed candidates preserved. Measured time includes executed process work, excludes referenced historical native/plan creation, initial routing and static-cache construction. No complete cold-run timing claim.'))
print(dict(final_state=str(current),accepted_steps=sum(r.get('accepted',False) for r in steps),operator_stop=reason),flush=True)
