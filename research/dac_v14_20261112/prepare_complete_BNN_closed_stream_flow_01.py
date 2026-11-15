"""Register a new closed-metadata/streaming full configuration; old queues freeze."""
import copy
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

root=D/'complete_BNN_closed_stream_flow_01'
root.mkdir(exist_ok=False);(root/'configs').mkdir()
proofs=[D/'existing_streaming_loader_current_validation_01/completion.json',
        D/'BNN_complete_cache_boundary_01/completion.json',
        D/'complete_resource_timing_equivalence_validation_01/completion.json']
for path in proofs:
    p=read(path)
    assert p['passed'] and all(sha(f)==h for f,h in p['source_sha256'].items())
prepared=D/'closed_cache_stream_source_preparation_01'
manifest=read(prepared/'manifest.json')
assert read(prepared/'cli_smoke.json')['passed']
for row in manifest['scripts']:
    assert sha(D/row['original'])==row['original_sha256']
    assert sha(D/row['variant'])==row['variant_sha256']
original=read(D/'complete_BNN_joint_index_flow_01/configs/bnn_native_joint_indexes.json')
config=copy.deepcopy(original)
config['endpoint_loader_strategy']='existing_streaming_v2_all_observations'
config['metadata_cache_strategy']='explicit_same_measured_flow_only'
files=[Path(__file__).resolve(),D/'prepare_closed_cache_stream_sources_v1.py',
       D/'endpoint_timing_policy_streaming_v2.py',D/'compare_complete_BNN_closed_stream_v1.py',
       D/'queue_complete_BNN_closed_stream_flow_01.py',prepared/'manifest.json',prepared/'sources.diff',
       prepared/'cli_smoke.json',*proofs,*[D/r['variant'] for r in manifest['scripts']]]
config['input_sha256'].update({str(f):sha(f) for f in files})
path=root/'configs/bnn_native_closed_stream.json';write(path,config)
assert config['phase_binary_sha256']==original['phase_binary_sha256']
assert config['route_command']==original['route_command']
assert all(config['input_sha256'].get(k)==v for k,v in original['input_sha256'].items())
write(root/'plan.json',dict(fixed_order=['bnn_native_closed_stream'],config=str(path),
    predecessor=str(D/'complete_BNN_joint_index_flow_01/queue'),prepared_files=[str(f) for f in files],
    qualification='One new full native BNN engineering configuration after the already registered one-pass index control, acquiring the same serial slot. Reuse original architecture/RRG/BLIF/pack/place and all three frozen phase binaries/count8/1.01/seed11/current-state resource and timing selection/envelopes. Generate all audit/full/query payloads inside the measured command and require actual metadata consumers to resolve there; replace legacy all-record endpoint loaders at four observation scripts with existing validated streaming v2. Fresh-route loading already used v2. These are two implementation changes versus one-pass legacy-path control; no one-factor parser speedup claim. All actual native/FULL/STA/physical/capacity/scope/rollback/seal gates and numeric precision unchanged; v2 adds native pin count and no-trailing-row guards. Prototype stream_v1 is explicitly not used. No prototype cache or historical route/candidate/query import. Full actual cost/quality stays inseparable. Compare every actual state/request/native protocol and payload against available actual controls before any same-behavior cost claim. Keep failures/divergences and denominator1; one shared-host observation, no statistical speedup. All earlier jobs/dependencies/versions untouched.'))
write(root/'preflight.json',dict(passed=True,native_calls=0,registered_roles=1,
    parser_actual_vectors_exact=4,existing_stronger_guards_preserved=True,
    source_derivation_manifest=str(prepared/'manifest.json'),
    all_11_CLI_smoke_passed=True,actual_native_flow_validated=False,
    source_sha256={str(f):sha(f) for f in [path,root/'plan.json',*files]}))
print(dict(prepared=True,root=str(root),native_calls=0),flush=True)
