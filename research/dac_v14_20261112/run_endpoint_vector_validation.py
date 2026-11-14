#!/usr/bin/env python3
"""Evaluate endpoint acceptance on actual previously legal CPD plateaus."""
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D, read, write, sha
from endpoint_timing_policy import load, decide

batch = D / 'native_endpoint_vector_dev_01'
batch.mkdir(exist_ok=False)
inputs = dict(R1=D/'native_reconvergence_eltwise_dev_01/runs/eltwise_layer_R1',
              R1_plateau=D/'postcoordination_R1_native_01/runs/eltwise_layer_R',
              A0=D/'native_reconvergence_eltwise_dev_01/runs/eltwise_layer_A0',
              A0_plateau=D/'native_frontier_native_A0_01/runs/eltwise_layer_R')
files = [Path(__file__), D/'run_endpoint_state_analysis.py', D/'endpoint_timing_policy.py',
         D/'endpoint_timing_policy_validation_01.json', D/'native_endpoint_vector_stage_01/binding.json',
         D/'native_endpoint_vector_experiment_01.json']
files += [p/name for p in inputs.values() for name in ['manifest.json','routed.route','independent_audit.json']]
binding = {str(p):sha(p) for p in files}
write(batch/'registration.json',dict(status='registered_before_analysis',source_sha256=binding,
      input_runs={n:str(p) for n,p in inputs.items()},native_analysis_calls_planned=5,route_search_calls=0,
      pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
      question='Read-only observer neutrality plus endpoint/domain vector comparison for completed R1/A0 legal CPD plateaus. No repeated route search.'))
records=[]
for role,source,off in [('R1_off',inputs['R1'],True)]+[(k,p,False) for k,p in inputs.items()]:
    out=batch/role
    command=[sys.executable,str(D/'run_endpoint_state_analysis.py'),'--source',str(source),'--batch',str(out)]
    if off:command.append('--trace-off')
    started=time.monotonic()
    with (batch/(role+'.stdout.log')).open('w') as stream:
        process=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
    records.append(dict(role=role,returncode=process.returncode,wrapper_process_seconds=time.monotonic()-started))
    write(batch/'progress.json',records)
    assert process.returncode==0,'Preserve completed evaluation, inspect failure; do not repeat automatically'
    print(role,read(out/'completion.json')['full_precision_cpd_s'],flush=True)
off,on=read(batch/'R1_off/completion.json'),read(batch/'R1/completion.json')
assert off['passed'] and on['passed'] and off['cpd_ns']==on['cpd_ns'] and off['route_body_sha256']==on['route_body_sha256']
decisions={}
for role in ['R1','A0']:
    before=load(batch/role/'runs/state/native_sta_frontier.jsonl')
    after=load(batch/(role+'_plateau')/'runs/state/native_sta_frontier.jsonl')
    decisions[role]={policy:decide(policy,before,after,True) for policy in ['strict','endpoint_vector']}
assert all(sha(p)==h for p,h in binding.items())
write(batch/'policy_comparison.json',dict(passed=True,decisions=decisions,
      observer_off_on_neutral=True,native_analysis_calls=5,route_search_calls=0,
      source_sha256={str(p):sha(p) for p in [batch/'registration.json',*list(batch.glob('*/endpoint_vector.json')),
          *list(batch.glob('*/completion.json'))]},
      qualification='Policy diagnostics on preserved legal states. R1 plateau was the prior physical-vector candidate; it is not automatically accepted under endpoint-vector semantics. Not yet autonomous branch trajectories.'))
write(batch/'completion.json',dict(status='endpoint_vector_validation_terminal',passed=True,records=records,
      native_analysis_calls=5,route_search_calls=0,decisions={role:{policy:dict(accepted=r['accepted'],reason=r['reason'],
          setup_improved=r['comparison'].get('setup_improved'),setup_regressed=r['comparison'].get('setup_regressed'))
          for policy,r in d.items()} for role,d in decisions.items()}))
print(read(batch/'completion.json')['decisions'],flush=True)
