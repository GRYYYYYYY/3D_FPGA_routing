"""Fixed development input pairs after existing registered work; never restart outputs."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'unified_input_integration_01';plan=read(root/'plan.json');q=root/'queue'
q.mkdir(exist_ok=False);lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound=plan['source_sha256'];assert all(sha(f)==h for f,h in bound.items())
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=bound))
prior=Path(plan['predecessor']);previous=read(prior/'registration.json');results={}
try:
 while not (prior/'completion.json').exists():
  p=process_identity(previous['pid']);assert p and p['state']!='Z' and p['start_ticks']==previous['start_ticks'],'Predecessor disappeared; inspect descendants before recovery'
  write(q/'status.json',dict(status='waiting_for_registered_recovery_chain',predecessor=str(prior)));time.sleep(15)
 # The shared slot alone is insufficient after a supervisor failure. Require a
 # genuinely completed predecessor chain; a failure needs manual reconciliation.
 assert read(prior/'completion.json')['status']=='registered_never_executed_tasks_terminal'
 serial=(D/'critical_scope_runner.lock').open('r');write(q/'status.json',dict(status='waiting_for_shared_serial_slot'));fcntl.flock(serial,fcntl.LOCK_EX)
 for name in plan['fixed_order']:
  assert all(sha(f)==h for f,h in bound.items())
  config=Path(plan['cases'][name]);case=root/name;case.mkdir(exist_ok=False);(case/'queue').mkdir();(case/'config.json').write_bytes(config.read_bytes())
  command=[sys.executable,str(D/'measure_process_tree_v1.py'),'--output',str(case/'measurement'),'--',sys.executable,str(D/'run_complete_unified_method_v1.py'),'--config',str(config),'--output',str(case/'flow')]
  with (q/(name+'.log')).open('w') as log:
   child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);identity=process_identity(child.pid)
   write(case/'queue/registration.json',dict(pid=child.pid,start_ticks=identity['start_ticks'],command=command,source_sha256=bound))
   write(q/'status.json',dict(status='running',case=name,pid=child.pid,start_ticks=identity['start_ticks']));code=child.wait()
  measure=read(case/'measurement/completion.json')
  assert not measure['live_descendants_after_command_exit'],'Do not launch next case over a surviving process'
  verified=False
  if code==0:
   with (q/(name+'_verification.log')).open('w') as log:
    check=subprocess.run([sys.executable,str(D/'verify_complete_unified_method_v1.py'),'--root',str(case)],stdout=log,stderr=subprocess.STDOUT).returncode
   verified=check==0 and (case/'completion.json').exists() and read(case/'completion.json')['passed']
  outcome='complete_legal_verified' if verified else 'execution_or_verification_failed'
  initial=case/'flow/resource_flow/initial/runs/state/manifest.json'
  if code and initial.exists():
   m=read(initial)
   if m.get('returncode') and not m.get('metrics',{}).get('routing_success_reported'):outcome='initial_route_failed'
  results[name]=dict(status=outcome,command_returncode=code,complete_seconds=measure['complete_command_wall_seconds'],measurement=str(case/'measurement/completion.json'),completion=str(case/'completion.json') if verified else None,quality=None if not verified else {k:read(case/'completion.json')[k] for k in ['CPD_ns','resources']})
  write(q/'results.json',results)
 write(q/'completion.json',dict(passed=True,status='all_registered_roles_terminal',registered_roles=len(plan['fixed_order']),verified_legal_roles=sum(r['status']=='complete_legal_verified' for r in results.values()),results=results,source_sha256=bound,qualification='Execution closure only, not universal benefit or confirmation completion. All failures/no-gain/worse retained. Independent paired interpretation and replay verification required.'))
 write(q/'status.json',dict(status='terminal'))
except Exception as exc:
 write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(exc),results=results,source_sha256=bound))
 raise
