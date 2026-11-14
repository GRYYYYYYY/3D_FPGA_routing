#!/usr/bin/env python3
"""Reconcile completed trajectories and live independent research owners."""
from datetime import datetime,timezone
from pathlib import Path
import shutil,time
from retained_prefix_workflow import D,read,write,sha
now=datetime.now(timezone.utc).isoformat();history=D/'continuation_history'/('exchange_recovery_'+str(time.time_ns()));history.mkdir(parents=True)
entries=[]
for batch,receipt,session in [('pending_reservation_dev_02','queue/registration.json',3442),('native_batch_equivalence_dev_01','queue/registration.json',34134),('critical_owner_exchange_dev_01','queue/registration.json',30220),('reservation_prune_recovery_dev_01','queue/registration.json',37856)]:
 b=D/batch;r=read(b/receipt);stat=Path('/proc')/str(r['pid'])/'stat'
 try:v=stat.read_text().split(') ',1)[1].split();live=v[19]==r['start_ticks'] and v[0]!='Z'
 except FileNotFoundError:live=False
 entries.append(dict(batch=batch,pid=r['pid'],start_ticks=r['start_ticks'],verified_live=live,tool_session=session,receipt=str(b/receipt),phase=read(b/'queue/status.json'),completion_exists=(b/'completion.json').exists()))
a=read(D/'multiobjective_archive_19/completion.json');summary=read(D/'automatic_exchange_progress_summary_01.json');assert summary['passed']
for filename in ['CONTINUATION.json','live_handoff.json']:
 p=D/filename;shutil.copy2(p,history/filename);x=read(p)
 x.update(updated_at=now,observed_at=now,research_state='active',current_goal_state='active',previous_goal_turn_classification='progress',old_caps_revoked=True,author_metadata_blocks_research=False,research_blockers=[],running_jobs=[e for e in entries if e['verified_live']],active_jobs=[e for e in entries if e['verified_live']],active_owners=[e for e in entries if e['verified_live']],queued_jobs=entries[1:],runners=entries[:1],supervisors=entries[1:])
 x['active_current_sta_batch']=dict(automatic='completed_four_actors',running='pending_reservation_dev_02',next='native_batch_equivalence_dev_01',critical_exchange='critical_owner_exchange_dev_01',prune_fix_pair='reservation_prune_recovery_dev_01')
 x['latest_multiobjective']=dict(archive='multiobjective_archive_19',points=a['records'],quality_counts=a['quality_counts'],retention_counts=a['retention_counts'],summary='multiobjective_tradeoff_summary_04.json',new_work_pushed=False)
 x['multiobjective_policy']['archive']='multiobjective_archive_19'
 x['latest_automatic_workflow'].update(status='four_actors_complete',summary='automatic_exchange_progress_summary_01.json',A0_strict_accepted_steps=2,A0_final_CPD_ns=13.413972155262854,A0_final_wire=2070933,A0_wire_vs_all_positive=12,A0_endpoint_accepted_steps=0,qualification='A0 two-step schedule operational but four-quality-axis dominated by all-positive one-step; time dominance unknown. Endpoint primary rejection does not exhaust owner-only alternatives from identical state.')
 x['latest_critical_owner_exchange']=dict(stage='critical_owner_exchange_stage_01/binding.json',query='critical_owner_exchange_query_01/completion.json',expansion='critical_owner_exchange_expansion_01/completion.json',minimal_connections=7,expanded_connections=13,minimal_current_path_model_delta_ps=364.0125978421338,expanded_optimistic_model_delta_ps=-185.82579919268483,expanded_new_queries=0,conditional_certificate_validation='conditional_distance_certificate_validation_01.json',native_controls='critical_owner_exchange_dev_01/registration.json',native_roles=5,native_status='queued_after_static_equivalence_owner',qualification='Core paths coexist only in a partial state. Noncritical pins still need restoration; no final CPD/legality claim. Kernel remains existing native search; new mechanism is closure/path adoption/schedule.')
 x['latest_reservation_prune_recovery']=dict(old_failed_stage='native_reservation_stage_03',old_batch='pending_reservation_dev_02',failure='Pruned multi-sink tree has stale sink-pointer lookup; ON membership assertion before any candidate',old_failure_class='implementation_error_not_QoR',fix='Prune-maintained reached bitset',new_stage='native_reservation_stage_04/binding.json',regression='reservation_multisink_regression_01/completion.json',old_failure_reproduced=True,new_tiny_passed=True,large_pair='reservation_prune_recovery_dev_01',large_status='queued_after_critical_exchange',qualification='Old batch rules/binary unchanged; original files preserved but abort is not graceful in-process rollback. New representative pair avoids mandatory repeat of all old arms; other scopes depend on evidence.')
 x['next_actions']=['Continue frozen stage03 reservation cohort; classify assertion failures as implementation errors and preserve logs, never QoR points. Inspect new terminal roles once, not unchanged tails.', 'Run existing static native batch equivalence after prior owner finishes; no historical-time speedup claim.', 'Execute five registered critical-owner exchange controls with preset-edge audit, full physical/native FULLSTA and exact fixed-root-budget decisions. Model headroom is not performance.', 'Run separately queued stage04 representative reservation off/on pair after existing owners. Require default-off large candidate reproduction and native cleanup, then evaluate starvation/CPD/resource impact.', 'Broaden endpoint/resource proposal portfolio: completed A0 endpoint actor misses already legal same-state owner-only alternatives. Generate alternatives from current feedback, preserve exact acceptance, reselect from each accepted state; no history-best algorithm selection.', 'After proof of useful mechanism, evaluate automatic pristine strong starts and fair native controls under frozen uniform parameter selection; measure complete same-environment configuration cost, preserve all failed/tail/resource outcomes.']
 x['git_publication']['new_work_pushed']=False;write(p,x)
with (D/'RESEARCH_PROTOCOL.md').open('a') as f:f.write('''

## 2026-11-14 自动轨迹完成、关键持有者交换及保留修复

四轨迹按原版完成。A0strict自动接受两步达到13.413972155262854ns，wire2070933/SB98/CB5067，较旧全组多12wire，未推进四质量轴前沿；完整时间支配未知。A0endpoint拒绝主提案但相同当前态已有合法owner-only向量改进，说明提案类未覆盖资源/次级机会，不否定该策略或终止研究。新提案组合须来自当前反馈，不逐电路挑历史最优。

独立关键持有者诊断：固定目标见证下，初始7连接范围的持有者绕行使当前路径模型+364.013ps；按其受保护松弛替代路径自动扩展至13连接。保留树/anchor不变、严格域包含且旧精确见证在新实际部分占用下可行，因此上下界相等，复用两个距离、0新查询；关键核心可共存，非关键缺失pin尚待恢复，185.826ps仅局部乐观空间。五原生控制独立登记在旧静态批处理之后，检查范围、目标见证采用、调度和成本/容量混合因素；现有原生核不因新选择器被宣称为新搜索原语。最终仍必须完整合法/真实资源/FULLSTA/固定原预算。

旧stage03保留ON在多sink部分剪枝后使用stale sink-pointer lookup触发断言，是候选前实现失败。旧批次保持版本与规则继续，不将其当负QoR或完整原生回滚。独立stage04两检查改用prune维护的reached位图；新12-LUT小图复现旧错且新off/on在保留其他sink时通过，关闭输出匹配。新增代表性A0 target-only physical开/关大图配对在已登记所有owner后排队；不强制重跑原八臂，新范围按证据决定。原冻结源码和结果、每进程保护及无整体日期/次数/矩阵停止条件均保留。
''')
with (D/'paper/bnn_joint_live_notes.md').open('a') as f:f.write('''

2026-11-14更新：四自动轨迹完成。Tfstrict/endpoint各接受1步；A0strict两步追回7.638ps，但finalwire2070933较旧全组2070921更差12，CPD同13.413972155ns，不能称调度推进前沿。A0endpoint0接受，但同态已有两个owner-only合法向量备选，提案接口需扩大而不是放宽接受规则。档案19现113记录。

关键持有者交换条件查询四项完成：初始7连接固定目标导致关键owner多549.838ps，抵消目标185.826ps且净差364.013ps。进一步发现6个非关键分支，扩展13连接；旧精确距离在严格新域仍有可行见证，以上下界相等认证复用，0新查询。核心路径可共存但非关键pin尚缺，不是最终路由。五独立原生对照已排队。

旧保留ON多sink索引断言已分为实现失败，旧批次未改；独立stage04改用reached位图，真实多sink回归复现旧错并验证修复。代表性大图新开/关对照后排队，不把小图通过当质量提升。新代码/实验/论文仍仅本地、未推送。
''')
write(history/'binding.json',dict(updated_at=now,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'automatic_exchange_progress_summary_01.json',D/'critical_owner_exchange_stage_01/binding.json',D/'reservation_multisink_regression_01/completion.json',D/'reservation_prune_recovery_dev_01/registration.json']},native_calls=0))
print(dict(live=[(e['batch'],e['verified_live']) for e in entries],archive_records=a['records']))
