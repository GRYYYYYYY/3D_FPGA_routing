#!/usr/bin/env python3
"""Reconcile terminal phase-order and matched native-export evidence into the focused paper."""
import shutil
import time
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
assert read(D / 'resource_first_timing_terminal_summary_01.json')['passed']
timing = read(D / 'export_policy_timing_01/completion.json')
resource = read(D / 'export_policy_resource_01/completion.json')
assert timing['passed'] and resource['passed']
composition = read(D / 'resource_first_composition_01.json')
assert composition['same_CPD_wire_SB_CB']
assert composition['endpoint_comparison_reference_to_resource_first']['setup_improved'] == 0
assert composition['endpoint_comparison_reference_to_resource_first']['setup_regressed'] == 0
h = p / 'data/ledger_history_20261113' / ('phase_export_policy_' + str(time.time_ns()))
h.mkdir()
for name in ['current_repair_main.tex', 'claims_evidence.md', 'mechanisms_and_ablation.md', 'DEVELOPMENT_STATUS.md', 'data/evidence_v14_ledger.json']:
    target = h / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p / name, target)
f = p / 'current_repair_main.tex'
s = f.read_text()
old = 'CPD-changing or forced-path timing transactions remain outside that validated scope.'
new = 'A further same-binary paired export experiment also validates an actual free-path CPD-changing transaction against independent candidate LOAD/FULL/STA. Forced-target-path timing transactions remain outside that validated scope.'
assert s.count(old) == 1
s = s.replace(old, new)
start = s.index(' Its first accepted legal transaction reduces CPD')
end = s.index(' Such a candidate would be lost', start)
s = s[:start] + (' Three automatically accepted transactions now reach13.607436,13.421610,13.413972 and13.228146 ns in order, with wire2059842,2059882,2059878 and2059882;79 SB and5061 CB remain fixed. The last repair expands an observed critical-owner dependency to nine networks and twelve connections. One noncritical connection spends about1.114955 ns of route-delay margin while a critical connection saves about0.185826 ns. Whole native STA improves CPD, but one setup component regresses, so the endpoint-vector policy rejects this step. Relative to the resource-phase input, the complete final vector has eleven improved and seventeen regressed setup components, with no increased hold violation. The fixed source near-critical band has one improvement and no regression. The local current-STA portfolio then yields no further admissible proposal; the research continues with resource and implementation questions.\n\n'
    'The resulting four quality coordinates and complete setup/hold endpoint vectors exactly equal the existing timing-first/guided-K8 endpoint, although the serialized route body differs. This is convergence to a known quality point, not a new frontier gain or a general proof that phase order commutes. All ten current winning-connection switch distances equal already-computed exact source-only optimistic references after graph/root/sink identity checks; no queries are repeated for this diagnosis. The reference relaxes occupancy, shared branches and native arithmetic, so it is not a global native-STA bound. These observations favor resource/runtime and other-scope interventions over merely increasing the same cone query budget.') + s[end:]
old = 'A subsequent resource-only export-level experiment may omit an unused graph dump while preserving actual FULL/STA and complete endpoint/per-pin precision; that optimization is not yet implemented or timed.'
assert s.count(old) == 1
tm, rm = timing['component_measurements'], resource['component_measurements']
new = (f'An independent optional graph-text policy now passes ten tiny native jobs and two same-binary BNN transactions, one CPD-changing and one resource-changing. Full and compact modes have identical native searches, actual candidate routes, complete frontier/constraint bytes and source recovery, and dedicated candidates agree with independent LOAD/FULL/STA. Native FULL and new STA still execute in compact mode; it omits only unused full graph text. Timing-cone selection explicitly requires a full export. In the timing case, full versus compact native-child times are{tm["full"]["native_child_seconds"]:.2f} versus{tm["compact"]["native_child_seconds"]:.2f} s; complete request times are{tm["full"]["request_seconds"]:.2f} versus{tm["compact"]["request_seconds"]:.2f} s. In the resource case, complete requests are{rm["full"]["request_seconds"]:.2f} versus{rm["compact"]["request_seconds"]:.2f} s. Each compact fused worker avoids about2.21 GiB of graph text while retaining about1.05 GiB of full source/candidate/restored frontier data. Measurement order is reversed between cases. These single paired component observations exclude separately recorded shared startup, use explicit exact-byte physical-audit reuse for the second candidate, and include extra LOAD controls only in validation-workflow totals. They are not formal repeated timing or cold whole-algorithm speedups. The terminal resource-first timing recovery segment takes1793.82 s:894.94 s is query/dependency/portfolio work,834.50 s is nested native transaction coordination, and49.76 s is preparation. The older interrupted segment remains separate; no stages are assembled into a synthetic complete configuration time.')
s = s.replace(old, new)
s = s.replace('data/joint_quality_projection_02.pdf', 'data/joint_quality_projection_03.pdf')
f.write_text(s)
version = p / 'data/manuscript_versions/current_repair_C171.tex'
assert not version.exists()
shutil.copy2(f, version)
claims = [
    ('C170', '资源先行current-STA完整局部轨迹与同质量终点', 'resource_first_timing_terminal_summary_01.json', '3次自动接受13.607436→13.421610→13.413972→13.228146ns，79SB/5061CB保持，最终wire2059882。第三次9net/12连接，严格CPD接受而endpoint-vector拒绝；最终与timing-first同完整向量/质量但路由体不同，未推进新前沿。10个静态距离参考严格匹配复用、0新查询，不作全局最优或Goal终止。恢复1793.82s与原中断段分开。'),
    ('C171', '可选图文本导出：实际时序/资源事务双重验证与组件开销', 'export_policy_large_queue_01/completion.json', '10项tiny及两种BNN同binary full/compact配对通过：搜索/真实路由/完整frontier与SDC/源恢复精确相同，独立candidate LOAD一致。实际FULL/newSTA及每pin精度不省，flag入缓存身份和candidate视图，compact禁止cone。单配对/反向顺序与父启动、审计复用和额外验证成本单列；不是全流程加速，forced-path仍未覆盖。'),
]
with (p / 'claims_evidence.md').open('a') as out:
    for key, title, link, claim in claims:
        out.write(f'\n| {key} | {title} | [可核查证据](../{link}) | {claim} |\n')
with (p / 'mechanisms_and_ablation.md').open('a') as out:
    out.write('\nC170–C171：资源先行三步与时序先行达同质量/完整endpoint vector，route body不同；不是新的Pareto改进或一般可交换性证明。第三步联合9net/12连接，允许非关键延迟增加并改善CPD，endpoint-vector因一项setup退化拒绝。原生核未发明新搜索器，机制贡献是currentSTA选择/容量依赖scope/调度与接受。当前winning cone10条物理静态距离已达宽松source-root参考，须把研究转向资源/开销/其他scope，而非只放大此cone预算。compact实际保留FULL、新STA和全部JSON精度，只有graph echo可选，时序cone调用须full；native FULL/STA integration与Python decoder/导出贡献分开验证。\n')
status = p / 'DEVELOPMENT_STATUS.md'
status.write_text('# C170–C171：资源先行局部轨迹完成，实际图导出优化验证\n\n3次接受最终13.228145689936355ns/2059882wire/79SB/5061CB，与既有timing-first/guided-K8完整endpoint向量相同，route body不同。无新四轴前沿；临界组合证实非关键余量可支持关键修复，不能标为endpoint-vector接受。档案285观测、原始失败与强A0/R1/U/Tf保留，缺失冷完整时间仍未知。10tiny和timing/resource实际导出同值验证通过，组件开销另列、未宣称全方法加速。原批次版本不改，后续独立compact/fused自动资源actor已登记并保留相同选择/搜索scope/预算/接受规则的native-only对照。Goal active，无日期/总调用/固定矩阵终止，新增本地。\n\n' + status.read_text())
files = [version, D / 'resource_first_timing_terminal_summary_01.json', D / 'resource_first_composition_01.json',
    D / 'resource_first_timing_prefix_02.json', D / 'multiobjective_archive_50/completion.json',
    D / 'multiobjective_tradeoff_summary_23.json', D / 'common_resource_budget_slices_09.json',
    D / 'export_policy_stage_01/binding.json', D / 'export_policy_tiny_01/completion.json',
    D / 'export_policy_timing_01/completion.json', D / 'export_policy_resource_01/completion.json',
    D / 'export_policy_large_queue_01/completion.json', D / 'fused_resource_development_01/queue/registration.json',
    D / 'export_policy_analysis_pool.py', D / 'pool_state_evaluator_v7.py', D / 'run_fused_resource_bundle_repair_v2.py',
    p / 'data/joint_quality_projection_binding_03.json']
ledger = read(p / 'data/evidence_v14_ledger.json')
for path in files:
    ledger['sources_sha256'][str(path.relative_to(D))] = sha(path)
ledger['sources_sha256']['paper/current_repair_main.tex'] = sha(f)
write(p / 'data/evidence_v14_ledger.json', ledger)
write(p / 'data/phase_export_policy_delta_binding_01.json', dict(passed=True, claims=[row[0] for row in claims],
    source_sha256={str(path): sha(path) for path in files}, manuscript_version=str(version), native_calls=0,
    qualification='New receipt/delta reconciliation only, without rerunning completed experiments or the full historical audit. Separate fixed-policy cold confirmation remains outstanding.'))
print(dict(claims=[row[0] for row in claims], ledger_sources=len(ledger['sources_sha256'])), flush=True)
