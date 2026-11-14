#!/usr/bin/env python3
"""Update research records after completed selected scopes and batch regression."""
from datetime import datetime,timezone
from pathlib import Path
import shutil,time
from retained_prefix_workflow import D,read,write,sha
now=datetime.now(timezone.utc).isoformat();history=D/'continuation_history'/('selected_batch_'+str(time.time_ns()));history.mkdir(parents=True)
entries=[]
for batch,receipt,session in [('bnn_automatic_trajectories_dev_02','registration.json',49688),('pending_reservation_dev_02','queue/registration.json',3442),('native_batch_equivalence_dev_01','queue/registration.json',34134)]:
 b=D/batch;r=read(b/receipt);stat=Path('/proc')/str(r['pid'])/'stat'
 try:v=stat.read_text().split(') ',1)[1].split();live=v[19]==r['start_ticks'] and v[0]!='Z'
 except FileNotFoundError:live=False
 status=b/('queue/status.json' if receipt.startswith('queue') else 'status.json')
 entries.append(dict(batch=batch,pid=r['pid'],start_ticks=r['start_ticks'],verified_live=live,tool_session=session,receipt=str(b/receipt),phase=read(status),completion_exists=(b/'completion.json').exists()))
a=read(D/'multiobjective_archive_18/completion.json');selected=read(D/'bnn_selected_group_summary_01.json');v=read(D/'bnn_selected_group_vector_analysis_01.json');assert selected['passed'] and v['passed'] and read(D/'native_batch_tiny_regression_02/completion.json')['passed']
for filename in ['CONTINUATION.json','live_handoff.json']:
 p=D/filename;shutil.copy2(p,history/filename);x=read(p)
 x.update(updated_at=now,observed_at=now,research_state='active',current_goal_state='active',previous_goal_turn_classification='progress',old_caps_revoked=True,author_metadata_blocks_research=False,research_blockers=[],running_jobs=[e for e in entries if e['verified_live']],active_jobs=[e for e in entries if e['verified_live']],active_owners=[e for e in entries if e['verified_live']],queued_jobs=entries[1:],runners=entries[:1],supervisors=entries[1:])
 x['active_current_sta_batch']=dict(strong='completed_twelve_legal',selected='completed_two_legal_R1_exact_reuse',automatic='bnn_automatic_trajectories_dev_02',next_independent='pending_reservation_dev_02',engineering_after_reservations='native_batch_equivalence_dev_01')
 x['latest_multiobjective']=dict(archive='multiobjective_archive_18',points=a['records'],quality_counts=a['quality_counts'],retention_counts=a['retention_counts'],summary='multiobjective_tradeoff_summary_03.json',vector_qualification='CPD/wire/SB/CB projection omits endpoint-vector differences; selectedTf versus old combination has two non-near endpoint regressions',new_work_pushed=False)
 x['multiobjective_policy']['archive']='multiobjective_archive_18'
 x['latest_selected_group_outcomes']=dict(summary='bnn_selected_group_summary_01.json',vectors='bnn_selected_group_vector_analysis_01.json',Tf_selected=13,Tf_old=16,Tf_CPD_vs_old_ps=0,Tf_wire_vs_old=-8,A0_selected=14,A0_old=29,A0_CPD_vs_old_ps=7.638334409421077,A0_wire_vs_old=-40,shared_workflow_seconds=849.9696681983769,complete_single_configuration_seconds=None,rule='Uniform frozen0.9 proxy fraction, no per-circuit historical choice')
 x['latest_static_native_batch']=dict(workspace='native_batch_workspace_02',stage='native_batch_stage_02/binding.json',regression='native_batch_tiny_regression_02/completion.json',regression_passed=True,tiny_objectives=4,tiny_requests=5,tiny_failed_then_success=True,reused_completed_tiny_processes=3,large_cases='native_batch_equivalence_dev_01/registration.json',large_status='registered_queued_after_reservations',large_case_requests=dict(BNN_A0=6,SPMV_failure_success=4),native_commits=0,complete_algorithm_speedup='unknown',qualification='Only independent proposals on one immutable source can be batched; accepted-state trajectories still require fresh occupancy/STA/target selection.',source_copy_failure_preserved='native_batch_workspace_recovery_01.json')
 x['next_actions']=['Continue actual live four-policy actors; each acceptance recomputes currentSTA and query feedback. Analyze migrated bottlenecks and policy divergence, not just first-step CPD.', 'Let stage03 reservation off/on controls execute only after original automatic owner is terminal; check default-off native reproduction, actual competition, final FULLSTA and resource vectors.', 'Run static batch engineering equivalence after reservations. Reproduce six BNN native transactions and SPMV failure/success/repeated requests, fresh post-batch STA, no new route commits.', 'If static equivalence passes, design fresh same-version isolated/batch component timing and decide on deeper in-process candidate FULLSTA/state reuse from measured costs. Historical timing is not a speedup cohort.', 'Develop fixed-timing resource proposals and fixed-resource timing repair beyond the current positive-winning-path operator; preserve transactional combinations and original strong baselines.', 'Append only new complete legal states; preserve endpoint regressions and full runtime unknowns, synchronize manuscript and avoid per-circuit historical best configuration.']
 x['git_publication']['new_work_pushed']=False
 write(p,x)
with (D/'RESEARCH_PROTOCOL.md').open('a') as f:f.write('''

## 2026-11-14 统一组选结果与独立静态批处理

原13/14连接登记已按原规则完成：Tf13与旧16连接CPD完全相同、wire再少8；A014与旧29连接相比CPD差7.638334409ps、wire少40，SB/CB各自不变。两个合法结果保留，统一0.9选点规则不据结果逐电路调整。Tf较旧组合有2个setup分量退化（最坏115.384ps，距当前最坏≥5.884ns），所以四轴质量投影支配不等于端点全面支配；A0同样保存向量退化。共享849.970s和核心时间不代替完整单配置时间。四轨迹队列已自动接续，保持v2版本、原输入与规则，接受后各自当前态重新筛选。

根据真实开销独立实现native_batch_stage_02：同一已加载起点运行多个独立请求，每个事务先恢复原占用/树再进入下一项；不跨已接受更新共享旧STA目标。四目标、重复请求、真实失败后成功、小图重新计算物理延迟及原生STA、歧义/重复输出拒绝通过。修复测试中过强的“所有目标均成功”假设时精确复用3个已完成单例进程，不重跑pack/place/route。旧源复制失败的符号链接与失败验证记录保留。大图工程等价登记在既有自动与保留批次之后，不改变任何旧作业；六BNN请求与SPMV失败/成功四请求只比较完整原生结果并验证状态恢复，候选质量仍绑定原独立FULLSTA。含额外验证的组件时间不能与历史单例耗时拼成完整算法加速；后续若一致，再统一版本和环境作隔离计时，并按实测收益决定更深的进程内STA/状态复用。
''')
with (D/'paper/bnn_joint_live_notes.md').open('a') as f:f.write('''

2026-11-14后续：统一组选两态全部合法。Tf13 CPD13.413972155262854ns、wire2074301/SB105/CB5062，相对旧16少8wire；四策略通过，较原Tf14setup改善0退化。但较旧组合2端点退化、最坏115.384ps、距当前最坏≥5.884ns。A014 CPD13.421610489672275ns、wire2070881/SB98/CB5067，相对旧29差7.638ps而少40wire；相对原A09改善7退化，仅strict/timing_under_resources通过。共享849.970s非完整单配置时间，档案18共112记录，四轨迹已接续且Tfstrict首步精确复用新接受态后重新查询。

静态原生事务批处理stage02已构建，小图四目标/重复/失败恢复及新鲜post-STA一致，3个已完成单例进程复用。新BNN6请求/SPMV失败成功4请求工程等价队列在原保留之后，尚无大图效果或正式加速结论；不替代多轮接受后的当前STA更新。新代码、结果、论文均为f7167bd之后本地新增、未推送。
''')
write(history/'binding.json',dict(updated_at=now,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'bnn_selected_group_summary_01.json',D/'native_batch_tiny_regression_02/completion.json',D/'native_batch_equivalence_dev_01/registration.json']},native_calls=0,qualification='Ownership and evidence reconciliation, no job mutation.'))
print(dict(active=[e['batch'] for e in entries if e['verified_live']],archive_records=a['records']))
