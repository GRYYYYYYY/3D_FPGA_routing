#!/usr/bin/env python3
"""Report plateau resource coupling, joint references, and actual native repair."""
import csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

op=read(D/'plateau_joint_opportunity_01.json');native=read(D/'joint_coordinated_native_01/completion.json')
transaction=read(D/'joint_coordinated_repair_01/analysis.json');decision=read(D/'plateau_R1_step_01/decision.json')
assert op['passed'] and native['passed'] and native['accepted'] and transaction['passed'] and decision['decision']['accepted']
assert all(sha(p)==h for p,h in op['source_sha256'].items())
assert all(sha(p)==h for p,h in transaction['source_sha256'].items())
nextfile=D/'native_sta_frontier_experiment_01.json';assert not nextfile.exists()
write(nextfile,dict(status='registered_not_implemented_not_submitted',
    question='Can an authoritative native all-connection timing frontier identify tied/near-critical groups and exact cluster-pin endpoints for a reproducible common repair policy?',
    evidence='A one-target plateau step preserves all other sink delays but occupies resources required by the next tied connection. Two-target joint resource-compatible repair of strongR1 passes nativeFULL/STA and improves6.01810→5.85466ns. Current target discovery still depends on sequential worst-path reports and location matching; robust group selection and equal-policy comparison require exact native pin/STA information.',
    inputs='Frozen matched count-two eltwise A0/R1/Tf packed/place/RRG/route states, plus accepted jointR1 state for frontier migration diagnosis. Preserve all old binaries, sources, routes and public snapshot.',
    implementation=['Inspect existing native timing echo/report capabilities first; vpr_api.cpp::vpr_analysis already calls tatum::write_echo under E_ECHO_ANALYSIS_TIMING_GRAPH. Reuse if it contains the necessary mappings.',
        'If needed, add a default-off read-only analysis exporter in an independent frozen stage, after timing_info->update(). Export all clustered net/pin identities, exact atom mappings, available SOURCE/SINK RR identities, actual native net_delay, raw setup/hold slack/criticality, and timing-domain information where supported. Record ignored/global/unmapped cases explicitly.',
        'Use native calculate_clb_net_pin_criticality/setup-slack and actual ClusteredPinAtomPinsLookup interfaces after inspecting their signatures. Do not infer exact atom pins from placement location or collect only guided connections.',
        'Use full precision and explicit seconds units; preserve original physical Tdel, native congestion and finalSTA. No selection/policy change in the observer stage.'],
    validation='Compare trace-off/on analysis on identical route inputs; require unchanged route/net/place hashes and nativeFULL/STA metrics. Compare exported native delays to audited zeroRC paths and ensure exact mapping to selected current ties and blocker connections. Existing completed route-search results are reused; new analysis calls answer observer questions, not repeated routing.',
    policy_followup='Build a common policy that groups tied/nearcritical connections on the original accepted state, generates jointly capacity-compatible alternatives and restores blockers transactionally. Use plateau lookahead as information without committing a scarce resource before joint selection. Normalize candidate costs by current path/slack effects; test independent versus joint selection separately.',
    matched_comparison='Once group selection/acceptance are stable, run the same entire policy and per-invocation work/scope from frozen A0/R1/Tf states, then additional seeds/circuits. CurrentR1 joint5.85466 is a development intervention, not a fully compared general router. Legal-input postrepair does not by itself improve failed-route success; retain the original prelegal guide/scope/failure research branch.',
    overhead='Separate original full-route, preparation/query, nativeSTA and audit costs. Reuse static graph/distances; evaluate persistent graph worker or in-process integration under equivalent decisions before formal same-environment timing.',
    per_process_limits=dict(timeout_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    global_limits='No global date, route-call or matrix stopping condition; an unhelpful branch changes the mechanism or development focus, not the overall objective.',
    source_sha256={str(p):sha(p) for p in [D/'plateau_joint_opportunity_01.json',D/'joint_coordinated_native_01/completion.json',D/'joint_coordinated_native_01/path_migration_analysis.json',D/'joint_critical_repair_experiment_01.json']}))
summary=dict(passed=True,status='plateau_counterfactual_joint_reference_and_native_gain_sealed',research_complete=False,quality_promoted=False,
    new_reference_queries=31,new_transaction_queries=4,new_queries_total=35,new_native_analysis_calls=1,new_route_search_calls=0,
    native_status_counts=dict(legal=1,failed=0,timeout=0,missing=0),reused_native_calls=1,
    plateau_step_CPD_ns=6.01810,plateau_followup_positive_targets=0,
    next_connection_free_capacity_gain_before_after_ns=[0.18582579919268483,0.0],
    ownership_changed_nodes=len(op['ownership_changes']),target_tree_identity_verified=True,
    fixed_background_joint_threshold_ns=op['conditional_joint_delay_threshold_seconds']*1e9,
    conditional_resource=op['conditional_shared_resource'],endpoint_only_joint_reference_ns=op['optimistic_joint_minimax_seconds']*1e9,
    optimistic_reference_pairs=[op['path_pairs_tested'],op['path_pairs_RR_capacity_feasible']],
    blockers=op['blockers'],blocker_sinks=op['total_blocker_sinks'],
    native_before_CPD_ns=native['before_cpd_ns'],native_after_CPD_ns=native['after_cpd_ns'],
    native_CPD_improvement_percent=(1-native['after_cpd_ns']/native['before_cpd_ns'])*100,
    native_STA=native['STA'],native_resources=native['physical_resources'],
    prototype_preparation_seconds=transaction['build_process_seconds'],query_core_seconds=sum(q['core_seconds'] for q in transaction['queries']),
    query_process_seconds=sum(q['process_seconds'] for q in transaction['queries']),native_analysis_process_seconds=native['process_seconds'],
    accepted_run=native['accepted_run'],
    limitations='One seen circuit/seed. Current result is originalstrongR1 plus a joint postroute transaction, not complete matched A0/R1/Tf policy or formal runtime evidence. Reference optimum belongs only to a two-endpoint zeroRC RRnode-capacity relaxation. Plateau acceptance alone did not improve CPD.',
    next_registered=nextfile.name,public_snapshot='f7167bd1fbeb267d7ffc02766eeb2e5966aec387',this_followup_pushed=False,
    source_sha256={str(p.relative_to(D)):sha(p) for p in [D/'plateau_joint_opportunity_01.json',D/'joint_coordinated_repair_01/analysis.json',D/'joint_coordinated_native_01/completion.json',D/'plateau_R1_step_01/decision.json',nextfile]})
write(D/'plateau_joint_repair_summary_01.json',summary)
paper=D/'paper';csvpath=paper/'data/plateau_joint_repair_v14.csv'
with csvpath.open('w') as f:
    w=csv.writer(f);w.writerow(['stage','CPD_ns','status','accepted_under_policy','new_native_analysis_calls'])
    w.writerows([['strong_R1',6.01810,'legal','baseline',0],['one_target_strict',6.01810,'legal',False,0],['one_target_plateau_branch',6.01810,'legal',True,0],['joint_two_target',5.85466,'legal',True,1]])
fragment=paper/'data/plateau_joint_repair_discussion_v14.tex'
fragment.write_text(r'''A separately registered componentwise-delay policy accepts the already completed R1 plateau candidate on an independent branch, without changing the old strict-CPD rejection or rerunning native analysis. Its pure decision tests include acceptance and 14 invalid, nonmonotone, incomplete or repeated-state controls. The new policy requires a complete zero-RC physical audit, exactly one strictly shortened connection, all other sink delays unchanged within the audit tolerance, and nonworsening native setup/hold CPD/WNS/TNS at reported precision. This plateau step still has CPD 6.01810\,ns. Its next five current worst-path connections all have exact zero free-capacity improvement, so acceptance alone has not produced further CPD gain.

A same-target counterfactual isolates resource competition: all five target trees, roots, sinks, retained anchors, prefixes and physical delays are identical before and after the plateau step. Only six RR ownership entries change. Before the step, the next tied connection (net 6587 pin 4) has a 0.185826\,ns free-capacity improvement; afterwards it has none. Thus componentwise nonworsening present delays do not guarantee preservation of another connection's future routing opportunity. The physical shortening is real, but the first move reserves part of the corridor that the next tied connection would use.

A joint reference frees both target-exclusive chains while retaining all other branches and networks. Each target individually reaches 0.856978\,ns, but forbidding their shared unit-capacity IPIN 82120 raises each exact cost to its original 1.042804\,ns. Therefore both cannot simultaneously fall below that threshold with this fixed background. This conditional local minimax statement is not a global physical or STA bound. Removing all other occupancy and reducing each target tree to its SOURCE reveals 0.849339\,ns alternatives that avoid the selected resource; tests of other shared resources and one new conflict refinement produce three distinct paths per target. Of nine path pairs, two satisfy the two-route RR-node capacities, both with maximum cost 0.849339\,ns. This matches the independent single-endpoint lower bound and solves that optimistic two-endpoint minimax relaxation within numerical tolerance. It does not yet restore other terminals or networks.

Both selected paths also attach to the actual retained trees at unchanged cost and have no mutual capacity conflict. Their remaining conflicts involve four other networks and four affected sinks. A six-network transaction reserves the two target paths together and restores those four sinks in ascending net/pin order. It passes unchanged-native FULL legality, independent physical/capacity checks and full STA. Both target delays decrease from 1.042804 to 0.849339\,ns. Six sink delays change in total, with three improvements and three regressions; all unrelated network traces remain identical. Final CPD improves from the strong R1 value 6.01810 to 5.85466\,ns (2.715807\%). Setup TNS improves from $-33483.7$ to $-33438.8$\,ns, and hold WNS/TNS remain zero. The worst path moves to a clk-domain path from the FPAddSub AlignModule register to the FPMult ExecuteModule register.

Occupied SB pairs increase from 39 to 40, CB crossing output sources from 969 to 970, and planar wirelength from 218,164 to 218,176. The prototype constructs and physically audits the transaction in 37.576534\,s; four query cores sum to 1.344968\,s within four query processes totaling 4.819448\,s. The native load/check/STA process takes 8.945292\,s. These stage measurements are not formal complete-route timing or an integrated implementation cost. This study uses 31 new reference queries, four transaction queries and one new legal native analysis call; the original plateau native evidence is reused. The gain supports joint critical-group selection and coordinated resource restoration on this development case, not plateau acceptance alone or broad method superiority. Exact native all-connection timing/pin information and equal-opportunity complete-policy A0/R1/Tf comparisons are the next work.
''')
main=paper/'main.tex';s=main.read_text();tag='\\input{data/coordinated_repair_discussion_v14.tex}';assert s.count(tag)==1
main.write_text(s.replace(tag,tag+'\n\\input{data/plateau_joint_repair_discussion_v14.tex}'))
old=paper/'data/coordinated_repair_discussion_v14.tex';s=old.read_text();s=s.replace('A separate acceptance-factor experiment is registered:', 'The following separate acceptance-factor experiment tests:');old.write_text(s)
claims=paper/'claims_evidence.md';s=claims.read_text()
s+='\n| C74 | 持平接受本身未改善CPD，当前延迟不退化仍可挤占其他关键连接的未来机会 | [新分支接受](../plateau_R1_step_01/decision.json)、[同目标反事实](../plateau_R1_counterfactual_01/analysis.json)、[综合机制证据](../plateau_joint_opportunity_01.json) | 复用旧native，strict拒绝保留；新分支下一5目标0收益。5目标树/端点/prefix相同，6个RR占用变化使net6587pin4的0.185826ns机会消失。未宣称plateau步骤已有CPD收益 |\n'
s+='| C75 | 固定背景的局部资源瓶颈不能当作物理全局上限，联合兼容路径仍有潜力 | [固定背景联合参考](../joint_critical_reference_01/analysis.json)、[联合路径池及实际接入](../plateau_joint_opportunity_01.json) | 共享容量1 IPIN82120限制两目标同时低于1.042804ns，仅对固定其他网/保留树成立。端点放松后每目标3个路径，9对中2对RR容量兼容且max0.849339ns，匹配独立LB，最优仅属于该两端点零RC图放松。两路径接实际树代价不变但仍有4网4汇冲突，非直接方法性能 |\n'
s+='| C76 | 两关键连接联合选择并恢复4阻塞汇点，在强R1上获得原生合法CPD收益 | [构造](../joint_coordinated_repair_01/analysis.json)、[原生FULL/STA](../joint_coordinated_native_01/completion.json)、[汇总](../plateau_joint_repair_summary_01.json)、[下一原生STA信息实验](../native_sta_frontier_experiment_01.json) | CPD6.01810→5.85466ns（2.715807%），TNS改善、hold不变；6网6汇延迟改变含3退化，其余网络不变。SB39→40/CB969→970/线长+12。构造含审计37.576534s，queryprocess4.819448s含core1.344968s，analysis8.945292s，非正式完整路由开销。本阶段35新query/1legalnativeanalysis，未做统一完整策略跨电路推广 |\n';claims.write_text(s)
status=paper/'DEVELOPMENT_STATUS.md';status.write_text('当前状态（优先于历史）：plateau接受后下一5目标无收益；同目标反事实确认资源挤占。联合两目标兼容路径+4阻塞汇恢复通过nativeFULL/STA，强R1 CPD6.01810→5.85466ns（2.715807%），SB/CB各+1、线长+12。35新查询/1新legalanalysis，旧plateau native复用，未推广一般方法。下一原生全连接STA/精确pin信息用于统一关键组选择和A0/R1/Tf完整策略对照；研究active，新增仅本地。\n\n'+status.read_text())
ledger=paper/'data/evidence_v14_ledger.json';v=read(ledger)
files=[D/'plateau_joint_repair_summary_01.json',D/'plateau_joint_opportunity_01.json',D/'plateau_R1_step_01/decision.json',D/'plateau_policy_implementation_01.json',D/'joint_coordinated_repair_01/analysis.json',D/'joint_coordinated_native_01/completion.json',D/'joint_coordinated_native_01/path_migration_analysis.json',nextfile,csvpath,fragment,old]
files += [D/n/'analysis.json' for n in ['plateau_R1_queries_02','plateau_R1_relaxed_02','plateau_R1_counterfactual_01','joint_critical_reference_01','endpoint_capacity_reference_01','endpoint_resource_327367_01','endpoint_resource_338492_01','endpoint_resource_413276_01','endpoint_resource_82112_01']]
for p in files:v['sources_sha256'][str(p.relative_to(D))]=sha(p)
v['plateau_joint_repair']=dict(status=summary['status'],new_queries=35,new_native_analysis_calls=1,baseline_R1_CPD_ns=6.01810,accepted_R1_joint_CPD_ns=5.85466,CPD_improvement_percent=summary['native_CPD_improvement_percent'],next_registered=nextfile.name)
write(ledger,v)
print(dict(status=summary['status'],CPD=[6.01810,5.85466],next=nextfile.name),flush=True)
