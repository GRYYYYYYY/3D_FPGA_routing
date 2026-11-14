#!/usr/bin/env python3
"""Bind completed BNN evidence; queued joint outcomes remain explicitly unknown."""
import shutil,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
paper=D/'paper';data=paper/'data';b=D/'bnn_direct_repair_dev_01'
c=read(b/'completion.json');archive=read(D/'multiobjective_archive_02/completion.json');assert c['passed'] and archive['passed']
assert all(sha(p)==h for p,h in c['source_sha256'].items())
w=c['roles']['weighted_soft'];p=c['roles']['physical_capacity']
assert w['cpd_s']==p['cpd_s']==1.3421610489672275e-08
for mode,r in c['roles'].items():
 d=read(b/(mode+'_decisions.json'));assert not d['strict']['accepted'] and not d['endpoint_vector']['accepted'] and d['resources_under_timing']['accepted']
 assert d['endpoint_vector']['comparison']['setup_improved']==d['endpoint_vector']['comparison']['setup_regressed']==0
before=read(D/'timing_cone_bnn_dev_02/Tf_cone.json') if (D/'timing_cone_bnn_dev_02/Tf_cone.json').exists() else read(Path(read(D/'timing_cone_bnn_dev_02/completion.json')['roles']['Tf']['cone']))
oldpins={(x['net'],x['pin']) for x in before['routed_connections']}
for mode in c['roles']:
 after=read(b/(mode+'_successor_cone.json'));assert oldpins-{(x['net'],x['pin']) for x in after['routed_connections']}=={(73897,1)}
costs=read(b/'process_costs.json')
summary=dict(passed=True,automatic_target=[73897,1],initial=dict(CPD_ns=13.421610489672275,wirelength=2074317,SB_pairs=105,CB_sources=5062),roles=c['roles'],
 full_precision_endpoint_vectors_unchanged=True,current_cone_counts=dict(before=len(oldpins),after=len(after['routed_connections'])),
 complete_shared_two_arm_workflow_seconds=c['complete_orchestrator_seconds'],complete_single_configuration_algorithm_seconds=None,process_costs=costs,
 archive=dict(path='multiobjective_archive_02',points=archive['points'],counts=archive['counts_by_quality_status']),
 interpretation='Weighted native control achieves more wire reduction at identical final CPD/SB/CB than physical-capacity candidate; no demonstrated new-capacity-mechanism quality advantage. Small effect (16/2074317 wire); shared-workflow time not configuration runtime.',
 next_registered='bnn_release_joint_dev_01/registration.json',new_work_pushed=False)
write(D/'bnn_multiobjective_progress_summary_01.json',summary)
tex=data/'bnn_multiobjective_progress_v14.tex';assert not tex.exists()
tex.write_text(r'''
\section{BNN current-state resource and capacity evidence}
\label{sec:bnn-current-resource}
\subsection{Problem and direct native control}
The pristine BNN Tf state has full-precision CPD 13.421610489672275 ns, wirelength 2074317, 105 used SB pairs and 5062 used CB sources. The exact worst-endpoint maximum-arrival cone contains 13 routed connections. Full-device, retained-tree capacity queries find one strictly shorter physical connection: net 73897, pin 1, by 7.639000543 ps. The selector chooses this connection automatically, with deterministic identifiers used only to break ranking ties. This is a connection-level opportunity, not a predicted endpoint CPD gain.

Two native transactions start from this identical state with identical target, modifiable tree scope and free-path request. The ordinary criticality-weighted native objective and the physical-delay objective with hard capacity constraints both shorten the selected connection and pass physical legality and native FULL/STA. Neither changes CPD or any setup/hold endpoint-vector component. Both remove 73897/pin 1 from the recomputed maximum-arrival cone, reducing its routed-connection set from 13 to 12. Remaining bottlenecks therefore matter even though this selected branch is no longer a maximum-arrival contributor. These observations motivate a joint intervention; they do not prove that the proposed combination will reduce CPD.

\begin{table}[t]
\centering\small
\caption{Completed BNN direct repair from identical pristine Tf. CPD is unchanged at full precision; counts are actual used resources.}
\label{tab:bnn-direct-resource}
\begin{tabular}{lrrr}
\hline
State & Wirelength & SB pairs & CB sources\\
\hline
Initial Tf & 2074317 & 105 & 5062\\
Native weighted & 2074301 & 105 & 5062\\
Physical capacity & 2074313 & 105 & 5062\\
\hline
\end{tabular}
\end{table}

Strict-CPD and endpoint-vector policies reject both candidates for exactly unchanged timing. The independent fixed-timing resource policy accepts both: CPD is below the original CPD times 1.01 cap, wirelength strictly decreases within its original bound, and SB/CB counts stay within the pre-registered bounds. No tolerance or rolling cap is used. These are new legal accepted resource transitions, unlike the earlier arithmetic eligibility replay. The ordinary native control saves 16 wire units, whereas the physical-capacity candidate saves four. The former dominates the latter in the four quality dimensions. Thus this example provides no quality advantage attributable to hard capacity or the physical-only objective. A 16-unit reduction from over two million wire units is a small mechanism observation, not a substantial engineering improvement.

\subsection{Joint frontier and scarce-channel mechanism}
The archive extension contains 90 actual run or observation records: 44 have no observed dominator, 12 remain unresolved because of printed CPD precision, and 34 are quality-dominated. The five appended records are the exact initial A0/R1/Tf observations and both new direct-repair candidates. Repeated or unequal-opportunity states remain labeled. Strong R1 uses wirelength 2068908, 86 SB pairs and 5072 CB sources at the same exact CPD as Tf. The weighted Tf repair remains a tradeoff because it uses ten fewer CB sources, despite more wire and SB occupancy. This descriptive frontier does not establish equal-opportunity algorithm superiority or complete-time dominance.

The same direct-opportunity screening on pristine strong A0 and R1 examines respectively 10 and 13 current-cone connections. A0 has no strictly positive direct delay opportunity within this scope; R1 has two, at 73896/pin 1 and 73897/pin 1. A0's stage result does not exclude near-critical or resource-reduction opportunities. Registered R1 transactions receive both selected opportunities, using the same paired native objectives and checks as Tf.

Relaxing background occupancy exposes three Tf capacity gaps. Net 26319/pin 1 offers 185.825799 ps in the relaxed model, but its witness includes critical owner net 26320 with zero margin to current worst slack. Protecting whole critical-network trees eliminates that improvement in this restricted query. This is not a global impossibility certificate and is not evidence for a free non-critical release. The smaller 7.639001 ps gaps at 68613/pin 1 and 73896/pin 1 survive critical-tree protection. Their actual occupying branches belong to nets 26497, 66577, 12754 and 57571; the 13 affected sink branches have positive pin-slack margins, with owner minima approximately 4.784--7.166 ns. These margins screen proposals only: legal detours and final endpoint timing still require complete native verification.

The next independently registered batch automatically combines the three positive direct/protected opportunities, releases precisely the implicated owner branches, and routes targets followed by their displaced owners with sequential occupancy updates. All paths remain native choices. Paired native objectives use identical requests; target-only and owner-only scopes provide corresponding ablations from the same pristine state. A combined transaction may have useful effects even when each isolated component leaves CPD unchanged. At this evidence seal the new batch is pending; its results are not included in the table or archive counts.

\subsection{Complete costs and engineering implications}
The completed two-arm direct diagnostic takes 885.791 s, including request preparation, both native observations, candidate serialization and audit, fresh FULL/STA and successor selection. This is a shared research-workflow time, not a standalone algorithm configuration measurement. The native transaction cores take 0.164 and 0.202 s. Their complete candidate-evaluation wrappers take 206.478 and 204.019 s, including native processes of approximately 102 s and independent physical audits of approximately 64 s. Core and wrapper times are nested; neither substitutes for end-to-end algorithm cost. Separate successor selections each take approximately 44 s. State reuse and in-process integration are therefore concrete engineering directions, subject to preserving complete correctness checks and accounting for failed candidates and rollback.

A separate exact preprocessing change computes saturated resources once per immutable occupancy state, then applies each target's own-net credit. All 13 actual Tf cases match the previous query inputs field for field, and 96 additional capacity conditions cover zero capacity, sharing, spare capacity, overuse and own-net credit. Saturation indexing takes 0.213 s and the case-construction component takes 1.215 s. These component timings are not compared against a different complete query workflow as a claimed speedup. New A0/R1 screens use this implementation; their timings remain distinct from the earlier Tf preprocessing version. New complete single-configuration repair time remains unknown, and no historical U timing is assigned to a current repair point.
''')
main=paper/'main.tex';text=main.read_text();needle='\\input{data/bnn_multiobjective_progress_v14.tex}';assert needle not in text;main.write_text(text.replace('\\section{Conclusion}',needle+'\n\n\\section{Conclusion}'))
with (paper/'claims_evidence.md').open('a') as f:
 f.write('\n| C110 | BNN自动直接修复形成真实资源接受态，原生对照更省线但时序完全持平 | [完整结果](../bnn_direct_repair_dev_01/completion.json)、[摘要与时间](../bnn_multiobjective_progress_summary_01.json)、[扩展档案](../multiobjective_archive_02/completion.json) | CPD13.421610489672275ns；wire2074317→2074301/2074313，SB105/CB5062不变；端点向量不变，关键锥13→12。严格/端点拒绝、资源策略接受。weighted四维支配physical；完整双臂885.791s不作算法单配置时间 |\n')
 f.write('| C111 | 当前容量与持有者余量给出联合修复依据，尚不等于收益 | [基线筛查](../bnn_baseline_capacity_screens_01/completion.json)、[保护关键查询](../bnn_slack_release_screen_01/protected_critical/completion.json)、[持有者](../bnn_slack_release_screen_01/owner_slack/completion.json)、[缓存等价验证](../current_query_case_cache_validation_01/completion.json)、[新批次登记](../bnn_release_joint_dev_01/registration.json) | A0无正直接候选，R1两个；Tf两处可释放非关键持有者的小机会，最大185.826ps机会涉及关键持有者。13实际case+96条件等价；联合/仅修复/仅持有者及原生配对已登记，结果未纳入此封存 |\n')
with (paper/'mechanisms_and_ablation.md').open('a') as f:f.write('\nC110–C111：BNN真实资源接受改动均未改变完整端点向量，但73897p1退出最大到达锥。weighted原生对照四维质量优于physical_capacity，不能归因新容量机制。后续3关键目标+13持有者分支组合及分量消融均从封存Tf出发；R1有相同选择机会。固定预算检查最终事务，失败整体回滚；新批次未用于当前结论。状态加载/全检查/选择开销远超核心，必须分别计时。\n')
with (paper/'README.md').open('a') as f:f.write('\nC110–C111追加BNN实际资源接受、强基线直接筛查、容量/余量组合依据及完整成本。档案90记录并保留精度未决和支配关系；新增联合实验仍独立进行。本地更新未推送。\n')
ledger=data/'evidence_v14_ledger.json';history=data/'ledger_history_20261113/before_bnn_multiobjective_progress_01.json';assert not history.exists();shutil.copy2(ledger,history);l=read(ledger)
names=['export_bnn_multiobjective_progress.py','bnn_multiobjective_progress_summary_01.json','bnn_direct_repair_dev_01/completion.json','bnn_direct_repair_dev_01/process_costs.json','bnn_direct_repair_dev_01/weighted_soft_decisions.json','bnn_direct_repair_dev_01/physical_capacity_decisions.json','bnn_direct_repair_dev_01/weighted_soft_successor_cone.json','bnn_direct_repair_dev_01/physical_capacity_successor_cone.json','extend_multiobjective_archive_bnn.py','multiobjective_archive_02/completion.json','multiobjective_archive_02/points.json','bnn_baseline_capacity_screens_01/completion.json','bnn_slack_release_screen_01/protected_critical/completion.json','bnn_slack_release_screen_01/owner_slack/completion.json','current_query_case_cache_validation_01/completion.json','current_query_case_cache.py','run_current_cone_capacity_queries_v2.py','prepare_bnn_release_batch.py','run_registered_native_transactions.py','bnn_release_joint_dev_01/registration.json','bnn_release_joint_dev_01/request_validation.json','paper/data/bnn_multiobjective_progress_v14.tex']
l['sources_sha256'].update({n:sha(D/n) for n in names});l['updated_at']=time.time();l['bnn_multiobjective_progress']=dict(claims=['C110','C111'],archive='multiobjective_archive_02',new_work_pushed=False);write(ledger,l)
print(dict(claims=['C110','C111'],sources=len(l['sources_sha256'])))
