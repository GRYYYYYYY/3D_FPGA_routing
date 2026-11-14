#!/usr/bin/env python3
"""Run registered static-state engineering diagnostics after existing cohorts."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'native_batch_equivalence_dev_01';q=b/'queue';q.mkdir(exist_ok=False);lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
prior=D/'pending_reservation_dev_02';old=read(prior/'queue/registration.json');reg=read(b/'registration.json');assert all(sha(p)==h for p,h in reg['source_sha256'].items())
def live():
 p=Path('/proc')/str(old['pid'])/'stat'
 try:s=p.read_text().split(') ',1)[1].split();return s[19]==old['start_ticks'] and s[0]!='Z'
 except FileNotFoundError:return False
assert live() or (prior/'completion.json').exists()
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],after=str(prior),previous_owner=old,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),b/'registration.json',D/'run_native_static_batch_analysis.py']},qualification='Independent native component diagnostics only after prior batch owner is terminal; no existing inputs/acceptance/version changes.'))
write(q/'status.json',dict(status='waiting_for_reservation_batch_owner',prior_pid=old['pid'],observed_at=time.time()))
while live():time.sleep(15)
if not (prior/'completion.json').exists():write(q/'dependency_failure.json',dict(reason='Prior owner terminal without completion; no launch'));raise SystemExit(2)
assert all(sha(p)==h for p,h in read(prior/'completion.json')['source_sha256'].items())
assert all(sha(p)==h for p,h in reg['source_sha256'].items());started=time.monotonic();results={}
for name,path in reg['cases'].items():
 case=b/name;command=[sys.executable,str(D/'run_native_static_batch_analysis.py'),'--registration',path,'--batch',str(case)];t=time.monotonic()
 with (b/(name+'.log')).open('w') as log:
  proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);write(q/'status.json',dict(status='running_static_state_equivalence',case=name,pid=proc.pid,command=command,observed_at=time.time()));code=proc.wait()
 results[name]=read(case/'completion.json') if (case/'completion.json').exists() else dict(passed=False,status='component_workflow_failed_preserved')
 results[name].update(returncode=code,complete_driver_process_seconds=time.monotonic()-t);write(b/'progress.json',results)
assert all(sha(p)==h for p,h in reg['source_sha256'].items())
write(b/'completion.json',dict(passed=all(r['passed'] for r in results.values()),cases=results,complete_shared_workflow_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None,source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'progress.json',Path(__file__).resolve()]},qualification='Component-equivalence cohort. Failures preserved, no route commits or whole-algorithm speedup claim; local cohort termination does not complete research.'))
write(q/'completion.json',dict(returncode=0 if all(r['passed'] for r in results.values()) else 1));raise SystemExit(0 if all(r['passed'] for r in results.values()) else 1)
