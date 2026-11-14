#!/usr/bin/env python3
"""Registered global seed policy from pristine roots, after actual new-client validation."""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

q=D/'stable_seed_transfer_dev_01/queue'
q.mkdir(parents=True,exist_ok=False)
lock=(q/'owner.lock').open('w')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
prior=D/'seed_census_client_validation_01'
owner=read(prior/'registration.json')
roots=[('eltwise_A0',D/'native_endpoint_vector_dev_01/A0',D/'full_route_graph_cache_e695_01'),
       ('bnn_A0',D/'native_extra_opportunity_bnn_01/A0_observation',D/'full_route_graph_cache_bnn_01'),
       ('bnn_R1',D/'native_extra_opportunity_bnn_01/R1_observation',D/'full_route_graph_cache_bnn_01'),
       ('bnn_Tf',D/'native_extra_opportunity_bnn_01/Tf_observation',D/'full_route_graph_cache_bnn_01')]
cases={}
for label,state,cache in roots:
    assert read(state/'completion.json')['passed']
    for mode in ['native','paired']:
        name=label+'_'+mode
        cases[name]=dict(initial_state=str(state),full_graph_cache=str(cache),domain_mode='unrestricted' if mode=='native' else 'paired',domain_feedback=mode=='paired',seed_order='delay_rr_id',
            source_sha256={str(path):sha(path) for path in [state/'completion.json',state/'endpoint_vector.json',cache/'completion.json']})
files=[Path(__file__).resolve(),D/'run_seed_census_shadow_resource_repair.py',D/'seed_census_analysis_pool_v2.py',
    D/'native_resources_from_receipt.py',D/'pool_state_evaluator_v7.py',D/'native_resource_census_stage_01/binding.json',
    D/'native_resource_census_eltwise_02/completion.json',D/'repair_seed_order_eltwise_01/completion.json',
    D/'fused_preset_tiny_01/completion.json',D/'current_crossing_share_selector_v2.py',D/'current_resource_bundle_v2.py',
    D/'multiobjective_acceptance_v2.py',prior/'registration.json']
bound={str(path):sha(path) for path in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bound,prerequisite_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),cases=cases,
    question='Does the mechanism-supported globally fixed physical-delay/RR-ID seed policy transfer to automatic pristine A0/R1/Tf trajectories, beyond its own-current native-only control? Can native counts shadow every independent physical audit before implementing a faster consumer?',
    uniform_parameters=dict(seed_order='delay_rr_id',bundle_size=8,rank_windows=3,accepted_steps=0,minimum_margin_s=.2e-9,
        deadline='exact original rootCPD',wire='ceil original rootwire*1.001',SB_CB='no original-root increase and monotonic selected objectives'),
    controls='Native-only and paired domain/failure-release receive the same root, selector, scope, cost, full-device range, seed policy, absolute budget and acceptance. After divergence each reselects on its own state. Paired offers additional constrained searches and pays all costs; equal compute is not claimed.',
    rationale='Single-transaction seed tests gave source-invariant actual trees/vectors/costs and217183wire under one global delay/RR-ID rule; this is development evidence, not per-circuit history-best configuration selection. Complete automatic runs from unmodified Tf and strong BNN roots test first and later steps without an injected repair prefix.',
    limits=dict(native_parent_plus_child=2,combined_VPR_maximum=3,child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='New independent batch, not confirmation or an overall fixed matrix stop. Full independent Python physical/scope audits remain active; native census is shadow-only. No faster consumer or cold-route speedup is claimed. Original native-order cohort and its archive owner remain unchanged; actual client validation must pass first.'))
write(q/'status.json',dict(status='waiting_for_actual_seed_census_client_validation'))
while True:
    actual=process_identity(owner['pid'])
    if not actual or actual['state']=='Z' or actual['start_ticks']!=owner['start_ticks']:break
    time.sleep(15)
assert (prior/'completion.json').exists(),'Prior client owner ended without receipt: reconcile, no duplicate submission'
if not read(prior/'completion.json')['passed']:
    write(q/'completion.json',dict(passed=False,status='client_prerequisite_not_passed_no_actor_submitted',source_sha256=bound))
    sys.exit(1)
started=time.monotonic();results={}
for name,case in cases.items():
    assert all(sha(path)==digest for path,digest in bound.items())
    assert all(sha(path)==digest for path,digest in case['source_sha256'].items())
    command=[sys.executable,str(D/'run_seed_census_shadow_resource_repair.py'),'--initial-state',case['initial_state'],
        '--batch',str(q.parent/name),'--full-graph-cache',case['full_graph_cache'],'--bundle-size','8',
        '--domain-mode',case['domain_mode'],'--graph-echo','compact','--seed-order','delay_rr_id','--accepted-steps','0','--rank-windows','3']
    if case['domain_feedback']:command.append('--domain-feedback')
    t=time.monotonic()
    with (q/(name+'.log')).open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',case=name,pid=process.pid,start_ticks=process_identity(process.pid)['start_ticks'],command=command))
        code=process.wait()
    receipt=q.parent/name/'completion.json'
    results[name]=dict(returncode=code,passed=code==0 and receipt.exists() and read(receipt)['passed'],completion=str(receipt),complete_actor_seconds=time.monotonic()-t)
    write(q/'results.json',results)
write(q/'completion.json',dict(passed=all(result['passed'] for result in results.values()),results=results,
    source_sha256=bound,complete_development_cohort_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None,
    qualification='Local development cohort terminal only; failed branches retained, whole goal continues to mechanism/quality/runtime analysis and broader or revised experiments.'))
