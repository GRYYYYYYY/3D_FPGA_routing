"""Read-only deterministic postprocessing owner; never launches native work."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'complete_serial_timing_budget_01';out=root/'analysis';out.mkdir(exist_ok=False)
lock=(out/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
q=root/'queue';original=read(q/'registration.json');files=[Path(__file__).resolve(),D/'compare_complete_serial_timing_budget_v1.py',q/'registration.json'];hashes={str(f):sha(f) for f in files}
write(out/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=hashes,scope='Read-only completed two-role timing-budget comparison; no native workers and no experiment ownership transfer.'))
while not (q/'completion.json').exists():
 p=process_identity(original['pid']);live=bool(p and p['state']!='Z' and p['start_ticks']==original['start_ticks'])
 write(out/'status.json',dict(status='waiting_for_timing_budget_terminal',verified_predecessor_live=live))
 if not live:
  write(out/'completion.json',dict(passed=False,reason='Original owner ended without terminal receipt; manual reconciliation required',native_calls=0));sys.exit(1)
 time.sleep(15)
assert all(sha(f)==h for f,h in hashes.items())
with (out/'comparison.log').open('w') as log:code=subprocess.run([sys.executable,str(D/'compare_complete_serial_timing_budget_v1.py')],stdout=log,stderr=subprocess.STDOUT).returncode
write(out/'completion.json',dict(passed=code==0,returncode=code,native_calls=0,source_sha256=hashes,comparison=str(root/'comparison.json')));write(out/'status.json',dict(status='terminal',passed=code==0))
