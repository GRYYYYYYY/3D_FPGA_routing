#!/usr/bin/env python3
"""Own one build-dependent small native crossing-domain regression."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'resource_domain_validation_queue_01';b.mkdir(exist_ok=False);lock=(b/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);stage=D/'resource_domain_stage_01';reg=read(stage/'registration.json');script=D/'resource_domain_workspace_01/vtr_flow/tasks/regression_tests/vtr_reg_strong/strong_retained_crossing_reuse/run_case.py';cmd=[sys.executable,str(script),'--old-vpr',str(D/'native_objective_stage_01/bin/vpr'),'--new-vpr',str(stage/'bin/vpr'),'--helpers',str(D),'--output',str(D/'resource_domain_tiny_regression_01')]
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],build_owner=reg,source_sha256={str(p):sha(p) for p in [script,Path(__file__).resolve()]},command=cmd))
def live():
 try:s=(Path('/proc')/str(reg['pid'])/'stat').read_text().split(') ',1)[1].split();return s[0]!='Z' and s[19]==reg['start_ticks']
 except FileNotFoundError:return False
while live():time.sleep(5)
if not(stage/'binding.json').exists():write(b/'completion.json',dict(passed=False,reason='Independent build failed; no native validation launched'));raise SystemExit(2)
assert sha(script)==read(b/'registration.json')['source_sha256'][str(script)]
with (b/'validation.log').open('w') as log:
 p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);write(b/'status.json',dict(status='running_native_regression',pid=p.pid));code=p.wait()
write(b/'completion.json',dict(passed=code==0,returncode=code))
