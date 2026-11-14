#!/usr/bin/env python3
"""Fresh process/receipt handoff; old batches and acceptance remain untouched."""
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from export_policy_analysis_pool import process_identity

now = datetime.now(timezone.utc).isoformat()
history = D / 'continuation_history' / ('export_policy_' + str(time.time_ns()))
history.mkdir()
owners = []
receipts = {}
for name, directory, session in [
    ('resource_first_timing_resume_01', D / 'resource_first_timing_resume_01/queue', 25087),
    ('export_policy_large_queue_01', D / 'export_policy_large_queue_01', 58978),
    ('fused_resource_development_01', D / 'fused_resource_development_01/queue', 53193),
    ('fused_resource_archive_queue_01', D / 'fused_resource_archive_queue_01', 24213),
]:
    reg = read(directory / 'registration.json')
    actual = process_identity(reg['pid'])
    live = bool(actual and actual['state'] != 'Z' and actual['start_ticks'] == reg['start_ticks'])
    terminal = read(directory / 'completion.json') if (directory / 'completion.json').exists() else None
    assert live or terminal is not None, 'Reconcile a missing owner before declaring a batch ended'
    phase = read(directory / 'status.json') if (directory / 'status.json').exists() else None
    owner = dict(batch=name, pid=reg['pid'], start_ticks=reg['start_ticks'], verified_live=live,
                 actual_process=actual, observed_at=now, registration=str(directory / 'registration.json'),
                 phase=phase, terminal_receipt=terminal, tool_session=session)
    if phase and 'pid' in phase:
        child = process_identity(phase['pid'])
        owner['phase_child_live'] = bool(child and child['state'] != 'Z' and child['start_ticks'] == phase['start_ticks'])
    if live:
        owners.append(owner)
    receipts[name] = owner
steps = read(D / 'resource_first_timing_resume_01/timing/steps.json')
steps = [s for s in steps if s['accepted']]
assert steps
latest = steps[-1]
build = read(D / 'export_policy_stage_01/build_result.json')
tiny = read(D / 'export_policy_tiny_01/completion.json')
assert build['returncode'] == 0 and tiny['passed']
large = {}
for case in ['timing', 'resource']:
    path = D / ('export_policy_' + case + '_01/completion.json')
    large[case] = read(path) if path.exists() else dict(status='pending_or_running', completion=str(path))
next_actions = [
    'Latest sealed eltwise transfer: native217050/26SB/968CB and paired217191/24SB/965CB at6.018101128546505ns, own-current fixed-budget menus exhausted; imported workflows117.15/118.13s not cold times. Isolated same-binary old/native/only6719canonical source arms recover old/new/old candidates. First-step topology and full vector, second request/domain and retained seed contents match; only seed traversal order differs. This proves serialization search-choice sensitivity, not equal weighted path costs or a specific heap tie. Do not attribute23wire to graph echo, decoder or improved guide scoring.',
    'Current registered fused BNN actors keep native serialization and all frozen parameters, target selection, requests and acceptance. Native-only already passed per-candidate gates beyond the old2accept pilot (observed3rdprefix2059567wire/84SB/5062CB at13.607436ns), but the whole actor seal is required before formal archival or calling it a final point. Wait for both own-current trajectories, then actual fused_resource_archive_queue_01 owner (session24213) extracts only sealed passed actors into multiobjective_fused_resource_final_01 and its joint strong-baseline report. This registered queue exists; do not create a competing archival owner.',
    'Next independent algorithm intervention should freeze a global traversal/seed policy shared by native/domain controls, and distinguish canonical/native representation effects from guide/domain scoring. Do not use order-insensitive physical tree identity as a search cache key or automatically reuse a native search after merely matching the current vector/topology. Keep exact ordered source route bytes in query identity. Prototype standalone adapter01 missed callback output directories and signal11; fixed02 precreates them and all3native candidates/source recovery pass. Original failed cost/logs retained; no running actor/source changed.',
    'Resource-first timing is now terminal after3actual accepted steps, ending at13.228145689936355ns/2059882wire/79SB/5061CB. It matches the prior timing-first resource quality and complete endpoint vectors, while route body differs. All10current winning connection source-root optimistic references exactly match after graph/root/sink identity checks with0newqueries. This is no new quality point, no general commutation or native-STA global proof. Preserve original versions, source and strictCPD/resource/hold/FULLSTA acceptance. Latest accepted step is read from sealed steps, not stale phase status. Recompute currentSTA after each commit. Local empty portfolio/failure is not overall research completion. Keep original2061627wire/79SB/5061CB absolute limits; do not roll budget forward or mix recovery segments into a cold time.',
    'Independent export_policy_large_queue_01 runs timing then resource same-binary paired full/compact graph-text export after10actual tiny children passed. Native FULL/newSTA and all full pin/endpoint/constraint JSON remain, only unused full timing graph echo is optional. Full/compact flags are fingerprinted and bound to actual receipts; compact manifests explicitly cannot select a timing cone. Live quality jobs keep old backend and decoder.',
    'Analyze full/compact actual routes, search, precision frontiers, restored/source gates and independent candidate LOAD before claiming safe integration. Timing case is actual CPD-changing free native paths; resource case is eight-network selective release. Forced target path operator remains outside this validation. One paired measurement per case and opposite order are component evidence, not a formal full-algorithm speedup.',
    'Whole current timing trajectory passed and archive50 has285legal observations, not285independent configurations. Resource-first terminal summary separates original interrupted and1793.82sresume segments; query/dependency/portfolio894.94s, native coordinators834.50s andprep49.76s are exclusive top-level categories. Archive all further legal states/rejections with exact versions and actual budgets. Compare both resource-first and timing-first trajectories on common resource slices, retaining strongA0/R1/U/Tf and missing-time uncertainty. Do not manufacture a point by combining an old routing time, new candidate quality and a shared recovery workflow.',
    'Highest-value next algorithm intervention remains own-current slack-funded release of genuinely capacity-blocking noncritical branches plus grouped critical repair. Use existing failure ownership evidence; final whole transaction nativeFULL/STA/resources acceptance, rollback and same-search/scope/selection/opportunity native controls. Do not require each partial step or module alone to improve CPD. If static-delay relaxation shows no path potential, change scope/domain/scheduling or objective, rather than only query budget.',
    'fused_resource_development_01 is a real single-owner dependency queue (session53193) after export_policy_large_queue_01 terminal and bothcasespassed; source/registered prerequisites fail closed without blind submission. run_fused_resource_bundle_repair_v2.py is already independently implemented: compact/fused observation+streaming reader, same K8/rank3 selector and root budgets, configurable local prefix; registered0continuesuntilnoadmissibleinthatmenu. Four pristine-root own-current native-only/paired cases use uniform settings; no per-circuit history-best. Previous two-step prefixes are rerun only to validate this new integrated backend, never to copy their timing. After actual integration passes, evaluate this automatic resource actor with fused native observation and streaming precision loader, keeping identical deterministic selection and absolute budgets for an engineering equivalence/control run. Timing-cone entry must explicitly request a real full graph echo; source timing is never reused as candidate timing. Keep failures and construction/check/STA/rollback/cache costs.',
    'Confirmation freezes version and circuit-independent parameter/selection rules. Broader cold route-plus-repair measurements remain required; prototype core/request/imported research workflow are separate. Missing author metadata, dates, route counts and local matrices never stop goal. Current additions local, last public snapshotf7167bd, no new push requested.',
]
for filename in ['CONTINUATION.json', 'live_handoff.json']:
    path = D / filename
    shutil.copy2(path, history / filename)
    value = read(path)
    value.update(updated_at=now, observed_at=now, research_state='active', current_goal_state='active',
        previous_goal_turn_classification='progress', research_blockers=[], old_caps_revoked=True,
        author_metadata_blocks_research=False, running_jobs=owners, queued_jobs=[], active_jobs=owners,
        active_owners=owners, supervisors=owners, runners=owners, next_actions=next_actions)
    archive = read(D/'multiobjective_archive_52/completion.json')
    value['latest_multiobjective'] = dict(archive='multiobjective_archive_52', points=archive['records'], summary='multiobjective_tradeoff_summary_24.json', quality_counts=archive['quality_counts'], retention_counts=archive['retention_counts'], record_count_is_not_configuration_count=True, complete_cold_configuration_seconds=None, new_work_pushed=False)
    value['multiobjective_policy']['archive']='multiobjective_archive_52'
    value['latest_phase_order_composition']=dict(summary='resource_first_composition_01.json',terminal='resource_first_timing_terminal_summary_01.json',same_known_quality_and_complete_endpoint_vectors=True,serialized_route_body_different=True,not_general_commutation_proof=True,new_queries_for_reference_reuse=0)
    value['latest_resource_first_timing']['pending_full_trajectory']=receipts['resource_first_timing_resume_01']['verified_live']
    value['latest_resource_first_timing']['owner']=receipts['resource_first_timing_resume_01']
    value['latest_native_pending']=dict(status='own_current_resource_continuation_and_terminal_archive',owners=owners)
    value['latest_fused_resource_archive']=receipts['fused_resource_archive_queue_01']
    value['latest_eltwise_serialization_mechanism']=dict(binding='fused_eltwise_order_mechanism_01.json',diagnostic='serialization_order_diagnostic_02/completion.json',isolated_order_swap_matches=['old','new','old'],guided_quality=dict(CPD_ns=6.018101128546505,wirelength=217191,SB_pairs=24,CB_sources=965),native_quality=dict(CPD_ns=6.018101128546505,wirelength=217050,SB_pairs=26,CB_sources=968),new23wire_not_a_guide_or_IO_quality_claim=True,whole_cold_time=None)
    pending=[owner for owner in owners if (owner.get('phase') or {}).get('status','').startswith('waiting_')]
    value['queued_jobs']=pending
    value['running_jobs']=[owner for owner in owners if owner not in pending]
    value['latest_fused_resource_development']=receipts['fused_resource_development_01']
    if (D/'serialization_mechanism_paper_binding_01.json').exists():value['latest_paper']=read(D/'serialization_mechanism_paper_binding_01.json')
    value['latest_resource_first_timing_observation'] = dict(
        accepted_steps=len(steps), latest_accepted=latest, terminal=receipts['resource_first_timing_resume_01']['terminal_receipt'],
        full_trajectory_pending=receipts['resource_first_timing_resume_01']['verified_live'],
        unchanged_registered_version=True, complete_cold_algorithm_seconds=None)
    value['latest_export_policy'] = dict(stage='export_policy_stage_01',
        build_seconds=build['complete_build_seconds'], tiny='export_policy_tiny_01/completion.json',
        tiny_passed=True, native_tiny_children=tiny['native_children'], queue=receipts['export_policy_large_queue_01'],
        large_results=large, full_native_FULLSTA_retained=True, full_pin_frontier_retained=True,
        graph_echo_optional=True, changed_running_quality_backend=False,
        complete_algorithm_speedup=None, complete_cold_configuration_seconds=None)
    value['latest_export_policy']['actual_native_scope_binding']='export_policy_native_binding_01.json'
    value['active_current_sta_batch'] = dict(owners=owners, registered_versions_unchanged=True,
        combined_native_VPR_maximum=3, timing_chain_maximum=1, export_chain_parent_plus_child=2,
        complete_cold_configuration_seconds=None)
    value['git_publication']['new_work_pushed'] = False
    write(path, value)
protocol = D / 'RESEARCH_PROTOCOL.md'
marker = '20261114_terminal_order_sensitive_fused_continuation'
if marker not in protocol.read_text():
    with protocol.open('a') as out:
        out.write(f'\n\n{now} {marker}\n' + '资源先行current-STA原批次已按原输入/版本/严格CPD+固定资源规则完成当前局部portfolio：3接受最终13.228145689936355ns/2059882wire/79SB/5061CB，完整setup/hold向量与既有timing-first资源终点一致而route body不同；不是新前沿或一般可交换性证明。原中断/恢复1793.82s分段保留，不拼冷完整时间。\n独立graph-text full/compact的10tiny与BNN时序/资源事务均通过，实际FULL、新STA、完整pin/endpoint/SDC精度、候选与源恢复精确同值；单次请求约减22%，仅组件，不是全路由加速。导出标志进入receipt/cache，时序cone仍须full。\n新Eltwise融合自动native/paired两actor终封，6.018101ns下217050/26SB/968CB和217191/24SB/965CB，额外141wire换2SB/3CB；相对旧217214少23wire经old/native/仅6719改序三臂复现old/new/old，seed内容相同顺序不同。收益归因于序列化/搜索选择敏感性，未证明等成本heap tie，不归因于图文本/新引导。后续确认固定全局遍历策略并在所有原生/引导对照共享；精确有序route身份不可只用拓扑/当前向量替代。初次局部adapter漏输出目录失败，02修复后3臂通过，保留失败与代价。\n新BNN own-current原生/配对按同K8/rank3、原根CPD/资源预算继续，accepted_steps=0表示无两次接受前缀限制，遇当前menu无可接受动作只结束该局部策略、不终止研究。私有prefix须actor终封才正式归档。fused_resource_archive_queue_01为真实已登记的单下游owner，待当前cohort terminal后归档已通过BNN actors，不重复Eltwise。当前正式档案52为295观测，论文C172六页与历史证据分别封存。\nGoal active：强A0/R1/U/Tf共同前沿保留，失败/未知冷完整时间分开；新参数/时序资源预算是设计取舍，无总体日期/总调用/固定矩阵/作者清单终止；本轮新增本地未推送。\n')
write(history / 'update_binding.json', dict(passed=True, observed_at=now, owners=receipts,
      native_calls=0, route_calls=0, source_sha256={str(p): sha(p) for p in [Path(__file__).resolve(),
          D / 'export_policy_stage_01/build_result.json', D / 'export_policy_tiny_01/completion.json',D/'export_policy_native_binding_01.json',D/'fused_eltwise_order_mechanism_01.json',D/'serialization_mechanism_paper_binding_01.json',D/'multiobjective_archive_52/completion.json']},
      updated_artifact_sha256={str(D / name): sha(D / name) for name in ['CONTINUATION.json', 'live_handoff.json', 'RESEARCH_PROTOCOL.md']}))
print(dict(active=[x['batch'] for x in owners], accepted_timing_steps=len(steps), latest_CPD_ns=latest['after_CPD_s'] * 1e9), flush=True)
