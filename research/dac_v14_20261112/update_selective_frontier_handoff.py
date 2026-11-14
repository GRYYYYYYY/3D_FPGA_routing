#!/usr/bin/env python3
"""Reconcile live owners with sealed frontier evidence and the independent new version."""
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from native_feedback_analysis_pool import process_identity

now = datetime.now(timezone.utc).isoformat()
history = D / 'continuation_history' / ('selective_frontier_' + str(time.time_ns()))
history.mkdir()
spec = [('native_resource_bundle_dev_01/queue', 78099), ('native_first_resource_dev_01/queue', 28042),
        ('strong_A0_timing_trajectories_01/queue', 84543), ('strong_A0_fast_resource_dev_01/queue', 67650),
        ('strong_A0_fast_K8_resource_dev_01/queue', 23126), ('failure_feedback_domain_dev_02', 24310),
        ('domain_failure_release_stage_01', 99365), ('domain_failure_release_validation_queue_01', 5535)]
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
paper = read(D / 'selective_frontier_paper_binding_01.json')
feedback = read(D / 'failure_feedback_domain_dev_02/completion.json')
assert all(x['passed'] for x in [archive, front, paper, feedback])
automatic_path = D / 'automatic_domain_release_dev_01/completion.json'
automatic = read(automatic_path) if automatic_path.exists() else None
tiny = read(D / 'domain_failure_release_tiny_01/completion.json')
assert tiny['passed']
next_actions = [
    'Preserve the independent domain_failure_release validation owner and registered binary/inputs/acceptance. Build and 8-child tiny default/isolation/real-failure recovery checks passed. Read actual final BNN replacement/FULLSTA/context seals before declaring equivalence or publishing a candidate; no observer timeout resubmission.',
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
    x['latest_native_pending'] = dict(status='automatic_native_release_validation_only' if automatic is None else 'automatic_native_release_terminal', owners=active)
    x['active_current_sta_batch'] = dict(owners=active, registered_versions_unchanged=True,
        prior_registered_batches_all_complete=True, maximum_current_native_workers=1)
    x['common_absolute_budget_reference'] = dict(source='common_resource_budget_slices_06.json',
        type='empirical_reference_not_math_bound_or_history_best_algorithm_score',
        A0_CB_cap_fast_CPD_plus40wire_minimum_observed_SB=86,
        A0_CB_cap_fast_CPD_0p1_wire_minimum_observed_SB=79,
        R1_other_wire_CB_envelope_minimum_observed_SB=72)
    x['latest_execution_cost'] = dict(source='resource_schedule_cohort_binding_01.json',
        strong_A0_K8_native_imported_workflow_seconds=829.3290150098242,
        strong_A0_K8_paired_imported_workflow_seconds=1248.2626643776894,
        selective_domain_imported_workflow_seconds=feedback['complete_imported_algorithm_workflow_seconds'],
        R1_K8_all_native_core_including_failure_seconds=18.699455428,
        nested_levels_not_additive=True, complete_cold_configuration_seconds=None,
        qualification='Exact actor completions/summaries authoritative; neither replay nor different-workload workflow ratio is a formal speedup.')
    x['latest_paper'] = paper
    x['multiobjective_policy'].update(archive='multiobjective_archive_44',
        current_batch='Independent automatic per-net domain failure release after sealed K4/K8/transfer/native-first pilots',
        final_archive_separate_from_branch_acceptance=True, legal_tradeoffs_retained=True, no_overall_stop=True)
    x['git_publication']['new_work_pushed'] = False
    x['git_publication']['new_results_pushed_applies_to'] = 'Only f7167bd public snapshot; all later work remains local'
    write(path, x)
protocol = D / 'RESEARCH_PROTOCOL.md'
marker = '20261114_selective_domain_frontier'
if marker not in protocol.read_text():
    with protocol.open('a') as f:
        f.write(f'\n\n{now} {marker}\n'
                '原有K4/K8、strong-A0 timing、迁移及native-first批次均已按原版本/输入/接受规则完成封存；不追改历史。档案44=264合法观察，失败单列、219完整时间不可比暂留。强A0/R1/U/Tf均保留，质量被支配与五维保留分开。A0 fast K8 native(2059603/86/5062)与paired(2059882/79/5061)同13.228145689936355ns；旧慢A0 pairedK4被质量支配，低wire/低CB旧角点仍保留。SPMV R1修复仍被强A0支配。\n'
                '容量证据推动按网释放：同8cut源/核/顺序仅31767无域得到合法72SB/2069104wire/5071CB，较自由回退−2SB/+64wire；真实FULLSTA/恢复封存通过。新独立native自动失败释放实现先保持全域，失败仅放开该net并重置搜索代价、保留先前成功占用；构建与8-child tiny兼容/恢复通过，大图独立验证后才归档。搜索失败本身不等于容量数学证明。原生容量/真实Tdel/FULLSTA/整体回滚保留。\n'
                '资源与时序预算只作设计取舍，不作全Goal限制。组合可整体验证，不要求每模块独立改善CPD。正式确认前统一冻结版本/K/选点/接受规则，与相同搜索范围、树范围、选择器和接受机会的强A0/R1/native比较；不逐电路选历史最优。加载态原生对照同用fresh累积拥塞价格，尚未恢复原route的PathFinder历史，进程内迁移需显式比较。完整冷routing+repair时间仍未知，不拼接旧U/修复核心/双策略工作流。论文按问题—机制—整体结果—取舍—消融—开销更新，新增本地。Goal active，无日期/次数/固定矩阵总停止条件。\n')
write(history / 'update_binding.json', dict(passed=True, observed_at=now, owners=owners,
      source_sha256={str(p): sha(p) for p in [Path(__file__).resolve(), D / 'multiobjective_archive_44/completion.json',
          D / 'multiobjective_tradeoff_summary_20.json', D / 'selective_frontier_paper_binding_01.json',
          D / 'failure_feedback_domain_dev_02/completion.json', D / 'domain_failure_release_tiny_01/completion.json']},
      artifact_sha256={str(D / f): sha(D / f) for f in ['CONTINUATION.json', 'live_handoff.json', 'RESEARCH_PROTOCOL.md']},
      native_calls=0, route_calls=0))
print(dict(active=[x['batch'] for x in active], archive_records=264, automatic_terminal=automatic is not None), flush=True)
