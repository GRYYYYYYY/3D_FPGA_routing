#!/usr/bin/env python3
"""Update current methods/results while preserving the exploratory evidence trail."""
import shutil,time
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';result=read(D/'critical_exchange_results_summary_01.json');portfolio=read(D/'portfolio_zero_bounds_summary_01.json');engineering=read(D/'static_batch_reservation_summary_01.json');assert result['passed'] and portfolio['passed'] and engineering['passed'];assert read(D/'multiobjective_archive_22/completion.json')['passed']
tex=p/'data/portfolio_frontier_progress_v14.tex';assert not tex.exists()
tex.write_text(r'''
\section{Current portfolio method and verified timing--resource outcomes}
\subsection{Problem and mechanism}
A primary group optimized for the current winning timing paths can be inadmissible under a fixed endpoint-vector or resource objective. We therefore use one fixed proposal order: primary 0.9 group, all-positive combined repair, target-only repair and owner-only repair, deduplicating equal native requests. Rejection advances to the next proposal on the same state; acceptance triggers fresh current STA and feedback on that policy's own state. If the first tier is exhausted, a second tier derives critical-owner dependencies from audited conflicts, expands the noncritical release scope along conditional owner paths, and tries native target-first followed by owner-first schedules. All circuits and policies use these rules; no per-circuit historical best is chosen. Native weighted search freely chooses every path. Conditional model certificates help construct the proposal and avoid repeated queries, but never substitute for final legality or STA.

Strict CPD, nonworse-CPD plus fixed-domain setup-vector improvement, timing-under-resources and resources-under-timing remain distinct exact acceptance modes. The new zero-headroom development mode fixes wire/SB/CB limits and CPD ceiling at the pristine routed start, without a rolling allowance. The timing objective requires current CPD improvement within those fixed resources; the resource objective requires current wire reduction within the fixed timing bound. A local menu stop is not proof that all FPGA routing opportunities are exhausted.

\subsection{Whole native controls and attribution}
All five critical-owner controls are legal. With the selected target path fixed, the seven-connection scope worsens CPD from 13.413972155262854 to 13.777984975149593 ns. Expanding the release closure to thirteen connections reaches 13.228145689936355 ns. The independently run free target-first native weighted control produces the identical complete candidate, so fixing the queried target witness is unnecessary in this case. The supported mechanism is dependency closure plus scheduling over the existing native kernel, not a new connection-search primitive.

\begin{table}[t]
\centering\small
\caption{Complete native outcomes from the same current Tf state. Wire/SB/CB count actual resources. P changes physical cost and capacity treatment together. Native free/preset weighted candidates share one exactly matched FULL/STA evaluation, with separate native execution provenance.}
\begin{tabular}{lrrrr}
\hline
Configuration & CPD (ns) & Wire & SB & CB\\
\hline
Current source & 13.413972 & 2074301 & 105 & 5062\\
Minimal preset weighted & 13.777985 & 2074321 & 105 & 5062\\
Expanded preset weighted & 13.228146 & 2074313 & 105 & 5062\\
Expanded free weighted & 13.228146 & 2074313 & 105 & 5062\\
Expanded preset P & 13.228146 & 2074349 & 106 & 5063\\
Expanded owner-first weighted & 13.413972 & 2074277 & 105 & 5062\\
\hline
\end{tabular}
\end{table}

The fast weighted state improves one setup component and regresses two, without a hold-violation regression. Both regressed endpoints remain at least 2.114957 ns above the new worst slack. Its exact endpoint-vector policy therefore rejects even though strict CPD and timing-under-resource policies accept. The physical/capacity bundle reaches the same CPD with thirty-six more wire units and one additional SB/CB resource, adding no four-axis quality benefit. Owner-first weighted repair preserves the complete endpoint vector and reduces wire by twenty-four. Target-first versus owner-first is consequently a real 185.826 ps versus thirty-six-wire tradeoff, not a reason to discard the latter state solely for worse CPD. These are small local wire changes, not area or power reductions.

\subsection{Automatic pristine starts and fixed-root requirements}
The generic exchange request is byte-identical to the successful native free control. A strict portfolio starting at pristine sealed Tf automatically accepts the primary thirteen-connection group and then the generated exchange, reaching 13.228145689936355 ns, wire2074313/SB105/CB5062. A separately parameterized zero-headroom timing actor repeats those exact decisions using matched native quality evidence. Relative to pristine Tf (13.421610489672275 ns, wire2074317/SB105/CB5062), CPD improves while wire decreases by four and SB/CB do not grow.

The zero-headroom resource actor instead rejects the faster exchange's intermediate wire increase and accepts owner-first, reaching 13.413972155262854 ns and wire2074277/SB105/CB5062: forty fewer wire units than its pristine start. Its subsequent proposal awaits new native work. This distinction preserves current transition progress versus fixed initial budgets. All these replay flows launch zero new native processes; they reuse exact already legal candidates while performing fresh current-state queries where needed. Their measured elapsed times exclude historical creation and are not complete cold algorithm times. Root-relative limits are not a shared absolute budget across A0/R1/Tf. New native portfolio trajectories from pristine strong A0/R1 and the resource continuation are independently registered and running; general cross-circuit or initial-routability superiority is unproven.

\subsection{Engineering and recovery evidence}
Large static-state batching completes six BNN and four repeated failed/successful SPMV transactions in two native processes, preserving every normalized result and fresh post-batch STA. BNN's native process takes 114.667 s and complete observed component workflow 144.397 s; SPMV takes 8.884 s and 12.862 s. These are observed component costs, not paired speedups or full configuration times. BNN's nested timers show 40.70 s loading the RRG within 42.87 s creating the device, plus 13.08 s packing load, 5.20 s circuit load and 7.42 s route load. These costs motivate state-loading reuse while preserving fresh pin-equivalence synchronization and complete native analysis.

All four old reservation-on failures are implementation assertions before candidate completion. The corrected stage04 large pair is legal: off has 13.785623309559014 ns, on has 13.607436066820355 ns, both with wire2070813/SB98/CB5067. Reservation prevents the demonstrated physical-cost starvation regression but only matches the earlier native weighted target-only outcome; it does not establish superiority over that stronger control. Separate native configurations sharing an exact evaluation now retain distinct code/request/environment records, and the shared evaluation's measured time is never reassigned as another method's runtime. Complete algorithm timing remains unknown.
''')
main=p/'main.tex';history=p/'data/ledger_history_20261113/main_before_portfolio_frontier_01.tex';assert not history.exists();shutil.copy2(main,history);s=main.read_text();start=s.index('\\begin{abstract}');end=s.index('\\end{abstract}',start)+len('\\end{abstract}')
abstract=r'''\begin{abstract}
Vertical connectivity and shared channel capacity make routed timing depend on coordinated resource choices. We study a reachability-constrained shared-crossing guide and a subsequent current-STA repair method under fixed packed netlists, placement and physical timing models. Initial guide experiments expose limited delay coverage, failures and runtime overhead. The repair method derives groups from current winning timing paths and scarce-resource owners, expands dependency closures, and invokes native search transactionally under exact timing or resource requirements. In one legal BNN development case, an automatic two-step sequence from a sealed pristine route reduces CPD from 13.421610 to 13.228146 ns while decreasing wire by four units and preserving SB/CB occupancy. A matched native free-choice control produces the same candidate, attributing this result to closure and scheduling rather than a new search primitive. An alternative schedule preserves more timing slack than the initial route while reducing forty wire units. Strong-start transfer experiments continue; suite-wide quality, initial routability and complete cold runtime gains are not established. We retain endpoint regressions, failures and code/input provenance, and separate final Pareto retention from intermediate acceptance.
\end{abstract}'''
s=s[:start]+abstract+s[end:]
old='Our contributions are a finite shared-crossing objective with explicit fallback behavior; fixed-input evaluation across switch-block (SB), output connection-box (CB-O), and hybrid (Hybrid-O) connectivity, separating two placement flows and three baseline identities; and mechanism analysis connecting improvements and regressions to coverage, final resources, changing worst paths, and runtime costs.'
new='Our study combines a finite shared-crossing objective and explicit fallback behavior with a current-STA coordination layer for native post-legal repair. The latter builds current-path groups, identifies resource-owner dependencies, and preserves exact final legality and timing while exploring timing--resource tradeoffs. Fixed-input controls separate initial-guide behavior, candidate scope, search schedule and existing native search; cross-circuit confirmation and complete runtime measurements remain ongoing.'
assert old in s;s=s.replace(old,new);s=s.replace('The results support conditional timing effects, not a general performance victory.', 'The initial-guide results support conditional timing effects, not a general performance victory. Later current-STA repair results and their narrower development populations are reported separately.')
needle=r'\input{data/portfolio_frontier_progress_v14.tex}';assert needle not in s;s=s.replace(r'\section{Conclusion}',needle+'\n\n'+r'\section{Conclusion}');main.write_text(s)
with (p/'claims_evidence.md').open('a') as f:
 f.write('\n| C127 | 五原生控制证实扩展闭包及调度取舍 | [完整结果及尾部](../critical_exchange_results_summary_01.json)、[五臂收据](../critical_owner_exchange_dev_01/completion.json) | 扩展自由weighted与preset同完整候选13.228145690ns；最小范围13.777984975ns退化。owner-first13.413972155ns/2074277wire；free target-first2074313wire，两退化端点距新最坏≥2.114957ns。physical同CPD但资源更差，不能归因为新kernel |\n')
 f.write('| C128 | 从封存原Tf自动取得时序/资源两种固定根预算取舍 | [自动及零余量流程](../portfolio_zero_bounds_summary_01.json)、[基础提案验证](../current_portfolio_validation_01/completion.json)、[双顺序及精确预算](../current_exchange_portfolio_validation_02.json) | timing零余量两接受到13.228145690ns，较原Tf少4wire；resource零余量到13.413972155ns、少40wire，后续native待执行。无人工起点注入，0新VPR，仅严格匹配质量复用；冷算法时间未知、根相对预算非跨方法共同绝对预算 |\n')
 f.write('| C129 | 大图批量等价与多sink修复的实际边界 | [工程与恢复汇总](../static_batch_reservation_summary_01.json)、[批量收据](../native_batch_equivalence_dev_01/completion.json)、[恢复收据](../reservation_prune_recovery_dev_01/completion.json) | 2进程10事务结果/新鲜postSTA一致，非正式加速。旧ON4项均实现断言；stage04大图ON回到13.607436ns，匹配旧weighted target-only，未胜更强控制 |\n')
 f.write('| C130 | 共用完整评估时保留独立配置和真实时间归属 | [档案22](../multiobjective_archive_22/completion.json)、[配置记录](../multiobjective_archive_22/points.csv)、[共享评估凭据](../multiobjective_archive_22/shared_evaluation_observations.json) | 120观察含复用评估、非120独立配置；native核/请求/环境与STA核分开，alias不借用创建时间，完整单配置成本仍未知。旧归档不改 |\n')
for name in ['README.md','mechanisms_and_ablation.md']:
 with (p/name).open('a') as f:f.write('\nC127–C130新增可验证正结果及限制：扩展自由原生与preset候选相同，原生kernel不变；两顺序形成CPD/线长取舍，根零余量自动流程成立。更新开发摘要和方法贡献，保留初始guide历史负结果；跨方法共同绝对预算、跨电路和冷完整成本继续验证。本地新增未推送。\n')
status=p/'DEVELOPMENT_STATUS.md';old=status.read_text();status.write_text('''# 当前开发状态（2026-11-14）

权威结果：C127–C130。原生自由选路在扩展关键持有者依赖闭包后达到CPD13.228145690ns，wire2074313/SB105/CB5062；与preset完全相同，贡献归于闭包和调度，非新搜索核。owner-first保持13.413972155ns且wire2074277，完整端点向量不变。两者保留Pareto取舍；fast有2端点退化但距新最坏≥2.114957ns。

封存原Tf起点的自动portfolio已取得两步结果，零增量根资源限制下时序方案CPD降低、wire比起点少4；零增量根时序限制下资源方案wire少40，后续候选尚待native。质量严格复用已完成真实路由，没有新native用于回放；不声称冷完整算法加速。A0/R1新原生轨迹正在运行，实时进程以live_handoff为准。

大图静态批处理2进程10事务等价、新鲜STA一致；stage04保留修复避免physical退化，但只匹配已有weighted结果。档案22含120观察与明确共享评估，未知时间不替换。下一步推进强原生等机会轨迹、共享绝对预算与跨电路确认，并依据已测加载成本优化独立分析进程。研究active，无整体停止日期、次数或矩阵上限，作者信息不阻塞。

以下为原样保留的历史记录，其“最新/待实施/无后台”措辞均不描述当前状态。

'''+old)
ledger=p/'data/evidence_v14_ledger.json';backup=p/'data/ledger_history_20261113/before_portfolio_frontier_01.json';assert not backup.exists();shutil.copy2(ledger,backup);l=read(ledger)
names=['export_portfolio_frontier_progress.py','critical_exchange_results_summary_01.json','summarize_critical_exchange_results.py','static_batch_reservation_summary_01.json','summarize_static_batch_and_recovery.py','portfolio_zero_bounds_summary_01.json','summarize_portfolio_and_zero_bounds.py','current_proposal_portfolio.py','make_current_proposal_portfolio.py','current_portfolio_validation_01/completion.json','make_current_exchange_portfolio.py','make_current_exchange_portfolio_v2.py','current_exchange_portfolio_validation_01.json','current_exchange_portfolio_validation_02.json','run_automatic_portfolio_repair.py','run_automatic_portfolio_repair_v2.py','run_automatic_portfolio_repair_v3.py','prepare_portfolio_execution.py','portfolio_execution_dev_01/registration.json','queue_portfolio_execution.py','append_native_observations_v2.py','append_native_observations_v3.py','multiobjective_archive_22/completion.json','paper/data/portfolio_frontier_progress_v14.tex']
l['sources_sha256'].update({n:sha(D/n) for n in names});l['updated_at']=time.time();l['portfolio_frontier_progress']=dict(claims=['C127','C128','C129','C130'],initial_guide_and_current_repair_populations_separate=True,strong_native_trajectories_running=True,new_work_pushed=False);write(ledger,l);print('Exported C127-C130 with current working abstract and methods')
