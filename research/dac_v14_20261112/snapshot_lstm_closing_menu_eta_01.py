"""Snapshot closed transactions and code-grounded conditional scheduling."""
import datetime
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

root=D/'LSTM_closing_menu_ETA_01';assert not root.exists()
repair=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/cp1r3_distinct_input_cohort_01/lstm/domain/flow/resource_flow/repair')
controller=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1r3/runtime/run_unified_resource_repair_v1.py')
code=controller.read_text()
assert 'for ci in range(min(3,len(cuts)))' in code
assert 'for oi in range(min(a.owner_rank_windows,len(groups)))' in code
reg=read(repair/'registration.json');assert reg['owner_rank_windows']==3
assert reg['bundle_size']==8 and reg['domain_mode']=='paired'
rows=[];bound={str(controller):sha(controller),str(repair/'registration.json'):sha(repair/'registration.json')}
root.mkdir()
for name in ['round_011/candidate_00','round_012/candidate_00','round_012/candidate_01']:
    tx=repair/name;done=read(tx/'completion.json');assert done['passed']
    closed={}
    for role,row in done['roles'].items():
        d=read(tx/(role+'_decisions.json'));c=d['endpoint_vector']['comparison']
        closed[role]=dict(status=row['status'],resources=row['resources'],cpd_s=row['cpd_s'],
            resource_acceptance=row['policies']['resources_under_timing'],
            source_wire_delta=d['resources_under_timing']['resource_delta']['wirelength'],
            wire_over_cap=max(0,row['resources']['wirelength']-2390475),
            setup_improved=c['setup_improved'],setup_regressed=c['setup_regressed'],
            hold_violation_regressions=c['hold_violation_regressions'])
    copied=root/'receipts'/name;copied.mkdir(parents=True)
    for f in [tx/'completion.json',tx/'process_costs.json',tx/'registration.json',
              *[tx/(role+'_decisions.json') for role in done['roles']]]:
        assert f.stat().st_size<2*1024**2
        (copied/f.name).write_bytes(f.read_bytes());bound[str(f)]=sha(copied/f.name)
    rows.append(dict(transaction=name,complete_transaction_seconds=done['complete_orchestrator_seconds'],roles=closed))
state=read(repair/'current_state.json');write(root/'current_state_snapshot.json',state)
assert state['accepted_steps']==12
single=[505.0548777580261,530.2649465538561]
double=[min(r['complete_transaction_seconds'] for r in rows),max(r['complete_transaction_seconds'] for r in rows)]
owner=[655.658279,662.136143];tail=839.158877
# Pending third scope remaining0..an observed whole double-pass duration;
# conditional three owner windows as calibrated from this circuit's native arm.
lo=(3*owner[0]+tail)/60;hi=(double[1]+3*owner[1]+tail)/60
extra_cycle=[3*single[0]/60,(3*double[1]+3*owner[1])/60]
roles=read(D/'submission_candidate_followup_02/role_status_and_eta.json')['role_states']
observed=datetime.datetime.now(datetime.timezone.utc).isoformat()
write(root/'progress_and_eta.json',dict(observed_at=observed,current_prefix_steps=12,
    current_state=state,closed_transactions=rows,complete_double_pass_seconds=double,
    complete_double_pass_mean_seconds=sum(r['complete_transaction_seconds'] for r in rows)/len(rows),
    confirmed_role_states=roles,pending_scope='round_012/candidate_02',
    conditional_no_further_commit=dict(remaining_domain_minutes=[lo,hi],
        confirmation_and_original_supplement_hours=[lo/60+2+10/60,hi/60+8+40/60]),
    extra_resource_owner_menu_cycle_minutes=extra_cycle,
    assumptions=['Pending scope residual0..observed1070s, not a measured completion prediction.',
        'Three owner windows as native calibration; actual current owner selection not yet produced.',
        'Tail839.16s and owner655.66..662.14s are native calibration, not measured domain remaining work.',
        'Four later roles2..8hours provisional; DLA not yet calibrated; original supplemental replay10..40min provisional.',
        'Any accepted resource or owner candidate restarts selection; extra cycles are possible without a fixed number or time cap.',
        'All ETA components are scheduling observations, never assembled into a measured full-role algorithm cost.'],
    additional_raw_admission_eta=None,queued_simple_cost_baseline_eta=None,
    whole_domain_quality_admitted=False,formal_pair_ratio=None,new_native_or_STA_calls=0,
    original_failures_preserved=True,current_rules_changed=False,source_sha256=bound))
(root/'ETA.md').write_text(f'''# 当前闭菜单阶段的条件性ETA

更新时间：{observed}。LSTM/domain保留12次提交；round012第二候选已完成，两臂均拒绝，第三候选运行中。第二候选domain为2390941/419/8316，超线长上限466；native为2390326/426/8316，少44线长但垂直资源无改善。三次已闭合双臂事务耗时约{double[0]:.2f}–{double[1]:.2f}秒；完整角色尚未终结，也没有正式配对比例。

冻结控制器每轮尝试最多3个资源窗口；未接受后可尝试最多3个owner窗口。当前已完成本轮前两个资源窗口。若第三窗口和后续owner窗口均不再提交，按同电路native的三个owner窗口与尾段校准，domain剩余约{lo:.1f}–{hi:.1f}分钟。加四个待执行角色暂估2–8小时及原补充重审10–40分钟，条件性剩余约{lo/60+2+10/60:.1f}–{hi/60+8+40/60:.1f}小时；raw准入耗时尚未标定，另外计算。

这不是无条件上界：owner数量尚未观察到；任何新提交会重新选组。再打开一轮资源/owner菜单，按已观察单臂/双臂/owner费用可额外增加约{extra_cycle[0]:.1f}–{extra_cycle[1]:.1f}分钟，新的超时和诊断也可延长。不存在额外轮次停止限制。基线已在raw准入后排队，其私有构建与实际审计尚未标定，不能附加一个已测完成时间。

LSTM/native原执行结束但原验证失败，质量未准入；domain仍运行；DLA-small与eltwise-SB共四角色未执行。上述拼接仅用于条件性排程，不作为完整算法成本。原失败、所有拒绝与实际费用保留，正文不添加当前检查点收益。
''')
print(dict(output=str(root),observed_at=observed,remaining_domain_minutes=[lo,hi],
    confirmation_plus_original_supplement_hours=[lo/60+2+10/60,hi/60+8+40/60],extra_cycle_minutes=extra_cycle))
