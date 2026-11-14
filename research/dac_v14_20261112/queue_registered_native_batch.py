#!/usr/bin/env python3
"""Single-owner dependency queue; never infer termination from stale metadata."""
import argparse,fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
p=argparse.ArgumentParser();p.add_argument('--after',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);a=p.parse_args()
prior=a.after.resolve();batch=a.batch.resolve();q=batch/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
reg=read(batch/'registration.json');e=read(prior/'execution_registration.json')
assert all(sha(path)==h for path,h in reg['source_sha256'].items())
assert not (batch/'execution_registration.json').exists()
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],after=str(prior),batch=str(batch),
 previous_owner=e,source_sha256={str(Path(__file__).resolve()):sha(__file__),str(batch/'registration.json'):sha(batch/'registration.json')},
 question='Run the independently registered strong-baseline batch only after the existing native controller is terminal, preserving both batch definitions.',limits='Existing individual-child guards apply; dependency waiting is not a research deadline.'))
def live():
 s=Path('/proc')/str(e['pid'])/'stat'
 try:return s.read_text().split(') ',1)[1].split()[19]==e['start_ticks']
 except FileNotFoundError:return False
write(q/'status.json',dict(status='waiting_for_verified_previous_owner',previous_pid=e['pid'],observed_at=time.time()))
while live():time.sleep(15)
if not (prior/'completion.json').exists():
 write(q/'status.json',dict(status='needs_reconciliation',reason='Previous owner is terminal without a completion receipt. No next native process launched.',observed_at=time.time()));sys.exit(2)
c=read(prior/'completion.json');assert all(sha(path)==h for path,h in c['source_sha256'].items())
assert all(sha(path)==h for path,h in reg['source_sha256'].items())
assert not (batch/'execution_registration.json').exists()
write(q/'status.json',dict(status='starting_next_batch',prior_passed=c['passed'],observed_at=time.time()))
cmd=[sys.executable,str(D/'run_registered_native_transactions.py'),'--batch',str(batch)]
with (batch/'controller.log').open('w') as log:
 proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
 write(q/'status.json',dict(status='running_next_batch',child_pid=proc.pid,command=cmd,observed_at=time.time()))
 code=proc.wait()
write(q/'completion.json',dict(status='terminal',returncode=code,previous_completion_sha256=sha(prior/'completion.json'),next_completion_exists=(batch/'completion.json').exists(),observed_at=time.time()))
sys.exit(code)
