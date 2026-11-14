#!/usr/bin/env python3
"""Authoritative terminal resource cohort and active timing/engineering owners."""
from datetime import datetime,timezone
from pathlib import Path
import shutil
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

now=datetime.now(timezone.utc).isoformat();history=D/'continuation_history'/('sealed_resource_timing_'+str(time.time_ns()));history.mkdir()
receipts={};active=[]
for name,directory,session in [
    ('fused_resource_development_01','fused_resource_development_01/queue',53193),
    ('fused_resource_archive_queue_01','fused_resource_archive_queue_01',24213),
    ('merge_seed_resource_archive_queue_01','merge_seed_resource_archive_queue_01',88338),
    ('seed_census_client_validation_01','seed_census_client_validation_01',33227),
    ('stable_seed_transfer_dev_01','stable_seed_transfer_dev_01/queue',67432),
    ('direct_scope_resource_equivalence_02','direct_scope_resource_equivalence_02/queue',60372),
    ('native_census_resource_equivalence_01','native_census_resource_equivalence_01/queue',23791),
    ('native_census_state_evaluator_validation_01','native_census_state_evaluator_validation_01',51883),
    ('resource_assurance_selector_validation_01','resource_assurance_selector_validation_01',50919),
    ('low_resource_dual_timing_02','low_resource_dual_timing_02/queue',76605),
]:
    root=D/directory;reg=read(root/'registration.json');p=process_identity(reg['pid'])
    live=bool(p and p['state']!='Z' and p['start_ticks']==reg['start_ticks'])
    terminal=next((read(root/f) for f in ['completion.json','failure.json'] if (root/f).exists()),None)
    assert live or terminal is not None,(name,'Missing owner requires reconciliation')
    phase=read(root/'status.json') if (root/'status.json').exists() else {}
    row=dict(batch=name,pid=reg['pid'],start_ticks=reg['start_ticks'],verified_live=live,
        actual_process=p,phase=phase,terminal_receipt=terminal,observed_at=now,
        registration=str(root/'registration.json'),tool_session=session)
    if 'pid' in phase:
        child=process_identity(phase['pid']);row['phase_child_actual']=child
        row['phase_child_live']=bool(child and child['state']!='Z' and child['start_ticks']==phase.get('start_ticks'))
    receipts[name]=row
    if live:active.append(row)
queued=[r for r in active if r['phase'].get('status','').startswith('waiting_')]
resource=read(D/'fused_resource_development_01/bnn_A0_feedback_K8/completion.json');assert resource['passed']
native=read(D/'BNN_extended_native_menu_01.json');assert native['passed']
archive=read(D/'multiobjective_low_resource_timing_02/completion.json');assert archive['passed']
paper=read(D/'sealed_resource_timing_paper_binding_01.json');assert paper['passed']
proofs=[read(D/name) for name in ['low_resource_timing_accept_01.json','low_resource_timing_accept_02.json']]
assert all(p['passed'] for p in proofs)
state_replay=read(D/'native_census_state_evaluator_validation_01/completion.json');assert state_replay['passed']
assert read(D/'native_resource_nonempty_selection_01/completion.json')['passed']
strict=D/'low_resource_dual_timing_02/strict';live_steps=read(strict/'steps.json')
actions=[
    'Original native-order resource cohort and its single archive/merge owners are now terminal PASSED, regardless of stale status files saying running/waiting. Native5accepts8scopes:13.607436066820355ns/2059591wire/82SB/5062CB,2061.278666s imported workflow,9children. Paired9accepts9scopes:13.607436066820355ns/2061353wire/43SB/5060CB,7293.636565s imported workflow,19children. Extra1762wire buys39SB/2CB; paired extra searches fully charged, no equal-compute or cold time claim. Both own-current menus exhausted, not global resource optimum or research end.',
    'Registered resource archive owner passed and merged seed/resource archive329 passed. Current canonical legal development archive is multiobjective_low_resource_timing_02 with332observations, adding full independent/input-sealed observation of the frozen7accept45SB prefix and two actual timing accepts. All original baselines/rejections retained, record counts are not independent configurations. Whole-resource endpoint43SB differs from the45SB composition root; never attach the13.413972ns timing value to43SB.',
    'Actual strict low-resource composition has at least2bound accepted steps:13.607436→13.421610→13.413972155262854ns,wire2061265→2061305→2061297,45SB/5060CB fixed. First target47878/p2 plus slack donors57399/p1,57596/p1,66543/p1:10setup improvements17regressions,0hold-violation increases; fixed source near12 has1improvement0regression. Endpoint809929 stays critical; winning cone adds47878/p1,47883/p1,57629/p1. Second move11setup improvements0regressions and8lesswire; both rules admit it from that strict state. Read actual live steps/current state for later commits, not this frozen2step prefix.',
    'First accept is strict-admissible/full-endpoint-vector-rejected; independent secondary branch still starts from the original45SB observation and cannot borrow the strict successor. low_resource_dual_timing_02 owner76605 runs strict then secondary using latestv4, exact fixedwire2061627/SB45/CB5060, same source/selector/scope/native opportunities; each reselects on its own STA. Constraints stay native default absent bnn.sdc, ideal ap_clk domain0, IO/setup/hold0, full52527endpoint IDs and52495setup/hold components. No epsilon or rolling caps. Compare actual commits separately from secondary admissibility.',
    'Next scientific intervention should depend on the remaining actual transactions.26319/p1 still competes with critical owner26320, so critical-owner exchange is distinct from only noncritical slack release; preserve whole-copy occupancy updates/nativeFULL/newSTA/rollback. If a good legal candidate violates only SB/CB envelope, diagnose that global resource-budget/search-objective mismatch before adjacent parameter sweeps. If full-vector branch stalls because spending noncritical slack is forbidden, an independently registered fixed-near-endpoint-vector plus bounded donor-slack strategy is justified by the first move near-band evidence; do not change current batch acceptance.',
    'Client fixed seed/census integration passed2actualchildren+1exactcache reuse, no forged/mutated controls accepted. Stable global delay_rr_id pristineA0/R1/Tf transfer owner67432 is now actually running; inspect its current case and real terminal receipts. Original native-order43SB cohort is not an optimized-delay-seed result. Preserve all registered versions; transfer, direct-scope owner60372 and fast-consumer owner23791 remain one live dependency chain, not inferred plans.',
    'Independent pool_state_evaluator_v8/state_resource_assurance/run_native_census_resource_repair are implemented. Actual sealed-worker replay passed equal full vectors and all counter fields,7guards including tamper/premature/cross-state/missing-final proof,0nativecalls. Candidate materialization1.3375/1.1925s vs independent7.0595/6.9705s, selected-final audit5.5705s, sequential component evidence only. Explicit native assurance never fabricates independent_audit.json. Only the actual selected final state receives its final independent proof; other private states retain their own publication requirement and complete evidence for later verification/archive.',
    'Selector interface validation passed4cases plus2nonempty native-source tests with4candidates each; ranking/cuts/full source resource scans unchanged. Native-count live equivalence owner23791 waits for actual direct-scope predecessor60372 terminal, then4uniform pristineA0 native/paired eltwise/BNN cases. Each requires a passed matching predecessor and checks every selection/acceptance/ordered route/full vector/final independent metrics. It includes final audit and all failed/materialization/STA/rollback costs. Do not infer whole automatic speedup from replay tests; cold complete configuration timing remains unknown.',
    'Current main manuscript C181v4 is6pages, joint plot uses219BNNobservations/123quality tuples fromarchive332 includingstrongA0/R1/U/Tf. Completed43SB point and registered45SB/two-timing-accept prefix are separately labeled; second timing point is4D-nondominated and quality-dominates strongR1 input, not5D/algorithm superiority. CB5059 oldstate and low-wire native states remain distinct; severalCB5060 predecessors become quality-dominated. Missing complete time remains unknown, no oldU or component/recovery/shared times assembled.',
    'Prototype timing integration remains a material next runtime target: first accepted round843.38s completed top-level child work, nativecore0.6668s and candidateanalysis206.49s nested, no artificial summation. Once resource live equivalence passes, consider native pooled/fused critical-repair observation and candidate-only full timing graph export with same globally fixed seed policy to isolate representation effects. Actual candidate FULL/newSTA and exact source restoration must remain; current timing batch keeps old backend.',
    'Goal active; meaningful progress is actual9step43SB terminal cohort, two real45SB timing accepts, native assurance implementation/real receipt and nonempty selector proof. No date/totalcalls/fixedmatrix/author metadata stop. All new work local, publicf7167bd unchanged. Per-process guards and total nativeVPR3 remain: one active pool parent+child2 plus independent timing1. Ordinary failed branches lead to diagnosis/next supported change, not research completion.',
]
for name in ['CONTINUATION.json','live_handoff.json']:
    path=D/name;shutil.copy2(path,history/name);value=read(path)
    value.update(updated_at=now,observed_at=now,research_state='active',current_goal_state='active',
        previous_goal_turn_classification='progress',research_blockers=[],old_caps_revoked=True,
        author_metadata_blocks_research=False,active_jobs=active,active_owners=active,supervisors=active,runners=active,
        queued_jobs=queued,running_jobs=[r for r in active if r not in queued],latest_owner_verification=receipts,
        next_actions=actions,latest_paper=paper)
    value['latest_multiobjective']=dict(archive='multiobjective_low_resource_timing_02',points=332,
        parent_merged_archive='multiobjective_merged_seed_resource_01',parent_records=329,
        summary='multiobjective_low_resource_timing_02/composition_summary.json',
        quality_counts=archive['quality_counts'],retention_counts=archive['retention_counts'],
        record_count_is_not_configuration_count=True,complete_cold_configuration_seconds=None,new_work_pushed=False)
    value['multiobjective_policy']['archive']='multiobjective_low_resource_timing_02'
    value['latest_paired_private_prefix']=dict(accepted_steps_observed=resource['accepted_steps'],
        latest_committed_evaluation=resource['final_state'],CPD_s=resource['final_CPD_s'],resources=resource['final_resources'],
        actor_seal_required=False,not_a_final_archive_point=False,terminal_receipt='fused_resource_development_01/bnn_A0_feedback_K8/completion.json')
    value['latest_completed_resource_comparison']=dict(native=native,paired=resource,paired_extra_wire=1762,
        paired_fewer_SB=39,paired_fewer_CB=2,complete_cold_configuration_seconds=None)
    value['latest_low_resource_dual_timing'].update(owner=receipts['low_resource_dual_timing_02'],
        bound_accepted_prefixes=['low_resource_timing_accept_01.json','low_resource_timing_accept_02.json'],
        actual_live_strict_accepted_steps=len(live_steps),actual_live_strict_current=read(strict/'current_state.json'),
        second_step_setup_vector_admissible=True,whole_trajectory_pending=True)
    value['latest_native_resource_census'].update(fast_acceptance_consumer_implemented=True,
        fast_state_evaluator='pool_state_evaluator_v8.py',actual_sealed_worker_replay_passed=True,
        fast_state_validation='native_census_state_evaluator_validation_01/completion.json',
        selector_nonempty_validation='native_resource_nonempty_selection_01/completion.json',
        full_automatic_equivalence_pending=True,live_equivalence_owner=receipts['native_census_resource_equivalence_01'],
        actual_client=receipts['seed_census_client_validation_01'],complete_algorithm_speedup=None)
    value['latest_direct_native_scope_audit'].update(native_count_fast_consumer_implemented=True,
        actual_integrated_equivalence_passed=None)
    value['latest_native_pending']=dict(status='global_seed_transfer_then_engineering_equivalence_and_independent_timing',owners=active)
    value['active_current_sta_batch']=dict(owners=active,combined_native_VPR_maximum=3,
        pool_parent_plus_child=2,parallel_timing_chain=1,registered_versions_unchanged=True)
    value['latest_fused_resource_development']=receipts['fused_resource_development_01']
    value['latest_fused_resource_archive']=receipts['fused_resource_archive_queue_01']
    value['next_algorithm_hypothesis']=actions[3:5]+actions[8:10]
    value['next_registered_not_implemented']=['Complete matched live fast-consumer trajectory proof',
        'Full cold route-plus-repair timing on frozen circuit-independent configuration and stronger native controls',
        'Broader success-rate/quality/tail confirmation from pristine Tf and strong native roots']
    value['git_publication']['new_work_pushed']=False
    write(path,value)
protocol=D/'RESEARCH_PROTOCOL.md';marker='20261114_sealed43SB_two_timing_accepts_native_consumer'
if marker not in protocol.read_text():
    with protocol.open('a') as out:
        out.write(f'\n\n{now} {marker}\n'
            '原native-order资源cohort已按原规则完整结束并归档：native5接受82SB/5062CB/2059591wire，'
            'paired9接受43SB/5060CB/2061353wire，同13.607436066820355ns；额外1762wire换39SB/2CB。'
            '导入流程2061.278666/7293.636565s、9/19native children，非等compute/冷完整时间。'
            '原归档/seed归并owner终封329观察；当前加完整封存45SB观察及两timing接受为332，强基线和全部旧记录保留。\n'
            '新严格时序composition从已登记第7资源prefix45SB开始，不从最终43SB开始：'
            '13.607436→13.421610→13.413972155262854ns，wire2061265→2061305→2061297，SB45/CB5060不变。'
            '第一步10setup改善17退化，hold违例无增加，固定near12内1改善0退化；端点809929未迁移，winning cone增加3连接。'
            '第二步11改善0退化、wire少8，两接受规则均认可该strict状态；独立次级轨迹不能借用这个先前被拒绝的strict successor。'
            '原selector已重算当前目标，完整两策略继续，wire2061627绝对上限不滚动。\n'
            'v8/state_resource_assurance原生计数私有接受+所选最终独立审查已实现，真实2worker回放/7负例通过，'
            'selector4case和两个非空4候选接口一致；不伪造independent_audit，未验证的其他state不能借最终proof发布。'
            '私有物化1.3375/1.1925s对逐候选独立7.0595/6.9705s、最终独立5.5705s，仅串行组件证据。'
            '真实native_census_resource_equivalence_01单owner23791等待direct-scope predecessor终封后4个相同pristine A0 native/paired case，'
            '逐目标/接受/有序route/完整向量/最终独立指标对照；含所有失败与final检查开销，未宣称冷全算法加速。\n'
            '首时序round843.38s顶层child工作、native core0.6668s和candidate分析206.49s嵌套记录，不重复相加。'
            '若完整vector因非关键donor余量使用而停滞，后续独立批可研究固定near-endpoint向量+有界donor预算，当前规则不改；'
            '若当前好候选仅因SB/CB预算拒绝，优先检查预算与搜索目标不一致，保持真实Tdel/nativeFULL/STA及事务回滚。\n'
            '新主稿C181v4六页，联合图219BNN观察/123坐标，43SB完整资源终点与45SB两步prefix分别标识；'
            'CB5059/低wire取舍保留，部分CB5060旧点受新点质量支配，完整时间未知时不作5D全面优势。'
            '所有新增本地未推送；Goal active，无总日期/次数/矩阵/作者停止，单进程保护及总VPR≤3持续。\n')
write(history/'update_binding.json',dict(passed=True,observed_at=now,owners=receipts,native_calls=0,route_calls=0,
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),D/'sealed_resource_timing_paper_binding_01.json',
        D/'multiobjective_low_resource_timing_02/completion.json',D/'native_census_state_evaluator_validation_01/completion.json']},
    updated_artifact_sha256={str(D/n):sha(D/n) for n in ['CONTINUATION.json','live_handoff.json','RESEARCH_PROTOCOL.md']}))
print(dict(active=[r['batch'] for r in active],archive_records=332,resource_final_SB=43,
           bound_timing_prefix_CPDas_ns=proofs[-1]['CPD_after_ns'],history=str(history)),flush=True)
