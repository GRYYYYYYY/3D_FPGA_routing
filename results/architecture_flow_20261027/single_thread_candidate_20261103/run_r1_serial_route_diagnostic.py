#!/usr/bin/env python3
"""Trace thread creation in fixed-input A0/R1/B2 routing, diagnostic only."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

root=Path(__file__).resolve().parents[3]
base=root/'results/architecture_flow_20261027'
here=Path(__file__).parent
names={'R1':'balance_relative3_spmv_s11_hybrid_o_n40_w100_p1_delay_critical_c6'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=here/'r1_serial_route_diagnostic_20261103';out.mkdir(exist_ok=False)
trace=here/'trace_pthread_create.so'
registration=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),names=names,
    trace_sha256=sha(trace),manifest_sha256={k:sha(base/'runs'/v/'manifest.json') for k,v in names.items()},
    scope='One fixed-input diagnostic; pthread interposition perturbs execution and misses direct clone syscalls. No performance claim.')
(out/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
results=[]
for role,name in names.items():
    source=base/'runs'/name;old=json.loads((source/'manifest.json').read_text());dest=out/role;dest.mkdir()
    for f in ('packed.net','placed.place'):shutil.copyfile(source/f,dest/f)
    cmd=list(old['command']); cmd[0]=str(here/'r1_serial_build/vpr/vpr')
    for flag,file in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:
        cmd[cmd.index(flag)+1]=str(dest/file)
    env=dict(os.environ);env.update(old['environment']);env['LD_PRELOAD']=str(trace)
    start=time.monotonic();samples=0;peak=0;timed_out=False
    with (dest/'stdout.log').open('w') as log:
        p=subprocess.Popen(['/usr/bin/prlimit','--as=68719476736:68719476736','--',*cmd],
                           cwd=dest,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        while p.poll() is None:
            try:peak=max(peak,len(list((Path('/proc')/str(p.pid)/'task').iterdir())));samples+=1
            except OSError:pass
            if time.monotonic()-start>1800:
                import signal
                os.killpg(p.pid,signal.SIGTERM);timed_out=True;break
            time.sleep(.01)
        rc=p.wait()
    text=(dest/'stdout.log').read_text(errors='replace')
    row=dict(role=role,returncode=rc,timeout=timed_out,thread_peak_sampled=peak,samples=samples,
             pthread_creation_trace_count=text.count('PTHREAD_CREATE_DIAGNOSTIC'),
             routing_success='Successfully routed' in text and 'VPR succeeded' in text,
             full_check_requested='router_opts.check_route: FULL' in text,
             native_legal='Checking to ensure routing is legal' in text,
             route_sha256=sha(dest/'routed.route') if (dest/'routed.route').exists() else None,
             elapsed_seconds=time.monotonic()-start)
    (dest/'result.json').write_text(json.dumps(row,indent=2)+'\n');results.append(row)
    print(role,'rc',rc,'peak',peak,'pthread traces',row['pthread_creation_trace_count'],flush=True)
(out/'summary.json').write_text(json.dumps(dict(registration_sha256=sha(out/'registration.json'),results=results),indent=2)+'\n')
