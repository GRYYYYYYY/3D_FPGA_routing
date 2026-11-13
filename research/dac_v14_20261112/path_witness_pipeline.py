#!/usr/bin/env python3
"""Serialize diagnostic build, native reproduction and physical checks after existing controls."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D, read, write, sha, source_files


def main():
    q=D/'path_witness_pipeline_01';q.mkdir(exist_ok=False)
    lock=(D/'path_witness_pipeline.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    scripts=['prepare_path_witness_candidate.py','run_path_witness.py','verify_path_witnesses.py','analyze_path_witness.py',
        'aggregate_native_reconvergence.py','analyze_native_reconvergence_v2.py','retained_prefix_workflow.py','routing_log_metrics.py',
        'path_witness_experiment_01.json','path_witness_implementation.json','path_witness_unbuilt.patch','path_witness_unit_01/validation.json']
    bindings={str(D/n):sha(D/n) for n in scripts};sources=source_files()
    identity=dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
        dependency_pid=400835,dependency_start_ticks='1932548087',dependency_batch='native_reconvergence_extension_pipeline_01',
        bindings=bindings,mutable_source_sha256=sources,retries=0,research_complete=False)
    write(q/'identity.json',identity);write(q/'state.json',dict(status='waiting_exact_reconvergence_extension_owner',time=time.time()))
    proc=Path('/proc/400835/stat')
    while proc.exists():
        try:f=proc.read_text().split(') ',1)[1].split()
        except FileNotFoundError:break
        if f[19]!=identity['dependency_start_ticks'] or f[0]=='Z':break
        time.sleep(15)
    try:
        dep=D/identity['dependency_batch'];assert (dep/'completion.json').exists()
        for c in ['spmv','softmax','bnn']:
            b=D/f'native_reconvergence_{c}_dev_01';assert read(b/'input_seal.json')['passed'] and (b/'completion.json').exists()
        steps=[
            ('aggregate_native_controls',[sys.executable,str(D/'aggregate_native_reconvergence.py'),'--out','native_reconvergence_circuit_summary.json']),
            ('build_path_witness',[sys.executable,str(D/'prepare_path_witness_candidate.py'),'--out','path_witness_candidate_01']),
            ('native_path_witness',[sys.executable,str(D/'run_path_witness.py'),'--out','path_witness_eltwise_dev_01']),
            ('verify_physical_paths',[sys.executable,str(D/'verify_path_witnesses.py'),str(D/'path_witness_eltwise_dev_01'),'--out','path_witness_physical_audit_01']),
            ('analyze_path_witness',[sys.executable,str(D/'analyze_path_witness.py'),str(D/'path_witness_eltwise_dev_01'),'--audit',str(D/'path_witness_physical_audit_01')])]
        for label,cmd in steps:
            for p,h in bindings.items():assert sha(p)==h,p
            assert sources==source_files(),'Mutable diagnostic source changed; preserve owner and inspect before recovery'
            write(q/'state.json',dict(status=label,time=time.time()))
            with (q/(label+'.log')).open('w') as log:
                r=subprocess.run(cmd,cwd=D.parents[1],stdout=log,stderr=subprocess.STDOUT)
            if r.returncode:raise RuntimeError(f'{label} returncode {r.returncode}; inspect log and preserved artifacts, no automatic retry')
        write(q/'completion.json',dict(status='diagnostic_pipeline_terminal_not_research_complete',time=time.time()))
        write(q/'state.json',dict(status='completed',time=time.time()))
    except Exception as e:
        write(q/'state.json',dict(status='requires_main_model_diagnosis',error=str(e),time=time.time(),research_blocked=False))
        raise


if __name__=='__main__':main()
