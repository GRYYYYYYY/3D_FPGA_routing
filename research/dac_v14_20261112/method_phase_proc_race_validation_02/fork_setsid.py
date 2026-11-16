import os,sys,time
mode=sys.argv[1]
if mode=='churn':
 for _ in range(120):
  pid=os.fork()
  if pid==0: os._exit(0)
  os.waitpid(pid,0)
 sys.exit(0)
pid=os.fork()
if pid==0:
 os.setsid()
 time.sleep(.1 if mode=='clean' else 60)
 os._exit(0)
if mode=='orphan': os._exit(0)
os.waitpid(pid,0)
