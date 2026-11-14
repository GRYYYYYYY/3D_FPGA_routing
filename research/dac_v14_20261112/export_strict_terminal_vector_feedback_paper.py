#!/usr/bin/env python3
"""Completed strict/vector contrast and a qualified same-state feedback hypothesis."""
from pathlib import Path
import shutil
import time
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';terminal=read(D/'low_resource_strict_terminal_summary_01.json')
endpoint=read(D/'low_resource_dual_timing_02/endpoint/completion.json')
assert terminal['passed'] and endpoint['passed'] and endpoint['accepted_steps']==0
archive=D/'multiobjective_low_resource_timing_03';assert read(archive/'completion.json')['records']==333
tail=read(D/'low_resource_equal_CPD_endpoint_tail_02.json');assert tail['passed'] and tail['near_regressed']==0
history=p/'data/ledger_history_20261113'/('strict_terminal_vector_feedback_'+str(time.time_ns()));history.mkdir()
for name in ['current_repair_main.tex','claims_evidence.md','mechanisms_and_ablation.md','DEVELOPMENT_STATUS.md','data/evidence_v14_ledger.json']:
    target=history/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p/name,target)
f=p/'current_repair_main.tex';s=f.read_text();s=s.replace('data/joint_quality_projection_06.pdf','data/joint_quality_projection_07.pdf')
s=s.replace('Archive332 contains219 BNN observations','Archive333 contains220 BNN observations').replace('registered two-accept timing prefix','completed three-accept strict timing phase').replace('collapsed to123 plotted coordinates','collapsed to124 plotted coordinates')
s=s.replace('holds45 SB and5060 CB while reaching13.413972 ns','holds45 SB and5060 CB while reaching13.228146 ns')
s=s.replace('Resource/timing (2) &13.413972&2061297&45&5060','Resource/timing (3) &13.228146&2061301&45&5060')
start=s.index('A separately registered composition freezes the earlier seven-accept45-SB/5060-CB resource prefix.')
end=s.index(r'\subsection{Automatic transfer exposes retained-tree order sensitivity}',start)
s=s[:start]+r'''A registered composition freezes the earlier seven-accept45-SB/5060-CB prefix, distinct from the final43-SB resource endpoint. Its current selector first chooses47878/pin2 plus three slack-bearing donors. Native whole replacement reduces CPD to13.421610490 ns, spending40 wire units without returning vertical resources. Ten setup components improve and seventeen regress; the full-vector policy rejects it. The fixed source near-critical band has one improvement and no regression. A second fresh transaction reaches13.413972155 ns with eleven setup improvements and no regressions. A third critical-owner exchange reaches13.228145690 ns and2061301 wire, preserving45 SB/5060 CB, and the strict current portfolio then terminates. Relative to the old same-CPD79-SB/5061-CB state, this buys34 SB and one CB for1419 wire. Full setup vectors differ by582 improvements and312 regressions, but all35 old near-critical components remain identical and no new component enters that fixed band. The strict imported repair phase costs3028.24 s; complete routing-plus-repair time remains unknown.

The independently initialized full-vector branch accepts none of six proposals and costs2747.93 s. This is not a general failure of secondary timing. A target-only proposal physically improves73896/pin1 but leaves the complete endpoint vector unchanged, exposing tied paths inside the same endpoint. Other aggregates worsen donors. A new same-source feedback rule excludes actions whose donors increased delay in the rejected aggregate. It proposes two small target actions with three donors, covering both current path patterns with a0.007639001 ns optimistic minimum gain. A fresh capacity/FULL/STA experiment is queued with the same exact vector rule and resource caps; no gain is inferred from the new scope alone.

'''.replace('\n+','\n')+s[end:]
f.write_text(s);v=p/'data/manuscript_versions/current_repair_C183.tex';assert not v.exists();shutil.copy2(f,v)
claims=[('C182','45SB严格时序三步终封与同CPD端点尾部','low_resource_strict_terminal_summary_01.json',
    '注册7步45SB/5060CB输入经过3次接受至13.228145689936355ns/2061301wire，strict菜单局部结束。相对旧79SB同CPD点多1419wire少34SB/1CB；全setup582改善312退化，固定旧35近关键组件逐值相同且无新进入。当前winning cone10源-only参考全复用、零新query且gap全零，仅乐观模型局部潜力证据。导入strict3028.24s不是完整冷配置时间。'),
    ('C183','次级六提案零接受的竞争解释与失败反馈组合','vector_feedback_subset_01/completion.json',
    '独立endpoint策略6提案0接受，2747.93s。target-only真实73896物理改善但全vector持平，证明同端点max-fanin plateau；combined有donor退化，不能把coverage/改规划当收益。新同源反馈按实际被拒aggregate剔除delay-increasing donor actions，自动得到68613/1+73896/1及3donor共5连接，压缩两路径最小乐观gain0.007639ns。仅准备与登记原生事务验证，接受规则/SDC/绝对caps不变，尚无实际收益。')]
with (p/'claims_evidence.md').open('a') as out:
    for key,title,link,claim in claims:out.write(f'\n| {key} | {title} | [证据](../{link}) | {claim} |\n')
with (p/'mechanisms_and_ablation.md').open('a') as out:
    out.write('\nC182–C183：strict三接受结束至13.228146ns/45SB/5060CB，不把该CPD套给43SB最终资源点。相对旧79SB同CPD点near35完全相同、无新near进入，582/312其他setup变化完整保留。endpoint6提案0接受不直接否定次级机制：单target物理变好而vector持平说明同端点并列max路径；大组合donor退化拒绝。新失败反馈从同source actual aggregate剔除已观察donor增延的actions，组合两小target覆盖两路径；不是把fraction.9换邻值或放宽向量。必须新native合法/STA及原caps验证，occupancy/order改变仍可导致失败。\n')
status=p/'DEVELOPMENT_STATUS.md';status.write_text('# C182–C183：strict三步终封与同源失败反馈组合\n\n当前联合档案333，BNN220观察124坐标。strict从注册45SB prefix至13.228146ns，资源仍45/5060；endpoint原始批6提案0接受。新反馈组合仅准备并登记待原生验证，未放宽规则、不改变当前/已完成批。最终43SB与诊断45SB两起点区分。恢复指令继续服务器研究；平台Goal工具状态单列于continuation，不据此改写科研证据。新增本地未推送。\n\n'+status.read_text())
files=[v,D/'low_resource_timing_accept_03.json',D/'low_resource_strict_terminal_summary_01.json',
    D/'low_resource_equal_CPD_endpoint_tail_02.json',D/'low_resource_dual_timing_02/endpoint/completion.json',
    D/'low_resource_dual_timing_02/endpoint/attempts.json',archive/'completion.json',archive/'composition_summary.json',
    p/'data/joint_quality_projection_binding_07.json',D/'vector_feedback_subset_01/plan.json',
    D/'vector_feedback_subset_01/completion.json',D/'vector_feedback_subset_native_01/queue/registration.json',
    D/'completed_resource_timing_dev_01/queue/registration.json',D/'native_census_resource_actor_cleanup_binding_01.json',
    D/'native_census_resource_equivalence_02/queue/registration.json']
ledger=read(p/'data/evidence_v14_ledger.json')
for path in files:ledger['sources_sha256'][str(path.relative_to(D))]=sha(path)
ledger['sources_sha256']['paper/current_repair_main.tex']=sha(f);write(p/'data/evidence_v14_ledger.json',ledger)
write(p/'data/strict_terminal_vector_feedback_delta_binding_01.json',dict(passed=True,claims=[c[0] for c in claims],
    source_sha256={str(path):sha(path) for path in files},manuscript_version=str(v),native_calls=0,
    qualification='Completed exact strict/vector phase contrast and new mechanism proposal only. Feedback native outcome, complete cold time and whole research completion remain unproven.'))
print(dict(claims=[c[0] for c in claims],ledger_sources=len(ledger['sources_sha256'])),flush=True)
