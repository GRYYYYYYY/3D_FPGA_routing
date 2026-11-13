#!/usr/bin/env python3
"""One owner: await the exact existing scope batch, verify it, then run registered controls."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D, read, write, sha


def main():
    q=D/'native_reconvergence_extension_pipeline_01';q.mkdir(exist_ok=False)
    lock=(D/'native_reconvergence_extension_pipeline.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    scripts=['analyze_post_legal_freeze.py','analyze_native_reconvergence_v2.py','run_post_legal_freeze.py','run_native_reconvergence_extension.py','analyze_native_reconvergence_extension.py',
             'retained_prefix_workflow.py','native_reconvergence_extension_01.json']
    bindings={str(D/n):sha(D/n) for n in scripts}
    identity=dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
        dependency_pid=350768,dependency_start_ticks='1932537829',dependency_batch='post_legal_freeze_eltwise_dev_01',
        bindings=bindings,retries=0,research_complete=False)
    write(q/'identity.json',identity)
    write(q/'state.json',dict(status='waiting_exact_existing_freeze_owner',time=time.time()))
    proc=Path('/proc/350768/stat')
    while proc.exists():
        try:fields=proc.read_text().split(') ',1)[1].split()
        except FileNotFoundError:break
        if fields[19]!=identity['dependency_start_ticks'] or fields[0]=='Z':break
        time.sleep(15)
    try:
        dep=D/identity['dependency_batch'];assert read(dep/'input_seal.json')['passed']
        assert (dep/'completion.json').exists()
        for p,h in bindings.items():assert sha(p)==h,p
        root=D.parents[1]
        steps=[('analyze_freeze',[sys.executable,str(D/'analyze_post_legal_freeze.py'),str(dep)])]
        for circuit in ['spmv','softmax','bnn']:
            name='native_reconvergence_'+circuit+'_dev_01'
            steps.extend([(circuit+'_count2',[sys.executable,str(D/'run_native_reconvergence_extension.py'),'--out',name,'--circuit',circuit]),
                (circuit+'_analysis',[sys.executable,str(D/'analyze_native_reconvergence_extension.py'),str(D/name)])])
        for label,cmd in steps:
            for p,h in bindings.items():assert sha(p)==h,p
            write(q/'state.json',dict(status=label,time=time.time()))
            with (q/(label+'.log')).open('w') as log:
                r=subprocess.run(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT)
            if r.returncode:raise RuntimeError(f'{label} returncode {r.returncode}; inspect preserved log, no automatic retry')
        write(q/'completion.json',dict(status='pipeline_terminal_not_research_complete',time=time.time()))
        write(q/'state.json',dict(status='completed',time=time.time()))
    except Exception as e:
        write(q/'state.json',dict(status='requires_main_model_diagnosis',error=str(e),time=time.time(),research_blocked=False))
        raise


if __name__=='__main__':main()
