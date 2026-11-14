#!/usr/bin/env python3
"""Launch new native reservations only after the existing automatic trajectories."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
prior=D/'bnn_automatic_trajectories_dev_02';e=read(prior/'registration.json');b=D/'pending_reservation_dev_01';q=b/'queue';q.mkdir(exist_ok=False);lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
reg=read(b/'registration.json');assert all(sha(p)==h for p,h in reg['source_sha256'].items())
def live():
 p=Path('/proc')/str(e['pid'])/'stat'
 try:return p.read_text().split(') ',1)[1].split()[19]==e['start_ticks']
 except FileNotFoundError:return False
assert live() or (prior/'completion.json').exists()
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],after=str(prior),prior_owner=e,
 source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),b/'registration.json',D/'run_reserved_native_transactions.py']},qualification='Queue only. Default-off/on native tests have not run; no earlier native work is interrupted.'))
write(q/'status.json',dict(status='waiting_for_automatic_trajectory_owner',prior_pid=e['pid'],observed_at=time.time()))
while live():time.sleep(15)
if not (prior/'completion.json').exists():write(q/'dependency_failure.json',dict(reason='Prior owner terminal without completion; no native launch'));raise SystemExit(2)
c=read(prior/'completion.json');assert all(sha(p)==h for p,h in c['source_sha256'].items());assert all(sha(p)==h for p,h in reg['source_sha256'].items())
command=[sys.executable,str(D/'run_reserved_native_transactions.py'),'--batch',str(b),'--selector','compact']
with (b/'controller.log').open('w') as log:
 p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);write(q/'status.json',dict(status='running_native_reservation_tests',pid=p.pid,command=command));code=p.wait()
write(q/'completion.json',dict(returncode=code,native_completion_exists=(b/'completion.json').exists()));sys.exit(code)
