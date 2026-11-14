#!/usr/bin/env python3
"""Launch new native reservations only after the existing automatic trajectories."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
prior=D/'native_batch_equivalence_dev_01';e=read(prior/'queue/registration.json');b=D/'critical_owner_exchange_dev_01';q=b/'queue';q.mkdir(exist_ok=False);lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
reg=read(b/'registration.json');assert all(sha(p)==h for p,h in reg['source_sha256'].items())
def live():
 p=Path('/proc')/str(e['pid'])/'stat'
 try:return p.read_text().split(') ',1)[1].split()[19]==e['start_ticks']
 except FileNotFoundError:return False
assert live() or (prior/'completion.json').exists()
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],after=str(prior),prior_owner=e,
 source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),b/'registration.json',D/'run_registered_exchange_transactions.py']},qualification='Queue only. Five independent critical-owner exchange controls have not run. Waiting is resource serialization only; existing native kernel does not depend on the static-batch feature succeeding.'))
write(q/'status.json',dict(status='waiting_for_static_batch_owner',prior_pid=e['pid'],observed_at=time.time()))
while live():time.sleep(15)
if not (prior/'completion.json').exists():write(q/'dependency_failure.json',dict(reason='Prior owner terminal without completion; no native launch'));raise SystemExit(2)
c=read(prior/'completion.json');assert all(sha(p)==h for p,h in c['source_sha256'].items());assert all(sha(p)==h for p,h in reg['source_sha256'].items())
command=[sys.executable,str(D/'run_registered_exchange_transactions.py'),'--batch',str(b),'--selector','compact']
with (b/'controller.log').open('w') as log:
 p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);write(q/'status.json',dict(status='running_critical_owner_exchange_controls',pid=p.pid,command=command));code=p.wait()
write(q/'completion.json',dict(returncode=code,native_completion_exists=(b/'completion.json').exists()));sys.exit(code)
