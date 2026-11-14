#!/usr/bin/env python3
"""Update manuscript with complete strong controls and bounded development claims."""
import shutil,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';summary=read(D/'bnn_strong_scope_summary_01.json');assert summary['passed'] and len(summary['rows'])==12
assert all(sha(path)==h for path,h in summary['source_sha256'].items())
assert read(D/'pending_reservation_tiny_regression_02/completion.json')['passed']
auto=read(D/'automatic_R1_replay_recovery_01/completion.json');assert auto['passed'] and auto['accepted_steps']==1 and auto['native_mode']=='reuse_only'
tex=p/'data/automatic_reservation_progress_v14.tex';assert not tex.exists()
text=r'''
\section{Completed strong controls and a competition-directed intervention}
\subsection{Whole outcomes and observed resource tradeoffs}
All twelve registered transactions from pristine strong A0/R1 now pass native FULL/STA and independent physical checks. Within a starting state and repair scope, native weighted and physical-delay/hard-capacity searches receive the same full-device domain, current-STA targets, request order, tree scope and acceptance opportunities. Across their objectives both physical cost and capacity treatment change together; these paired arms do not isolate capacity alone.

\begin{table}[t]
\centering\small
\caption{Completed strong-baseline development transactions. W denotes native weighted search, P physical-delay/hard-capacity search. Changes are relative to each arm's own pristine source. Counts are actual occupied resources.}
\begin{tabular}{llrrrr}
\hline
Source/scope & Cost & CPD (ns) & $\Delta$wire & $\Delta$SB & $\Delta$CB\\
\hline
A0 combined & W & 13.413972 & +88 & 0 & 0\\
A0 combined & P & 13.413972 & +172 & +5 & +3\\
A0 targets & W & 13.607436 & $-20$ & 0 & 0\\
A0 targets & P & 13.785623 & $-20$ & 0 & 0\\
A0 owners & W & 13.607436 & $-8$ & 0 & 0\\
A0 owners & P & 13.607436 & +32 & 0 & 0\\
R1 combined & W & 13.413972 & $-8$ & 0 & 0\\
R1 combined & P & 13.413972 & +8 & 0 & 0\\
R1 targets & W & 13.413972 & $-20$ & 0 & 0\\
R1 targets & P & 13.413972 & $-20$ & 0 & 0\\
R1 owners & W & 13.421610 & 0 & 0 & 0\\
R1 owners & P & 13.421610 & +16 & 0 & 0\\
\hline
\end{tabular}
\end{table}

Only combined repair lowers A0's CPD. Weighted target-only repair instead preserves CPD and reduces wire by twenty, so it remains a legitimate resource-budget candidate despite strict-CPD rejection. For R1, target-only repair already attains 13.413972155262854 ns, reduces wire by twenty and has no endpoint-vector regression. Adding owner reroutes attains the same CPD with more wire and setup regressions. Owner release therefore has a demonstrated interaction for the shown Tf/A0 states, not a universal advantage. The physical-delay/hard-capacity bundle adds no improvement on the four quality axes over the weighted arm of any matched scope here. This does not determine complete runtime or every endpoint-vector comparison.

The observed joint archive includes strong A0/R1, U, Tf and repaired states. Earlier U observations on SPMV, some elementwise states and the BNN physical owner-only A0 state are quality-dominated by recorded strong baselines. Some comparisons differ in convergence or repair opportunities: they are descriptive state comparisons, not fair complete-algorithm superiority claims. Full runtime, convergence, opportunity, batch and CPD precision remain row-specific. Quality-dominated states with unknown comparable runtime are not erased. Current same-CPD R1/A0/Tf states retain the previously reported CB versus wire/SB tradeoff; fixed-architecture occupancy changes do not imply area or power changes.

\subsection{Measured cost and automatic current-state control}
The complete shared twelve-arm development workflow takes 5302.923 s. Executed diagnostic-native wrappers sum to 1725.222 s, candidate audits to 513.095 s, complete candidate FULL/STA wrappers to 2541.699 s and successor selection to 409.574 s. The remaining 113.332 s covers coordinator work outside these child intervals. Actual repair-search cores sum to only 12.195 s within the diagnostic wrapper intervals; this nested sum must not be added again. State construction, loading, checking and timing dominate this prototype. These are shared-workflow/component costs, excluding original routing and cache construction, not complete single-configuration algorithm times or historical U timing.

The automatic current-STA controller now implements fresh feedback, group selection, native replacement, FULL/STA, exact acceptance or rollback and target reselection after each acceptance. Independently queued Tf/A0 strict and endpoint-vector trajectories keep their registered version and initial states; no fresh trajectory outcome is claimed here. An R1 read-only exact-reuse diagnostic accepts one existing native result, reducing CPD from 13.421610489672275 to 13.413972155262854 ns and wire by twenty. New feedback from its own accepted state then finds no positive group in this operator class. Zero new native processes were launched for that diagnostic. A relative-path integration assertion was recovered from preserved completed artifacts; the earlier 415.271 s child work and 8.628 s recovery segment remain separate, with total cold algorithm time unknown. A local positive-winning-path operator stop does not exhaust resource-only or near-critical proposals.

\subsection{Observed sequential competition and pending-target reservations}
The A0 target-only physical arm exposes a concrete counterexample: although legal, it worsens CPD by 178.186798649 ps. Earlier target net 73896 takes three capacity-one nodes on the original path of later target 73897. Reconstructing the exact temporary occupancy and own-net retained-tree credit gives an independent capacity-feasible shortest delay of 1.2209908917260037 ns, exactly the native result, versus 1.0428040930765548 ns originally. This supports sequential competition rather than a failed shortest-path calculation for this event; it is not an impossibility bound on other schedules.

An isolated native version reserves original resources for unprocessed explicit critical targets, releases its own net's reservations during each search, updates occupancy after each replacement and clears virtual occupancy on both success and rollback. Donors remain released. A real small native off/on regression passes unchanged-input, unchanged-original-STA and occupancy-restoration checks. An initial runtime failure exposed missing sink indexing on route-file-loaded trees and was fixed using VPR's existing net-bound tree-copy constructor; failed versions and logs remain preserved. Large BNN benefit is unknown. A separately registered target-only/combined by weighted/physical by off/on batch waits after existing trajectories. Default-off must reproduce old candidate bodies, and final candidates still require independent physical legality, complete native FULL/STA and exact fixed-budget decisions. If reservation merely exchanges starvation for other detours or failures, scheduling or joint allocation becomes the next discriminating intervention.
'''
tex.write_text(text)
main=p/'main.tex';s=main.read_text();needle=r'\input{data/automatic_reservation_progress_v14.tex}';assert needle not in s and r'\section{Conclusion}' in s;main.write_text(s.replace(r'\section{Conclusion}',needle+'\n\n'+r'\section{Conclusion}'))
with (p/'claims_evidence.md').open('a') as f:
 f.write('\n| C118 | 强A0/R1十二臂全部合法与完整开发流程成本 | [十二臂汇总](../bnn_strong_scope_summary_01.json)、[完成收据](../bnn_strong_release_joint_dev_01/completion.json)、[多目标逐状态](../multiobjective_tradeoff_summary_01.json) | A0仅组合降CPD；R1仅目标已足够，owner额外开销/退化；weighted在四质量轴无劣于physical成对臂。共享流程5302.923s、核心累计12.195s，不是完整单配置时间。收敛/机会不同的档案只描述状态 |\n')
 f.write('| C119 | 自动流程已实现，R1精确复用后重选验证 | [流程冻结](../automatic_workflow_stage_01/binding.json)、[R1恢复收据](../automatic_R1_replay_recovery_01/completion.json)、[新四轨迹登记](../bnn_automatic_trajectories_dev_02/registration.json) | 一次接受后当前态重查无正组选，0新native；415.271s原子进程与8.628s恢复分列、完整冷启动未知。Tf/A0独立轨迹尚排队，局部算子终止非Goal结束 |\n')
 f.write('| C120 | A0顺序竞争反例与独立原生保留候选 | [因果临时态](../A0_target_order_causal_summary_01.json)、[stage03](../native_reservation_stage_03/binding.json)、[微型回归](../pending_reservation_tiny_regression_02/completion.json)、[独立登记](../pending_reservation_dev_02/registration.json) | 早期目标占三个容量1节点使后目标增加178.186798649ps，精确条件查询=原生；保留开/关小图记账/恢复通过，BNN收益未知，仍须关侧复现/trace/完整合法与FULLSTA，不声称新算法已提升质量 |\n')
for name in ['README.md','mechanisms_and_ablation.md']:
 with (p/name).open('a') as f:f.write('\nC118–C120更新强A0/R1十二臂、完整共享流程/核心不同口径、已实现自动流程与R1只读回放、临时容量顺序竞争及保留资源独立候选。后续批次仍按原版本运行；已构建/微型回归不代替BNN质量结果。新成果均在f7167bd之后，仅本地、未推送。\n')
ledger=p/'data/evidence_v14_ledger.json';history=p/'data/ledger_history_20261113/before_automatic_reservation_01.json';assert not history.exists();shutil.copy2(ledger,history);l=read(ledger)
names=['export_automatic_reservation_progress.py','bnn_strong_scope_summary_01.json','summarize_strong_scope_results_01.py','multiobjective_tradeoff_summary_01.json','summarize_multiobjective_frontier_01.py','automatic_workflow_stage_01/binding.json','automatic_R1_replay_recovery_01/completion.json','A0_target_order_causal_summary_01.json','native_reservation_stage_03/binding.json','native_reservation_stage_03/build_result.json','pending_reservation_tiny_regression_02/completion.json','pending_reservation_dev_02/registration.json','paper/data/automatic_reservation_progress_v14.tex']
l['sources_sha256'].update({n:sha(D/n) for n in names});l['updated_at']=time.time();l['automatic_reservation_progress']=dict(claims=['C118','C119','C120'],strong_twelve_complete=True,reservation_large_benefit_unknown=True,new_work_pushed=False);write(ledger,l)
print('Exported C118-C120',len(l['sources_sha256']))
