#!/usr/bin/env python3
"""Reconcile the first completed strong-A0 pair and current-state grouping method."""
import shutil,time
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';data=p/'data';b=D/'bnn_strong_release_joint_dev_01';decisions={}
for mode in ['weighted_soft','physical_capacity']:
 d=read(b/('A0_combined_'+mode+'_decisions.json'));assert read(b/('A0_combined_'+mode+'_evaluation/completion.json'))['passed'];decisions[mode]=d
assert decisions['weighted_soft']['strict']['comparison']['cpd_after_s']==decisions['physical_capacity']['strict']['comparison']['cpd_after_s']==1.3413972155262854e-08
v=read(D/'critical_group_planner_stage_01/binding.json');assert all(sha(path)==h for path,h in v['source_sha256'].items())
tex=data/'strong_A0_pair_progress_v14.tex';assert not tex.exists()
tex.write_text(r'''
\section{First strong-A0 pair and automatic current-state grouping}
\subsection{Strong baseline outcome and endpoint tail}
The first paired combined transactions from pristine strong A0 have completed native FULL/STA and independent physical checks. Native weighted search reduces CPD from 13.607436066820355 to 13.413972155262854 ns, with 88 additional wire units and unchanged SB/CB counts. Twelve setup components improve and ten regress; no hold violation worsens. Strict CPD and the registered timing-under-resources policy accept, whereas endpoint-vector and wire-reduction policies reject. The largest setup regression is approximately 557.48 ps. All ten regressed endpoints remain at least 1.896 ns above the current worst slack and none enters the current 0.2 ns near-critical set. These regressions remain reported rather than being erased by the CPD gain.

The physical-delay plus hard-capacity pair reaches exactly the same CPD, but adds 172 wire units, five SB pairs and three CB sources relative to A0. Only strict CPD accepts. This outcome again supplies no quality advantage for that objective/capacity bundle over matched native weighted search; it does not isolate hard capacity as a single factor. Remaining strong-baseline scope controls continue under the original registration.

\begin{table}[t]
\centering\small
\caption{Actual current development states at identical exact 13.413972155262854 ns CPD. Full standalone algorithm time remains unknown.}
\begin{tabular}{lrrr}
\hline
State & Wirelength & SB pairs & CB sources\\
\hline
A0 combined weighted & 2070921 & 98 & 5067\\
R1 targets weighted & 2068888 & 86 & 5072\\
Tf combined weighted & 2074309 & 105 & 5062\\
\hline
\end{tabular}
\end{table}

The states express resource tradeoffs: A0 lies between R1 and Tf in CB occupancy while also lying between them in wirelength and SB use. R1 reaches this CPD through two direct repairs without releasing owners. Thus owner release is useful for the demonstrated Tf state but is not necessary for every starting state. This is a descriptive joint frontier with different repair scopes, not a whole-algorithm superiority or area/power claim.

\subsection{From exhaustive reference to automatic proposal}
The initial small reference tests every existing candidate subset: eight each for Tf/R1 and sixteen for A0. A new DAG dynamic program aggregates winning timing paths by their candidate-action bit masks, preserving exact path multiplicities and counting a physical action only once when it maps to multiple atom nodes. It agrees with all 32 exhaustive profiles. A 121-node synthetic diamond DAG with $2^{40}$ paths compresses to two action patterns; coverage and duplicate-action checks pass. Candidate-action pattern counts can still grow exponentially, so this is not a polynomial guarantee in the number of actions.

A bounded branch-and-bound selector retains a fixed fraction of the best current-path gain proxy and minimizes the union of target and owner repair connections. Twelve actual-state/fraction comparisons agree with exhaustive selection; donor-overlap ties and a time-guard case are also checked. If the per-call guard triggers, it preserves a feasible incumbent and explicitly withholds proxy optimality. These are process protections, not research termination conditions. Proxy gains omit post-repair competition and new critical paths, and do not guarantee final CPD.

The current-state planner now reads certified current STA, direct and protected-owner query feedback, derives donor branches from actual trees, and constructs a native request. At a uniform 0.9 fraction it reproduces Tf's 13-connection group and A0's 14-connection group. The accepted Tf successor explicitly has no positive cover in this proposal class. Request construction is byte-identical to the already queued Tf experiment, so that validation creates no duplicate native job. The smaller-scope native outcomes remain pending.

Original design caps and current transition progress are distinct in the new multi-round interface. Six existing first-step decisions are unchanged. On actual legal states, moving from target-only to combined repair improves CPD but increases wire by eight; it therefore passes the timing policy and fails resource progress. The reverse transition can reduce resources within its timing cap while failing strict CPD. Ten checks preserve legality/transaction gates and constant initial budgets. These arithmetic checks make no new route commits, and complete automatic multi-round native integration remains a separate step.
''')
main=p/'main.tex';s=main.read_text();needle='\\input{data/strong_A0_pair_progress_v14.tex}';assert needle not in s;main.write_text(s.replace('\\section{Conclusion}',needle+'\n\n\\section{Conclusion}'))
with (p/'claims_evidence.md').open('a') as f:
 f.write('\n| C116 | 强A0首组配对完成，CPD降低但保留资源/端点退化 | [A0分析](../bnn_strong_A0_combined_analysis_01.json)、[weighted判定](../bnn_strong_release_joint_dev_01/A0_combined_weighted_soft_decisions.json)、[physical判定](../bnn_strong_release_joint_dev_01/A0_combined_physical_capacity_decisions.json) | weighted CPD13.607436066820355→13.413972155262854ns，wire+88/SB0/CB0，setup12好10差；最坏退化557.48ps但离当前最坏至少1.896ns。physical同CPD但wire+172/SB+5/CB+3。其余对照继续、完整算法时间未知 |\n')
 f.write('| C117 | 当前路径动作模式DP/自动选组与多轮接受接口已校验 | [路径DP](../critical_action_patterns_validation_01.json)、[选组](../critical_group_selector_validation_01.json)、[自动接口](../automatic_group_planning_validation_01.json)、[固定锚点](../fixed_anchor_acceptance_validation_01.json) | 32真实子集对照一致；合成2^40路径压缩为2模式；14选组/4接口/10多轮算术检查。选组仅代理模型、13/14连接实际结果待队列，0新增native用于验证；未声称完成全部多轮原生集成 |\n')
for name in ['README.md','mechanisms_and_ablation.md']:
 with (p/name).open('a') as f:f.write('\nC116–C117新增强A0首次合法配对及端点退化尾部、三起点同CPD资源取舍；当前路径模式DP和自动请求构造替代手工历史目标列表，代理/实际原生结果分开，未来多轮预算锚点与当前进步比较已分离验证。\n')
ledger=data/'evidence_v14_ledger.json';history=data/'ledger_history_20261113/before_strong_A0_pair_01.json';assert not history.exists();shutil.copy2(ledger,history);l=read(ledger)
names=['export_strong_A0_pair.py','bnn_strong_A0_combined_analysis_01.json','bnn_strong_release_joint_dev_01/A0_combined_weighted_soft_decisions.json','bnn_strong_release_joint_dev_01/A0_combined_physical_capacity_decisions.json','critical_action_patterns.py','critical_action_patterns_validation_01.json','select_critical_action_group.py','critical_group_selector_validation_01.json','plan_current_critical_group.py','prepare_native_group_step.py','automatic_group_planning_validation_01.json','critical_group_planner_stage_01/binding.json','fixed_anchor_acceptance.py','fixed_anchor_acceptance_validation_01.json','paper/data/strong_A0_pair_progress_v14.tex']
l['sources_sha256'].update({n:sha(D/n) for n in names});l['updated_at']=time.time();l['strong_A0_pair']=dict(claims=['C116','C117'],baseline_scope_controls_pending=True,new_work_pushed=False);write(ledger,l)
print('Exported C116-C117',len(l['sources_sha256']))
