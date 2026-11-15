"""One serial owner for full fresh BNN resource-plus-timing measurements."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'complete_resource_timing_full_flow_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert read(D/'cold_timing_cli_integration_01/completion.json')['passed']
files=[Path(__file__).resolve(),root/'plan.json',D/'cold_timing_cli_integration_01/completion.json',*map(Path,plan['implementation_files']),*sorted((root/'configs').glob('*.json'))];bindings={str(f):sha(f) for f in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=bindings,scope=plan['qualification']))
prior=Path(plan['predecessor']);owner=read(prior/'registration.json')
while not (prior/'completion.json').exists():
 p=process_identity(owner['pid']);live=bool(p and p['state']!='Z' and p['start_ticks']==owner['start_ticks'])
 write(q/'status.json',dict(status='waiting_for_timing_budget_pair_terminal',verified_predecessor_live=live,predecessor=str(prior)))
 if not live:
  write(q/'completion.json',dict(passed=False,status='predecessor_owner_ended_without_receipt',results={},source_sha256=bindings));sys.exit(1)
 time.sleep(15)
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX)
results={}
for name in plan['fixed_order']:
 assert all(sha(f)==h for f,h in bindings.items())
 case=root/name;case.mkdir();(case/'queue').mkdir();config=Path(plan['cases'][name]);(case/'config.json').write_bytes(config.read_bytes())
 command=[sys.executable,str(D/'measure_process_tree_v1.py'),'--output',str(case/'measurement'),'--',sys.executable,str(D/'run_complete_resource_timing_flow_v1.py'),'--config',str(config),'--output',str(case/'flow')]
 with (q/(name+'.log')).open('w') as log:
  child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);pid=process_identity(child.pid)
  write(case/'queue/registration.json',dict(pid=child.pid,start_ticks=pid['start_ticks'],command=command,source_sha256=bindings))
  write(q/'status.json',dict(status='running',case=name,pid=child.pid,start_ticks=pid['start_ticks'],command=command));code=child.wait()
 ok=code==0 and (case/'flow/completion.json').exists() and read(case/'flow/completion.json')['passed'] and read(case/'measurement/completion.json')['passed']
 if ok:
  with (q/(name+'_verification.log')).open('w') as log:code=subprocess.run([sys.executable,str(D/'verify_complete_resource_timing_flow_v1.py'),'--root',str(case)],stdout=log,stderr=subprocess.STDOUT).returncode
  ok=code==0
 results[name]=dict(passed=ok,returncode=code,completion=str(case/'completion.json'));write(q/'results.json',results)
passed=len(results)==len(plan['fixed_order']) and all(x['passed'] for x in results.values())
write(q/'completion.json',dict(passed=passed,results=results,source_sha256=bindings));write(q/'status.json',dict(status='terminal',passed=passed))
