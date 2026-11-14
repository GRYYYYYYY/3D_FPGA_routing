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
q = D / 'resource_first_timing_dev_01/queue'
r = read(q / 'registration.json')
actual = process_identity(r['pid'])
live = bool(actual and actual['state'] != 'Z' and actual['start_ticks'] == r['start_ticks'])
terminal = read(q / 'completion.json') if (q / 'completion.json').exists() else None
assert live or terminal is not None
phase = read(q / 'status.json')
phase_actual = process_identity(phase['pid'])
owner = dict(batch='resource_first_timing_dev_01', pid=r['pid'], start_ticks=r['start_ticks'],
    verified_live=live, actual_process=actual, phase=phase, terminal_receipt=terminal, tool_session=81566,
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
    'Preserve the actual resource_first_timing_dev_01 single owner and registered run_independent_critical_portfolio_v2.py/stable native backend. Do not switch the running decoder/kernel after the streaming optimization. First accepted prefix13.607436→13.421610ns,2059882wire/79SB/5061CB is sealed independently; read current steps and native completions before reporting later progress.',
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
    x['latest_resource_first_timing'] = dict(owner=owner, prefix='resource_first_timing_prefix_01.json',
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
        'endpoint_loader_streaming_validation_01', 'endpoint_loader_streaming_integration_01'})
    x['latest_paper'] = paper
    x['multiobjective_policy'].update(archive='multiobjective_archive_47',
        current_batch='Own-current resource-first timing with tighter absolute vertical limits and original-root wire budget',
        legal_tradeoffs_retained=True, final_archive_separate_from_branch_acceptance=True, no_overall_stop=True)
    x['git_publication']['new_work_pushed'] = False
    write(path, x)
protocol = D / 'RESEARCH_PROTOCOL.md'
marker = '20261114_uniform_fused_streaming_resource_first'
if marker not in protocol.read_text():
    with protocol.open('a') as out:
        out.write(f'\n\n{now} {marker}\n'
            '统一K8从pristine强A0根的四actor完整按原版本/规则封存；档案47=282合法观察、失败另列。BNN原生同CPD减少4wire/8SB，paired同CPD+275wire/−15SB/−1CB；Eltwise paired24SB/965CB较旧K4少1SB，其6+3网分组无fallback触发，不归因释放。CPD略差但更低wire/CB的角点继续保留，SPMV仍被强A0质量支配。\n'
            '同worker实际候选FULL/新STA/打印/源恢复经tiny及BNN实际scope验证通过，独立同binary LOAD全部导出精确相同；源receipt不充作candidate。两次Python guard错误（tuple/list与6位打印检查用于全精度candidate）保留，复用已封存worker及通过审计、0重复repair恢复并新做2验证LOAD。fused COMPLETE28.757含candidate observer，QUERY7.859；恢复段372.048不拼旧worker时间当冷算法点。\n'
            '源根放松七新查询三复用后十个当前fast最坏连接switch-distance仍等于现状；反向/虚拟边审计纠正0重查，仅放松参考非全局STA证明。独立资源先行→timing正在执行：垂直79/5061固定，wire2061627锚原始根而非再抬0.1%。已接受首步13.607436→13.421610ns/2059882wire，17非关键setup退化不冒称端点策略接受，近关键12项1改善0退化；同endpoint的winning连接10→13，后续当前STA重选。该前缀不是全轨迹/顺序交换性/新前沿结论。\n'
            '独立流式端点reader保留逐行JSON校验和完整数字/ID：两个357MiB真实文件向量摘要精确一致，约11s→5s、RSS1.73GiB→0.18–0.21GiB；7损坏输入和实际已验证候选接入通过、0新native。运行中的timing不换版本。full echo每态753.92MiB是后续export-level优化依据，尚未实现/计时；不能把省dump称省STA。\n'
            '主线短稿按问题—机制—整体结果—Pareto—消融—开销组织并版本化，旧64页证据稿及全部旧快照保留。确认仍须统一版本/选点规则，从Tf和强原生起点自动完整运行，与相同搜索域/树域/选择/接受机会原生对照，并同环境正式冷计时。无每模块单独改善CPD前置门槛，无总体日期/总调用/固定矩阵停止条件；Goal active、作者信息不阻科研，新增本地未推送。\n')
write(history / 'update_binding.json', dict(passed=True, observed_at=now, actual_owner=owner,
    source_sha256={str(p): sha(p) for p in [Path(__file__).resolve(), D / 'multiobjective_archive_47/completion.json',
        D / 'candidate_full_sta_native_binding_01.json', D / 'endpoint_loader_streaming_integration_01/completion.json',
        D / 'resource_first_timing_prefix_01.json', D / 'streaming_timing_prefix_paper_binding_01.json']},
    artifact_sha256={str(D / n): sha(D / n) for n in ['CONTINUATION.json', 'live_handoff.json', 'RESEARCH_PROTOCOL.md']},
    native_calls=0, route_calls=0))
print(dict(active=[o['batch'] for o in active], archive=282, focused_paper_pages=paper['pages']), flush=True)
