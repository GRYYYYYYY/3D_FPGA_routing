#!/usr/bin/env python3
"""One dependent pilot owner; waits for a stable free slot in the four-case expansion."""
import os,json,time,subprocess,fcntl,socket,sys
from pathlib import Path
D=Path(__file__).resolve().parent;B=D/'h2_expansion_01';R=D.parents[1]
def put(name,data):
 p=D/name;tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(p)
def live_vpr():
 found=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   cmd=(p/'cmdline').read_bytes().split(b'\0')
   if cmd and cmd[0].decode()==str(B/'bin/vpr'):found.append(int(p.name))
  except (OSError,UnicodeError):pass
 return found
lock=(D/'feedback_queue.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
reg=json.loads((B/'registration.json').read_text());owner=reg['pid'];assert reg['host']==socket.gethostname()
def start_ticks(pid):
 return Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()[19]
initial_ticks=start_ticks(owner)
identity={'pid':os.getpid(),'host':socket.gethostname(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'start_ticks':start_ticks(os.getpid()),'dependency_pid':owner,'dependency_start_ticks':initial_ticks,'command':[str(R/'.venv-lazagna/bin/python'),str(D/'run_feedback.py'),'--out','feedback_dev_01'],'policy':'Start after >=2 of four expansion cases are terminal, every case has started, and at most 2 expansion VPR processes remain. Total VPR concurrency <=3; formal timing excluded.'}
put('feedback_queue_identity.json',identity)
while True:
 completed=[c for c in reg['circuits'] if (B/f'{c}_observations.json').exists() or (B/f'{c}_supervisor_error.json').exists()]
 started=all((B/'runs'/f'{c}_F/manifest.json').exists() or (B/f'{c}_supervisor_error.json').exists() for c in reg['circuits'])
 live=live_vpr();put('feedback_queue_state.json',dict(status='waiting_for_slot',completed_cases=completed,live_dependency_vpr=live,observed_at=time.time()))
 if len(completed)>=2 and started and len(live)<=2:break
 try:assert start_ticks(owner)==initial_ticks
 except (OSError,AssertionError):
  put('feedback_queue_state.json',dict(status='dependency_owner_missing_requires_diagnosis',live_dependency_vpr=live,completed_cases=completed));sys.exit(2)
 time.sleep(20)
with (D/'feedback_dev_01.log').open('x') as out:
 proc=subprocess.Popen(identity['command'],cwd=R,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
 put('feedback_queue_state.json',dict(status='running_pilot',pilot_pid=proc.pid,pilot_start_ticks=start_ticks(proc.pid),started_at=time.time()))
 code=proc.wait()
put('feedback_queue_state.json',dict(status='pilot_terminal',returncode=code,finished_at=time.time()))
