#!/usr/bin/env python3
"""Reconcile live owners with sealed frontier evidence and the independent new version."""
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from native_feedback_analysis_pool import process_identity

now = datetime.now(timezone.utc).isoformat()
history = D / 'continuation_history' / ('automatic_release_' + str(time.time_ns()))
history.mkdir()
spec = [('native_resource_bundle_dev_01/queue', 78099), ('native_first_resource_dev_01/queue', 28042),
        ('strong_A0_timing_trajectories_01/queue', 84543), ('strong_A0_fast_resource_dev_01/queue', 67650),
        ('strong_A0_fast_K8_resource_dev_01/queue', 23126), ('failure_feedback_domain_dev_02', 24310),
        ('domain_failure_release_stage_01', 99365), ('domain_failure_release_validation_queue_01', 5535), ('uniform_feedback_resource_dev_01/queue', 91522)]
owners = []
for name, session in spec:
    folder = D / name
    r = read(folder / 'registration.json')
    actual = process_identity(r['pid'])
    live = bool(actual and actual['state'] != 'Z' and actual['start_ticks'] == r['start_ticks'])
    terminal_path = folder / ('build_result.json' if name == 'domain_failure_release_stage_01' else 'completion.json')
    terminal = read(terminal_path) if terminal_path.exists() else None
    assert live or terminal is not None, (name, actual)
    phase = read(folder / 'status.json') if (folder / 'status.json').exists() else {}
    owners.append(dict(batch=name, pid=r['pid'], start_ticks=r['start_ticks'], verified_live=live,
                       actual_process=actual, terminal_receipt=terminal, phase=phase,
                       phase_is_historical_when_terminal=terminal is not None, tool_session=session,
                       registration=str(folder / 'registration.json'), observed_at=now))
active = [o for o in owners if o['verified_live']]
archive = read(D / 'multiobjective_archive_44/completion.json')
front = read(D / 'multiobjective_tradeoff_summary_20.json')
paper = read(D / 'automatic_release_paper_binding_01.json')
feedback = read(D / 'failure_feedback_domain_dev_02/completion.json')
assert all(x['passed'] for x in [archive, front, paper, feedback])
automatic_path = D / 'automatic_domain_release_dev_01/completion.json'
automatic = read(automatic_path) if automatic_path.exists() else None
tiny = read(D / 'domain_failure_release_tiny_01/completion.json')
assert tiny['passed']
next_actions = [
    'Automatic native failure release validation is fully terminal and passed. Preserve the subsequent uniform_feedback_resource_dev_01 single owner, native-only and paired-feedback own-current K8 trajectories from pristine native A0 eltwise/BNN starts; registered binary/inputs/acceptance stay fixed. Read actor-final seals before archival; never resubmit from an observation timeout.',
    'All original K4/K8/transfer/native-first/strong-A0 timing cohorts are terminal and sealed. Never treat their stale last-actor status as a live job. They are fixed historical evidence, not reasons to stop the research goal.',
    'The selective 7-domain candidate is real: same source8-cut scope/kernel/query order, one released net,72SB/2069104wire/5071CB at exact13.228145689936355ns. The exact source unrestricted control is74SB/2069040wire/5071CB. Automatic native release now tests whether the same point can be obtained without a manually supplied net or restarting previous restorations. Do not keep pressure/order tuning on a domain certified infeasible even at minimum occupancy.',
    'Use the shared physical frontier including strong A0/R1/U/Tf and repairs, not only internal points. A0-fast native K8 gives2059603wire/86SB/5062CB; paired K8 gives2059882/79/5061, same exactCPD. Lower-CB oldRq/reassignment and lower-wire slower native-first states still offer tradeoffs; old slow A0 pairedK4 is quality dominated. SPMV R1repair remains strong-A0 quality dominated.',
    'After native release validation, integrate an automatic portfolio with own-current selector and per-net feedback, circuit-independent K/scope/strategy parameters. Test causal contributions by equal-source native scope/objective/opportunity controls, including native-first scheduling. K1/K4/K8 developmental pilots are not one frozen confirmation algorithm.',
    'The whole A0 K8 group is endpoint-positive though first K4 component is flat and rejected: allow mechanism-backed combination transactions without demanding individual CPD gains. This diagnostic is not an independent pristine-root endpoint-policy success. For algorithm evaluation automatically start from sealed Tf and strong native roots; no manually injected accepted prefix.',
    'Full cost remains the practical bottleneck. Worker source FULLSTA, construction, independent serialization/physical audit, candidate FULLSTA, failures and seals are separate. Consider in-process candidate FULLSTA or checked state reuse after equivalence gates. Complete cold single-configuration routing-plus-repair time remains unknown; do not use oldU timing, core times or sums of unrelated workflows.',
    'Loaded postlegal contexts use actual occupancy and STA but fresh PathFinder accumulated price history. Preserve/reset policy must be explicit and compared before in-process transfer. Preserve physicalTdel/native congestion/legality/resources/rollback.',
    'Freeze uniform version/parameters/selection rules before confirmation with strong A0/R1/native controls receiving equal search domains, selectors, allowed tree ranges and acceptance opportunities. Parameter development and design budgets are authorized; none is an overall Goal date/call/matrix cap.',
]
for name in ['CONTINUATION.json', 'live_handoff.json']:
    path = D / name
    shutil.copy2(path, history / name)
    x = read(path)
    x.update(updated_at=now, observed_at=now, research_state='active', current_goal_state='active',
             old_caps_revoked=True, author_metadata_blocks_research=False, research_blockers=[],
             previous_goal_turn_classification='progress', running_jobs=active, queued_jobs=[],
             active_jobs=active, active_owners=active, supervisors=active, runners=active,
             next_actions=next_actions)
    x['current_terminal_cohorts'] = [o['batch'] for o in owners if o['terminal_receipt'] is not None]
    x['actor_terminal_but_parent_cohort_active'] = []
    x['latest_multiobjective'] = dict(archive='multiobjective_archive_44', points=264,
        summary='multiobjective_tradeoff_summary_20.json', quality_counts=archive['quality_counts'],
        retention_counts=archive['retention_counts'], quality_is_not_five_dimensional_frontier=True,
        BNN_quality_or_precision_uncertain_groups=len(front['bnn_observed_quality_frontier']),
        strong_baseline_dominated_nonbaseline_records=front['nonbaseline_records_quality_dominated_by_strong_baseline'],
        record_count_is_not_configuration_count=True, complete_cold_configuration_seconds=None, new_work_pushed=False)
    x['latest_strong_A0_fast_resource'] = dict(terminal=True, K8_native='strong_A0_native_only_K8_summary_01.json',
        K8_paired='strong_A0_paired_K8_summary_01.json',
        critical_structure='A0_K8_final_critical_structure_02.json',
        critical_structure_correction='01 had int-versus-string cone key comparison error;02 uses saved JSON,zero newnative',
        native_quality=dict(CPD_ns=13.228145689936355, wirelength=2059603, SB_pairs=86, CB_sources=5062),
        paired_quality=dict(CPD_ns=13.228145689936355, wirelength=2059882, SB_pairs=79, CB_sources=5061))
    x['latest_resource_bundle'] = dict(terminal=True, batch='native_resource_bundle_dev_01',
        K8_mechanism='R1_fast_bundle8_mechanism_01.json', source='resource_schedule_cohort_binding_01.json')
    x['latest_native_first_resource'] = dict(terminal=True, batch='native_first_resource_dev_01',
        source='resource_schedule_cohort_binding_01.json', prospective_quality_known=True,
        SPMV_exact_paired_route_vectors=True, formal_speedup=None)
    x['latest_selective_domain'] = dict(batch='failure_feedback_domain_dev_02', passed=True,
        completion=feedback, archive='multiobjective_archive_44',
        improvement_over_same_source_free=dict(wirelength=64, SB_pairs=-2, CB_sources=0, CPD_s=0))
    x['latest_automatic_native_release'] = dict(batch='automatic_domain_release_dev_01',
        stage='domain_failure_release_stage_01', build_passed=True, tiny_passed=True,
        tiny='domain_failure_release_tiny_01/completion.json',
        native_source='domain_failure_release_workspace_01/vpr/src/route/h3d_joint_native_repair.h',
        pool='native_feedback_analysis_pool.py', final_completion=automatic,
        final_context_must_pass_before_archival=True, new_work_pushed=False)
    x['latest_native_pending'] = dict(status='uniform_K8_pristine_native_root_resource_development', owners=active)
    x['active_current_sta_batch'] = dict(owners=active, registered_versions_unchanged=True,
        prior_registered_batches_all_complete=True, maximum_current_native_workers=1)
    x['common_absolute_budget_reference'] = dict(source='common_resource_budget_slices_06.json',
        type='empirical_reference_not_math_bound_or_history_best_algorithm_score',
        A0_CB_cap_fast_CPD_plus40wire_minimum_observed_SB=86,
        A0_CB_cap_fast_CPD_0p1_wire_minimum_observed_SB=79,
        R1_other_wire_CB_envelope_minimum_observed_SB=72)
    x['latest_execution_cost'] = dict(source='resource_schedule_cohort_binding_01.json',
        strong_A0_K8_native_imported_workflow_seconds=read(D/'strong_A0_native_only_K8_summary_01.json')['complete_imported_state_workflow_seconds'],
        strong_A0_K8_paired_imported_workflow_seconds=read(D/'strong_A0_paired_K8_summary_01.json')['complete_imported_state_workflow_seconds'],
        selective_domain_imported_workflow_seconds=feedback['complete_imported_algorithm_workflow_seconds'],
        R1_K8_all_native_core_including_failure_seconds=18.699455428,
        nested_levels_not_additive=True, complete_cold_configuration_seconds=None,
        qualification='Exact actor completions/summaries authoritative; neither replay nor different-workload workflow ratio is a formal speedup.')
    x['latest_uniform_feedback_resource'] = dict(batch='uniform_feedback_resource_dev_01',owner=owners[-1],registration='uniform_feedback_resource_dev_01/queue/registration.json',controller='run_pooled_feedback_bundle_repair.py',new_work_pushed=False,complete_cold_configuration_seconds=None)
    x['latest_automatic_native_release']['mechanism']='automatic_domain_release_mechanism_01.json'
    x['latest_automatic_native_release']['endpoint_band']='automatic_domain_release_endpoint_band_01.json'
    x['latest_execution_cost']['automatic_domain_release_imported_workflow_seconds']=automatic['complete_imported_algorithm_workflow_seconds']
    x['latest_execution_cost']['automatic_domain_release_core_seconds']=read(D/'automatic_domain_release_mechanism_01.json')['native_search_core_seconds']
    x['latest_paper'] = paper
    x['multiobjective_policy'].update(archive='multiobjective_archive_44',
        current_batch='Automatic native release validated; subsequent own-current uniform K8 from pristine strong-native A0 roots',
        final_archive_separate_from_branch_acceptance=True, legal_tradeoffs_retained=True, no_overall_stop=True)
    x['git_publication']['new_work_pushed'] = False
    x['git_publication']['new_results_pushed_applies_to'] = 'Only f7167bd public snapshot; all later work remains local'
    write(path, x)
protocol = D / 'RESEARCH_PROTOCOL.md'
marker = '20261114_automatic_release_validated_uniform_pristine_roots'
if marker not in protocol.read_text():
    with protocol.open('a') as f:
        f.write(f'\n\n{now} {marker}\n自动C++ failure-release已完成tiny与BNN真实替换/FULLSTA/最终封存：初始8域仅自动释放31767p1，精确复现72SB/2069104wire/5071CB、CPD13.228145689936355ns；并非新增独立前沿点。strict拒绝，端点9setup改善零退化接受；固定源近关键23项全部不变，不宣称后续CPD必提升。完整输入态流程287.624s、native core6.693s为嵌套，真实冷routing+repair时间未知。current_state.remaining_domain_nets遗留字段是初始spec，实际最终7域以原生trace/独立audit与automatic_domain_release_mechanism_01为准。\n后续独立uniform_feedback_resource_dev_01已登记并执行：pristine强原生eltwise/BNN A0根、同K8/根CPD/根wire+0.1%预算，native-only和paired自动feedback各自在自己当前态重选，先free后domain评价且固定优先domain接受；无手工释放net或已接受修复前缀注入。两步/三rank窗口只是本地机制probe，不是全Goal停止条件。原运行/封存版本不改，源/图/参数/接受机会明确，同输入历史证据尽量复用；确认阶段仍需更广起点(Tf及强A0/R1)、统一冻结规则与正式全流程计时。Goal active，无整体日期/总次数/固定矩阵停止条件；论文C163已同步，全部新增本地未推送。\n')
write(history / 'update_binding.json', dict(passed=True, observed_at=now, owners=owners,
      source_sha256={str(p): sha(p) for p in [Path(__file__).resolve(), D / 'multiobjective_archive_44/completion.json',
          D / 'multiobjective_tradeoff_summary_20.json', D / 'automatic_release_paper_binding_01.json',
          D / 'failure_feedback_domain_dev_02/completion.json', D / 'domain_failure_release_tiny_01/completion.json',D/'automatic_domain_release_mechanism_01.json',D/'uniform_feedback_resource_dev_01/queue/registration.json']},
      artifact_sha256={str(D / f): sha(D / f) for f in ['CONTINUATION.json', 'live_handoff.json', 'RESEARCH_PROTOCOL.md']},
      native_calls=0, route_calls=0))
print(dict(active=[x['batch'] for x in active], archive_records=264, automatic_terminal=automatic is not None), flush=True)
