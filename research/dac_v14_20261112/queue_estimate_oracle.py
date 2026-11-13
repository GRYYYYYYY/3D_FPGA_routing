#!/usr/bin/env python3
from pathlib import Path
import json,time,os,subprocess,fcntl,hashlib,sys,socket
D=Path(__file__).resolve().parent;R=D.parents[1];dependency=D/'estimate_trace_dev_01';runner=D/'run_estimate_oracle.py'
def write(name,obj):
 p=D/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(obj,indent=2)+'\n');t.replace(p)
def ticks(pid):return Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()[19]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def live():
 result=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   a=(p/'cmdline').read_bytes().split(b'\0')[0].decode()
   if a.startswith(str(D)+'/') and a.endswith('/bin/vpr'):result.append(int(p.name))
  except (OSError,UnicodeError):pass
 return result
lock=(D/'estimate_oracle_queue.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
recovery=dependency/('finalization_identity.json' if (dependency/'finalization_identity.json').exists() else 'recovery_identity.json')
parent=json.loads((recovery if recovery.exists() else dependency/'registration.json').read_text())['pid'];parent_ticks=ticks(parent) if not (dependency/'completion.json').exists() else None
identity=dict(pid=os.getpid(),start_ticks=ticks(os.getpid()),host=socket.gethostname(),dependency_pid=parent,dependency_start_ticks=parent_ticks,runner_sha256=sha(runner),analyzer_sha256=sha(D/'analyze_estimates.py'),binary_sha256=sha(D/'estimate_diagnostics/exact_distances'),command=[str(R/'.venv-lazagna/bin/python'),str(runner)],policy='After decision-neutral P/Rq trace batch sealed, run admitted independent full Dijkstra against all logged candidates, 16GiB1800s80GiB; no live router mutation. Existing<=2VPR/noformalactive guards retained.')
write('estimate_oracle_queue_identity.json',identity)
while True:
 processes=live();complete=(dependency/'completion.json').exists()
 write('estimate_oracle_queue_state.json',dict(status='waiting_for_sealed_reuse_pilot_and_slot',dependency_complete=complete,live_vpr=processes,observed_at=time.time()))
 marker=D/'formal_timing_active.json'
 formal_active=marker.exists() and json.loads(marker.read_text()).get('status')=='active'
 if complete and len(processes)<=2 and not formal_active:break
 if not complete:
  try:assert ticks(parent)==parent_ticks
  except (OSError,AssertionError):
   write('estimate_oracle_queue_state.json',dict(status='dependency_missing_requires_diagnosis',live_vpr=processes));sys.exit(2)
 time.sleep(20)
assert json.loads((dependency/'input_seal.json').read_text())['passed']
assert sha(runner)==identity['runner_sha256'] and sha(D/'estimate_diagnostics/exact_distances')==identity['binary_sha256']
with (D/'estimate_oracle_registered.log').open('x') as log:
 p=subprocess.Popen(identity['command'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 write('estimate_oracle_queue_state.json',dict(status='running_pilot',pilot_pid=p.pid,pilot_start_ticks=ticks(p.pid),started_at=time.time()));code=p.wait()
write('estimate_oracle_queue_state.json',dict(status='pilot_terminal',returncode=code,finished_at=time.time()))

if code==0:
 assert sha(D/'analyze_estimates.py')==identity['analyzer_sha256']
 with (D/'estimate_oracle_analysis.log').open('x') as log:
  result=subprocess.run([str(R/'.venv-lazagna/bin/python'),str(D/'analyze_estimates.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 write('estimate_oracle_queue_state.json',dict(status='analysis_terminal',oracle_returncode=code,analysis_returncode=result.returncode,finished_at=time.time()))
