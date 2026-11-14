#!/usr/bin/env python3
"""Wait for the actual single quality owner; then run independent large equivalence."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'native_repair_queue_validation_queue_01';b.mkdir(exist_ok=False);lock=(b/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prior=D/'pooled_resource_repair_dev_01';r=read(prior/'queue/registration.json');files=[Path(__file__).resolve(),D/'validate_native_repair_queue_bnn.py',D/'native_repair_analysis_pool.py',D/'pool_state_evaluator_v2.py',D/'native_repair_queue_stage_01/binding.json',D/'native_repair_queue_tiny_regression_01/completion.json',D/'current_resource_bundle_validation_01/completion.json',prior/'queue/registration.json'];bound={str(p):sha(p) for p in files};assert read(D/'native_repair_queue_tiny_regression_01/completion.json')['passed'];write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],prior_owner=r,source_sha256=bound,after=str(prior),qualification='Large new native repair pool equivalence follows the actual original quality owner, never overlaps two large loaded parents or changes original active code. Failure does not terminate research.'))
def live():
 try:s=Path('/proc',str(r['pid']),'stat').read_text().split(') ',1)[1].split();return s[0]!='Z' and s[19]==r['start_ticks']
 except FileNotFoundError:return False
write(b/'status.json',dict(status='waiting_for_original_quality_owner',prior_pid=r['pid'],observed_at=time.time()))
while live():time.sleep(15)
assert (prior/'queue/completion.json').exists(),'Prior owner terminal without receipt: inspect, do not resubmit';assert all(sha(p)==h for p,h in bound.items());command=[sys.executable,str(D/'validate_native_repair_queue_bnn.py')]
with (b/'execution.log').open('w') as out:
 proc=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT);write(b/'status.json',dict(status='running_large_equivalence',pid=proc.pid,observed_at=time.time()));code=proc.wait()
write(b/'completion.json',dict(passed=code==0,returncode=code,qualification='Local large engineering validation terminal; continuous research stays active. Preserve failed native jobs and do not repeat completed references just to refill a report.'))
