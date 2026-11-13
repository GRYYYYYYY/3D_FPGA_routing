#!/usr/bin/env python3
"""Start the registered target-query pilot after the feedback pilot terminates."""
from pathlib import Path
import os,json,time,hashlib,fcntl,socket,subprocess,sys
D=Path(__file__).resolve().parent;R=D.parents[1]
def write(name,obj):
 p=D/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(obj,indent=2)+'\n');t.replace(p)
def ticks(pid):return Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()[19]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def live():
 found=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   args=(p/'cmdline').read_bytes().split(b'\0');binary=args[0].decode()
   if binary.startswith(str(D)+'/') and binary.endswith('/bin/vpr'):found.append(int(p.name))
  except (OSError,UnicodeError):pass
 return found
lock=(D/'generation_confirmation_queue.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
runner=D/'run_generation_confirmation.py';candidate=D/'profile_generation_candidate_01'
dependency=json.loads((D/'feedback_bnn_queue_identity.json').read_text())
identity=dict(pid=os.getpid(),start_ticks=ticks(os.getpid()),host=socket.gethostname(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),runner_sha256=sha(runner),candidate_binary_sha256=sha(candidate/'bin/vpr'),dependency=dependency,command=[str(R/'.venv-lazagna/bin/python'),str(runner),'--out','generation_confirmation_dev_01'],policy='After bnn F/U terminal and <=2 other live VPR, confirm bnn O against sealed U; one worker, normal max3, original64GiB. Failure of prerequisite is diagnosed, not silently treated as a quality reference.')
write('generation_confirmation_queue_identity.json',identity)
while True:
 state=json.loads((D/'feedback_bnn_queue_state.json').read_text());running=live()
 write('generation_confirmation_queue_state.json',dict(status='waiting_for_bnn_reference_and_slot',dependency_state=state['status'],live_vpr=running,observed_at=time.time()))
 if state['status']=='pilot_terminal' and len(running)<=2:break
 try:assert ticks(dependency['pid'])==dependency['start_ticks']
 except (OSError,AssertionError):
  write('generation_confirmation_queue_state.json',dict(status='dependency_missing_requires_diagnosis',dependency_state=state,live_vpr=running));sys.exit(2)
 time.sleep(20)
assert sha(runner)==identity['runner_sha256'];assert sha(candidate/'bin/vpr')==identity['candidate_binary_sha256']
with (D/'generation_confirmation_dev_01.log').open('x') as log:
 proc=subprocess.Popen(identity['command'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 write('generation_confirmation_queue_state.json',dict(status='running_pilot',pilot_pid=proc.pid,pilot_start_ticks=ticks(proc.pid),started_at=time.time()))
 code=proc.wait()
write('generation_confirmation_queue_state.json',dict(status='pilot_terminal',returncode=code,finished_at=time.time()))
