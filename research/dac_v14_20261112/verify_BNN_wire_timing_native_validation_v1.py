"""Actual native legality, wire-budget outcome and preregistered predictions."""
import json
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof
from endpoint_timing_policy_streaming_v2 import compare
from multiobjective_acceptance_v2 import decide

root=D/'BNN_wire_timing_native_validation_01'
assert not (root/'verification.json').exists()
plan=read(root/'plan.json');execution=read(root/'queue/execution_receipt.json')
assert all(sha(f)==h for f,h in execution['source_sha256'].items())
proposal=Path(plan['construction']);prediction=Path(plan['prediction'])
construction=read(proposal/'completion.json');predicted=read(prediction/'completion.json')
assert construction['passed'] and predicted['passed'] and predicted['prediction_registered_before_native_LOAD']
assert sha(plan['candidate_route'])==plan['candidate_route_sha256']==construction['candidate_sha256']
source=Path(plan['source_state']);source_run=run_dir(source)
before=read(source/'endpoint_vector.json');before_axes=require_publication_proof(source)['resource_axes']
files=[Path(__file__).resolve(),root/'plan.json',root/'queue/execution_receipt.json',
       proposal/'completion.json',prediction/'completion.json',prediction/'connection_predictions.json',
       prediction/'slack_screen.json',source/'completion.json',source/'endpoint_vector.json',source_run/'routed.route']
measurement=read(root/'measurement/completion.json')
assert measurement['returncode']==execution['returncode']
assert not measurement['live_descendants_after_command_exit']
files.append(root/'measurement/completion.json')
state=root/'candidate_evaluation';actual_legal=execution['command_passed']
outcome=dict(status='native_or_independent_gate_failed',quality=None,
             returncode=execution['returncode'],policy_accepted=False)
if actual_legal:
    closed=read(state/'completion.json')
    assert closed['passed'] and all(closed['checks'].values())
    assert closed['native_analysis_calls']==1 and closed['route_search_calls']==0
    assert read(state/'input_seal.json')['passed']
    reg=read(state/'registration.json')
    assert not reg['observation_only'] and reg['candidate_route']==plan['candidate_route']
    assert all(sha(f)==h for f,h in reg['source_sha256'].items())
    run=run_dir(state);manifest=read(run/'manifest.json')
    assert manifest['metrics']['native_full_check_passed']
    assert sha(manifest['command'][0])==plan['candidate_STA_binary_sha256']
    assert sha(run/'routed.route')==construction['candidate_sha256']
    assert sha(run/'packed.net')==sha(source_run/'packed.net')
    assert sha(run/'placed.place')==sha(source_run/'placed.place')
    for key in ['packed.net','placed.place','routed.route']:
        assert sha(run/key)==manifest['outputs'][key]['sha256']
    axes=require_publication_proof(state)['resource_axes']
    vector=read(state/'endpoint_vector.json');endpoints=compare(before,vector)
    assert endpoints['compatible']
    decision=decide('resources_under_timing',before,vector,before_axes,axes,
        cpd_limit_s=plan['CPD_limit_s'],resource_limits=plan['resource_limits'],
        native_valid=True,transaction_complete=True,resource_objectives=('wirelength',))
    predicted_rows=read(prediction/'connection_predictions.json')
    wanted={(r['net'],r['pin']) for r in predicted_rows};native={}
    for line in (run/'native_sta_frontier.jsonl').open():
        row=json.loads(line)
        if row.get('type')=='pin' and (row['net'],row['pin']) in wanted:
            native[row['net'],row['pin']]=row
    assert set(native)==wanted
    checks=[dict(net=r['net'],pin=r['pin'],predicted_s=r['after_s'],
                  actual_native_s=native[r['net'],r['pin']]['native_net_delay_s'],
                  exact=r['after_s']==native[r['net'],r['pin']]['native_net_delay_s']) for r in predicted_rows]
    write(root/'actual_prediction_checks.json',checks)
    screen=read(prediction/'slack_screen.json')
    model_counterexample=screen['model_screen_passed'] and (
        not endpoints['cpd_nonworse'] or endpoints['hold_violation_regressions']>0)
    outcome=dict(status='legal_evaluated',evaluation=str(state),CPD_ns=vector['cpd_s']*1e9,
        resources=axes,policy_accepted=decision['accepted'],decision=decision,endpoint_comparison=endpoints,
        structural_counts_match_actual=axes==construction['structural_full_route_resources'],
        all_34_predicted_connection_delays_exact=all(r['exact'] for r in checks),
        model_screen_counterexample=model_counterexample,actual_binary_sha256=sha(manifest['command'][0]),
        independent_complete_physical_audit=True,complete_single_configuration_seconds=None)
    files += [state/'completion.json',state/'registration.json',state/'input_seal.json',state/'endpoint_vector.json',
              run/'manifest.json',run/'independent_audit.json',run/'native_sta_frontier.jsonl',root/'actual_prediction_checks.json']
else:
    if (state/'completion.json').exists():
        outcome['actual_failure_receipt']=read(state/'completion.json');files.append(state/'completion.json')
write(root/'verification.json',dict(passed=True,registered_roles=1,legal_native_observations=int(actual_legal),
    failed_roles=int(not actual_legal),native_calls_new=0,outcome=outcome,
    actual_imported_candidate_evaluation_seconds=measurement['complete_command_wall_seconds'],
    actual_sampled_tree_PSS_peak_kib=measurement['sampled_tree_PSS_peak_kib'],
    actual_missing_memory_observations=measurement['missing_memory_observations'],
    complete_single_configuration_seconds=None,committed_to_original_actor=False,
    source_sha256={str(f):sha(f) for f in files},
    qualification='Exactly one actual candidate LOAD with the same candidate-STA binary as the source, fresh FULL/STA and independent complete physical audit. Scope, route/input hashes and original CPD/resource/hold envelopes are explicit. Policy accepts wire decrease under fixed timing/vertical caps, allowing setup tradeoffs; actual endpoint changes are retained. Model/delay or structural count disagreement is retained as a counterexample without rewriting actual legal quality or repeating native execution. Failure denominator1 is retained. Imported-candidate LOAD cost includes its actual work; original routing/resource/timing branches, terminal selection, construction and prediction are upstream and not a complete fresh configuration. No7933s or other old whole time is attached to this candidate. Original actors and archive remain unchanged until a separate explicit archival step.'))
print(dict(passed=True,legal=actual_legal,outcome={k:v for k,v in outcome.items() if k in
    ['status','CPD_ns','resources','policy_accepted','all_34_predicted_connection_delays_exact','model_screen_counterexample']}),flush=True)
