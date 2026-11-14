#!/usr/bin/env python3
"""Report completed post-publication eligibility evidence without a QoR claim."""
from retained_prefix_workflow import D,read,write,sha
from analyze_native_reconvergence_v2 import observe
from verify_path_witnesses_v2 import fields
assert read(D/'current_eligibility_study_closure_01.json')['passed']
b=D/'current_eligibility_eltwise_dev_02';r=read(b/'eligibility_analysis.json');p=D/'paper'
rows={x['arm']:x for x in r['observations'] if not x['reused']};timings=[]
for batch in ['current_eligibility_eltwise_dev_01','current_eligibility_eltwise_dev_02']:
 for a in ['C2','E2','E1']:
  rd=D/batch/'runs'/('eltwise_layer_'+a);x=observe(rd);logs=(rd/'stdout.log').read_text().splitlines();probe=fields(next(l for l in reversed(logs) if l.startswith('H3D_RESIDUAL_SUMMARY ')))
  timings.append(dict(batch=batch,arm=a,complete_process_seconds=x['process_seconds'],router_seconds=x['router_seconds'],planning_seconds=x['planning_seconds'],residual_probe_seconds=float(probe['seconds']),outside_router_seconds=x['process_seconds']-x['router_seconds'],status=x['status']))
write(D/'current_eligibility_timing_01.json',dict(passed=True,rows=timings,build_seconds={name:read(D/name/'build_result.json')['wall_seconds'] for name in ['current_eligibility_stage_01','current_eligibility_stage_02']},scope='Ordered instrumented development runs and diagnostic-equivalence recovery. Planning/probe are nested router subitems. Per-process data only; no formal speedup, research-cycle distribution or independent repetition inference.'))
tex=r'''The separately registered current-criticality eligibility pilot is complete. At an actual setup search it suppresses only the local soft-guide pointer when native float criticality is below the existing planning threshold, leaving the stored assignment available for later searches. Native congestion, physical delay, final STA, RCV behavior and all query budgets remain unchanged; the outside option is disabled. The default-off binary reproduces the frozen control. The first implementation exhausted its diagnostic row cap on unguided searches. Its three completed routes remain archived. A diagnostic-only correction logs guide-bearing searches; three same-setting reproductions match original physical routes, final guides, original cost/query/prefix/heap records, influence rows and domain records. These are three study roles plus three diagnostic reproductions, not six independent quality samples. All pass native FULL, independent route/guide checks and input sealing.

With complete guided-search records, the count-two and first-legal modes suppress 534/4,590 and 79/1,284 guided searches, respectively. Their later eligibility transitions include 121/15 reactivations with the same preferred-resource list. These are trajectory events, not independent nets. Each recorded influence edge belongs to an unsuppressed search; raw edge rows remain sampled. Both modes restore the same complete 6.20812\,ns route as their matched controls, with 118/955 SB/CB net occupancies. First-legal termination remains iteration 42. Count-two termination increases from 62 to 69; native per-iteration routing/heap counters first differ at iteration 44. No full per-node search equivalence is inferred from the earlier matching counters. Total guided crossing evaluations rise from 35,448 to 39,318 and residual-query expansions from 364,731 to 461,258 under count two. Thus removing low-criticality pressure does not establish a quality or work reduction, and the gate is not promoted. Count-two CPD remains 3.157475\% worse than the matched 6.01810\,ns A0 and old-R1 references; inherited count-one benefits are not credited to this gate.

\begin{table}[t]
\centering
\caption{Corrected eligibility pilot; one seen circuit, ordered development costs. Planner time is nested in process time.}
\label{tab:current-eligibility-v14}
\begin{tabular}{lrrrr}
\hline
Role & CPD (ns) & Iters & Process (s) & Plan (s)\\
\hline
'''
for a in ['C2','E2','E1']:
 x=rows[a];tex+=f"{a} & {x['legal_cpd_ns']:.5f} & {x['iterations']} & {x['process_seconds']:.3f} & {x['planning_seconds']:.3f} \\\\\n"
tex+=r'''\hline
\end{tabular}
\end{table}
'''
tex+='\nCorrected C2/E2/E1 router times are '+ '/'.join(f"{rows[a]['router_seconds']:.2f}" for a in ['C2','E2','E1'])+r'\,s; residual-probe API subitems are '+ '/'.join(f"{next(x for x in timings if x['batch'].endswith('02') and x['arm']==a)['residual_probe_seconds']:.6f}" for a in ['C2','E2','E1'])+r'\,s. The CSV and timing ledger retain both attempts. Ordered instrumented times support cost accounting, not a formal speedup. This evidence postdates the public snapshot f7167bd and remains a local development result.'+'\n'
fragment=p/'data/current_eligibility_discussion_v14.tex';assert not fragment.exists();fragment.write_text(tex)
main=p/'main.tex';s=main.read_text();a='\\input{data/outside_quality_discussion_v14.tex}';assert s.count(a)==1;s=s.replace(a,a+'\n\\input{data/current_eligibility_discussion_v14.tex}');main.write_text(s)
old=p/'data/outside_quality_discussion_v14.tex';s=old.read_text();a='This is an unimplemented hypothesis, not an explanation established by the outside experiment or a reason to enlarge query budgets.';assert a in s;s=s.replace(a,'The following independent eligibility pilot tests this hypothesis; the outside experiment alone does not establish its causal explanation or justify larger query budgets.');old.write_text(s)
claims=p/'claims_evidence.md';s=claims.read_text();a='未实施/提交，也不据本轮平局终止整个目标';assert a in s;s=s.replace(a,'原登记后已实施并完成，结果见C61；本轮平局不终止整个目标')
s+='\n| C61 | 实际criticality引导资格已完成，最终质量无收益且count2多7轮 | [完整决策/配对审计](../current_eligibility_eltwise_dev_02/eligibility_analysis.json)、[阶段封存](../current_eligibility_study_closure_01.json)、[全部状态/资源/费用](data/current_eligibility_v14.csv)、[两批分项计时](../current_eligibility_timing_01.json)、[日志修复登记](../current_eligibility_trace_recovery_01.json) | 首批3角色均legal，但诊断cap被无guide搜索耗尽；保留首批，修正仅记录guided后3次同参数复现旧route/guide/cost/query/heap/prefix/influence/domain精确，不能当6个独立质量样本。新记录E2/E1全覆盖4590/1284guided搜索，停用534/79次，同preferred重新启用121/15次；实际采样influence边均属于未停用搜索。二者完整route及CPD6.20812ns、SB118/CB955同匹配控制；首次合法42轮不变，count2从62增至69，native计数首次差异44轮。count2相对A0/旧R1的6.01810ns仍退化3.157475%，不把继承的count1收益归给新gate。全记录事件不是独立net；全体heap边未逐一重放。原生FULL/独立route/guide/input通过，不推广，无正式speedup主张；本地新结果晚于已公开f7167bd |\n'
claims.write_text(s)
for name in ['mechanisms_and_ablation.md','DEVELOPMENT_STATUS.md']:
 with (p/name).open('a') as f:
  f.write('\n\n2026-11-13 当前实际关键度资格消融完成（[C61证据](claims_evidence.md)）。仅搜索局部指针、原计划保留，native float门槛0.7；outside模式关闭，预算不变。首批日志覆盖问题经独立stage02纠正并完成三角色严格等价复现。E2/E1实际534/79次停用与121/15次同偏好重新启用有完整guide-search记录；仍同完整物理route6.20812ns和118/955资源，count2多7轮(69 vs62)，首次合法42不变，不推广。成本与失效历史完整保留，不以诊断复现作为独立样本、也不作正式速度结论。此批晚于GitHub已推f7167bd，仅在本地论文更新；研究目标保持active。\n')
ledger=p/'data/evidence_v14_ledger.json';v=read(ledger)
for rel in ['current_eligibility_eltwise_dev_02/eligibility_analysis.json','current_eligibility_study_closure_01.json','current_eligibility_timing_01.json','current_eligibility_trace_recovery_01.json','paper/data/current_eligibility_v14.csv','paper/data/current_eligibility_discussion_v14.tex','paper/data/outside_quality_discussion_v14.tex']:
 v['sources_sha256'][rel]=sha(D/rel)
v['current_guide_eligibility']=dict(status='sealed_not_promoted',report='current_eligibility_eltwise_dev_02/eligibility_analysis.json',native_roles=6,unique_study_roles=3,diagnostic_reproductions=3,scope='One seen circuit/two native stopping rules, post-publication local evidence',cpd_ns=6.20812,count2_iterations_control_enabled=[62,69],count1_iterations=42,suppressed=[534,79],same_preference_reactivations=[121,15])
write(ledger,v)
print('Wrote C61, method/results/cost fragment and bound evidence ledger')
