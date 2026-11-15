import os,time,sys
if os.fork()==0:
 os.setsid();time.sleep(30)
else:
 time.sleep(30 if sys.argv[1]=='timeout' else .15)
