#!/usr/bin/env python3
"""Use immutable stage02 for measured-only tracing and independent validation."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D, read, write, sha


def main():
    lock=(D/'path_witness_pipeline.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stage=D/'path_witness_candidate_02';binding=read(stage/'binding.json')
    files=['run_path_witness_v2.py','verify_path_witnesses_v2.py','analyze_path_witness_v2.py',
        'retained_prefix_workflow.py','routing_log_metrics.py','analyze_native_reconvergence_v2.py','path_witness_v2_experiment_01.json']
    bindings={str(D/n):sha(D/n) for n in files};bindings[str(stage/'binding.json')]=sha(stage/'binding.json')
    bindings[str(stage/'bin/vpr')]=binding['binary_sha256']
    bindings.update({str(stage/'src'/p):h for p,h in binding['source_sha256'].items()})
    q=D/'path_witness_v2_pipeline_01';q.mkdir(exist_ok=False)
    write(q/'identity.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
        bindings=bindings,retries=0,mutable_cpp_source_pinned=False,research_complete=False))
    steps=[
        ('native_measured_witness',[sys.executable,str(D/'run_path_witness_v2.py'),'--out','path_witness_eltwise_dev_02','--stage',stage.name]),
        ('verify_complete_paths',[sys.executable,str(D/'verify_path_witnesses_v2.py'),str(D/'path_witness_eltwise_dev_02'),'--out','path_witness_physical_audit_02']),
        ('analyze_complete_witness',[sys.executable,str(D/'analyze_path_witness_v2.py'),str(D/'path_witness_eltwise_dev_02'),'--audit',str(D/'path_witness_physical_audit_02')])]
    try:
        for label,cmd in steps:
            for p,h in bindings.items():assert sha(p)==h,p
            write(q/'state.json',dict(status=label,time=time.time()))
            with (q/(label+'.log')).open('w') as log:
                r=subprocess.run(['prlimit','--as=68719476736','--core=0','--']+cmd,cwd=D.parents[1],stdout=log,stderr=subprocess.STDOUT)
            if r.returncode:raise RuntimeError(f'{label} returncode {r.returncode}; inspect exact preserved step, no automatic retry')
        write(q/'completion.json',dict(status='measured_witness_pipeline_terminal_not_research_complete',time=time.time()))
        write(q/'state.json',dict(status='completed',time=time.time()))
    except Exception as e:
        write(q/'state.json',dict(status='requires_main_model_diagnosis',error=str(e),time=time.time(),research_blocked=False))
        raise


if __name__=='__main__':main()
