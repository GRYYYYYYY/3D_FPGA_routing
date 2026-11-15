"""One read-only postprocessor after the registered integration queue terminates."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
r=D/'unified_input_integration_01';out=r/'analysis';out.mkdir(exist_ok=False)
lock=(out/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
script=D/'compare_unified_input_integration_v1.py';bound={str(p):sha(p) for p in [Path(__file__).resolve(),script,r/'plan.json',r/'queue/registration.json']}
write(out/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=bound,native_calls=0))
reg=read(r/'queue/registration.json')
while not (r/'queue/completion.json').exists():
 p=process_identity(reg['pid'])
 if not p or p['state']=='Z' or p['start_ticks']!=reg['start_ticks']:
  write(out/'completion.json',dict(passed=False,status='predecessor_missing_without_receipt',native_calls=0));raise SystemExit(1)
 write(out/'status.json',dict(status='waiting_for_registered_integration_queue'));time.sleep(30)
assert all(sha(f)==h for f,h in bound.items())
with (out/'comparison.log').open('w') as log:code=subprocess.run([sys.executable,str(script)],stdout=log,stderr=subprocess.STDOUT).returncode
write(out/'completion.json',dict(passed=code==0,returncode=code,source_sha256=bound,native_calls=0))
write(out/'status.json',dict(status='terminal',passed=code==0))
