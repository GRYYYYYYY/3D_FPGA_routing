"""Fix circuit/layout selection and source rules before deferred release activation."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from cp1r3_confirmation_cohort_v1 import ROOT
from seed_census_analysis_pool_v2 import process_identity

home=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home');parent=home/'confirmation_releases/current_sta_cp1r2'
release=home/'confirmation_releases/current_sta_cp1r3';workspace=home/'confirmation_workspaces/cp1r3_distinct_input_cohort_01'
assert not ROOT.exists() and not workspace.exists()
candidate_inventory=D/'independent_input_candidates_02/completion.json';assert read(candidate_inventory)['passed']
selected=[('lstm','heldout_lstm_s21_hybrid_o_n125_w100_p0','two_layer_edge_encoded_Hybrid_O','different_circuit_and_actual_packed_placement'),
    ('dla_small','heldout_dla_like.small_s21_hybrid_o_n100_w100_p0','two_layer_edge_encoded_Hybrid_O','different_circuit_and_actual_packed_placement'),
    ('eltwise_sb','training_eltwise_layer_s11_sb_n40_w100_p0','two_layer_edge_encoded_SB_only','known_circuit_alternate_architecture_full_controller_confirmation')]
inputs=[];files=[Path(__file__).resolve(),candidate_inventory,D/'independent_input_candidates_02/inputs.json']
known={r['native']['declared_physical_identity']['circuit'] for r in read(D/'mechanism_selection_evidence_01/pairs.json')}
for identifier,name,family,purpose in selected:
    source=D.parents[1]/'results/architecture_flow_20261027/runs'/(name+'_a0');packing=source.with_name(name+'_place')
    manifest=source/'manifest.json';provenance=packing/'manifest.json';m=read(manifest);p=read(provenance);command=m['command']
    for record in [m,p]:assert record['command'][record['command'].index('--merge_constant_generators')+1]=='off'
    assert all(m['outputs'][n]['sha256']==p['outputs'][n]['sha256'] for n in ['packed.net','placed.place'])
    paths=dict(architecture=Path(command[1]),circuit=Path(command[2]),graph=Path(command[command.index('--read_rr_graph')+1]),packed=source/'packed.net',placement=source/'placed.place')
    hashes={k:m['shared_inputs'][str(paths[k])]['sha256'] for k in ['architecture','circuit','graph']};hashes.update(packed=m['outputs']['packed.net']['sha256'],placement=m['outputs']['placed.place']['sha256'])
    assert all(f.is_file() for f in paths.values()) and '--sdc_file' not in command
    if identifier in ['lstm','dla_small']:assert hashes['circuit'] not in known
    copies={k:dict(source=str(f),destination=str(workspace/identifier/'inputs'/(k+f.suffix)),sha256=hashes[k],bytes=f.stat().st_size) for k,f in paths.items()}
    inputs.append(dict(id=identifier,source_name=source.name,source_manifest=str(manifest),packing_manifest_source=str(provenance),copies=copies,purpose=purpose,
        declared_physical_identity=dict(circuit_sha256=hashes['circuit'],architecture_sha256=hashes['architecture'],graph_sha256=hashes['graph'],packed_sha256=hashes['packed'],placement_sha256=hashes['placement'],architecture_family=family),
        known_historical_input=True,source_route_will_not_be_imported=True,historical_QoR_not_used_for_selection=True,explicit_application_timing_claim=False))
    files += [manifest,provenance]
assert len({i['declared_physical_identity']['circuit_sha256'] for i in inputs})==3
predecessor=D/'robot_p1_prefix_recovery_01/queue';reg=read(predecessor/'registration.json');live=process_identity(reg['pid'])
assert live and live['state']!='Z' and live['start_ticks']==reg['start_ticks']
phase_template=D/'cp1r2_cross_circuit_cohort_01/conv_hls_phase_runtime.json';parent_contract=read(parent/'contract.json')
unchanged=['fixed_configuration','route_fixed_options','route_input_options','native_defaults','execution_environment','phase_binary_sha256','query_engine_sha256','query_validation_sha256','mechanism_order','acceptance','input_contract','scope','outcome_policy','cost','limits']
assert all(k in parent_contract for k in unchanged)
patch=read(D/'observation_precision_patch_02/preparation.json');expected={**patch['patched_workers_sha256'],'observation_timing_identity_v2.py':patch['helper_sha256']}
scripts=['preregister_cp1r3_distinct_input_cohort_01.py','activate_cp1r3_distinct_input_cohort_01.py','package_cp1r3_public_source_01.py','generate_cp1r3_cohort_driver_01.py','cp1r3_confirmation_cohort_v1.py','queue_cp1r3_distinct_input_cohort_01.py','seal_cp1r3_distinct_cohort_outcomes_01.py','validate_cp1r3_cohort_administration_01.py','packed_input_contract_v1.py','retained_prefix_workflow.py','seed_census_analysis_pool_v2.py','endpoint_timing_policy_streaming_v2.py','restore_confirmation_cp1r2_dependencies.py']
for name in scripts:compile((D/name).read_text(),name,'exec');files.append(D/name)
files += [phase_template,parent/'release_manifest.json',parent/'contract.json',D/'confirmation_release_cp1r3_01/plan.json',D/'confirmation_release_cp1r3_01/queue/registration.json',D/'robot_p1_prefix_recovery_01/plan.json',predecessor/'registration.json',D/'cp1r3_cohort_administration_revision_01.json',D/'cp1r3_cohort_administration_validation_01/completion.json',D/'observation_precision_patch_02/preparation.json',D/'cp1_public_source_restoration_01/wheel_sources.json']
assert read(D/'cp1r3_cohort_administration_validation_01/completion.json')['passed']
ROOT.mkdir()
protocol=dict(passed=True,status='registered_specification_pending_activation',selected_inputs=inputs,registered_inputs=3,registered_roles=6,fixed_arm_order=['native','domain'],
    release=str(release),parent_release=str(parent),parent_release_manifest_sha256=sha(parent/'release_manifest.json'),expected_precision_runtime_sha256=expected,unchanged_contract_fields=unchanged,
    workspace=str(workspace),predecessor=str(predecessor),phase_runtime_template=str(phase_template),actual_release_and_configs_frozen=False,
    activation='Wait for original predecessor and shared serial lock; require CP1r3 package/guard/import checks, exact unchanged parent rules, metadata-to-byte admission, exact source+wheel reconstruction and relocated checker; freeze actual release/config digests before the first native call.',
    source_sha256={str(f):sha(f) for f in files},predecessor_identity_at_registration=live,
    independence='Two known historical distinct circuit/netlists outside the10configuration matrix plus one known circuit on an applicable SB-only family. Three actual source inputs, not six independent samples; no old tree imported. Hybrid-O n125/n100 are device sizes, not distinct architecture families. Declared identities require actual byte/placement/root verification; no unseen holdout or external application timing claim.',
    fixed_rules='Unchanged CP1 root envelopes, current STA/group/domain/per-net release/owner/acceptance/terminal relationship; only CP1r3 observation precision correction. Native has matching target, owner, convergence opportunities; count8/threshold1.01,1worker,200iterations,failurepredictoroff,normal1800s child guards. No triage/empty-query development patch included.',
    retain='Every selected input/role, including unexecuted input-admission failure, routing execution timeout, initial congestion failure, legal no-cut/no-gain, tradeoff and degradation. No outcome-selected replacement, retry or rule change. Programmer/infrastructure faults retain receipts and require reconciliation.',
    cost='Actual complete per-arm command includes release admission/indexes/fresh routing/resource/owner/terminal/timing and all required checks/rejections/rollback. Input provisioning, source reconstruction and external research verification remain separate; report CPD,wire,SB,CB,full endpoints,time/PSS/missing observations from each same role.',
    full_method_time_cap=None,research_total_call_cap=None,new_native_calls=0,new_independent_results=0,complete_goal=False,
    qualification='Preregistered source/input/rule specification only. Runtime is not yet generated, actual configurations/admission and large byte provisioning have not passed. All active confirmation configs are sealed in plan.json/preflight.json later, before native work. This protocol neither overwrites local/frozen updates nor stops research at cohort completion.')
write(ROOT/'protocol.json',protocol)
write(ROOT/'registration_preflight.json',dict(passed=True,source_syntax_checked=True,administration_boundary_tests=True,metadata_packing_and_route_declarations_match=True,
    protocol_inputs=3,protocol_roles=6,actual_CP1r3_checker_passed=False,public_reconstruction_passed=False,physical_provisioning_passed=False,native_calls_new=0,
    protocol_sha256=sha(ROOT/'protocol.json'),deferred_physical_copy_bytes=sum(r['bytes'] for i in inputs for r in i['copies'].values())))
print(dict(passed=True,protocol_inputs=3,protocol_roles=6,actual_activation_pending=True,new_native_calls=0))
