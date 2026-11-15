"""One actual terminal-wire/current-STA full flow after all earlier registered trials."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'complete_BNN_terminal_wire_flow_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
files=[Path(__file__).resolve(),root/'plan.json',Path(plan['config']),*map(Path,plan['prepared_files'])]
hashes={str(p):sha(p) for p in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=hashes,scope=plan['qualification']))
prior=Path(plan['predecessor']);previous=read(prior/'registration.json')
while not (prior/'completion.json').exists():
 actual=process_identity(previous['pid']);live=bool(actual and actual['state']!='Z' and actual['start_ticks']==previous['start_ticks'])
 write(q/'status.json',dict(status='waiting_for_registered_robot_release_ablation_terminal',verified_predecessor_live=live,predecessor=str(prior)))
 if not live:
  write(q/'completion.json',dict(passed=False,status='predecessor_ended_without_receipt',results={},native_calls_new=0,source_sha256=hashes));sys.exit(1)
 time.sleep(15)
write(q/'status.json',dict(status='waiting_for_current_serial_owner_to_release_slot',predecessor_passed=read(prior/'completion.json')['passed']))
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX)
assert all(sha(p)==h for p,h in hashes.items())
baseline=Path(plan['baseline_completion'])
if not baseline.exists() or not read(baseline).get('passed'):
 write(q/'completion.json',dict(passed=False,status='required_closed_stream_baseline_unavailable',native_calls_new=0,source_sha256=hashes));sys.exit(1)
case=root/'bnn_native_terminal_wire';case.mkdir();(case/'queue').mkdir();(case/'config.json').write_bytes(Path(plan['config']).read_bytes())
command=[sys.executable,str(D/'measure_process_tree_v1.py'),'--output',str(case/'measurement'),'--',sys.executable,
 str(D/'run_complete_resource_terminal_wire_timing_v1.py'),'--config',plan['config'],'--output',str(case/'flow')]
with (q/'measured_command.log').open('w') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);identity=process_identity(child.pid)
 write(case/'queue/registration.json',dict(pid=child.pid,start_ticks=identity['start_ticks'],command=command,source_sha256=hashes))
 write(q/'status.json',dict(status='running',case=case.name,pid=child.pid,start_ticks=identity['start_ticks']));code=child.wait()
command_ok=code==0 and (case/'flow/completion.json').exists() and read(case/'flow/completion.json')['passed'] and read(case/'measurement/completion.json')['passed']
verification_ok=False
if command_ok:
 with (q/'case_verification.log').open('w') as log:
  verify_code=subprocess.run([sys.executable,str(D/'verify_complete_resource_terminal_wire_timing_v1.py'),'--root',str(case)],stdout=log,stderr=subprocess.STDOUT).returncode
 verification_ok=verify_code==0 and (case/'completion.json').exists() and read(case/'completion.json')['passed']
results={case.name:dict(passed=command_ok and verification_ok,command_passed=command_ok,verification_passed=verification_ok,
 returncode=code if not command_ok else verify_code,failure_stage=None if command_ok and verification_ok else 'measured_command' if not command_ok else 'readonly_case_verification',completion=str(case/'completion.json'))}
write(q/'results.json',results)
with (q/'comparison.log').open('w') as log:
 compare_code=subprocess.run([sys.executable,str(D/'compare_BNN_terminal_wire_full_flow_v1.py')],stdout=log,stderr=subprocess.STDOUT).returncode
passed=compare_code==0 and (root/'comparison.json').exists() and read(root/'comparison.json')['passed']
write(q/'completion.json',dict(passed=passed,execution_all_legal=results[case.name]['passed'],results=results,
 comparison=str(root/'comparison.json'),source_sha256=hashes,qualification=plan['qualification']))
write(q/'status.json',dict(status='terminal',passed=passed))
