#!/usr/bin/env python3
"""Extend strong baseline opportunities to the same relaxed-capacity screening stage."""
import os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
b=D/'bnn_baseline_relaxed_screens_01';b.mkdir(exist_ok=False);observations=read(D/'timing_cone_bnn_dev_02/completion.json');assert observations['passed']
roles={arm:dict(state=observations['roles'][arm]['state'],cone=observations['roles'][arm]['cone']) for arm in ['A0','R1']}
files=[Path(__file__).resolve(),D/'run_current_graph_relaxed_queries.py',D/'audit_current_cone_queries.py',D/'current_query_case_cache.py',D/'current_query_case_cache_validation_01/completion.json',D/'timing_cone_bnn_dev_02/completion.json',D/'bnn_physical_query_graph_01/graph_binding.json',D/'rr_audit_cache_bnn_01/completion.json']
write(b/'registration.json',dict(status='registered_before_work',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],roles=roles,
 question='Do strong A0/R1 have capacity gaps under the same background-relaxation screen already given to Tf? No legal candidate inferred before actual owner replacement and FULLSTA.',
 cache_change='New exact same-state saturation reuse; all13 Tf input cases equal plus96 capacity conditions validated. Tf historical timing remains a different preprocessing version, not spliced into these points.',
 source_sha256={str(p):sha(p) for p in files},limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),native_calls=0))
costs=[];results={}
for arm,r in roles.items():
 q=b/arm;ok=True
 calls=[('run_current_graph_relaxed_queries.py',['--capacity-batch',D/'bnn_baseline_capacity_screens_01'/arm,'--batch',q,'--query-graph',D/'bnn_physical_query_graph_01'],arm+'_query'),
        ('audit_current_cone_queries.py',['--batch',q,'--query-graph',D/'bnn_physical_query_graph_01','--audit-cache',D/'rr_audit_cache_bnn_01'],arm+'_audit')]
 for script,args,tag in calls:
  assert shutil.disk_usage(D).free>=80*1024**3
  cmd=[sys.executable,str(D/script),*map(str,args)];t=time.monotonic();status='completed'
  with (b/(tag+'.log')).open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   try:code=proc.wait(timeout=1800)
   except subprocess.TimeoutExpired:
    status='timeout';os.killpg(proc.pid,signal.SIGTERM)
    try:code=proc.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
  costs.append(dict(tag=tag,command=cmd,status=status if code==0 or status=='timeout' else 'failed',returncode=code,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs)
  if code:ok=False;break
 if ok:
  a=read(q/'analysis.json');assert a['passed'];cp=read(D/'bnn_baseline_capacity_screens_01'/arm/'analysis.json');cd={(x['net'],x['pin']):x['physical_seconds'] for x in cp['results']};results[arm]=dict(status='audited',targets=len(a['results']),positive=[dict(net=x['net'],pin=x['pin'],gain_ns=x['improvement_ns'],capacity_gap_ns=(cd[x['net'],x['pin']]-x['physical_seconds'])*1e9) for x in a['results'] if x['improvement_ns']>1e-6])
 else:results[arm]=dict(status='failed_or_timeout_preserved')
 write(b/'progress.json',results);print(arm,results[arm],flush=True)
write(b/'completion.json',dict(passed=all(r['status']=='audited' for r in results.values()),roles=results,complete_orchestrator_seconds=time.monotonic()-start,
 source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'progress.json',b/'process_costs.json']},native_calls=0,
 qualification='Relaxed witnesses are optimistic references, not legal replacements. These screens extend baseline opportunities; owner slack/protected paths and full native transaction remain required.'))
