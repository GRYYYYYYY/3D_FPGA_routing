#!/usr/bin/env python3
"""Mock continuation sequencing and failure preservation; no solver runs."""
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import continue_strict_study as continuation


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data))


def fixture(root,fail):
    continuation.BASE=root
    circuits=['attention_layer','bnn','eltwise_layer','gemm_layer','softmax','spmv']
    families=['sb','cb_o','hybrid_o']
    write(root/'benchmark_protocol.json',{'training':circuits,'architectures':families})
    write(root/'training_jobs.json',{'jobs':[{}]*594,'source_sha256':{}})
    for circuit in circuits:
        for family in families:
            d=root/'training_cases'/f'{circuit}_{family}'
            write(d/'result.json',dict(status='completed',registered_routes=33,legal_routes=0,failed_routes=33))
            write(d/'audit_summary.json',dict(passed=True,registered_route_count=33,legal_count=0,
                  failed_count=33,legal=[],failed=[{}]*33))
    stem='_'.join(circuits);d=root/'training_invocations'
    write(d/(stem+'.json'),dict(complete_suite=True,unstarted_pairs=[],results=[{'status':'completed'}]*18))
    write(d/(stem+'_input_integrity.json'),{'passed':True})
    for name,value in [('p1_training_preflight_state.json',{'status':'passed'}),
                       ('p1_training_partition_weight_review.json',{'status':'resolved'}),
                       ('seccomp_guard_unit_validation.json',{}),('execution_contract.json',{}),
                       ('execution_resource_amendment.json',{}),('runtime_dependency_binding.json',{}),
                       ('partition_balance_sensitivity_protocol.json',{})]:write(root/name,value)
    calls=[]
    def run(cmd,**kwargs):
        script=Path(cmd[1]).name;calls.append(script)
        if fail and script=='run_seccomp_full_workload_pilot.py':raise subprocess.CalledProcessError(1,cmd)
        if script=='select_flatland_configs.py':write(root/'selected_configs.json',{'status':'frozen_before_heldout'})
        if script=='analyze_flatland_training.py':write(root/'training_analysis/summary.json',{'status':'all_registered_training_attempts_accounted'})
        if script=='run_seccomp_full_workload_pilot.py':write(root/'seccomp_full_workload_validation.json',{'status':'passed'})
    values=iter([1234,None])
    real_read_bytes=Path.read_bytes
    def read_bytes(path):
        if str(path)=='/proc/1234567/cmdline':
            return b'python\0/tmp/run_flatland_training.py\0'+b'\0'.join(x.encode() for x in circuits)+b'\0'
        return real_read_bytes(path)
    # Owner identity, command line and child executions are synthetic.
    with patch.object(continuation,'identity',side_effect=lambda _:next(values,None)),\
         patch.object(Path,'read_bytes',read_bytes),patch.object(continuation.subprocess,'run',side_effect=run):
        if fail:
            try:continuation.main(1234567,1234)
            except subprocess.CalledProcessError:pass
            else:raise AssertionError('pilot failure must stop the chain')
        else:continuation.main(1234567,1234)
    state=json.loads((root/'strict_continuation/state.json').read_text())
    if fail:
        assert state['status']=='needs_diagnosis' and 'run_flatland_evaluation.py' not in calls
        assert len(state['completed_stages'])==4
    else:
        assert state['status']=='awaiting_scientific_and_integrity_closure'
        assert len(calls)==len(state['completed_stages'])==14
    return calls


def main():
    with TemporaryDirectory(prefix='continuation_sequence_test_') as tmp:
        for fail in (False,True):
            root=Path(tmp)/str(fail);root.mkdir();fixture(root,fail)
    print('continuation sequencing runs all 14 mocked stages and stops before heldout on pilot failure')


if __name__=='__main__':main()
