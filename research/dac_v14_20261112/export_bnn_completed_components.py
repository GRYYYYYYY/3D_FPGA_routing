#!/usr/bin/env python3
"""Reconcile the current manuscript with complete six-arm and component-cost evidence."""
import shutil,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';data=p/'data';six=read(D/'bnn_six_scope_component_summary_01.json');bench=read(D/'compact_cone_benchmark_01/completion.json')
assert six['passed'] and bench['passed'] and len(six['rows'])==6 and len(bench['rows'])==10
for c in [six,bench]:assert all(sha(path)==h for path,h in c['source_sha256'].items())
ledger=data/'evidence_v14_ledger.json';history=data/'ledger_history_20261113/before_completed_components_01.json';assert not history.exists();shutil.copy2(ledger,history)
tex=data/'bnn_joint_component_progress_v14.tex';shutil.copy2(tex,data/'ledger_history_20261113/before_completed_components_01.tex');s=tex.read_text()
s=s.replace('for combined and target-only scopes','for combined, target-only and owner-only scopes')
s=s.replace('Targets physical-cap. & 13.421610 & $-4$ & 0 & 0\\\\', 'Targets physical-cap. & 13.421610 & $-4$ & 0 & 0\\\\\n+Owners weighted & 13.421610 & 16 & 0 & 0\\\\\n+Owners physical-cap. & 13.421610 & 112 & 2 & 2\\\\'.replace('\n+','\n'))
s=s.replace('Owner-only results remain pending and can still distinguish release effects from owner rerouting itself.', 'Both owner-only candidates are now complete: CPD is unchanged, one/two setup components improve with no regressions, and wirelength increases by 16/112 respectively. Only endpoint-vector acceptance succeeds. Across both objectives, neither component alone lowers CPD, while their combination does. The weighted combination improves 15 setup components: one overlaps the owner-only improvement and 14 appear only in the combination. These controlled outcomes support an interaction between released owner branches and target repair. They do not identify which individual owner is necessary.')
s=s.replace('contains 94 actual observations','contains 96 actual observations')
tex.write_text(s)
new=data/'compact_selector_progress_v14.tex';assert not new.exists()
new.write_text(r'''
\section{Reducing current-STA scheduling overhead}
\subsection{Implementation and exact scheduling checks}
The prototype's full timing-echo reader reconstructs every graph object and every timing tag before selecting a small current cone. An independent reader stores incoming-edge incidence, source/destination indices, disabled flags and maximum delays compactly, retaining arrival tags only for the selected launch domains and slack tags for the selected endpoints. It checks complete incoming incidence and uses the same native float32 maximum recurrence. Every equal winning fanin is preserved; missing domains or inconsistent recurrences remain explicit unknowns. This reader serves selection only and does not replace native FULL/STA or independent physical legality checks.

Differential fixtures cover equal fanins, disabled arcs, distinct float32 results, two launch domains, absent domain-specific arrivals, inconsistent recurrences and rejection of invalid disabled flags. The accepted BNN state also agrees field for field with the existing full parser. An interleaved development benchmark then compares complete selector processes on the same immutable initial BNN, accepted BNN and SPMV states. All ten outputs match in selected endpoint identities, every traced proposal/gap/winning edge, routed connection mappings and unknown statuses. No native routing or STA is repeated for these checks.

\begin{table}[t]
\centering\small
\caption{Selector-component development benchmark. Whole-process medians in seconds; existing native experiments continued in parallel.}
\begin{tabular}{lrrr}
\hline
State & Full & Compact & Samples/method\\
\hline
BNN initial & 44.964 & 18.570 & 2\\
BNN accepted & 43.837 & 18.396 & 2\\
SPMV & 4.422 & 2.069 & 1\\
\hline
\end{tabular}
\end{table}

\subsection{Cost scope and adoption boundary}
The measured component ratios are approximately 0.413, 0.420 and 0.468. These are small interleaved component samples, not a formal whole-router or complete repair-algorithm speedup. Initial graph/state construction, candidate failures, native replacement, complete checks, STA and rollback remain part of future complete algorithm timing. The frozen selector candidate binds its source, differential checks and benchmark receipts. A separate future coordinator validates these receipts before enabling compact successor selection. Existing native and queued strong-baseline cohorts keep their registered full parser, so their runtimes are not retroactively replaced by the compact measurements. The current manuscript and archive continue to mark complete standalone algorithm time unknown.
''')
main=p/'main.tex';s=main.read_text();needle='\\input{data/compact_selector_progress_v14.tex}';assert needle not in s;main.write_text(s.replace('\\section{Conclusion}',needle+'\n\n\\section{Conclusion}'))
with (p/'claims_evidence.md').open('a') as f:
 f.write('\n| C114 | Tf六臂已完成，仅组合降低CPD，端点集合支持交互 | [六臂](../bnn_six_scope_component_summary_01.json)、[交互](../bnn_weighted_component_interaction_01.json)、[档案](../multiobjective_archive_09/completion.json) | 两种目标函数各三scope均合法；仅持有者CPD平，setup改善1/2但wire+16/+112；仅目标CPD平；组合降CPD。weighted组合15端点=owner重叠1+组合独有14。不隔离每个owner或hardcapacity单因素，强基线公平比较继续 |\n')
 f.write('| C115 | 紧凑setup选择器保持全部选择语义并减少组件时间 | [实现](../compact_timing_cone.py)、[差分](../compact_timing_cone_validation_01/completion.json)、[交错计时](../compact_cone_benchmark_01/completion.json)、[冻结候选](../compact_selector_stage_01/binding.json) | 10次实际状态选择全部字段一致；BNN2+2/SPMV1+1小样本。中位44.964→18.570、43.837→18.396、4.422→2.069秒。0原生路由/STA调用；非完整算法加速。运行/排队原生版本未改，未来集成仍待独立批次 |\n')
with (p/'README.md').open('a') as f:f.write('\nC114–C115：当前正文六臂表及仅持有者结论已更新，新增紧凑选择器实现/差分/组件开销章节。旧快照不变，强基线对照仍在运行，完整算法时间未知。\n')
with (p/'mechanisms_and_ablation.md').open('a') as f:f.write('\n六臂补齐：两个目标函数下仅组合降低CPD，owner-only仅改善1/2端点且增加资源；weighted组合有14个独有改善分量。选择器工程候选在3状态10进程保持全部字段精确一致，节省组件开销；未替代全量正确性检查、未修改现有原生cohort。\n')
l=read(ledger);names=['export_bnn_completed_components.py','bnn_six_scope_component_summary_01.json','bnn_weighted_component_interaction_01.json','multiobjective_archive_09/completion.json','compact_timing_cone.py','current_sta_arrival_cone_compact.py','validate_compact_timing_cone.py','compact_timing_cone_validation_01/completion.json','benchmark_compact_cone.py','compact_cone_benchmark_01/completion.json','compact_selector_stage_01/binding.json','run_registered_native_transactions_v2.py','paper/data/bnn_joint_component_progress_v14.tex','paper/data/compact_selector_progress_v14.tex']
l['sources_sha256'].update({n:sha(D/n) for n in names});l['updated_at']=time.time();l['completed_components']=dict(claims=['C114','C115'],native_baseline_pending=True,new_work_pushed=False);write(ledger,l)
print(dict(sources=len(l['sources_sha256']),claims=['C114','C115']))
