#!/usr/bin/env python3
"""Real sealed-worker replay for v8; never fabricate or submit native evidence."""
import copy
import os
from pathlib import Path
import resource
import signal
import time

from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from sealed_native_pool_replay import SealedNativePoolReplay
from pool_state_evaluator_v7 import PoolStateEvaluator as IndependentEvaluator
from pool_state_evaluator_v8 import PoolStateEvaluator as CensusEvaluator
from state_resource_assurance import resource_assurance,require_publication_proof
from run_native_scope_policy_v4 import run_dir

b=D/'native_census_state_evaluator_validation_01';b.mkdir(exist_ok=False)
prior=D/'seed_census_client_validation_01';owner=read(prior/'registration.json')
files=[Path(__file__).resolve(),D/'pool_state_evaluator_v7.py',D/'pool_state_evaluator_v8.py',
    D/'state_resource_assurance.py',D/'native_resources_from_receipt.py',D/'sealed_native_pool_replay.py',
    D/'native_census_state_evaluator_preparation_01.json',prior/'registration.json']
bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bindings,prerequisite_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),
    question='Do the same actual sealed native workers produce equal full timing vectors and resource metrics through independent-per-candidate and native-count/final-independent state consumers, while refusing premature or cross-state publication?',
    native_calls=0,route_calls=0,limits=dict(active_validation_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='Real dependency waiter and read-only native evidence replay. No native jobs are submitted or restarted, and no origin receipts are modified. A component result is not an automatic repair outcome or cold speedup.'))
write(b/'status.json',dict(status='waiting_for_actual_seed_census_client_terminal'))
while True:
    actual=process_identity(owner['pid'])
    if not actual or actual['state']=='Z' or actual['start_ticks']!=owner['start_ticks']:break
    time.sleep(15)
if not (prior/'completion.json').exists() or not read(prior/'completion.json')['passed']:
    write(b/'completion.json',dict(passed=False,status='actual_client_not_passed_no_replay_started',
        native_calls=0,source_sha256=bindings,qualification='Requires diagnosis, not overall research termination.'))
    raise SystemExit(1)
assert all(sha(path)==h for path,h in bindings.items())
resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));signal.alarm(1800)
started=time.monotonic();pool=SealedNativePoolReplay(prior/'pool')
sources=dict(canonical=D/'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8/round_000/candidate_00/reuse_on_evaluation',
             native=D/'fused_resource_development_01/eltwise_A0_feedback_K8/round_000/candidate_00/reuse_on_evaluation')
workers=read(prior/'results.json');reference=D/'repair_seed_order_eltwise_01/delay_rr_id_canonical_independent_LOAD'
independent=IndependentEvaluator(pool,sources['canonical'],D/'full_route_graph_cache_e695_01',b/'independent_context')
fast=CensusEvaluator(pool,sources['canonical'],D/'full_route_graph_cache_e695_01',b/'native_context')
records=[];negative=[];final=None;first=None
for label,source in sources.items():
    worker=workers[label]['worker'];actual=Path(worker['native_directory'])/'candidate/routed.route'
    write(b/'status.json',dict(status='materializing_actual_sealed_receipt',case=label))
    source_result=fast.evaluate(run_dir(source)/'routed.route',b/(label+'_source'),
        native_resource_worker=worker,native_resource_kind='input',physical_reference=source,native_observation=worker)
    assert source_result['passed'] and source_result['physical_audit_reused']
    baseline=independent.evaluate(actual,b/(label+'_independent'),native_observation=independent.candidate_observation(worker))
    candidate=b/(label+'_native')
    result=fast.evaluate(actual,candidate,native_resource_worker=worker,native_resource_kind='candidate',
                         native_observation=fast.candidate_observation(worker))
    assert result['passed'] and baseline['passed'] and result['independent_physical_audit_deferred']
    assert not (run_dir(candidate)/'independent_audit.json').exists(), 'Counter fabricated an independent audit'
    observed=resource_assurance(candidate);expected=resource_assurance(b/(label+'_independent'))
    assert not observed['independent_physical_audit'] and expected['independent_physical_audit']
    assert all(expected['physical_metrics'][k]==v for k,v in observed['physical_metrics'].items())
    fv,bv=read(candidate/'endpoint_vector.json'),read(b/(label+'_independent')/'endpoint_vector.json')
    rv=read(reference/'endpoint_vector.json')
    assert all(fv[k]==bv[k]==rv[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
    try:require_publication_proof(candidate)
    except (AssertionError,FileNotFoundError):negative.append(label+'_premature_publication')
    else:raise AssertionError('Deferred candidate published without its own final proof')
    if first is None:first=candidate
    final=candidate
    records.append(dict(case=label,passed=True,resources=observed['resource_axes'],
        native_assurance_materialization_seconds=result['timing']['complete_evaluation_request_seconds'],
        independent_materialization_seconds=baseline['timing']['complete_evaluation_request_seconds'],
        qualification='Same sealed actual receipt; sequential component replay costs, not a formal full-algorithm speedup.'))
    write(b/'results.json',records)
    print(records[-1],flush=True)
    if label=='canonical':
        path=run_dir(candidate)/'native_resource_assurance.json';original=path.read_bytes()
        changed=read(path);changed['bound_native_view']['resource_axes']['SB_pairs']+=1;write(path,changed)
        try:
            try:resource_assurance(candidate)
            except AssertionError:negative.append('private_assurance_tamper')
            else:raise AssertionError('Changed native-count state admitted')
        finally:path.write_bytes(original)
        forged=copy.deepcopy(worker);forged['native_seed_order']='rr_id'
        try:fast.evaluate(actual,b/'forged_control',native_resource_worker=forged,native_resource_kind='candidate',native_observation=fast.candidate_observation(worker))
        except AssertionError:negative.append('forged_actual_resource_control')
        else:raise AssertionError('Forged actual control admitted')
        try:fast.evaluate(actual,b/'wrong_kind',native_resource_worker=worker,native_resource_kind='input',native_observation=fast.candidate_observation(worker))
        except AssertionError:negative.append('candidate_relabeled_input')
        else:raise AssertionError('Candidate consumed as original input')
independent.close();fast.close(final_state=final)
assert require_publication_proof(final)['publication_independently_validated']
try:require_publication_proof(first)
except (AssertionError,FileNotFoundError):negative.append('other_state_cannot_borrow_final_proof')
else:raise AssertionError('Another private state silently acquired final certification')
bad=CensusEvaluator(pool,sources['canonical'],D/'full_route_graph_cache_e695_01',b/'missing_final_context')
try:bad.close(final_state=None)
except AssertionError:negative.append('missing_selected_final_state')
else:raise AssertionError('Context sealed without a final independent state')
assert not read(b/'missing_final_context/input_seal.json')['passed']
assert all(sha(path)==h for path,h in bindings.items())
write(b/'completion.json',dict(passed=True,cases=records,negative_controls=negative,native_calls=0,route_calls=0,
    exact_vectors_and_all_native_count_fields_match_independent=True,no_independent_audit_fabricated=True,
    final_selected_state=str(final),final_independent_proof=str(final/'final_independent_validation.json'),
    other_private_states_not_published=True,complete_component_replay_seconds=time.monotonic()-started,
    complete_single_configuration_algorithm_seconds=None,
    source_sha256={str(path):sha(path) for path in [b/'registration.json',b/'results.json',b/'native_context/input_seal.json',
        b/'native_context/completion.json',b/'independent_context/completion.json',final/'final_independent_validation.json']},
    qualification='Actual completed native worker/census consumer replay. Production stateful actor and broader BNN shadow comparison still require their own integration proof. Final audit belongs only to its exact state; original native creation cost never reused as current runtime.'))
write(b/'status.json',dict(status='passed'))
print(dict(passed=True,negative_controls=negative,native_calls=0),flush=True)
