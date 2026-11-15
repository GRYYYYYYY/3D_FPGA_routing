"""Real process-tree tests for unlimited, timed and externally interrupted phases."""
import os,signal,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'method_phase_supervision_validation_01';b.mkdir(exist_ok=False)
runtime=D/'standalone_unified_method_dev_02';supervisor=runtime/'supervise_method_phase.py'
program=b/'fork_setsid.py';program.write_text('''import os,sys,time
mode=sys.argv[1]
pid=os.fork()
if pid==0:
 os.setsid()
 if mode=='clean':time.sleep(.1)
 else:time.sleep(60)
 os._exit(0)
if mode=='orphan':os._exit(0)
os.waitpid(pid,0)
''')
checks=[]
for mode in ['clean','timeout','orphan','interrupted']:
    receipt=b/(mode+'.json');cmd=['/usr/bin/python3',str(supervisor),'--receipt',str(receipt)]
    if mode=='timeout':cmd+=['--seconds','0.3']
    cmd+=['--','/usr/bin/python3',str(program),mode]
    with (b/(mode+'.log')).open('x') as log:
        p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        if mode=='interrupted':
            limit=time.monotonic()+5
            while not receipt.with_suffix('.active.json').exists():
                assert time.monotonic()<limit;time.sleep(.01)
            time.sleep(.1);p.send_signal(signal.SIGTERM)
        code=p.wait(timeout=10)
    r=read(receipt);assert not r['residual_descendants']
    if mode=='clean':assert r['passed'] and code==0 and r['status']=='completed'
    else:assert not r['passed'] and code!=0 and r['killed_private_descendants']
    if mode=='timeout':assert r['status']=='wall_timeout'
    if mode=='orphan':assert r['status']=='live_descendant_after_root_exit'
    if mode=='interrupted':assert r['status'].startswith('Phase supervisor received signal')
    checks.append(dict(mode=mode,status=r['status'],killed=len(r['killed_private_descendants'])))
write(b/'completion.json',dict(passed=True,real_fork_setsid_checks=checks,whole_method_time_limit=None,native_calls_new=0,source_sha256={str(supervisor):sha(supervisor),str(Path(__file__).resolve()):sha(__file__)},qualification='Real process lifecycle tests, not solver quality or runtime equivalence. Existing queued component supervisor unchanged.'))
print(checks,flush=True)
