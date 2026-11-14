#!/usr/bin/env python3
"""Reconcile completed grouping outcomes and independent batching development."""
import shutil,time
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';s=read(D/'bnn_selected_group_summary_01.json');v=read(D/'bnn_selected_group_vector_analysis_01.json');assert s['passed'] and v['passed'];tiny=read(D/'native_batch_tiny_regression_02/completion.json');assert tiny['passed']
tex=p/'data/selected_batch_progress_v14.tex';assert not tex.exists()
tex.write_text(r'''
\section{Uniform group selection outcomes and static-state amortization}
\subsection{Whole outcomes under a fixed selection rule}
The previously registered uniform 0.9 current-path proxy rule has completed both native weighted transactions from pristine Tf and strong A0. The rule retains at least 90\% of the best current-winning-path gain proxy, then minimizes the union of target and owner repair branches. It was frozen before these outcomes, rather than selected per circuit from historical results. R1's two-target selected request exactly matches a completed native control and is reused.

\begin{table}[t]
\centering\small
\caption{Completed fixed-rule group outcomes versus the original all-positive group. Same pristine source, native cost, full-device domain, original budgets and one transaction opportunity; the submitted subset changes to test group selection.}
\begin{tabular}{lrrrr}
\hline
Source & Branches & CPD (ns) & Wire & SB/CB\\
\hline
Tf all-positive & 16 & 13.413972 & 2074309 & 105/5062\\
Tf selected & 13 & 13.413972 & 2074301 & 105/5062\\
A0 all-positive & 29 & 13.413972 & 2070921 & 98/5067\\
A0 selected & 14 & 13.421610 & 2070881 & 98/5067\\
\hline
\end{tabular}
\end{table}

Both selected states pass complete native FULL/STA and physical checks. Tf selection preserves exact CPD and saves eight wire units relative to its larger group. Against pristine Tf, fourteen setup components improve with none regressing, so all four policies accept. Against the larger repaired group, however, two setup components regress, by at most 115.384 ps, and none improves. Both remain at least 5.884 ns from the selected worst slack and the 0.2 ns near-critical set is unchanged. Thus four-axis CPD/wire/SB/CB dominance does not mean every endpoint improves; vector evidence remains attached to the state.

A0 selection saves forty wire units relative to its larger group at 7.638334409 ps greater CPD. Against pristine A0 it improves nine setup components and regresses seven; strict CPD and timing-under-resource policies accept, while endpoint-vector and wire-reduction policies reject. Against the larger repaired group, three setup components improve and twelve regress, with a maximum regression of 178.186 ps. This is a legitimate observed tradeoff, not a failed candidate solely because another transaction has better CPD. Subsequent automatic actors must select from their own accepted state; a later transaction may address the migrated bottleneck without restoring every unnecessary branch. Those trajectory results remain pending.

The two-transaction shared workflow takes 849.970 s, including native diagnostic processes, candidate audits, full candidate STA and successor selection. Search cores are 0.600 s for Tf and 0.573 s for A0; these are nested component times, not complete algorithm runtimes. Earlier independent workflow timings do not constitute a paired speedup measurement.

\subsection{Independent static-state batching branch}
Repeated static loading dominates the prototype cost. An isolated native version factors the existing transaction routine into an explicit request interface and supports a fully parsed list of independent requests on one loaded state. Each transaction still restores original occupancy and leaves global route trees unchanged. Objective values are passed explicitly without changing environment variables. This batching is for alternative proposals from one immutable state; it must not replace current-STA reselection after an accepted update.

A real tiny regression compares all four native cost modes with isolated execution, repeats a request after objective changes, and includes an actual capacity-infeasible physical-soft transaction followed by a successful transaction. Complete tree edges, physical delays, capacities, feasibility, objective and heap statistics match after excluding only elapsed fields. Fresh post-batch physical delay reconstruction and native STA equal the original state. Ambiguous single-plus-batch and duplicate-output manifests are rejected. Previously completed isolated test processes are reused explicitly after correcting a test assumption that all four modes would succeed; no packing or routing flow is repeated. This proves the tested bookkeeping and equivalence behavior, not BNN quality or performance.

A separately registered engineering cohort waits after the existing automatic and reservation cohorts: six completed A0 scope/cost requests share one loaded BNN state, and repeated failed/successful SPMV requests test recovery. Final candidate quality remains attached to each original individual FULL/STA evaluation. Batch cost includes extra post-batch fresh STA validation and is not compared to old isolated times as a speedup. Full cold single-configuration timing and state reuse across accepted changes remain separate work.
''')
main=p/'main.tex';text=main.read_text();needle=r'\input{data/selected_batch_progress_v14.tex}';assert needle not in text;main.write_text(text.replace(r'\section{Conclusion}',needle+'\n\n'+r'\section{Conclusion}'))
with (p/'claims_evidence.md').open('a') as f:
 f.write('\n| C121 | 统一0.9组选的真实合法结果与端点代价 | [组选汇总](../bnn_selected_group_summary_01.json)、[向量及近关键](../bnn_selected_group_vector_analysis_01.json)、[完成收据](../bnn_cover_selected_dev_01/completion.json) | Tf13保持CPD且比16连接少8wire，较旧修复态2端点退化但离最坏≥5.884ns；A014比29连接少40wire而CPD差7.638ps。两态均合法，规则预先统一冻结，完整单配置时间未知；四策略轨迹继续 |\n')
 f.write('| C122 | 同态原生事务批量复用的独立实现和真实小图验证 | [构建绑定](../native_batch_stage_02/binding.json)、[微型回归](../native_batch_tiny_regression_02/completion.json)、[大图登记](../native_batch_equivalence_dev_01/registration.json) | 四目标/重复请求结果一致，真实失败后成功、重新计算原生延迟与STA恢复、歧义及重复输出拒绝通过。0新pack/route流程，复用3个已完成单例进程；BNN/SPMV大图仍排队，非新质量或完整算法加速证据 |\n')
for name in ['README.md','mechanisms_and_ablation.md']:
 with (p/name).open('a') as f:f.write('\nC121–C122加入统一组选的Tf资源收益与A0时序/线长取舍，保留端点向量退化；新增静态原生事务批量复用分支及小图真实失败恢复验证。大图等价与完整性能未知，既有当前STA/保留实验不改。本地新增未推送。\n')
ledger=p/'data/evidence_v14_ledger.json';hist=p/'data/ledger_history_20261113/before_selected_batch_01.json';assert not hist.exists();shutil.copy2(ledger,hist);l=read(ledger)
names=['export_selected_batch_progress.py','summarize_selected_group_results_01.py','analyze_selected_group_vectors_01.py','bnn_selected_group_summary_01.json','bnn_selected_group_vector_analysis_01.json','native_batch_implementation_02.json','native_batch_stage_02/binding.json','native_batch_stage_02/build_result.json','native_batch_tiny_regression_02/completion.json','native_batch_evidence.py','run_native_static_batch_analysis.py','prepare_native_batch_equivalence.py','native_batch_equivalence_dev_01/registration.json','queue_native_static_batch.py','paper/data/selected_batch_progress_v14.tex']
l['sources_sha256'].update({n:sha(D/n) for n in names});l['updated_at']=time.time();l['selected_batch_progress']=dict(claims=['C121','C122'],selected_outcomes_complete=True,large_batch_equivalence_pending=True,new_work_pushed=False);write(ledger,l);print('Exported C121-C122')
