#!/usr/bin/env python3
"""Queue the new selection policy after the already submitted strong-baseline batch."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
prior=D/'bnn_strong_release_joint_dev_01';batch=D/'bnn_cover_selected_dev_01';q=batch/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
reg=read(batch/'registration.json');assert all(sha(p)==h for p,h in reg['source_sha256'].items())
assert not (batch/'execution_registration.json').exists()
submission=read(prior/'queue/registration.json')
def live(e):
 p=Path('/proc')/str(e['pid'])/'stat'
 try:return p.read_text().split(') ',1)[1].split()[19]==e['start_ticks']
 except FileNotFoundError:return False
assert live(submission) or (prior/'execution_registration.json').exists()
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],after=str(prior),previous_submission_owner=submission,
 source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),batch/'registration.json',D/'run_registered_native_transactions_v3.py']},
 question='After both already-registered native cohorts, evaluate uniform0.9 critical-path group selection with compact scheduling and exact fixed-anchor acceptance.'))
write(q/'status.json',dict(status='waiting_for_previous_submitted_batch_to_start',prior_queue_pid=submission['pid'],observed_at=time.time()))
while not (prior/'execution_registration.json').exists():
 if not live(submission):
  write(q/'status.json',dict(status='needs_reconciliation',reason='Previous submission owner terminal before native execution receipt; no launch.'));sys.exit(2)
 time.sleep(15)
e=read(prior/'execution_registration.json');write(q/'status.json',dict(status='waiting_for_previous_native_owner',prior_pid=e['pid'],observed_at=time.time()))
while live(e):time.sleep(15)
if not (prior/'completion.json').exists():
 write(q/'status.json',dict(status='needs_reconciliation',reason='Previous native owner terminal without completion receipt; no launch.'));sys.exit(2)
c=read(prior/'completion.json');assert all(sha(p)==h for p,h in c['source_sha256'].items())
assert all(sha(p)==h for p,h in reg['source_sha256'].items())
command=[sys.executable,str(D/'run_registered_native_transactions_v3.py'),'--batch',str(batch),'--selector','compact']
with (batch/'controller.log').open('w') as log:
 proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
 write(q/'status.json',dict(status='running_selected_batch',child_pid=proc.pid,command=command,observed_at=time.time()));code=proc.wait()
write(q/'completion.json',dict(status='terminal',returncode=code,native_completion_exists=(batch/'completion.json').exists(),observed_at=time.time()));sys.exit(code)
