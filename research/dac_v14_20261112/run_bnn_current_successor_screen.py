#!/usr/bin/env python3
"""Advance opportunity analysis from an actual accepted current-STA state."""
import os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3))
prior=D/'bnn_release_joint_dev_01';name='Tf_combined_weighted_soft';state=prior/(name+'_evaluation');cone=prior/(name+'_successor_cone.json')
assert read(state/'completion.json')['passed'] and read(cone)['passed']
for policy in ['strict','endpoint_vector','timing_under_resources','resources_under_timing']:
 p=read(prior/(name+'_'+policy+'_state.json'));assert p['accepted'] and Path(p['state'])==state
b=D/'bnn_current_successor_screen_01';b.mkdir(exist_ok=False)
files=[Path(__file__).resolve(),state/'completion.json',state/'endpoint_vector.json',cone,prior/(name+'_decisions.json'),D/'run_current_cone_capacity_queries_v3.py',D/'audit_current_cone_queries.py',D/'run_current_graph_relaxed_queries.py',D/'derive_current_release_opportunities.py',D/'query_current_protected_critical.py']
write(b/'registration.json',dict(status='registered_before_query',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
 source_state=str(state),source_cone=str(cone),question='After the accepted joint repair and fresh STA, do current retained-tree capacity opportunities remain, and which new owner releases survive protection of current critical nets?',
 reuse='Explicit past BNN query batches considered only under exact case fingerprints, same graph/driver, and sealed source/output checks. No pristine-state distance is presumed current.',
 source_sha256={str(p):sha(p) for p in files},native_calls=0,qualification='Offline current-state diagnosis only. No change to already registered native batches. Shared accepted weighted state is currently identical across all four policies; future divergent states require separate screens.'))
q=b/'capacity';r=b/'relaxed';owner=b/'owners';protected=b/'protected';g=D/'bnn_physical_query_graph_01';cache=D/'rr_audit_cache_bnn_01'
args=['--state',state,'--batch',q,'--query-graph',g,'--audit-cache',cache,'--cone',cone]
for old in [D/'bnn_slack_release_screen_01/Tf_capacity',D/'bnn_baseline_capacity_screens_01/A0',D/'bnn_baseline_capacity_screens_01/R1']:args+=['--reuse-batch',old]
calls=[('run_current_cone_capacity_queries_v3.py',args,'capacity_query'),('audit_current_cone_queries.py',['--batch',q,'--query-graph',g,'--audit-cache',cache],'capacity_audit'),
 ('run_current_graph_relaxed_queries.py',['--capacity-batch',q,'--batch',r,'--query-graph',g],'relaxed_query'),('audit_current_cone_queries.py',['--batch',r,'--query-graph',g,'--audit-cache',cache],'relaxed_audit'),
 ('derive_current_release_opportunities.py',['--capacity-batch',q,'--relaxed-batch',r,'--state',state,'--output',owner,'--audit-cache',cache],'owner_slack'),
 ('query_current_protected_critical.py',['--capacity-batch',q,'--opportunities',owner/'completion.json','--output',protected,'--audit-cache',cache,'--query-graph',g],'protected_query')]
costs=[];ok=True
for script,args,tag in calls:
 assert shutil.disk_usage(D).free>=80*1024**3
 cmd=[sys.executable,str(D/script),*map(str,args)];t=time.monotonic();status='completed'
 with (b/(tag+'.log')).open('w') as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  write(b/'active_child.json',dict(pid=proc.pid,tag=tag,command=cmd))
  try:code=proc.wait(timeout=1800)
  except subprocess.TimeoutExpired:
   status='timeout';os.killpg(proc.pid,signal.SIGTERM)
   try:code=proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
 costs.append(dict(tag=tag,status=status if code==0 or status=='timeout' else 'failed',returncode=code,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs)
 if code:ok=False;break
result=dict(passed=ok,complete_orchestrator_seconds=time.monotonic()-start,native_calls=0,source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'process_costs.json']})
if ok:
 a=read(q/'analysis.json');ex=read(q/'execution.json');p=read(protected/'completion.json')
 result.update(capacity_positive=[dict(net=x['net'],pin=x['pin'],gain_ns=x['improvement_ns']) for x in a['results'] if x['improvement_ns']>1e-6],protected_positive=[dict(target=x['target'],gain_ns=x['gain_ns']) for x in p['rows'] if x['gain_ns']>1e-6],new_queries=ex['new_queries'],reused_queries=ex['reused_queries'])
write(b/'completion.json',result);print(result,flush=True)
