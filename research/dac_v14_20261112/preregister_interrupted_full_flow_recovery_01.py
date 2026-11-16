"""Freeze four old-actor continuations behind their registered readonly audit."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'interrupted_flow_recovery_01';assert not (root/'protocol.json').exists()
assert read(root/'validation.json')['passed']
inventory=read(D/'interrupted_stage_reconciliation_01/inventory.json')
pred=D/'interrupted_stage_reconciliation_01/queue';reg=read(pred/'registration.json');live=process_identity(reg['pid'])
assert live and live['state']!='Z' and live['start_ticks']==reg['start_ticks']
home=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home');parent=home/'confirmation_releases/current_sta_cp1r2'
arms=[]
for row in inventory['rows']:
    flow=Path(row['flow']);closed=row['pair']=='clstm_input_contract_pair_02' and row['arm']=='native'
    assert row['resource_closed']==closed
    arms.append(dict(pair=row['pair'],arm=row['arm'],original_flow=str(flow),original_transaction=row['transaction'],original_role=row['role'],
        recovery_mode='timing_only_after_closed_resource' if closed else 'resource_then_timing',
        historical_failed_measurement=str(flow.parent/'measurement/completion.json')))
assert len(arms)==4
unchanged=read(D/'robot_p1_prefix_recovery_01/plan.json')['unchanged_algorithm_files']
algorithms=list(unchanged)+['run_registered_independent_stream_transactions_v1.py','audit_native_feedback_objective_cached.py','audit_native_objective_cached.py','audit_failure_release_domain.py','audit_retained_crossing_domain.py','make_current_proposal_portfolio.py','current_group_feedback_cold_v1.py']
files=[D/n for n in ['same_actor_stage_reuse_v1.py','same_actor_timing_prefix_v1.py','generate_interrupted_stage_adapters_01.py',
    'validate_same_actor_stage_reuse_01.py','prepare_interrupted_flow_dispatch_01.py','run_interrupted_full_flow_recovery_v1.py',
    'admit_interrupted_flow_recovery_01.py','queue_interrupted_full_flow_recovery_01.py','validate_interrupted_flow_dispatch_01.py','preregister_interrupted_full_flow_recovery_01.py']]
files += [root/'validation.json',root/'dispatch_revision.json',D/'interrupted_stage_adapter_01/validation.json',D/'interrupted_stage_reconciliation_01/inventory.json',D/'interrupted_stage_reconciliation_01/plan.json',pred/'registration.json',parent/'release_manifest.json',*sorted((root/'runtime_extension').glob('*.py'))]
assert all(sha(p)==h for p,h in read(root/'validation.json')['source_sha256'].items())
for p in [p for p in files if p.suffix=='.py']:compile(p.read_text(),str(p),'exec')
(root/'arms').mkdir()
write(root/'protocol.json',dict(passed=True,status='registered_four_arm_development_recovery_pending_actual_stage_audit',
    predecessor=str(pred),predecessor_identity=live,arms=arms,release=str(home/'confirmation_releases/current_sta_cp1r3'),parent_release=str(parent),
    parent_release_manifest_sha256=sha(parent/'release_manifest.json'),unchanged_algorithm_files=algorithms,
    source_sha256={str(p):sha(p) for p in files},
    fixed_rules='Retain each original root, accepted prefix, rejected legal archive, seed/domain/release/owner choices, acceptance and terminal policies. CLSTM/native retains completed resource/terminal/handoff and original first timing portfolio/query work; other3 resume resource checkpoints. Frozen confirmation/menu/runtime stay unchanged.',
    activation='After real serial stage audit and predecessor process exit, require selected case passed in actual audit summary, current CP1r3 packaging/manifest and unchanged algorithm bytes. Seal actual per-arm plan and audit digests before measured recovery. Audit/metadata failures remain unexecuted; never auto-replay partial native/STA or change old manifests.',
    cost='Actual new suffix wall/PSS/missing observations measured per arm. Original failed attempt costs retained separately; no cold complete method cost, optimized native/domain time ratio or new independent samples reconstructed.',
    ordinary_negative_terminal_is_valid=True,automatic_retry=False,new_independent_inputs=0,new_native_calls_so_far=0,
    full_method_time_cap=None,total_research_call_cap=None,research_complete=False,
    qualification='Runnable development prefix continuation registration. Real byte/STA admission, recovery execution, complete outcomes and endpoint/pair verification are pending; no new QoR or confirmation result.'))
print(dict(passed=True,registered_recovery_arms=4,native_calls_new=0))
