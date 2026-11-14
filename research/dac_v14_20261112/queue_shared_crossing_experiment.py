#!/usr/bin/env python3
"""One registered resource-pair owner, sequenced after the current native portfolio."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'shared_crossing_repair_dev_01';q=b/'queue';q.mkdir(exist_ok=False);lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);reg=read(b/'registration.json');prior=D/'portfolio_execution_dev_01';owner=read(prior/'queue/registration.json');assert all(sha(p)==h for p,h in reg['source_sha256'].items());tiny=D/'resource_domain_tiny_regression_02/completion.json';assert read(tiny)['passed']
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],after=str(prior),prior_owner=owner,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),b/'registration.json',D/'run_shared_crossing_experiment.py',tiny]},question='Execute automatically ranked native off/on sharing pairs only after the existing frozen quality chain becomes terminal; a prior branch negative result does not terminate research.'))
def live():
 try:s=(Path('/proc')/str(owner['pid'])/'stat').read_text().split(') ',1)[1].split();return s[0]!='Z' and s[19]==owner['start_ticks']
 except FileNotFoundError:return False
write(q/'status.json',dict(status='waiting_for_current_portfolio_owner',prior_pid=owner['pid'],observed_at=time.time()))
while live():time.sleep(15)
if not(prior/'completion.json').exists():write(q/'dependency_failure.json',dict(reason='Prior owner terminal without completion; preserve ambiguous evidence for main-model diagnosis, no duplicate launch'));raise SystemExit(2)
c=read(prior/'completion.json');assert all(sha(p)==h for p,h in c['source_sha256'].items());assert all(sha(p)==h for p,h in reg['source_sha256'].items());assert all(sha(p)==h for p,h in read(q/'registration.json')['source_sha256'].items())
command=[sys.executable,str(D/'run_shared_crossing_experiment.py'),'--batch',str(b),'--selector','compact'];t=time.monotonic()
with (b/'execution.log').open('w') as out:
 proc=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT);write(q/'status.json',dict(status='running_native_sharing_pairs',pid=proc.pid,command=command,prior_passed=c['passed'],observed_at=time.time()));code=proc.wait()
write(q/'completion.json',dict(returncode=code,passed=code==0,complete_coordinator_seconds=time.monotonic()-t,prior_quality_cohort_passed=c['passed'],qualification='Shared development workflow cost excludes prior-quality work. Not complete cold single-configuration time. A failed arm does not terminate other arms or the active research goal.'))
