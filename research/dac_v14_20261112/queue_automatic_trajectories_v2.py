#!/usr/bin/env python3
"""Independent strict/endpoint trajectories from pristine Tf/A0, after old cohorts."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'bnn_automatic_trajectories_dev_02';b.mkdir(exist_ok=False);owner=(b/'owner.lock').open('w');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
prior=D/'bnn_cover_selected_dev_01';submission=read(prior/'queue/registration.json');obs=read(D/'timing_cone_bnn_dev_02/completion.json')
roles={arm+'_'+policy:dict(initial_state=obs['roles'][arm]['state'],policy=policy) for arm in ['Tf','A0'] for policy in ['strict','endpoint_vector']}
files=[Path(__file__).resolve(),D/'run_automatic_current_STA_repair_v2.py',D/'current_group_feedback.py',D/'current_native_reuse.py',D/'current_native_reuse_validation_02/completion.json',D/'automatic_operator_boundary_02/completion.json',D/'critical_group_planner_stage_01/binding.json',D/'fixed_anchor_acceptance_validation_01.json',D/'timing_cone_bnn_dev_02/completion.json']
assert read(D/'current_native_reuse_validation_02/completion.json')['passed'] and read(D/'automatic_operator_boundary_02/completion.json')['passed']
bindings={str(p):sha(p) for p in files}
def live(e):
 p=Path('/proc')/str(e['pid'])/'stat'
 try:return p.read_text().split(') ',1)[1].split()[19]==e['start_ticks']
 except FileNotFoundError:return False
assert live(submission) or (prior/'execution_registration.json').exists()
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],roles=roles,after=str(prior),previous_submission_owner=submission,source_sha256=bindings,
 question='Can fully automatic current-STA group repair reproduce the first gain from pristineTf/A0 and then select its own successors under independently evolving strict and endpoint-vector acceptance?',
 objective='weighted_soft',fraction=.9,limits='1800s and64GiB per executed child,80GiB disk reserve; no fixed trajectory round count or research deadline',
 reuse='Exact current-state plan/native requests and completed failures may be reused; all creation costs remain attached to old artifacts. Same initial state per policy, own accepted state thereafter.',
 qualification='Development imported-state trajectories, not cold complete end-to-end router timing. Individual operator termination or failed workflow does not stop other policies or the research goal. Already registered native cohorts unchanged.'))
write(b/'status.json',dict(status='waiting_for_selected_batch_start',previous_queue_pid=submission['pid'],observed_at=time.time()))
while not (prior/'execution_registration.json').exists():
 if not live(submission):write(b/'dependency_failure.json',dict(reason='Previous submission owner terminal without native receipt; no launch'));sys.exit(2)
 time.sleep(15)
e=read(prior/'execution_registration.json');write(b/'status.json',dict(status='waiting_for_selected_native_owner',prior_pid=e['pid'],observed_at=time.time()))
while live(e):time.sleep(15)
if not (prior/'completion.json').exists():write(b/'dependency_failure.json',dict(reason='Previous native owner terminal without completion receipt; no launch'));sys.exit(2)
assert all(sha(p)==h for p,h in read(prior/'completion.json')['source_sha256'].items())
assert all(sha(p)==h for p,h in bindings.items())
history=[D/'bnn_release_joint_dev_01',D/'bnn_strong_release_joint_dev_01',prior];plans=[D/'automatic_group_plan_Tf_01/plan.json',D/'automatic_group_plan_A0_01/plan.json'];results={}
for name,role in roles.items():
 actor=b/name;cmd=[sys.executable,str(D/'run_automatic_current_STA_repair_v2.py'),'--initial-state',role['initial_state'],'--batch',str(actor),'--policy',role['policy'],'--objective','weighted_soft','--fraction','.9','--query-graph',str(D/'bnn_physical_query_graph_01'),'--audit-cache',str(D/'rr_audit_cache_bnn_01')]
 for plan in plans:cmd+=['--reuse-plan',str(plan)]
 for old in history:cmd+=['--reuse-native-batch',str(old)]
 for q in [D/'bnn_slack_release_screen_01/Tf_capacity',D/'bnn_baseline_capacity_screens_01/A0',D/'bnn_baseline_capacity_screens_01/R1']:cmd+=['--reuse-query-batch',str(q)]
 start=time.monotonic()
 with (b/(name+'.log')).open('w') as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);write(b/'status.json',dict(status='running_policy_trajectory',actor=name,pid=proc.pid,command=cmd,observed_at=time.time()));code=proc.wait()
 if (actor/'completion.json').exists():results[name]=read(actor/'completion.json')
 else:results[name]=dict(passed=False,returncode=code,status='workflow_failed_preserved')
 results[name]['driver_process_seconds']=time.monotonic()-start;write(b/'progress.json',results)
 plans+=list(actor.glob('step_*/feedback/proposal/plan.json'));history+=list(actor.glob('step_*/transaction'))
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=all(x['passed'] for x in results.values()),roles=results,source_sha256=bindings,
 qualification='Four independent development policy trajectories. Measured actor time excludes all historical creation reused explicitly; no full cold-run router speedup claim. Operator stops are not research completion.'))
