#!/usr/bin/env python3
"""Single build-dependent owner for the isolated native fork regression."""
import fcntl,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
stage=D/'analysis_fork_stage_02';q=D/'analysis_fork_validation_queue_01';q.mkdir(exist_ok=False);lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
reg=read(stage/'registration.json');script=D/'analysis_fork_workspace_01/vtr_flow/tasks/regression_tests/vtr_reg_strong/strong_analysis_fork/run_case.py'
command=[sys.executable,str(script),'--vpr',str(stage/'bin/vpr'),'--fixture',str(D/'reservation_multisink_regression_01'),'--architecture',str(D.parents[1]/'vendor/lazagna-vtr9-buildfix-src/vtr_flow/arch/timing/k6_N10_mem32K_40nm_fc_abs.xml'),'--circuit',str(D/'reservation_workspace_02/vtr_flow/tasks/regression_tests/vtr_reg_strong/strong_pending_multisink/fixture.blif'),'--helpers',str(D),'--output',str(D/'analysis_fork_tiny_regression_01')]
write(q/'registration.json',dict(pid=__import__('os').getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],after_build=reg,command=command,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),script]},limits=dict(simultaneous_VPR_processes_including_parent_and_current_batch=3,child_seconds=60,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),role='Independent read-only tiny native regression; does not acquire or change native quality cohort ownership.'))
def live():
 try:s=(Path('/proc')/str(reg['pid'])/'stat').read_text().split(') ',1)[1].split();return s[0]!='Z' and s[19]==reg['start_ticks']
 except FileNotFoundError:return False
while live():time.sleep(5)
if not (stage/'binding.json').exists():write(q/'completion.json',dict(passed=False,reason='Independent build failed; no regression started'));raise SystemExit(2)
assert sha(script)==read(q/'registration.json')['source_sha256'][str(script)]
with (q/'regression.log').open('w') as out:
 proc=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT);write(q/'status.json',dict(status='running_tiny_regression',pid=proc.pid));code=proc.wait()
write(q/'completion.json',dict(passed=code==0,returncode=code,result=str(D/'analysis_fork_tiny_regression_01/completion.json')))
