import os,sys,time
mode=sys.argv[1]
pid=os.fork()
if pid==0:
 os.setsid()
 if mode=='clean':time.sleep(.1)
 else:time.sleep(60)
 os._exit(0)
if mode=='orphan':os._exit(0)
os.waitpid(pid,0)
