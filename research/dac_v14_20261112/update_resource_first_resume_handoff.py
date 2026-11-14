#!/usr/bin/env python3
"""Record sealed current research and the actual active resource-first timing owner."""
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from candidate_full_sta_analysis_pool import process_identity

now = datetime.now(timezone.utc).isoformat()
history = D / 'continuation_history' / ('uniform_fused_streaming_' + str(time.time_ns()))
history.mkdir()
q = D / 'resource_first_timing_resume_01/queue'
r = read(q / 'registration.json')
actual = process_identity(r['pid'])
live = bool(actual and actual['state'] != 'Z' and actual['start_ticks'] == r['start_ticks'])
terminal = read(q / 'completion.json') if (q / 'completion.json').exists() else None
assert live or terminal is not None
phase = read(q / 'status.json')
phase_actual = process_identity(phase['pid'])
owner = dict(batch='resource_first_timing_resume_01', pid=r['pid'], start_ticks=r['start_ticks'],
    verified_live=live, actual_process=actual, phase=phase, terminal_receipt=terminal, tool_session=25087,
    phase_child_live=bool(phase_actual and phase_actual['state'] != 'Z' and phase_actual['start_ticks'] == phase['start_ticks']),
    observed_at=now, registration=str(q / 'registration.json'))
active = [owner] if live else []
archive = read(D / 'multiobjective_archive_47/completion.json')
front = read(D / 'multiobjective_tradeoff_summary_21.json')
paper = read(D / 'streaming_timing_prefix_paper_binding_01.json')
fused = read(D / 'candidate_full_sta_native_binding_01.json')
decoder = read(D / 'endpoint_loader_streaming_integration_01/completion.json')
prefix = read(D / 'resource_first_timing_prefix_01.json')
assert all(x['passed'] for x in [archive, front, paper, fused, decoder, prefix])
next_actions = [
    'Preserve the actual resource_first_timing_resume_01 single owner and registered run_independent_critical_portfolio_v3.py/prepare_native_group_step_v2.py/stable native backend. The original segment ended at transaction_preparation_failed because its legacy input_identity equated backend/runtime/history with problem identity; current negative/real-plan validation passed with0native and resume reuses the existing current-state portfolio/accepted state/budgets. Do not switch the running decoder/kernel after the streaming optimization. First accepted prefix13.607436→13.421610ns,2059882wire/79SB/5061CB is sealed independently; read current steps and native completions before reporting later progress.',
    'Analyze the full own-current resource-first timing trajectory against timing-first resource records after actual terminal/context gates. Absolute wire2061627 comes from original pristine A0;79SB/5061CB remains tight. Each commit requires exact CPD improvement and refreshed currentSTA. Prefix contains17noncritical setup regressions, so do not call it endpoint-vector acceptance; fixed-source near-critical12components have1improvement0regressions.',
    'Actual candidate same-worker native FULL/newSTA integration is validated on tiny and the BNN resource eight-network case. Dedicated candidate vectors equal independent same-binary LOAD exports; restored/following source exact and all physical/scope checks passed. Use explicit installed-candidate receipts, never the original-input receipt for candidate metrics.',
    'Before using the fused backend for CPD-changing or forced-target-path timing transactions, add that actual matched case. Resource-case flatCPD and nine changed components do not cover every operator. Current timing phase intentionally uses its validated older backend. Two Python admission errors and all costs are preserved; recovered sealed search/transaction audits were reused with0newrepair calls.',
    'For future independent algorithm versions use the all-row streaming endpoint loader after the passed two357MiB real-trace digest/7negative-input/actual-candidate materialization checks. Old≈11s/new≈5s and RSS≈1.73GiB→0.18–0.21GiB are component measurements, not complete routing speed. New decoder strengthens COMPLETE pin census, preserves full precision and every JSON row validation.',
    'Next measured overhead hypothesis: resource-only graph echo is753.92MiB/state, frontier357.20MiB/state, repeated source/candidate/restored. Consider an independent output-level variant that omits an unused full graph dump while retaining actual FULL/freshSTA, all endpoint/clock identities, all required raw pin data and separate candidate/source gates. Export full graph on entry to timing-cone diagnosis. resource_only_export_optimization_hypothesis_01.json is not implemented or timed.',
    'Do not keep increasing the same fast-A0 timing-query budget: full_root_timing_potential_02 is an exact source-root switch-delay relaxation for all10current winning connections and shows zero extra potential after all prefix/occupancy restrictions removed. Seven changed queries plus3exactreuses; no query repeated to fix reverse/virtual-edge audit. This is not a global native-STA proof and does not stop resource/runtime/other-root/other-circuit research.',
    'Keep the joint population with strong A0/R1/U/Tf. Uniform K8 from pristine roots gives BNN native2059563/86SB/5062CB or paired2059842/79SB/5061CB at13.607436066820355ns; fast counterparts cost40morewire for13.228145689936355ns. Eltwise paired24SB/965CB has no fallback trigger, so attribute to grouping/domain choice. SPMV remains strong-A0 quality dominated. Missing complete runtime remains provisional retention, not fictional fifth-axis domination.',
    'Confirmation must freeze one version and circuit-independent selection/strategy, automatically execute from sealed Tf and strong native roots, and compare with same-search/scope/selection/opportunity native controls. Current pilot K1/K4/K8, different roots/opportunities and imported-stage times cannot become one history-best algorithm point. No requirement each module alone improvesCPD before combination.',
    'Cold complete routing+repair remains unknown. Fused COMPLETE28.757s includes candidate observer; QUERY sums7.859s. Recovery372.048s reuses a prior161.843sworker and includes2newvalidation-onlyLOADjobs; neither sum nor ratio is a fresh cold method point. Keep failed Python stages, setup/materialization/audit/STA/rollback and native/parent/query costs separate. No historical U substitution.',
    'Keep updating focused current_repair_main.tex with results/limitations and immutable manuscript versions; full chronological evidence remains separately sealed. Native prices are fresh loaded-context history, not original PathFinder accumulation. Fixed architecture occupancy is not area/power. Goal active without author/date/call/matrix stop; all new work local, last public snapshotf7167bd.',
]
for filename in ['CONTINUATION.json', 'live_handoff.json']:
    path = D / filename
    shutil.copy2(path, history / filename)
    x = read(path)
    x.update(updated_at=now, observed_at=now, research_state='active', current_goal_state='active',
        previous_goal_turn_classification='progress', old_caps_revoked=True, author_metadata_blocks_research=False,
        research_blockers=[], running_jobs=active, queued_jobs=[], active_jobs=active, active_owners=active,
        supervisors=active, runners=active, next_actions=next_actions)
    x['latest_multiobjective'] = dict(archive='multiobjective_archive_47', points=282,
        summary='multiobjective_tradeoff_summary_21.json', quality_counts=archive['quality_counts'],
        retention_counts=archive['retention_counts'], quality_is_not_five_dimensional_frontier=True,
        BNN_quality_or_precision_uncertain_groups=len(front['bnn_observed_quality_frontier']),
        record_count_is_not_configuration_count=True, complete_cold_configuration_seconds=None, new_work_pushed=False)
    x['latest_uniform_feedback_resource'] = dict(batch='uniform_feedback_resource_dev_01', terminal=True,
        completion='uniform_feedback_resource_dev_01/queue/completion.json', all4actors_passed=True,
        BNN_native=dict(CPD_ns=13.607436066820355, wirelength=2059563, SB_pairs=86, CB_sources=5062),
        BNN_paired=dict(CPD_ns=13.607436066820355, wirelength=2059842, SB_pairs=79, CB_sources=5061),
        eltwise_native=dict(CPD_ns=6.018101128546505, wirelength=217050, SB_pairs=26, CB_sources=968),
        eltwise_paired=dict(CPD_ns=6.018101128546505, wirelength=217214, SB_pairs=24, CB_sources=965),
        not_a_frozen_broad_confirmation_score=True, complete_cold_configuration_seconds=None)
    x['latest_fused_candidate_native'] = dict(binding='candidate_full_sta_native_binding_01.json', passed=True,
        stage='candidate_full_sta_stage_01', materializer='pool_state_evaluator_v5.py',
        decoder_optimized_materializer='pool_state_evaluator_v6.py', actual_large='candidate_full_sta_bnn_03/completion.json',
        complete_cold_configuration_seconds=None)
    x['latest_endpoint_decoder'] = dict(source='endpoint_timing_policy_streaming_v2.py',
        benchmark='endpoint_loader_streaming_validation_01/completion.json',
        integration='endpoint_loader_streaming_integration_01/completion.json', passed=True,
        old_load_seconds=[11.48187131434679, 10.796349842101336], new_load_seconds=[5.098116137087345, 5.310098733752966],
        all_full_vectors_exact=True, corruption_cases=7, native_calls=0, applied_to_running_timing=False,
        complete_algorithm_speedup=None)
    x['latest_source_root_potential'] = dict(completion='full_root_timing_potential_02/completion.json',
        source_root_distances_equal_current_for10winning_connections=True, newqueries=7, exactreuses=3,
        repeated_queries=0, reference_is_not_native_STA_global_bound=True)
    x['latest_resource_first_timing'] = dict(owner=owner,prior_interrupted_segment='resource_first_timing_dev_01/timing/completion.json',identity_guard='native_problem_identity_validation_01/completion.json',resume_version='run_independent_critical_portfolio_v3.py', prefix='resource_first_timing_prefix_01.json',
        prefix_CPD_before_ns=prefix['CPD_before_ns'], prefix_CPD_after_ns=prefix['CPD_after_ns'],
        prefix_resources=prefix['actual_resources'], absolute_limits=prefix['fixed_absolute_resources'],
        own_current_STA=True, pending_full_trajectory=True)
    x['active_current_sta_batch'] = dict(owners=active, registered_versions_unchanged=True,
        prior_uniform_cohort_complete=True, current_native_VPR_limit=1, complete_cold_configuration_seconds=None)
    x['latest_native_pending'] = dict(status='resource_first_timing_trajectory_active' if live else 'resource_first_timing_terminal_review', owners=active)
    x['current_terminal_cohorts'] = sorted(set(x.get('current_terminal_cohorts', [])) | {
        'uniform_feedback_resource_dev_01/queue', 'candidate_full_sta_tiny_queue_01',
        'candidate_full_sta_bnn_queue_01 (Python comparison failure preserved)',
        'candidate_full_sta_bnn_03 (successful recovery and independent controls)',
        'endpoint_loader_streaming_validation_01', 'endpoint_loader_streaming_integration_01','resource_first_timing_dev_01 (preparation identity mismatch; accepted prefix retained)'})
    x['latest_paper'] = paper
    x['multiobjective_policy'].update(archive='multiobjective_archive_47',
        current_batch='Own-current resource-first timing with tighter absolute vertical limits and original-root wire budget',
        legal_tradeoffs_retained=True, final_archive_separate_from_branch_acceptance=True, no_overall_stop=True)
    x['git_publication']['new_work_pushed'] = False
    write(path, x)
protocol = D / 'RESEARCH_PROTOCOL.md'
marker = '20261114_problem_identity_resume_same_budget'
if marker not in protocol.read_text():
    with protocol.open('a') as out:
        out.write(f'\n\n{now} {marker}\n资源先行timing原段在首个合法接受后因transaction_preparation_failed局部结束；返回码0不作完成科研或算法无收益结论。真实原因：旧input_identity把shared_inputs里的观察器、运行库和历史工具也当成预算问题输入，相同RRG/网表/布局/架构/电路/有效参数/SDC被误拒。新prepare_native_group_step_v2保留所有来源哈希，只把上述真实输入和规范化参数用于锚点等价，另校验packing/placement与封存输出一致；3项问题改变反例均拒绝，原失败plan在0native下正确准备。\n独立resource_first_timing_resume_01已从已接受13.421610ns/2059882wire/79SB/5061CB及已完成当前STA portfolio续跑，不重做首步/旧查询。固定wire2061627、79SB/5061CB、搜索核、排名和严格CPD/hold/FULLSTA/物理接受规则不变；resume强制同原绝对预算，旧失败/时间单列。不同guard版本的分段时间不拼成冷完整方法时间，端点流式reader仍未切换到运行中的timing。\nGoal active，无总体日期/总调用/固定矩阵终止条件，无作者阻断；方法、关键路径变化和组件代价已进入5页主线短稿及64页历史证据，新增本地未推送。\n')
write(history / 'update_binding.json', dict(passed=True, observed_at=now, actual_owner=owner,
    source_sha256={str(p): sha(p) for p in [Path(__file__).resolve(), D / 'multiobjective_archive_47/completion.json',
        D / 'candidate_full_sta_native_binding_01.json', D / 'endpoint_loader_streaming_integration_01/completion.json',
        D / 'resource_first_timing_prefix_01.json', D / 'streaming_timing_prefix_paper_binding_01.json',D/'native_problem_identity_validation_01/completion.json',q/'registration.json']},
    artifact_sha256={str(D / n): sha(D / n) for n in ['CONTINUATION.json', 'live_handoff.json', 'RESEARCH_PROTOCOL.md']},
    native_calls=0, route_calls=0))
print(dict(active=[o['batch'] for o in active], archive=282, focused_paper_pages=paper['pages']), flush=True)
