#!/usr/bin/env python3
"""Seal the completed stronger native control without racing the cohort archive owner."""
import collections
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import compare
from run_native_scope_policy_v4 import run_dir

b=D/'fused_resource_development_01/bnn_A0_native_only_K8'
out=D/'BNN_extended_native_menu_01.json'
assert not out.exists()
c=read(b/'completion.json');reg=read(b/'registration.json')
assert c['passed'] and all(sha(path)==digest for path,digest in c['source_sha256'].items())
assert read(b/'evaluation_context/input_seal.json')['passed'] and read(b/'pool/completion.json')['passed']
steps=read(b/'steps.json');attempts=read(b/'attempts.json')
initial=Path(c['initial_state']);final=Path(c['final_state'])
comparison=compare(read(initial/'endpoint_vector.json'),read(final/'endpoint_vector.json'))
categories=collections.Counter()
for row in read(b/'process_costs.json'):
    tag=row['tag']
    category=('native_worker_request' if tag.endswith('_native_worker_request') else
        'worker_source_materialization' if tag.endswith('_worker_state_materialization') else
        'transaction_reconstruction_audit' if tag.endswith('_transaction_audit') else
        'domain_trace_audit' if tag.endswith('_domain_audit') else
        'actual_vs_reconstructed_trees' if tag.endswith('_actual_vs_reconstructed_tree_check') else
        'candidate_materialization_and_physical_audit' if tag.endswith('_pooled_FULL_STA') else
        'selector' if tag.endswith('_current_resource_selection') else tag)
    categories[category]+=row['complete_process_seconds']
old=D/'uniform_feedback_resource_dev_01/bnn_A0_native_only_K8'
oldc=read(old/'completion.json')
files=[Path(__file__).resolve(),b/'registration.json',b/'completion.json',b/'steps.json',b/'attempts.json',
    b/'process_costs.json',b/'evaluation_context/input_seal.json',b/'pool/completion.json',
    initial/'endpoint_vector.json',final/'endpoint_vector.json',run_dir(final)/'independent_audit.json',
    old/'completion.json',D/'fused_resource_archive_queue_01/registration.json']
write(out,dict(passed=True,local_operator_stop=c['operator_stop'],accepted_steps=len(steps),attempted_scopes=len(attempts),
    final_state=str(final),CPD_ns=c['final_CPD_s']*1e9,resources=c['final_resources'],
    original_two_accept_native_resources=oldc['final_resources'],
    same_original_root_and_uniform_K8=True,root_budget=reg['anchor'],whole_endpoint_comparison=comparison,
    accepted_trajectory=[dict(round=row['round'],**row['pair']['reuse_off']['resources'],CPD_s=row['pair']['reuse_off']['CPD_s']) for row in steps],
    exclusive_workflow_seconds=dict(categories),unclassified_coordinator_seconds=c['complete_imported_algorithm_workflow_seconds']-sum(categories.values()),
    complete_imported_workflow_seconds=c['complete_imported_algorithm_workflow_seconds'],
    complete_single_configuration_algorithm_seconds=None,native_children=c['native_analysis_children'],
    legal_rejected_arms=sum(arm['status']=='legal_evaluated' and not arm['accepted'] for attempt in attempts for arm in attempt['pair'].values()),
    source_sha256={str(path):sha(path) for path in files},native_calls=0,
    qualification='Completed stronger own-current unrestricted native control, not a new guided mechanism. Further native opportunities can improve the observed joint frontier too; old86SB/two-accept point is a fixed pilot prefix, not a converged universal baseline. New implementation also preserves native serialized tree order, so prefix extension and representation versions remain explicit. Actor is individually sealed; the actual registered downstream archive owner will add this and the paired actor after cohort terminal, avoiding competing writers. Resource minima and full cold-route time are not claimed.'))
print(dict(accepted=len(steps),resources=c['final_resources'],workflow_seconds=c['complete_imported_algorithm_workflow_seconds'],costs=dict(categories)),flush=True)
