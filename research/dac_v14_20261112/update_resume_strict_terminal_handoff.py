#!/usr/bin/env python3
"""Explicit resume: preserve actual jobs, terminal evidence and platform status."""
from datetime import datetime,timezone
from pathlib import Path
import shutil
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

now=datetime.now(timezone.utc).isoformat();history=D/'continuation_history'/('resume_strict_terminal_'+str(time.time_ns()));history.mkdir()
receipts={};active=[]
for name,directory,session in [
    ('fused_resource_development_01','fused_resource_development_01/queue',53193),
    ('seed_census_client_validation_01','seed_census_client_validation_01',33227),
    ('stable_seed_transfer_dev_01','stable_seed_transfer_dev_01/queue',67432),
    ('direct_scope_resource_equivalence_02','direct_scope_resource_equivalence_02/queue',60372),
    ('native_census_resource_equivalence_01','native_census_resource_equivalence_01/queue',23791),
    ('native_census_resource_equivalence_02','native_census_resource_equivalence_02/queue',84229),
    ('low_resource_dual_timing_02','low_resource_dual_timing_02/queue',76605),
    ('completed_resource_timing_dev_01','completed_resource_timing_dev_01/queue',2326),
    ('vector_feedback_subset_native_01','vector_feedback_subset_native_01/queue',58975),
]:
    root=D/directory;reg=read(root/'registration.json');p=process_identity(reg['pid'])
    live=bool(p and p['state']!='Z' and p['start_ticks']==reg['start_ticks'])
    terminal=next((read(root/f) for f in ['completion.json','failure.json'] if (root/f).exists()),None)
    assert live or terminal is not None,(name,'Missing owner requires reconciliation')
    phase=read(root/'status.json') if (root/'status.json').exists() else {}
    row=dict(batch=name,pid=reg['pid'],start_ticks=reg['start_ticks'],verified_live=live,actual_process=p,
        phase=phase,terminal_receipt=terminal,observed_at=now,registration=str(root/'registration.json'),tool_session=session)
    if 'pid' in phase:
        child=process_identity(phase['pid']);row['phase_child_actual']=child
        row['phase_child_live']=bool(child and child['state']!='Z' and child['start_ticks']==phase.get('start_ticks'))
    receipts[name]=row
    if live:active.append(row)
queued=[r for r in active if r['phase'].get('status','').startswith('waiting_')]
archive=read(D/'multiobjective_low_resource_timing_03/completion.json');assert archive['passed'] and archive['records']==333
strict=read(D/'low_resource_strict_terminal_summary_01.json');assert strict['passed']
vector=read(D/'low_resource_dual_timing_02/endpoint/completion.json');assert vector['passed']
paper=read(D/'strict_terminal_vector_feedback_paper_binding_01.json');assert paper['passed']
feedback=read(D/'vector_feedback_subset_01/completion.json');assert feedback['passed']
actions=[
    'User explicitly said 恢复. Scientific work continues on real server owners. get_goal was checked twice after that request and reports usageLimited, not active/paused/blocked/complete; available goal tools cannot set active or clear usage limit. Record this platform automatic-continuation status honestly; do not invent a reset, create a replacement goal, mark research complete/blocked or revive old date/call/matrix/author restrictions. Existing server jobs/queues are unaffected. Manual user-directed work and evidence updates were actually performed.',
    'Current canonical legal observation archive333 is multiobjective_low_resource_timing_03. Full native-order resource cohort is sealed: native82SB/5062CB/2059591wire and paired43SB/5060CB/2061353wire at13.607436066820355ns, native5/paired9accepts,2061.28/7293.64s imported workflow,9/19nativechildren. Additional1762wire buys39SB/2CB. This is not equal-compute/cold time; metadata versions and all old records preserved.',
    'Registered45SB source-prefix strict phase now terminal PASSED after3actual accepts:13.607436→13.421610→13.413972→13.228145689936355ns, final2061301wire/45SB/5060CB,3028.242633s imported repair. Same-CPD old79SB point uses1419lesswire but34moreSB/1moreCB. Entire endpoint vector differs582better/312worse; all35oldnear components and near-set membership stay identical. Relative to own45SB source11better/17worse, no increased hold violation. All10final winning source-only distances exactly reused with0gap and0newqueries, only optimistic static zero-RC reference, not global native proof.',
    'Independent full-vector branch terminal PASSED with6proposals0accepts and2747.930289s imported/reuse workflow; it reused exact common work and is not standalone cold algorithm time. Rejections: primary/all-positive combined and critical-owner exchanges regress full setup components; target-only and owner-only endpoint-flat. In target-only, actual73896/p1switch delay improves by0.007639ns but complete vector remains unchanged: tied max paths within the same endpoint. Do not conclude secondary timing mechanisms ineffective from this menu.',
    'New feedback plan vector_feedback_subset_01 is derived from the same rejected aggregate/current source only. Exclude actions with donors whose observed physical delay increased; retained targets68613/p1+73896/p1 with donors3914/p7882,47973/p2,57360/p1 form5connections. Both compressed current path patterns are covered, minimum optimistic gain0.007639001ns. It is a new exact source/request, not previous historical-best configuration, no relaxed acceptance/tolerance. Actual native/FULLSTA is required because changed occupancy/order can invalidate aggregate monotonicity.',
    'Actual vector_feedback_subset_native_01 owner58975 waits for completed_resource_timing_dev_01 owner2326, then prepares one native whole transaction on the original45SB input with unchanged full-vector/strict rules and exactcaps2061627wire/45SB/5060CB. It will record legal/process success separately from policy acceptance and donor/vector changes. Current menu/probe failure never ends research. Do not silently replace it by a near-band policy; first test this mechanism with the existing full-vector rule.',
    'completed_resource_timing_dev_01 owner2326 follows the completed original dual-policy owner and is active: each fully automatic resource endpoint, native82SB and paired43SB, receives fresh full-graph observation and the same native current-STA strict repair opportunities under original-root wire and its own post-resource vertical cap. Both roots come from complete resource menus, not selected prefixes. This is a stronger entire-phase native control; quality and all phase times remain separate, no reused creation time assigned to a cold configuration.',
    'Global delay_rr_id pristine A0/R1/Tf transfer owner67432 is active. Its full-independent-audit source version remains frozen. Direct-scope live equivalence owner60372 waits for its terminal; native-count live equivalence owner84229 waits for direct-scope terminal. Native-count owner01 was replaced before any actor/native submission solely to add try/finally pool retirement and failed final-check cost logging; owner02/newactorv2 normal search/selection/acceptance unchanged, old0-submission receipt preserved. Do not create competing pools/writers.',
    'Native-count private evaluator8, resource assurance and final selected-state independent proof passed real2worker replay/7negative guards, selector4cases plus2nonempty4candidate source tests,0newVPR. Whole automatic live equivalent trajectories still unproven. Counter evidence stays native; no fake independent audit. Only the selected final state is independently publication-certified; all other private native-legal states retain complete evidence and their own verification requirement. When archiving their nondominated alternatives, perform required state-specific validation rather than discarding them or borrowing the final proof.',
    'Next whole-scope comparison should extend timing-first fast-A0 resource menus beyond historical2accept pilots as well as completed resource-first timing roots; do not attribute prefix/opportunity differences to phase ordering. Resource-weighted unrestricted native pricing is a mechanism-distinct stronger control suggested by82vs43SB and extra wire, potentially avoiding paired hard-domain search overhead. Same fixed global settings/native controls, true Tdel/FULLSTA and final resource accounting remain mandatory. Do not merely sweep adjacent delay/query budgets.',
    'Current focused C183v2 paper is6pages, joint figure220BNNobservations/124unique quality coordinates fromarchive333 includes strongA0/R1/U/Tf. It explicitly separates43SB resource endpoint from45SB strict timing phase and completed zero-accept vector control; the new feedback scope is pending. Cold configuration timing, broader frozen-policy/initial-routability/tail confirmation remain outstanding. New work local, publicf7167bd unchanged; no push/commit requested.',
]
for name in ['CONTINUATION.json','live_handoff.json']:
    path=D/name;shutil.copy2(path,history/name);value=read(path)
    value.update(updated_at=now,observed_at=now,research_state='ongoing',current_goal_state='usageLimited',
        goal_tool_state_observed=dict(status='usageLimited',tokensUsed=15026399,timeUsedSeconds=177584,
            checked_after_explicit_resume=True,available_tool_can_clear_usage_limit=False),
        explicit_user_resume_received=True,platform_automatic_continuation_limited=True,
        previous_goal_turn_classification='progress',research_blockers=[],old_caps_revoked=True,
        author_metadata_blocks_research=False,active_jobs=active,active_owners=active,supervisors=active,runners=active,
        queued_jobs=queued,running_jobs=[r for r in active if r not in queued],latest_owner_verification=receipts,
        next_actions=actions,latest_paper=paper)
    value['latest_multiobjective']=dict(archive='multiobjective_low_resource_timing_03',points=333,
        parent_merged_archive='multiobjective_merged_seed_resource_01',summary='multiobjective_low_resource_timing_03/composition_summary.json',
        quality_counts=archive['quality_counts'],retention_counts=archive['retention_counts'],
        record_count_is_not_configuration_count=True,complete_cold_configuration_seconds=None,new_work_pushed=False)
    value['multiobjective_policy']['archive']='multiobjective_low_resource_timing_03'
    value['latest_low_resource_dual_timing'].update(owner=receipts['low_resource_dual_timing_02'],
        whole_trajectory_pending=False,strict_accepted_steps=3,secondary_accepted_steps=0,
        strict_terminal_summary='low_resource_strict_terminal_summary_01.json',
        final_strict_CPD_ns=strict['CPD_final_ns'],final_strict_resources=strict['final_resources'],
        strict_imported_workflow_seconds=strict['complete_imported_strict_workflow_seconds'],
        secondary_imported_reuse_workflow_seconds=vector['complete_imported_state_workflow_seconds'],
        complete_single_configuration_algorithm_seconds=None)
    value['latest_completed_resource_timing']=receipts['completed_resource_timing_dev_01']
    value['latest_vector_feedback_subset']=dict(preparation='vector_feedback_subset_01/completion.json',
        actual_native_outcome_pending=True,owner=receipts['vector_feedback_subset_native_01'])
    value['latest_native_resource_census'].update(live_equivalence_owner=receipts['native_census_resource_equivalence_02'],
        live_actor='run_native_census_resource_repair_v2.py',
        cleanup_binding='native_census_resource_actor_cleanup_binding_01.json',full_automatic_equivalence_pending=True)
    value['latest_native_pending']=dict(status='active_pristine_transfer_full_resource_timing_and_engineering_controls',owners=active)
    value['active_current_sta_batch']=dict(owners=active,combined_native_VPR_maximum=3,
        pool_parent_plus_child=2,serial_native_chain=1,registered_versions_unchanged=True)
    value['next_algorithm_hypothesis']=actions[3:7]+actions[9:10]
    value['git_publication']['new_work_pushed']=False
    write(path,value)
protocol=D/'RESEARCH_PROTOCOL.md';marker='20261114_resume_strict_terminal_vector_feedback'
if marker not in protocol.read_text():
    with protocol.open('a') as out:
        out.write(f'\n\n{now} {marker}\n'
            '用户明确“恢复”，继续服务器科研与已有队列。平台get_goal两次显示usageLimited，当前工具无恢复active接口；'
            '该平台自动续跑状态单列，不能伪称active或借此设科研blocked/complete/重建Goal，已有实验不重启。\n'
            'strict45SB/5060CB三接受已终封13.228145689936355ns/2061301wire，导入3028.242633s；'
            '独立全vector6提案0接受，导入/复用2747.930289s，非单配置冷时间。与旧79SB同CPD点多1419wire少34SB/1CB，'
            'setup582改善312退化但旧near35全部逐值/集合相同；最终10winning源-only参考全0gap，0新queries，不作native全局最优界。\n'
            'target-only中73896/p1真实物理改善而全vector持平，说明同端点并列path；aggregate的donor退化不等于机制未触发。'
            '新同源failure-feedback剔除actual增延donor actions，自动得68613/1+73896/1与3donor共5连接，'
            '覆盖两path patterns最小乐观gain0.007639ns，未重复旧请求、未放宽vector/caps。'
            '单owner58975待整资源endpoint时序owner2326后新native/FULLSTA验证，尚无收益。\n'
            '整资源phase已完成native82/paired43源，两者同当前STA/原生修复机会在owner2326执行，'
            '原root wire上限不滚动，post-resource垂直caps各自明示；不把43SB与45SB新CPD拼接。'
            'native-count live owner01仅在提交0actor时更换owner02/84229，补final异常时必退native pool并记录cost，'
            '正常版本输入/搜索/接受不变，原运行实验不改。\n'
            '当前联合档案333观察，主稿C183v2六页，220BNN观察/124坐标；全vector失败有机制解释、反馈scope待验证。'
            '完整冷算法、跨电路冻结确认/成功率/尾部未完成，科研持续；单进程保护和总VPR≤3保持，'
            '无总体日期/总调用/矩阵/作者清单停止，新增本地未推送。\n')
write(history/'update_binding.json',dict(passed=True,observed_at=now,owners=receipts,native_calls=0,route_calls=0,
    platform_goal_status='usageLimited',explicit_resume_requested=True,
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),D/'strict_terminal_vector_feedback_paper_binding_01.json',
        D/'low_resource_strict_terminal_summary_01.json',D/'multiobjective_low_resource_timing_03/completion.json',
        D/'vector_feedback_subset_01/completion.json']},
    updated_artifact_sha256={str(D/n):sha(D/n) for n in ['CONTINUATION.json','live_handoff.json','RESEARCH_PROTOCOL.md']}))
print(dict(active=[r['batch'] for r in active],archive_records=333,platform_goal_status='usageLimited',
           scientific_work='ongoing on explicit user instruction',history=str(history)),flush=True)
