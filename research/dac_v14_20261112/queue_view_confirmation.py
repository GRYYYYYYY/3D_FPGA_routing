#!/usr/bin/env python3
from pathlib import Path
import json,time,os,subprocess,fcntl,hashlib,sys,socket
D=Path(__file__).resolve().parent;R=D.parents[1];dependency=D/'closure_view_dev_01';runner=D/'run_view_confirmation.py'
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
lock=(D/'view_confirmation_queue.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
parent=json.loads((dependency/'registration.json').read_text())['pid'];parent_ticks=ticks(parent) if not (dependency/'completion.json').exists() else None
identity=dict(pid=os.getpid(),start_ticks=ticks(os.getpid()),host=socket.gethostname(),dependency_pid=parent,dependency_start_ticks=parent_ticks,runner_sha256=sha(runner),binary_sha256=sha(D/'closure_view_candidate_01/bin/vpr'),command=[str(R/'.venv-lazagna/bin/python'),str(runner),'--out','view_confirmation_dev_01'],policy='After closure_view_dev_01 sealed and <=2 live VPR, bnn V against sealed U, original64GiB/1800s/disk80GiB; max3VPR. Exact view intersection and storage only.')
write('view_confirmation_queue_identity.json',identity)
while True:
 processes=live();complete=(dependency/'completion.json').exists()
 write('view_confirmation_queue_state.json',dict(status='waiting_for_sealed_view_pilot_and_slot',dependency_complete=complete,live_vpr=processes,observed_at=time.time()))
 if complete and len(processes)<=2:break
 if not complete:
  try:assert ticks(parent)==parent_ticks
  except (OSError,AssertionError):
   write('view_confirmation_queue_state.json',dict(status='dependency_missing_requires_diagnosis',live_vpr=processes));sys.exit(2)
 time.sleep(20)
assert json.loads((dependency/'input_seal.json').read_text())['passed']
assert sha(runner)==identity['runner_sha256'] and sha(D/'closure_view_candidate_01/bin/vpr')==identity['binary_sha256']
with (D/'view_confirmation_dev_01.log').open('x') as log:
 p=subprocess.Popen(identity['command'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 write('view_confirmation_queue_state.json',dict(status='running_pilot',pilot_pid=p.pid,pilot_start_ticks=ticks(p.pid),started_at=time.time()));code=p.wait()
write('view_confirmation_queue_state.json',dict(status='pilot_terminal',returncode=code,finished_at=time.time()))
