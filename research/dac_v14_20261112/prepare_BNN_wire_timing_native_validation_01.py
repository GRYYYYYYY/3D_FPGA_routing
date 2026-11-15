"""Freeze one concrete branch-composition LOAD; no native search is submitted here."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from run_native_scope_policy_v4 import run_dir

root=D/'BNN_wire_timing_native_validation_01';root.mkdir(exist_ok=False)
proposal=D/'BNN_wire_timing_composition_01';prediction=D/'BNN_wire_composition_timing_prediction_01'
proofs=[proposal/'completion.json',prediction/'completion.json',D/'terminal_wire_selector_merge_validation_01/completion.json']
for path in proofs:
    proof=read(path)
    assert proof['passed'] and all(sha(f)==h for f,h in proof['source_sha256'].items())
    if 'artifact_sha256' in proof:
        assert all(sha(path.parent/n)==h for n,h in proof['artifact_sha256'].items())
constructed=read(proofs[0]);assert constructed['status']=='complete_structural_candidate_pending_native_FULL_STA'
source=Path(constructed['state']);run=run_dir(source);vector=read(source/'endpoint_vector.json')
binary=D/'timing_cone_stage_03/bin/vpr';binding=D/'timing_cone_stage_03/binding.json'
assert sha(binary)==read(binding)['binary_sha256']==sha(read(run/'manifest.json')['command'][0])
files=[Path(__file__).resolve(),D/'queue_BNN_wire_timing_native_validation_01.py',
       D/'verify_BNN_wire_timing_native_validation_v1.py',D/'run_independent_timing_cone_analysis_stream_v1.py',
       D/'endpoint_timing_policy_streaming_v2.py',D/'multiobjective_acceptance_v2.py',D/'state_resource_assurance.py',
       D/'measure_process_tree_v1.py',binary,binding,*proofs,proposal/'candidate.route',
       prediction/'connection_predictions.json',prediction/'slack_screen.json']
plan=dict(fixed_order=['composed_candidate_LOAD'],predecessor=str(D/'complete_BNN_closed_stream_flow_01/queue'),
    source_state=str(source),source_run=str(run),construction=str(proposal),prediction=str(prediction),
    candidate_route=constructed['candidate_route'],candidate_route_sha256=constructed['candidate_sha256'],
    full_graph_cache=str(D/'complete_resource_timing_full_flow_01/bnn_native/flow/resource_flow/full_graph_cache'),
    CPD_limit_s=vector['cpd_s'],resource_limits=constructed['original_resources'],
    candidate_STA_binary_sha256=sha(binary),prepared_files=[str(f) for f in files],
    qualification='One fixed concrete terminal-wire/timing composite candidate, chosen before this native evaluation, with no new search. The terminal rule was developed on a completed native resource menu: equal vertical resources, lower wire, exact current setup/CPD non-regression and no increased hold violation; deterministic least-wire choice. Composition changes3nets disjoint from17timing-modified nets, checks full node capacity and unchanged other-net bytes. Structural2059607wire/82SB/5062CB and34binary32 predictions are not native legal quality. Original source CPD13.228145689936355ns and source resource envelope are fixed for wire-under-timing acceptance; full actual endpoint changes retained, no CPD tolerance or endpoint-vector requirement inferred. Use source-matched d7candidate-STA binary with fresh FULL/STA/independent physical audit/input seals and compare all34predictions. No original actor commit or whole-cost splice. Wait until every already registered engineering predecessor terminal, then take common serial slot; all prior dependencies/owners unchanged. Imported candidate evaluation only, not a new cold full configuration or independent test sample; retain failures/counterexamples and denominator1.')
write(root/'plan.json',plan)
write(root/'preflight.json',dict(passed=True,native_calls=0,registered_roles=1,
    candidate_unchanged=sha(plan['candidate_route'])==plan['candidate_route_sha256'],
    actual_source_observer_binary_matched=True,source_sha256={str(f):sha(f) for f in [root/'plan.json',*files]}))
print(dict(prepared=True,root=str(root),native_calls=0),flush=True)
