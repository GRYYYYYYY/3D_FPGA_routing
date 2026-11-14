#!/usr/bin/env python3
"""Update joint-frontier, resource-potential, native-domain and complete-cost evidence."""
import shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';census=read(D/'resource_opportunity_census_01/completion.json');scopes=read(D/'shared_crossing_scopes_01/completion.json');a0=read(D/'A0_portfolio_archive_summary_01.json');cost=read(D/'A0_portfolio_execution_cost_01.json');assert all(x['passed'] for x in [census,scopes,a0,cost]);assert read(D/'resource_domain_tiny_regression_02/completion.json')['passed'];points=read(D/'multiobjective_archive_24/points.json');summary=read(D/'multiobjective_tradeoff_summary_07.json');rows=[]
for name,state in [('A0 root',D/'timing_cone_bnn_dev_02/A0'),('R1 root',D/'timing_cone_bnn_dev_02/R1'),('Tf root',D/'timing_cone_bnn_dev_01/Tf')]:
 row=next(r for r in points if r['state']==str(state));rows.append(dict(label=name,**row))
for group in summary['bnn_observed_quality_frontier']:
 records=[r for r in points if r['id'] in group['records']]
 if any('A0_endpoint/round_002/proposal_05' in r['id'] for r in records):label='A0 archive';row=next(r for r in records if 'A0_endpoint/round_002/proposal_05' in r['id'])
 elif any('expanded_free_weighted' in r['id'] for r in records):label='Tf free';row=next(r for r in records if 'expanded_free_weighted' in r['id'])
 elif any('R1_target_only_weighted' in r['id'] for r in records):label='R1 native';row=next(r for r in records if 'R1_target_only_weighted' in r['id'])
 elif any('owner_first' in r['id'] for r in records):label='Tf owner-first';row=records[0]
 else:assert all(r['arm']=='U' for r in records);label='U formal';row=records[0]
 rows.append(dict(label=label,**row,collapsed_record_ids=[r['id'] for r in records]))
write(D/'current_joint_frontier_overview_01.json',dict(passed=True,archive='multiobjective_archive_24',rows=rows,qualification='Three pristine roots plus all five distinct observed BNN quality-frontier groups. Input-matched descriptive states, not per-circuit configuration nomination or equal-convergence/opportunity algorithm superiority. U CPD is rounded and retains an interval; no timing borrowed across points.'))
tex=p/'data/resource_sharing_and_archive_v14.tex';assert not tex.exists();body=r'''
\section{Joint frontier retention and resource-oriented development}
\subsection{Whole outcomes before local acceptance}
The completed strong-A0 endpoint actor tries thirteen proposals, exactly reuses four old native observations, launches nine new native transaction coordinators and accepts two updates. Its branch terminates locally at13.599797732410934 ns, wire2070797/SB98/CB5067, because no remaining current-menu proposal satisfies the endpoint-vector rule. This does not terminate the research or erase rejected legal routes. In particular, an automatically generated target-first critical-owner exchange is legal at13.413972155262854 ns and wire2070781/SB98/CB5067. Relative to pristine A0 it improves CPD and removes fifty-two wire units; at the same CPD it removes140 more wire units than the earlier A0 combined native repair. Its single regressed setup component remains2.300783 ns above the new worst slack. The endpoint actor rejects it, but it advances the observed four-quality-axis frontier and is retained in the final archive. Its owner-first counterpart has the same wire and slower CPD, with a different endpoint-vector tradeoff. Search-state acceptance and final candidate retention therefore remain separate.

\begin{table}[t]
\centering\small
\caption{Matched-input BNN roots and all five distinct collected quality-frontier groups. Original method/convergence and subsequent repair opportunities differ; this is a descriptive state comparison. U CPD is rounded. No historical timing is attached to repair states.}
\begin{tabular}{lrrrr}
\hline
State & CPD (ns) & Wire & SB & CB\\
\hline
'''
for row in rows:body+=f"{row['label']} & {row['CPD_ns']:.6f} & {row['wirelength']} & {row['SB_pairs']} & {row['CB_sources']}\\\\\n"
body+=r'''\hline
\end{tabular}
\end{table}

\subsection{Resource loss and mechanism choice}
A streaming census over four sealed legal states exactly reproduces all existing planar-wire, SB/CB unique-resource and per-net occupation counts, launching zero native or routing flows. None of pristine A0/R1/Tf or the accepted A0 endpoint state has a pure cross-layer-and-return excursion. Their layer-cut reference requires5103 crossing nets. Actual resource counts exceed the terminal-layer-only reference by62,55 and64 at the three pristine roots. That difference ignores topology, capacity and physical timing; it is an optimistic reference, not a feasible saving or global optimum. The75k-scale slack-bearing removal scopes are overlapping, before reconnection, and cannot be summed into final savings.

This evidence changes the intervention from removing layer excursions to sharing an existing crossing among more branches. The selector derives all noncritical crossing-source groups whose pruning leaves another crossing in the same net's tree, screening every affected sink at more than0.2 ns above current worst slack. It ranks removed resources per pruned sink, then fewer sinks, larger minimum margin and IDs, uniformly across states. A0/R1/Tf yield72/62/70 scopes; all independently choose net31972,pin8. Pruning this connection removes one CB while retaining an SB that might support reconnection. The minimum screening margins are12.185249 ns for A0 and11.999423 ns for R1/Tf. This remains a feasibility hypothesis until native routing and complete STA.

\subsection{Native ablation and independent design requirements}
The independent default-off native resource-domain version permits selected connections to extend only through crossing sources already held by their current partial tree. Original physical delay and congestion costs remain intact; occupancy updates after each replacement. A real two-layer regression demonstrates retained-crossing reuse, intentional failure when no crossing remains, unchanged native output with the feature off, original-state restoration and fresh independent FULL/STA of the successful candidate. A failed forced-layer fixture collided IO pads; the recovery preserves that record and reuses its completed packing and valid placement, moving only CLBs and the shared input. It does not rerun packing.

Six independent development roles compare unrestricted and reuse-only native weighted search from pristine A0/R1/Tf, holding request, removed/retained branches and order fixed. They are queued after the existing frozen portfolio. All use one absolute development envelope: CPD at most13.607436066820355 ns, wire at most2076392, SB at most105 and CB at most5072. The rule takes maxima across the specified pristine roots, with wire multiplied by1001/1000 and rounded upward using integer arithmetic. The resource objective requires SB and CB both nonincreasing and at least one strictly decreasing. Strict CPD and the original endpoint rule are still recorded. This is a registered development design point, not a rolling tolerance, universal selection policy or research stopping rule. No-new-crossing is a local ablation domain; later private joint transactions may temporarily use new resources and check final budgets as a whole. If unrestricted native search already produces the same route, the result belongs to selection/scheduling rather than a new search primitive.

\subsection{Complete observed cost and remaining scope}
The completed A0 endpoint imported-state workflow takes3909.490 s. Its nine transaction coordinators consume3302.222 s at the outer level. Nested costs are1266.189 s in native state-analysis drivers,383.069 s in cached physical candidate audits,1471.399 s in full candidate-analysis drivers and129.370 s in successor selection. The nine actual native processes take860.893 s, while search cores sum to7.744 s; these nested levels must not be added together. All failed, rejected, unchanged and reused candidates remain in the accounting. Initial routing and historical evidence creation are excluded, so complete cold single-configuration runtime is still unknown. This measured loading/analysis bottleneck supports integrating the separately validated state-reuse workers in a future independent version; the running quality cohort retains its original binary and policy.
''';tex.write_text(body)
main=p/'main.tex';s=main.read_text();needle=r'\input{data/resource_sharing_and_archive_v14.tex}';assert needle not in s;s=s.replace(r'\section{Conclusion}',needle+'\n\n'+r'\section{Conclusion}');main.write_text(s)
with (p/'claims_evidence.md').open('a') as f:
 f.write('\n| C133 | 强A0合法拒绝候选推进联合质量前沿 | [已完成actor与候选](../A0_portfolio_archive_summary_01.json)、[档案24](../multiobjective_archive_24/completion.json)、[根与全部五前沿组](../current_joint_frontier_overview_01.json) | 13提案、2接受；另有13.413972155ns/2070781wire/SB98/CB5067被端点策略拒绝但合法非支配，较原A0少52wire、同CPD较旧A0组合少140。单setup退化距新最坏≥2.300783ns。非整体科研结束 |\n')
 f.write('| C134 | 资源诊断支持共享跨层而非删除层返回绕行 | [四态精确census](../resource_opportunity_census_01/completion.json)、[全部输出摘要封存](../resource_census_artifact_seal_01.json)、[共享范围](../shared_crossing_scopes_01/completion.json) | 4态0纯返回绕行，A0/R1/Tf高于端点切割参考62/55/64；参考非可行节省。72/62/70组，统一排序首选同net31972/p8。原始物理指标逐项匹配，0原生/route调用 |\n')
 f.write('| C135 | 保留跨层资源域已真实双层验证，六臂待运行 | [实现与回归](../resource_domain_stage_01/native_validation_binding_01.json)、[tiny完整结果](../resource_domain_tiny_regression_02/completion.json)、[六臂登记](../shared_crossing_repair_dev_01/registration.json)、[共同绝对预算](../shared_crossing_repair_dev_01/shared_design_requirements.json)、[实际排队身份](../shared_crossing_repair_dev_01/queue/registration.json)、[完整成本](../A0_portfolio_execution_cost_01.json) | 关项原native完全一致，开项共享成功/无保留时不可行/占用恢复/候选FULLSTA。共享域是隔离实验、非永久边界；大型资源收益未知。3909.490s导入态流程与7.744s核分开，均非冷完整算法时间 |\n')
with (p/'mechanisms_and_ablation.md').open('a') as f:f.write('\nC133–C135：已完成A0端点actor的合法拒绝点改进联合质量前沿；0层返回绕行反证改变资源干预位置，转向已保留跨层源共享。统一资源/sink排序与共同绝对开发预算六臂排队，完整物理/STA仍须验证。No-new域只隔离当前机制，不限制未来事务组合；成本分外层/子流程/核，冷完整时间未知。\n')
status=p/'DEVELOPMENT_STATUS.md';status.write_text('# 最新：C133–C135（资源共享独立开发）\n\nA0 endpoint本轮终态13提案/2接受；另有合法13.413972155ns、wire2070781/SB98/CB5067被端点策略拒绝但保留非支配，较原A0少52wire，同CPD较旧组合少140。完整导入态工作流3909.490s，非冷完整算法时间。档案24=129观察，五个BNN质量前沿组包含强原生R1、A0候选、U与Tf。\n\n四态census无层返回绕行，改研究跨层树干共享。resource_domain_stage01已构建、双层回归通过；shared_crossing_repair_dev01六角色在既有portfolio后接续，实际大图资源收益未知。共同绝对预算已登记，旧v3运行版本不改；所有新增仅本地，未推送。\n\n'+status.read_text())
ledger=p/'data/evidence_v14_ledger.json';history=p/'data/ledger_history_20261113/before_resource_sharing_01.json';assert not history.exists();shutil.copy2(ledger,history);l=read(ledger)
files=[tex,D/'A0_portfolio_archive_summary_01.json',D/'A0_portfolio_execution_cost_01.json',D/'multiobjective_archive_24/completion.json',D/'multiobjective_archive_24/points.csv',D/'multiobjective_tradeoff_summary_07.json',D/'current_joint_frontier_overview_01.json',D/'resource_opportunity_census_01/completion.json',D/'resource_census_artifact_seal_01.json',D/'shared_crossing_scopes_01/completion.json',D/'resource_domain_stage_01/native_validation_binding_01.json',D/'resource_domain_tiny_regression_02/completion.json',D/'shared_crossing_repair_dev_01/registration.json',D/'shared_crossing_repair_dev_01/shared_design_requirements.json',D/'shared_crossing_repair_dev_01/queue/registration.json']
for path in files:l['sources_sha256'][str(path.relative_to(D))]=sha(path)
write(ledger,l);print(dict(sources=len(l['sources_sha256']),frontier_groups=len(summary['bnn_observed_quality_frontier']),claims=['C133','C134','C135']))
