#!/usr/bin/env python3
"""Record the no-improvement result and its capacity-coupling explanation."""
import csv
from datetime import datetime,timezone
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

names=['current_sta_queries_01','fixed_sta_queries_01','current_sta_relaxed_01','blocker_subset_reference_01']
docs={name:read(D/name/'analysis.json') for name in names}
for doc in docs.values():
    assert doc['passed'] and all(sha(p)==h for p,h in doc['source_sha256'].items())
dynamic=docs[names[0]];fixed=docs[names[1]];relaxed=docs[names[2]];subsets=docs[names[3]]
assert len(dynamic['results'])==5 and len(fixed['results'])==2 and len(subsets['rows'])==6
assert all(r['improvement_ns']==0 for r in dynamic['results']+fixed['results']+subsets['rows'])
positive=[r for r in relaxed['results'] if r['improvement_ns']>1e-6];assert len(positive)==1
target=positive[0]
nextfile=D/'coordinated_critical_repair_experiment_01.json';assert not nextfile.exists()
write(nextfile,dict(status='registered_not_implemented_not_submitted',
    question='Can a bounded coordinated repair realize the shorter current-critical path while rerouting its three blocking nets and preserving final timing?',
    evidence='CurrentSTA five target fixed-tree/fixed-other-capacity queries and frozen-target two controls all exact with zero gain. Onlynet6587pin4 has a relaxed gap0.379290599ns. Releasing any one or two of the three observed blocker nets still gives zero gain; releasing all admits the relaxed optimum. One conflicting resource carries an eight-sink shared subtree.',
    input_run=str(D/'critical_repair_validation_01/runs/eltwise_layer_R'),
    selection='Derive target and blockers from sealed relaxed/subset witnesses, not a new hardcoded circuit-specific net list. This pilot inherits one observed critical target; broader online candidate selection remains unvalidated.',
    implementation_plan=['Use an independent copy of the current route. Reserve the selected target suffix; preserve its remaining branches.',
        'For each blocking resource, identify all descendant sinks. Remove only the affected subtree plus newly dangling exclusive ancestors; preserve all other branches and unrelated nets.',
        'Reattach affected blocker sinks under current occupancy, with reserved target resources unavailable to blocker nets. Reuse static graph and capacities; recompute each changing tree prefix and occupancy after every attachment.',
        'First deterministic net/sink order, then separately registered order controls if order causes failure. A failed attachment discards the entire transaction.',
        'Only complete candidate routes may be loaded by unchanged VPR. Require FULL legality and fullSTA, keep the original route and all rejected candidates. Do not reuse the prior one-target-only physical guard for multi-net acceptance.'],
    affected_scope=subsets['blocked_resource_downstream'],
    acceptance='Strictly lower final native CPD after all blocker nets are legally restored; separately record WNS/TNS and every changed sink delay. Legal or timing rejection rolls back the whole transaction. Real Tdel and final STA remain untouched.',
    comparisons=['Original accepted state reused at exact hashes as no-repair quality control.',
        'Single-target/free-capacity repair already exhausted; no rerun needed for unchanged input.',
        'Report target benefit and blocker degradation separately, plus final CPD/tails/resources/complete prototype cost.',
        'If promising, match A0/R1/Tf with identical coordination, scope and per-invocation work opportunities before promotion.'],
    discriminants=['All blockers restored and CPD improves: develop bounded coordination as a general repair stage; evaluate matched baselines.',
        'Reroute fails: distinguish retained-subtree restriction/order from resource infeasibility; consider alternative target witnesses or bounded neighborhood expansion, not a global impossibility claim.',
        'Target improves but blocker or other near-critical paths dominate: change joint timing objective/acceptance or candidate selection.',
        'Runtime dominated by repeated graph loads orSTA: preserve full cost evidence and move successful policy to persistent/in-process execution.'],
    qualification='Three blockers are necessary only within the tested release set. Other one/two-net alternatives outside that set have not been ruled out. Capacity release is not a realizable route, and0.379290599ns is not an achieved CPD reduction.',
    per_process_limits=dict(timeout_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    scope_policy='No global date/count/matrix stopping condition. Per-invocation bounded neighborhoods/order trials do not terminate overall research.',
    source_sha256={str(D/name/'analysis.json'):sha(D/name/'analysis.json') for name in names}))

summary=dict(passed=True,status='current_STA_single_connection_plateau_and_blocker_coupling_verified',
    previous_goal_turn='progress',native_analysis_calls=0,route_search_calls=0,new_queries=18,
    current_cpd_ns=6.20393,accepted_route_unchanged=True,quality_promoted=False,
    dynamic_targets=len(dynamic['results']),fixed_targets=len(fixed['results']),
    positive_relaxed_targets=[dict(net=target['net'],pin=target['pin'],gap_ns=target['improvement_ns'])],
    minimum_release_cardinality_in_observed_three_net_set=3,
    unchanged_current_targets=[dict(net=r['net'],pin=r['pin'],physical_ns=r['physical_seconds']*1e9,expansions=r['expansions'],core_seconds=r['query_seconds']) for r in dynamic['results']],
    blocker_subtrees=subsets['blocked_resource_downstream'],
    interpretation='Refreshed targets do not improve this state under single-target fixed-tree/free-capacity repair. The one remaining relaxed opportunity requires coordinated resource changes within the observed blocker set. This rejects a simple sequential-free-capacity continuation here, not all current-STA or coordinated repair mechanisms.',
    fairness='Frozen target control has2 selected connections, refreshed has5; both exhaust selected sets, but this is not equal wall/work budget speed evidence. No new native quality result. Four of five refreshed targets have no relaxed fixed-tree gain.',
    source_sha256={name+'/analysis.json':sha(D/name/'analysis.json') for name in names},
    next_registered=nextfile.name,public_snapshot='f7167bd1fbeb267d7ffc02766eeb2e5966aec387',this_followup_pushed=False)
write(D/'current_sta_repair_summary_01.json',summary)
paper=D/'paper';csvpath=paper/'data/current_sta_repair_v14.csv'
with csvpath.open('w') as f:
    w=csv.writer(f);w.writerow(['target_net','pin','current_ns','capacity_ns','relaxed_ns','capacity_expansions','capacity_core_seconds'])
    for r in dynamic['results']:
        z=next(z for z in relaxed['results'] if (z['net'],z['pin'])==(r['net'],r['pin']))
        w.writerow([r['net'],r['pin'],r['current_physical_seconds']*1e9,r['physical_seconds']*1e9,z['physical_seconds']*1e9,r['expansions'],r['query_seconds']])
fragment=paper/'data/current_sta_repair_discussion_v14.tex'
fragment.write_text(r'''The current-STA continuation now tests all five inter-cluster connections on the migrated worst path. A generic selector reads the accepted state's setup report, packed netlist, placement and route; it has no circuit-specific target whitelist. Matching uses the reported driver net and sink cluster location, with ambiguities explicitly retained as a conservative target set rather than an asserted exact atom-pin mapping. The five current targets have unambiguous recorded location matches. The same audited zero-RC, full-device, retained-tree capacity query finds exact path costs equal to their current physical delays: 1.228630, 0.663513, 0.477688, 0.849339 and 0.663513\,ns. No improving candidate exists under that model, so no unchanged candidate is submitted to native analysis. The accepted CPD remains 6.20393\,ns. Frozen initial-target controls also have zero gain on the current state. Both policies exhaust their selected sets (five versus two targets); this is not an equal-work or equal-time performance comparison.

Relaxing other-net occupancy changes only the first target's optimal cost: net 6587 pin 4 decreases from 1.228630 to 0.849339\,ns, a 0.379291\,ns local opportunity. The other four targets have no relaxed fixed-tree improvement. The shorter witness conflicts with three unit-capacity RR nodes owned by nets 2570, 6563 and 7541. A six-query subset experiment releases each singleton and each pair of these networks, preserving all other occupancy and tree conditions; none admits a shorter path. Releasing all three admits the already audited fully relaxed optimum, so no duplicate all-three query is needed. The empty-set result is also reused from the exact fixed-capacity query. Necessity of three releases applies only within this observed three-net set; alternative blocker sets elsewhere in the graph are not excluded.

The conflicting resource of net 2570 serves eight of its nine sinks, while the other two blockers each have one sink. Thus the next intervention must examine coordinated repair and shared-subtree handling rather than just refreshing a single target or increasing its query budget. Releasing a network's occupancy is not an actual reroute: all affected sinks must be restored before native FULL/STA acceptance, and blocker timing regressions can erase the target's local gain. This study performs 18 new reference queries (five fixed-capacity, two frozen-target controls, five relaxed, six proper-subset releases) and no new native routing or analysis calls. It rejects simple single-target fixed-tree/free-capacity continuation at this state; it neither establishes global timing optimality nor rules out coordinated, subtree-changing or different-domain interventions.
''')
main=paper/'main.tex';s=main.read_text();tag='\\input{data/critical_capacity_discussion_v14.tex}';assert s.count(tag)==1
main.write_text(s.replace(tag,tag+'\n\\input{data/current_sta_repair_discussion_v14.tex}'))
old=paper/'data/critical_capacity_discussion_v14.tex';s=old.read_text()
s=s.replace("The next registered intervention selects targets from each accepted state's STA, rather than retaining the original worst-path targets.","The following registered continuation selects targets from the accepted state's STA, rather than retaining the original worst-path targets.")
old.write_text(s)
claims=paper/'claims_evidence.md';s=claims.read_text()
s+='\n| C70 | 当前STA更新目标后，单连接固定树/固定其他占用修复仍无增益 | [当前目标](../current_sta_queries_01/analysis.json)、[冻结目标控制](../fixed_sta_queries_01/analysis.json)、[汇总](../current_sta_repair_summary_01.json) | 当前5目标及原2目标在同一接受状态均exact等于当前物理延迟，0候选/0native；CPD保持6.20393。5对2为各自集合穷尽，非等工作量速度比较。拒绝本状态下简单逐连接继续修复，不推断全局最优 |\n'
s+='| C71 | 唯一剩余放松机会受多网络资源耦合限制 | [放松查询](../current_sta_relaxed_01/analysis.json)、[阻塞子集参考](../blocker_subset_reference_01/analysis.json)、[协调修复登记](../coordinated_critical_repair_experiment_01.json) | net6587pin4存在0.379291ns局部放松差，3个容量1资源冲突；3单例+3二元集合均0收益，全3释放可用已审计放松最优witness。仅对该3网集合成立，非全图最小阻塞集；一个资源涉及8/9汇共享子树。尚未恢复这些网络，不是合法方法或CPD收益；当前轮18新参考查询、0native |\n'
claims.write_text(s)
status=paper/'DEVELOPMENT_STATUS.md';status.write_text('当前状态（优先于历史）：当前STA的5连接及冻结2连接固定容量查询均精确0收益；5连接放松后仅net6587pin4有0.379291ns机会。其3阻塞网的6个非空真子集均0收益，需在该集合内同时释放3网；其中1个阻塞资源影响8汇共享子树。18新查询，0native，接受路由未变。下一协调修复已登记未实施；研究active，新增仅本地。\n\n'+status.read_text())
ledger=paper/'data/evidence_v14_ledger.json';v=read(ledger)
for p in [*[D/name/'analysis.json' for name in names],D/'current_sta_repair_summary_01.json',nextfile,csvpath,fragment,old]:
    v['sources_sha256'][str(p.relative_to(D))]=sha(p)
v['current_sta_repair']=dict(status=summary['status'],new_queries=18,native_calls=0,CPD_ns=6.20393,dynamic_fixed_target_counts=[5,2],positive_relaxed_targets=1,observed_blocker_set_minimum_releases=3,next_registered=nextfile.name)
write(ledger,v)
print(dict(status=summary['status'],queries=18,native_calls=0,next=nextfile.name),flush=True)
