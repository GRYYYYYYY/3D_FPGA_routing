#!/usr/bin/env python3
"""Refresh real owners, composition hypothesis and exact resource/vector policy."""
from datetime import datetime,timezone
from pathlib import Path
import shutil
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

now=datetime.now(timezone.utc).isoformat();history=D/'continuation_history'/('low_resource_timing_'+str(time.time_ns()));history.mkdir()
receipts={};owners=[]
for name,directory,session in [
    ('fused_resource_development_01','fused_resource_development_01/queue',53193),
    ('fused_resource_archive_queue_01','fused_resource_archive_queue_01',24213),
    ('merge_seed_resource_archive_queue_01','merge_seed_resource_archive_queue_01',88338),
    ('seed_census_client_validation_01','seed_census_client_validation_01',33227),
    ('stable_seed_transfer_dev_01','stable_seed_transfer_dev_01/queue',67432),
    ('direct_scope_resource_equivalence_02','direct_scope_resource_equivalence_02/queue',60372),
    ('low_resource_dual_timing_02','low_resource_dual_timing_02/queue',76605),
]:
    root=D/directory;reg=read(root/'registration.json');p=process_identity(reg['pid'])
    live=bool(p and p['state']!='Z' and p['start_ticks']==reg['start_ticks'])
    terminal=next((read(root/f) for f in ['completion.json','failure.json'] if (root/f).exists()),None)
    assert live or terminal is not None,(name,'Missing owner requires reconciliation')
    phase=read(root/'status.json') if (root/'status.json').exists() else {}
    item=dict(batch=name,pid=reg['pid'],start_ticks=reg['start_ticks'],verified_live=live,
        actual_process=p,phase=phase,terminal_receipt=terminal,observed_at=now,
        registration=str(root/'registration.json'),tool_session=session)
    if 'pid' in phase:
        c=process_identity(phase['pid']);item['phase_child_actual']=c
        item['phase_child_live']=bool(c and c['state']!='Z' and c['start_ticks']==phase.get('start_ticks'))
    receipts[name]=item
    if live:owners.append(item)
diag=read(D/'low_resource_timing_headroom_04/completion.json');assert diag['passed']
paper=read(D/'low_resource_headroom_paper_binding_01.json');assert paper['passed']
proof=read(D/'explicit_envelope_timing_policy_validation_01.json');assert proof['passed']
paired=D/'fused_resource_development_01/bnn_A0_feedback_K8';steps=read(paired/'steps.json');last=steps[-1]
winner=next(row for row in last['pair'].values() if row.get('evaluation')==last['committed_evaluation'])
observation=Path(diag['observation_state']);vector=read(observation/'endpoint_vector.json')
clock_echo=Path(read(observation/'completion.json')['run'])/'native_sta_frontier.jsonl.constraints.echo'
constraints=dict(echo=str(clock_echo),sha256=sha(clock_echo),SDC='bnn.sdc not supplied; native default timing constraints',
    clock_domains=[dict(id=0,name='ap_clk',clock_source_timing_node=0)],clock_model='ideal',
    launch_capture_pairs=[[0,0]],input_output_delays_s=0,setup_hold_constraints_s=0,
    endpoint_ids=len(vector['endpoint_ids']),setup_components=len(vector['setup']),hold_components=len(vector['hold']),
    vector_key='timing node, atom pin, name, launch clock, capture clock',
    hold_rule='No increased negative hold slack; positive margin may decrease without hold violation.',
    numerical_rule='Exact native float values represented at full precision; no epsilon/rounding/rolling budget.')
queued=[r for r in owners if r['phase'].get('status','').startswith('waiting_')]
actions=[
    'Preserve original native-order resource actor and all registered clients/archives/transfer/direct-equivalence owners. Original paired private prefix is refreshed from steps;8accepts44SB/5060CB/2061341wire observed, CPD13.607436ns. The45SB input for the new timing diagnostic is the explicitly frozen seventh accepted prefix, not falsely called latest or final after the resource branch advances. Final archive requires actor seal; no competing writer.',
    'New current-cone headroom diagnostic04 passed on the frozen45SB prefix: native FULL/STA complete vector equals source; exact max-arrival cone has1endpoint and10routed connections. Five source-only static-switch gaps remain:26319/p1 and47878/p2 each0.18582579919268483ns,68613/p1,73896/p1,73897/p1 each0.007639000543235852ns. Seven exact graph/driver/root/sink/anchor references reused, three absent queries8.83s, actual forward edges verified after removing reverse virtual anchor. Occupancy, mandatory branches and sharing are relaxed; never sum as feasible CPD improvement or native global bound.',
    'Original diagnostic01 native observation passed but wrapper omitted explicit graph echo; retain138.44s and failure. New explicit-export observer02 native/full-vector/current cone passed138.08s; cache discovery mistakenly selected obsolete01, then03 stopped at3missing exact references.04 reuses all successful native/cone/query artifacts and queries just3missing inputs. Record both observation segments and all failures; no route searches in this diagnostic, no fabricated cold or single-method time.',
    'low_resource_dual_timing_02 actual owner76605 now runs strict then secondary from the same frozen45SB/5060CB prefix full observation, wire2061627 anchored at pristine root, no rolling budgets. run_independent_critical_portfolio_v4 inherits latestv3 problem identity fixes, changes only resource-bounded endpoint policy. Both modes have same fresh currentSTA selector, proposal/scope/full-device native search and full physical/FULLSTA checks; each reselects after own accepts. Reuse native outcomes only for exact same current source/request, never copy a strict successor after divergence. All repairs use native search: this is composition/acceptance evidence, not custom capacity-mechanism superiority.',
    'Strict reference remains timing_under_resources requiring exact CPD decrease. Secondary endpoint_under_resources requires CPD nonworse plus all fixed endpoint/clock setup components nonworse and at least one strict improvement, no increased hold violation and same fixed caps. Nine negative controls include one-ULP regression, budget overflow, identity change, hold violation, incomplete native transaction and visited state. Seven actual recorded policy cases pass; one existing native82SB whole-trajectory endpoint is strict-rejected/vector-admissible, not proof of an automatic flat first step enabling later CPD.',
    'Record automatic proposals, every strict rejection/secondary admissibility and actual commits separately. Analyze whether flat accepts remove tied bottlenecks and precede later CPD improvement or only resource/time cost. Current initial cone endpoint809929; actual next proposals come from live current selector, not permanent net/pin whitelist. Native bnn.sdc absent: default single ap_clk domain0, ideal clock, setup/hold and IO constraints0; exact echo digest and52527endpoint IDs/52495setup/hold components bound. Use every full-precision component; report actual near-band and critical-path migration after commits.',
    'Primary source/routing cohorts remain pending, client/global stable policy and direct audit engineering comparisons retain their original actual owners. Combined count at most original pool2 plus new timing chain1; after original terminates next registered pool2 may coexist with timing1. All per-process64GiB/1800s/disk80GiB protections remain; a failed branch/probe does not end research. low_resource_dual_timing_01 ended before any repair because its failed diagnostic dependency was not overridden;02 is new independent registered attempt after actual diagnostic passed.',
    'Full algorithm confirmation still requires pristine automatic strongA0/R1/Tf trajectories with fixed circuit-independent rule, strong native equivalent opportunities and same-environment complete route-plus-repair timing. Current imported strategy workflows, two-policy research wall time, analysis segments/core queries and oldU formal times remain distinct. Resource45/44 states not yet final; no new final CPD point or runtime speedup claimed.',
    'FocusedC178 six-page paper binds diagnostic/policy delta and default constraints; private low-resource prefix is explicitly diagnostic and excluded from final figure/score. Current updates local, publicf7167bd unchanged. Goal active, previous turn progress, no dates/totalroutecalls/fixedmatrix/authors termination; move from results to supported mechanism/engineering changes, not only repeated status checks.',
]
for name in ['CONTINUATION.json','live_handoff.json']:
    path=D/name;shutil.copy2(path,history/name);value=read(path)
    value.update(updated_at=now,observed_at=now,research_state='active',current_goal_state='active',
        previous_goal_turn_classification='progress',research_blockers=[],old_caps_revoked=True,
        author_metadata_blocks_research=False,active_jobs=owners,active_owners=owners,supervisors=owners,runners=owners,
        queued_jobs=queued,running_jobs=[r for r in owners if r not in queued],latest_owner_verification=receipts,
        next_actions=actions,latest_paper=paper)
    value['latest_paired_private_prefix']=dict(accepted_steps_observed=len(steps),latest_committed_evaluation=last['committed_evaluation'],
        CPD_s=winner['CPD_s'],resources=winner['resources'],actor_seal_required=True,not_a_final_archive_point=not(paired/'completion.json').exists())
    value['latest_low_resource_headroom']=dict(summary='low_resource_timing_headroom_04/completion.json',passed=True,
        positive_connections=[{k:r[k] for k in ['net','pin','potential_ns']} for r in diag['rows'] if r['potential_ns']>0],
        source_state=diag['source_state'],observation_state=diag['observation_state'],reused_queries=7,new_queries=3,
        native_route_search_calls=0,prior_analysis_segments=diag['prior_successful_native_analysis_segments'],
        optimistic_relaxation_not_feasible_CPD_gain=True)
    value['latest_low_resource_dual_timing']=dict(owner=receipts['low_resource_dual_timing_02'],
        input_prefix_accepts=7,fixed_absolute_limits=dict(wirelength=2061627,SB_pairs=45,CB_sources=5060),
        implementation='run_independent_critical_portfolio_v4.py',policy_validation='explicit_envelope_timing_policy_validation_01.json',
        constraints=constraints,composition_diagnostic_only=True,complete_single_configuration_algorithm_seconds=None,
        old_no_submission_failure='low_resource_dual_timing_01/queue/completion.json')
    value['latest_fused_resource_development']=receipts['fused_resource_development_01']
    value['latest_fused_resource_archive']=receipts['fused_resource_archive_queue_01']
    value['active_current_sta_batch']=dict(owners=owners,combined_native_VPR_maximum=3,
        pool_parent_plus_child=2,parallel_timing_chain=1,registered_original_versions_unchanged=True)
    value['latest_native_pending']=dict(status='resource_and_independent_current_STA_composition',owners=owners)
    value['next_algorithm_hypothesis']=actions[1:6]
    value['git_publication']['new_work_pushed']=False
    merged=D/'multiobjective_merged_seed_resource_01/completion.json'
    if merged.exists() and read(merged).get('passed'):
        value['latest_multiobjective'].update(archive=merged.parent.name,points=read(merged)['records'])
        value['multiobjective_policy']['archive']=merged.parent.name
    write(path,value)
protocol=D/'RESEARCH_PROTOCOL.md';marker='20261114_low_resource_headroom_dual_acceptance'
if marker not in protocol.read_text():
    with protocol.open('a') as out:
        out.write(f'\n\n{now} {marker}\n'
            '原资源配对actor原版本继续，观察8接受44SB/5060CB/2061341wire/13.607436ns，未终封不作最终结果。'
            '新timing composition严格固定此前第7个合法prefix45SB/5060CB/2061265wire，不随原actor推进改输入。\n'
            '该prefix完整原生FULL/STA全向量一致；精确current winning cone1端点809929/10连接。'
            '5项源-only静态gap：26319/p1、47878/p2各0.18582579919268483ns；68613/p1、73896/p1、73897/p1各0.007639000543235852ns。'
            '7严格参考命中，只新增3项8.83s，去反向虚拟anchor后核实际正向边。路径放松capacity/保留树/共享，不相加为可实现CPD收益或全局native界。\n'
            '独立观察01漏显式echo，FULL/STA通过138.44s；02补echo后通过138.08s，cone成功但误选旧未封cache01；'
            '03遇3cache缺失停止，04仅补3离线距离，保留全部失败、成功native及分段成本，无重跑成功route/query。\n'
            '真实low_resource_dual_timing_02 owner76605已启动strict后endpoint两策略，'
            '相同冻结起点、完整当前STA选择、scope/native全设备搜索/真实替换/物理/FULLSTA和固定wire2061627/SB45/CB5060预算。'
            'v4继承最新v3 problem-identity修复；strict CPD严格下降原规则不变，次级CPD非退化且全setup端点/domain向量不退化并至少1改善，'
            'hold违例不增加。分叉后各选自身当前状态，仅严格同源同请求复用。单ULP退化也拒绝，不用epsilon/滚动budget。'
            '7已有真实状态策略case+9负例验证通过，不等于新自动修复已有效。\n'
            'BNN没有外部bnn.sdc，native默认ap_clk单域0、ideal、IO和setup/hold约束0；echo SHA和52527endpoint IDs、52495setup/hold组件固定。'
            '逐候选记录strict拒绝/secondary可接受与实际commit，随后是否CPD改善及并列瓶颈/资源开销分别分析，不能只记admissible即accept。'
            '原始dual01未通过诊断依赖而0repair结束；02新独立登记，未越过guard。\n'
            '并发原pool2+timing1，总VPR≤3；所有单进程超时/内存/磁盘保护保留，局部失败不止Goal。'
            '导入策略时间/双策略研究时间/诊断分析分段/core/冷完整route+repair分列，不用旧U替代；'
            '新C178六页稿已封存，私有prefix排除最终图/方法分数，本轮本地未推送。Goal active，无总日期/调用/矩阵/作者清单停止。\n')
write(history/'update_binding.json',dict(passed=True,observed_at=now,owners=receipts,native_calls=0,route_calls=0,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'low_resource_timing_headroom_04/completion.json',
        D/'explicit_envelope_timing_policy_validation_01.json',D/'low_resource_headroom_paper_binding_01.json']},
    updated_artifact_sha256={str(D/n):sha(D/n) for n in ['CONTINUATION.json','live_handoff.json','RESEARCH_PROTOCOL.md']}))
print(dict(active=[r['batch'] for r in owners],paired_private_accepts=len(steps),
    composition_root_SB=45,positive_headroom=5,history=str(history)),flush=True)
