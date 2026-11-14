#!/usr/bin/env python3
"""Export only completed paired scopes; leave owner-only and baseline outcomes pending."""
import shutil,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';data=p/'data';b=D/'bnn_release_joint_dev_01';rows=[]
for scope in ['combined','target_only']:
 for mode in ['weighted_soft','physical_capacity']:
  name='Tf_'+scope+'_'+mode;d=read(b/(name+'_decisions.json'));c=read(b/(name+'_evaluation/completion.json'));assert c['passed']
  rows.append(dict(role=name,CPD_ns=d['endpoint_vector']['comparison']['cpd_after_s']*1e9,resource_delta=d['resources_under_timing']['resource_delta'],policies={k:r['accepted'] for k,r in d.items()}))
screen=read(D/'bnn_current_successor_screen_01/completion.json');assert screen['passed'] and not screen['capacity_positive'] and not screen['protected_positive']
write(D/'bnn_joint_component_summary_01.json',dict(passed=True,rows=rows,current_state_diagnosis=screen,owner_only='pending',strong_baseline='queued under real dependency owner',qualification='Completed paired-scope development comparison; no full algorithm runtime or confirmation claim.'))
tex=data/'bnn_joint_component_progress_v14.tex';assert not tex.exists()
tex.write_text(r'''
\section{Joint repair components and the updated search boundary}
\subsection{Completed paired scopes}
Both objectives now have complete native FULL/STA and independent physical audits for combined and target-only scopes from the identical pristine Tf state. The combined scope releases actual conflicting owner branches and routes three critical targets followed by their displaced owners. Target-only uses the same three critical targets while retaining the owner trees. Every native path is chosen freely; per-connection occupancy is updated throughout each transaction. Original policy decisions and fixed budgets are preserved.

\begin{table}[t]
\centering\small
\caption{BNN completed component outcomes. Changes are relative to pristine Tf; CPD is abbreviated here, with full precision used in all decisions.}
\begin{tabular}{lrrrr}
\hline
Scope and objective & CPD(ns) & $\Delta$wire & $\Delta$SB & $\Delta$CB\\
\hline
Combined weighted & 13.413972 & $-8$ & 0 & 0\\
Combined physical-cap. & 13.413972 & 92 & 2 & 2\\
Targets weighted & 13.421610 & $-16$ & 0 & 0\\
Targets physical-cap. & 13.421610 & $-4$ & 0 & 0\\
\hline
\end{tabular}
\end{table}

The weighted combination reduces exact CPD from 13.421610489672275 to 13.413972155262854 ns. Fifteen setup endpoint/domain components improve, none regress, and hold violations do not increase. All four registered policies accept. The physical-delay plus hard-capacity combination achieves exactly the same CPD and setup-vector changes, but uses more wire, SB and CB resources. Strict CPD and endpoint-vector policies accept it; both fixed-resource policies reject its resource excess. The two target-only candidates leave the complete setup/hold endpoint vectors and CPD unchanged, so only their resource policies accept. This supports owner release as a contributor to the combined timing gain. Owner-only results remain pending and can still distinguish release effects from owner rerouting itself. The comparison changes both objective and capacity handling between paired implementations, so it does not isolate hard capacity alone.

These are useful tradeoffs even within the native weighted implementation: target-only saves 16 wire units with unchanged CPD, whereas the combination saves eight and improves CPD. Neither dominates the other in the selected quality axes. An additional arithmetic replay fixes wirelength, SB and CB upper bounds exactly to the initial counts, with no resource headroom and no CPD tolerance. The existing weighted combination satisfies both timing-under-resources and resources-under-timing conditions; the physical combination satisfies neither. This replay runs no native search and makes no new commits. Core, observation-wrapper and full algorithm time remain distinct; the existing 430.808 s weighted combined-arm workflow excludes earlier shared query/cache preparation and is not a standalone algorithm timing.

\subsection{Verified mechanism and remaining coupling}
Actual native timing graphs explain the earlier single-target plateau. Connections 73896/pin 1 and 73897/pin 1 tie at two LUT merge nodes, 449947 and 450152. Shortening 73897 alone leaves the competing 73896 arrival dominant. Native float32 maximum-arrival recurrences are verified at both merges; this is stronger evidence than equal final CPD alone.

After accepting the weighted combination, fresh STA selects ten current-cone routed connections. Exact same-state capacity queries and independent path audits find no strictly shorter connection within the retained-tree scope. Background relaxation leaves one optimistic 185.825799 ps gap at 26319/pin 1, but preserving current critical-network trees removes that opportunity. These are restricted-model observations, not a global routing impossibility result. The six-stage current-state diagnosis takes 364.114 s, makes no native routing calls, and cannot be attached to the earlier candidate as its standalone runtime. Its ten query inputs differ from historical complete fingerprints, so all ten are newly measured.

The current maximum-arrival subgraph contains two winning edge paths. Connection 26320/pin 1 precedes 26319/pin 1 on both. The relaxed resource opportunity therefore involves a critical owner in series with its prospective beneficiary. A local delay reduction cannot be translated directly into CPD gain without accounting for the owner's replacement and all newly competing paths. This result motivates coupled critical transactions as a separate future mechanism; it does not justify treating the owner as a free noncritical release.

Meanwhile, a separately registered strong A0/R1 batch receives the same direct, relaxed and protected-owner screening stages and paired native search opportunities. A0 automatically selects four targets and 25 affected owner branches; R1 selects three and three. Combined, target-only and owner-only requests share identical scope within each objective pair. Its real dependency queue preserves the ongoing batch and starts native execution only after the previous owner is terminal with a verified receipt. These baseline outcomes are pending and cannot yet support algorithm superiority. The current descriptive archive contains 94 actual observations; quality dominance, matched complete-time dominance and unresolved runtime retention are separate. Repeat-level observed timing dominance is not statistical configuration superiority or a rule for selecting each circuit's historical best.
''')
main=p/'main.tex';s=main.read_text();needle='\\input{data/bnn_joint_component_progress_v14.tex}';assert needle not in s;main.write_text(s.replace('\\section{Conclusion}',needle+'\n\n\\section{Conclusion}'))
with (p/'claims_evidence.md').open('a') as f:
 f.write('\n| C112 | BNN组合与仅目标两种目标函数配对完成，支持持有者释放贡献 | [四臂](../bnn_joint_component_summary_01.json)、[零资源余量回放](../bnn_zero_resource_headroom_replay_01.json)、[真实时序传播](../bnn_direct_timing_transfer_01.json) | weighted组合CPD13.413972155262854ns、wire-8/SB0/CB0；仅目标CPD不变、wire-16；physical组合资源更差，无法隔离hardcapacity单因素。仅持有者与强基线仍待完成；回放无新增native/提交 |\n')
 f.write('| C113 | 接受状态的新查询已完成，剩余机会涉及串联关键持有者 | [当前诊断](../bnn_current_successor_screen_01/completion.json)、[依赖](../bnn_current_critical_dependencies_01.json)、[强基线登记](../bnn_strong_release_joint_dev_01/registration.json)、[真实队列](../bnn_strong_release_joint_dev_01/queue/registration.json) | 当前10连接无直接及保护关键树后的短路径收益；放松的185.826ps机会与串联关键26320耦合。仅限制当前模型，不作全局无解结论。强基线后续已提交，未计入成功结论 |\n')
with (p/'README.md').open('a') as f:f.write('\nC112–C113归并已完成BNN四臂组件、真实LUT并列瓶颈、零资源余量回放、接受态10目标诊断及关键串联依赖；仅持有者及强基线仍在实际队列中。\n')
with (p/'mechanisms_and_ablation.md').open('a') as f:f.write('\nC112–C113：相同三目标仅修复均持平；释放+联合weighted降CPD而不增加资源，支持释放贡献但仅持有者未完成。physical+hardcapacity捆绑未胜过nativeweighted，不解释为hardcapacity单因素失败。接受态10目标直接/保护关键网络筛查无进一步收益，串联关键owner机会独立研究；整体Goal继续，强A0/R1公平机会队列已实际提交。\n')
ledger=data/'evidence_v14_ledger.json';history=data/'ledger_history_20261113/before_bnn_joint_component_01.json';assert not history.exists();shutil.copy2(ledger,history);l=read(ledger)
names=['export_bnn_joint_component_progress.py','bnn_joint_component_summary_01.json','bnn_zero_resource_headroom_replay_01.json','bnn_direct_timing_transfer_01.json','bnn_current_critical_dependencies_01.json','analyze_bnn_current_critical_dependencies.py','bnn_current_successor_screen_01/completion.json','bnn_current_successor_screen_01/registration.json','run_current_cone_capacity_queries_v3.py','run_bnn_current_successor_screen.py','bnn_strong_release_joint_dev_01/registration.json','bnn_strong_release_joint_dev_01/queue/registration.json','queue_registered_native_batch.py','paper/data/bnn_joint_component_progress_v14.tex']
l['sources_sha256'].update({n:sha(D/n) for n in names});l['updated_at']=time.time();l['bnn_joint_component']=dict(claims=['C112','C113'],owner_only_pending=True,new_work_pushed=False);write(ledger,l)
print('Exported C112-C113',len(l['sources_sha256']))
