"""Isolated Linux subreaper for one component; timeout never permits a retry."""
import argparse,ctypes,json,os,signal,subprocess,time
from pathlib import Path

def ident(pid):
 try:
  fields=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
  return dict(pid=pid,state=fields[0],start_ticks=fields[19])
 except FileNotFoundError:return None

def descendants():
 pending=[os.getpid()];seen={};
 while pending:
  parent=pending.pop()
  try:children=Path('/proc',str(parent),'task',str(parent),'children').read_text().split()
  except FileNotFoundError:continue
  for token in children:
   pid=int(token)
   if pid not in seen:
    row=ident(pid)
    if row is not None:seen[pid]=row;pending.append(pid)
 return seen

def kill_owned():
 killed=[]
 # SIGSTOP closes the ordinary fork race; pidfds prevent PID reuse signaling.
 while True:
  live=[r for r in descendants().values() if r['state']!='Z']
  if not live:break
  held=[]
  for row in live:
   try:
    fd=os.pidfd_open(row['pid']);current=ident(row['pid'])
    if current is None or current['start_ticks']!=row['start_ticks']:os.close(fd);continue
    signal.pidfd_send_signal(fd,signal.SIGSTOP);held.append((fd,row))
   except ProcessLookupError:continue
  extra=[r for r in descendants().values() if r['state']!='Z' and r['pid'] not in {r['pid'] for _,r in held}]
  for fd,row in held:
   try:signal.pidfd_send_signal(fd,signal.SIGKILL);killed.append(row)
   except ProcessLookupError:pass
   finally:os.close(fd)
  time.sleep(.02)
 return killed

def main():
 p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);p.add_argument('--seconds',type=float);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
 assert (a.seconds is None or a.seconds>0) and not a.receipt.exists();cmd=a.command[1:] if a.command[:1]==['--'] else a.command;assert cmd
 libc=ctypes.CDLL(None,use_errno=True);assert libc.prctl(36,1,0,0,0)==0,'Linux subreaper unavailable'
 def interrupted(signum,frame):
  raise InterruptedError('Phase supervisor received signal '+str(signum))
 signal.signal(signal.SIGTERM,interrupted)
 signal.signal(signal.SIGINT,interrupted)
 start=time.monotonic();child=subprocess.Popen(cmd,start_new_session=True);identity=ident(child.pid);observed={};reason=None
 active=a.receipt.with_suffix('.active.json');active.write_text(json.dumps(dict(supervisor=ident(os.getpid()),child=identity,command=cmd,seconds=a.seconds)))
 try:
  while child.poll() is None:
   observed.update(descendants())
   if a.seconds is not None and time.monotonic()-start>=a.seconds:reason='wall_timeout';break
   time.sleep(.05)
  observed.update(descendants())
  if reason is None and any(r['state']!='Z' for r in descendants().values()):reason='live_descendant_after_root_exit'
 except InterruptedError as error:
  reason=str(error)
 finally:
  signal.signal(signal.SIGTERM,signal.SIG_IGN);signal.signal(signal.SIGINT,signal.SIG_IGN)
  killed=kill_owned();code=child.wait()
  while True:
   try:pid,_=os.waitpid(-1,os.WNOHANG)
   except ChildProcessError:break
   if not pid:time.sleep(.02);continue
 residual=descendants();assert not residual
 data=dict(passed=code==0 and reason is None,returncode=code,status=reason or ('completed' if code==0 else 'failed'),command=cmd,child=identity,observed_descendants=list(observed.values()),killed_private_descendants=killed,residual_descendants=residual,complete_seconds=time.monotonic()-start,no_retry=True)
 a.receipt.write_text(json.dumps(data,indent=2)+'\n');raise SystemExit(0 if data['passed'] else 1)
if __name__=='__main__':main()
