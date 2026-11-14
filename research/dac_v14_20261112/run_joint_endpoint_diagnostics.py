#!/usr/bin/env python3
"""Measure previously unavailable endpoint vectors of automatic joint repairs."""
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D, read, write, sha
from endpoint_timing_policy import decide

b=D/'joint_endpoint_diagnostics_01'
b.mkdir(exist_ok=False)
inputs={'R1_joint':D/'native_frontier_native_R1_01/runs/eltwise_layer_R',
        'Tf':D/'native_reconvergence_eltwise_dev_01/runs/eltwise_layer_Tf',
        'Tf_joint':D/'native_frontier_native_Tf_01/runs/eltwise_layer_R'}
files=[Path(__file__),D/'run_endpoint_state_analysis.py',D/'endpoint_timing_policy.py',D/'native_endpoint_vector_stage_01/binding.json']
files += [p/n for p in inputs.values() for n in ['manifest.json','routed.route','independent_audit.json']]
write(b/'registration.json',dict(status='registered_before_analysis',source_sha256={str(p):sha(p) for p in files},
    question='Full precision policy divergence and current-STA target migration after automatically generated joint transactions.',
    native_analysis_calls_planned=3,route_search_calls=0,inputs={k:str(p) for k,p in inputs.items()},
    limits=dict(process_timeout_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='New endpoint information; do not repeat route search or treat timings as formal.'))
records=[]
for role,source in inputs.items():
    cmd=[sys.executable,str(D/'run_endpoint_state_analysis.py'),'--source',str(source),'--batch',str(b/role)]
    start=time.monotonic()
    with (b/(role+'.log')).open('w') as log:
        p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
    records.append(dict(role=role,returncode=p.returncode,complete_process_seconds=time.monotonic()-start))
    write(b/'progress.json',records)
    assert p.returncode==0,'Retain failure and diagnose; never auto-repeat completed process'
    print(role,read(b/role/'completion.json')['full_precision_cpd_s'],flush=True)
comparisons={}
for role,original in [('R1',D/'native_endpoint_vector_dev_01/R1'),('Tf',b/'Tf')]:
    before=read(original/'endpoint_vector.json'); after=read(b/(role+'_joint')/'endpoint_vector.json')
    comparisons[role]={policy:decide(policy,before,after,True) for policy in ['strict','endpoint_vector']}
write(b/'policy_comparison.json',comparisons)
write(b/'completion.json',dict(status='terminal',passed=True,records=records,
    decisions={k:{p:{n:v for n,v in r.items() if n!='comparison'} for p,r in rows.items()} for k,rows in comparisons.items()},
    source_sha256={str(p):sha(p) for p in [b/'registration.json',*b.glob('*/endpoint_vector.json'),*b.glob('*/completion.json')]}))
print(read(b/'completion.json')['decisions'],flush=True)
