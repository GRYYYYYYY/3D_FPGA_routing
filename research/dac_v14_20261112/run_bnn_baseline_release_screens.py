#!/usr/bin/env python3
"""Read-only matched owner-slack and protected-critical screens for A0/R1."""
import os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3))
b=D/'bnn_baseline_release_screens_01';b.mkdir(exist_ok=False)
obs=read(D/'timing_cone_bnn_dev_02/completion.json');rel=D/'bnn_baseline_relaxed_screens_01'
assert read(rel/'completion.json')['passed']
files=[Path(__file__).resolve(),D/'derive_current_release_opportunities.py',D/'query_current_protected_critical.py',rel/'completion.json',D/'timing_cone_bnn_dev_02/completion.json']
write(b/'registration.json',dict(status='registered_before_work',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
 question='Give strong A0/R1 the same actual-owner/slack and protected-critical opportunity screen as pristine Tf before concluding scope exhaustion or choosing next matched repairs.',
 source_sha256={str(p):sha(p) for p in files},native_calls=0))
costs=[];results={}
for arm in ['A0','R1']:
 capacity=D/'bnn_baseline_capacity_screens_01'/arm;owner=b/(arm+'_owners');protected=b/(arm+'_protected')
 calls=[('derive_current_release_opportunities.py',['--capacity-batch',capacity,'--relaxed-batch',rel/arm,'--state',obs['roles'][arm]['state'],'--output',owner,'--audit-cache',D/'rr_audit_cache_bnn_01'],arm+'_owners'),
        ('query_current_protected_critical.py',['--capacity-batch',capacity,'--opportunities',owner/'completion.json','--output',protected,'--audit-cache',D/'rr_audit_cache_bnn_01','--query-graph',D/'bnn_physical_query_graph_01'],arm+'_protected')]
 ok=True
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
  r=read(protected/'completion.json');assert r['passed'];results[arm]=dict(status='audited',positive=[dict(target=x['target'],gain_ns=x['gain_ns'],owners=sorted({n for c in x['conflicts'] for n in c['releasable_noncritical_owners']})) for x in r['rows'] if x['gain_ns']>1e-6])
 else:results[arm]=dict(status='failed_or_timeout_preserved')
 write(b/'progress.json',results);print(arm,results[arm],flush=True)
write(b/'completion.json',dict(passed=all(r['status']=='audited' for r in results.values()),roles=results,complete_orchestrator_seconds=time.monotonic()-start,
 source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'progress.json',b/'process_costs.json']},native_calls=0,
 qualification='Protected witnesses still need actual feasible owner reroutes and complete native FULLSTA. No legal-quality or global impossibility claim. Existing native batch remains unchanged.'))
