#!/usr/bin/env python3
"""Serialize independent native opportunity controls after the resource-pair owner."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'native_extra_opportunity_bnn_01';q=b/'queue';q.mkdir(exist_ok=False);lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prior=D/'shared_crossing_repair_dev_01';owner=read(prior/'queue/registration.json');reg=read(b/'registration.json');assert all(sha(p)==h for p,h in reg['source_sha256'].items())
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],after=str(prior),prior_owner=owner,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),b/'registration.json',D/'run_native_extra_opportunity.py']},question='Finish unchanged resource pairs, then execute original native binaries with extra convergence opportunity. Neither a prior negative result nor this local three-arm cohort completes the research goal.'))
def live():
 try:s=(Path('/proc')/str(owner['pid'])/'stat').read_text().split(') ',1)[1].split();return s[0]!='Z' and s[19]==owner['start_ticks']
 except FileNotFoundError:return False
write(q/'status.json',dict(status='waiting_for_resource_pair_owner',prior_pid=owner['pid'],observed_at=time.time()))
while live():time.sleep(15)
if not(prior/'completion.json').exists():write(q/'dependency_failure.json',dict(reason='Prior owner terminal without completion; preserve unknown outcome, no duplicate launch'));raise SystemExit(2)
assert all(sha(p)==h for p,h in read(prior/'completion.json')['source_sha256'].items());assert all(sha(p)==h for p,h in reg['source_sha256'].items())
command=[sys.executable,str(D/'run_native_extra_opportunity.py')]
with (b/'execution.log').open('w') as out:
 proc=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT);write(q/'status.json',dict(status='running_original_native_extra_opportunity',pid=proc.pid,command=command,observed_at=time.time()));code=proc.wait()
write(q/'completion.json',dict(returncode=code,passed=code==0,qualification='Local original-native opportunity cohort terminal; continuing research remains active.'))
