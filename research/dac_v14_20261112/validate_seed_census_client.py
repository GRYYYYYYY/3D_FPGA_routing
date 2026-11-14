#!/usr/bin/env python3
"""One actual native pool after the registered quality cohort, including mutation/cache guards."""
import copy
import os
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import NativeAnalysisPool,process_identity
from native_resources_from_receipt import bound_native_resources
from actual_route_tree_identity import tree_identity
from endpoint_timing_policy_streaming_v2 import load
from run_native_scope_policy_v4 import run_dir

b=D/'seed_census_client_validation_01'
b.mkdir(exist_ok=False)
prior=D/'fused_resource_development_01/queue'
owner=read(prior/'registration.json')
files=[Path(__file__).resolve(),D/'seed_census_analysis_pool_v2.py',D/'native_resources_from_receipt.py',
    D/'native_resource_census_stage_01/binding.json',D/'native_resource_census_eltwise_02/completion.json',prior/'registration.json']
bound={str(path):sha(path) for path in files}
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bound,prerequisite_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),
    question='Do frozen per-pool seed/census controls reach the actual child, remain in receipt/cache identity, and reject mutation or forged resource views before incorrect reuse?',
    limits=dict(this_chain_parent_plus_child=2,combined_native_VPR_maximum=3,child_seconds=1800,memory_bytes=64*1024**3),
    qualification='Real dependency queue: waits for the original cohort owner to terminate before starting another loaded native parent. No original actor is interrupted or changed. This validates the new client/native count interface; a fast algorithm consumer is still separate.'))
write(b/'status.json',dict(status='waiting_for_registered_quality_cohort_terminal'))
while True:
    actual=process_identity(owner['pid'])
    if not actual or actual['state']=='Z' or actual['start_ticks']!=owner['start_ticks']:break
    time.sleep(15)
assert (prior/'completion.json').exists(),'Terminal owner without receipt requires reconciliation, not a blind restart'
assert all(sha(path)==digest for path,digest in bound.items())
assert read(D/'native_resource_census_eltwise_02/completion.json')['passed']
started=time.monotonic()
sources=dict(canonical=D/'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8/round_000/candidate_00/reuse_on_evaluation',
             native=D/'fused_resource_development_01/eltwise_A0_feedback_K8/round_000/candidate_00/reuse_on_evaluation')
source=run_dir(sources['canonical'])
command=list(read(source/'manifest.json')['command'])
command[0]=str(D/'native_resource_census_stage_01/bin/vpr')
if '--route'in command:command.remove('--route')
for flag,name in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:command[command.index(flag)+1]=str(source/name)
if '--verify_route_file_switch_id'not in command:command+=['--verify_route_file_switch_id','on']
static=[Path(command[1]),Path(command[2]),Path(command[command.index('--read_rr_graph')+1]),source/'packed.net',source/'placed.place']
guard=D.parents[1]/'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard'
tx=D/'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8/round_001/candidate_00'
reference=D/'repair_seed_order_eltwise_01/delay_rr_id_canonical_independent_LOAD'
expected_tree=tree_identity(run_dir(reference)/'routed.route')
expected_vector=read(reference/'endpoint_vector.json')
pool=NativeAnalysisPool(b/'pool',command,static,guard,seed_order='delay_rr_id',native_census=True)
results={};negative=[]
try:
    for label,state in sources.items():
        worker=pool.analyze(run_dir(state)/'routed.route',echo=False,native_request=tx/'request.txt',crossing_domain=tx/'domain.txt',
            domain_failure_release=True,candidate_full_sta=True,reuse=False)
        assert worker['passed'] and worker['native_seed_order']=='delay_rr_id' and worker['native_resource_census_requested']
        candidate=Path(worker['native_directory'])/'candidate'
        assert tree_identity(candidate/'routed.route')==expected_tree
        vector=load(candidate/'native_sta_frontier.jsonl')
        assert all(vector[key]==expected_vector[key] for key in ['cpd_s','setup','hold','constraints_sha256'])
        views={kind:bound_native_resources(worker,kind) for kind in ['input','candidate','restored_source']}
        assert views['input']['physical_metrics']==views['restored_source']['physical_metrics']
        assert views['candidate']['resource_axes']==dict(wirelength=217183,SB_pairs=24,CB_sources=965)
        results[label]=dict(worker=worker,native_resource_views=views)
        write(b/'results.json',results)
    worker=results['canonical']['worker']
    for key,value in [('native_seed_order','rr_id'),('native_resource_census_requested',False)]:
        forged=copy.deepcopy(worker);forged[key]=value
        try:bound_native_resources(forged,'candidate')
        except AssertionError:negative.append('forged_'+key)
        else:raise AssertionError('Forged resource control accepted')
    for attribute,value in [('seed_order','rr_id'),('native_census',False)]:
        original=getattr(pool,attribute);setattr(pool,attribute,value)
        try:
            try:pool.analyze(run_dir(sources['canonical'])/'routed.route',echo=False,native_request=tx/'request.txt',crossing_domain=tx/'domain.txt',domain_failure_release=True,candidate_full_sta=True)
            except AssertionError:negative.append('mutation_'+attribute)
            else:raise AssertionError('Mutated frozen control reached a native submission/cache hit')
        finally:setattr(pool,attribute,original)
    before=len(pool.jobs)
    reused=pool.analyze(run_dir(sources['canonical'])/'routed.route',echo=False,native_request=tx/'request.txt',crossing_domain=tx/'domain.txt',domain_failure_release=True,candidate_full_sta=True)
    assert reused['reused'] and len(pool.jobs)==before and reused['native_child_seconds'] is None
    # The resource view consumes the immutable original receipt, not a reused timing wrapper.
    assert bound_native_resources(worker,'candidate')['resource_axes']['wirelength']==217183
finally:pool.close()
assert all(sha(path)==digest for path,digest in bound.items())
write(b/'completion.json',dict(passed=True,actual_fixed_policy_census_reached_native_children=True,
    source_representation_invariance=True,bound_native_resource_counts_valid=True,negative_controls=negative,
    native_children=len(pool.jobs),exact_cache_reuses=len(pool.reuse),complete_component_validation_seconds=time.monotonic()-started,
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),b/'registration.json',b/'results.json',b/'pool/completion.json']},
    qualification='Actual parent/child/client integration after cohort end, not algorithm QoR or cold timing. Frozen controls rejected before submission/cache; forged views rejected before counting. Exact cache reuse borrows no original time. Counts remain native assurance, with independent physical proof from the separately validated exact candidate.'))
print(dict(passed=True,native_children=len(pool.jobs),negative_controls=negative),flush=True)
