#!/usr/bin/env python3
"""Report the factorial query result and redirect development by decision evidence."""
import collections
import csv
import math
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

b=D/'tree_aware_candidate_offline_01'
a=read(b/'analysis.json');potential=read(D/'critical_path_opportunity_01/analysis.json')
assert a['passed'] and potential['passed']
for doc in [a,potential]:
    assert all(sha(p)==h for p,h in doc['source_sha256'].items())
il=[r for r in a['rows'] if r['mode']==3]
counts=collections.Counter();pairs=[]
for row in il:
    u=row['upper_seconds'];v=row['actual_nonpreferred_extension_upper_seconds']
    if u is None or v is None:continue
    state='equal' if math.isclose(u,v,rel_tol=1e-12,abs_tol=1e-24) else 'preferred_lower_upper' if u<v else 'alternative_lower_upper'
    counts[state]+=1
    pairs.append(dict(search=row['search'],net=row['net'],pin=row['pin'],iteration=row['iteration'],
        criticality=row['criticality'],high_criticality=row['high_criticality'],preferred_upper_seconds=u,
        nonpreferred_upper_seconds=v,comparison=state))
decision=dict(passed=True,paired_valid_witness_contexts=len(pairs),high_criticality_paired_contexts=sum(r['high_criticality'] for r in pairs),
    upper_comparison=dict(counts),rows=pairs,
    current_final_worst_path_connections=potential['connections'],
    current_final_worst_path_guided_connections=sum(c['in_guided_query_contexts'] for c in potential['connections']),
    current_final_worst_path_guided_nets=sum(c['net_in_guided_query_contexts'] for c in potential['connections']),
    decision='Do not promote or further prioritize query precision from aggregate coverage alone. Existing valid paired preferred/nonpreferred witnesses do not overlap high-criticality contexts; final worst-path connections are outside this guided query population. Next estimate fixed-other-net capacity-feasible repair potential of these connections before choosing a native intervention. Keep the tested tree-aware query model for future consumer integration.',
    qualification='Comparison of two witnessed upper bounds is not an optimality/dominance certificate. Current final worst-path absence does not rule out indirect congestion effects or earlier timing-path changes. Final-path selection is retrospective and not an online policy.',
    source_sha256={str(p):sha(p) for p in [Path(__file__),b/'analysis.json',D/'critical_path_opportunity_01/analysis.json']})
write(b/'decision_relevance.json',decision)
register=D/'critical_capacity_potential_experiment_01.json'
assert not register.exists()
write(register,dict(status='registered_not_implemented_not_submitted',native_route_calls=0,
    question='Can current final critical connections be shortened while preserving other nets and retained branches, or do useful alternatives require coordinated congestion repair?',
    evidence='Two current Tf worst-path inter-cluster connections have no final guide and no guided-search context. For net5479 pin36, same-input A0/R1/A1 route suffixes spliced into current tree reduce physical RR cost from3.265075ns to0.663513ns but each conflicts with three occupied unit-capacity resources. All six baseline transplant proposals conflict somewhere.',
    input='Reuse actual_search_tree_eltwise_dev_01/T2 final legal route, exact RRG, packed/place inputs, plus critical_path_opportunity_01 endpoint/retained-tree alternatives. No new native trace needed for this diagnostic.',
    arms=['Relaxed: exact zero-RC shortest extension from retained prefixes after pruning only the target-exclusive chain; ignore other-net occupancy.',
          'Fixed-other-nets: same graph and retained tree, disallow a new RR node when other-net occupancy exhausts its capacity; stop at retained-tree nodes and charge actual prefix once.'],
    domain='Full-device reference graph, explicitly a diagnostic domain and not a claim that the last native search used that BB. Permit physical cross-layer edges without a single-cross model restriction. Derive source/seed eligibility from graph/tree and state the difference from historical actual-heap eligibility.',
    checks=['Frozen input identity, physical edges/switches and zero RC.',
            'Small graph independent Floyd reference for the new capacity/tree adapter; existing generic query core may be reused by exact source hash.',
            'Reference result must not exceed the known current legal path when that path is admitted; missing paths and exclusions explained.',
            'All returned suffixes intersect retained tree only at anchor; check other sink reachability, RR occupancy and recomputed current prefix.',
            'Native FULL (including reserved OPIN/nonconfig/bus mux) and final STA remain necessary before calling any alternative realizable method performance.'],
    followup='If fixed-other-net shorter witnesses exist, test transactional native timing repair/selection on appropriate current-criticality targets; otherwise identify blocking net/resource sets for bounded coordinated reroute. Do not simply increase preferred-query budget. Include matched A0/R1/Tf with the same scope and convergence opportunity for actual quality comparisons.',
    limitations='Retrospective final-path selection is a potential diagnostic, not deployable algorithm selection. No global optimum, source-cut impossibility or CPD gain inferred from absence/presence in this local model.',
    limits=dict(timeout_seconds=1800,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3),
    source_sha256={str(p):sha(p) for p in [b/'analysis.json',b/'decision_relevance.json',D/'critical_path_opportunity_01/analysis.json']}))

paper=D/'paper';csvpath=paper/'data/tree_aware_query_v14.csv'
assert not csvpath.exists()
with csvpath.open('w') as f:
    writer=csv.writer(f);writer.writerow(['arm','contexts','paths','fixed_tree_extensions','inherited_only_paths','high_criticality_fixed_extensions','expansions','exact','query_core_seconds','modeled_alternative_dominance'])
    for arm,s in a['summaries'].items():
        writer.writerow([arm,s['queries'],s['paths'],s['fixed_tree_extensions'],s['inherited_only_paths'],s['high_criticality_fixed_extensions'],s['expansions'],s['exact'],s['query_seconds'],s['modeled_nonpreferred_better']])
fragment=paper/'data/tree_aware_query_discussion_v14.tex'
fragment.write_text(r'''The tree-aware factorial query study now replays all 3,809 captured guided searches, with the same 256-expansion, 16,384-label and 65,536-heap-entry limits. P retains the single-additional-preferred-cross query; I also admits actual sink-layer seeds whose retained ancestry already satisfies that preferred crossing; L terminates a reverse query at any current-tree node, allowing a virtual goal only for an eligible queued seed; IL combines both factors. These restrictions affect the offline query graph, not native legal routing branches. The adapter passes 14,400 independent forward-phase Floyd comparisons on 600 random graphs, including zero cycles, missing sources, work and storage limits; 3,600 additional original-adapter controls reproduce P. All ten previous actual focus queries reproduce their original P outputs and paths, excluding elapsed time.

\begin{center}\small
\begin{tabular}{lrrrr}
\toprule
Arm & Paths & Fixed-tree & Inherited only & Expansions\\
\midrule
P & 996 & 910 & 0 & 854,229\\
I & 1,091 & 1,091 & 296 & 829,254\\
L & 927 & 927 & 0 & 863,501\\
IL & 1,091 & 1,091 & 296 & 826,257\\
\bottomrule
\end{tabular}
\end{center}

Every returned physical edge, bounding-box admission, seed prefix and preferred-crossing identity is independently checked against the original zero-RC RRG. L/IL witnesses have no additional retained-tree intersection. All reported lower frontiers are checked by separate nonheuristic Dijkstra through states below the claimed threshold, using $10^{-24}$\,s absolute plus $10^{-12}$ relative numerical tolerance. None of the 15,236 queries reports exactness or a certificate that the available nonpreferred alternative dominates the modeled preferred class.

The coverage increase has substantial tradeoffs. Relative to P, IL gains 322 paths and loses 227; among contexts with paths in both arms, 134 upper bounds decrease, 61 increase and 574 agree. These are witnessed-cost comparisons, not optimal-cost comparisons. The changed outcomes cover 84 distinct connections; 35 changed contexts have criticality at least the native float 0.9 threshold. Fixed-tree witnesses in that high-criticality population increase from 10 to 31. I and IL happen to return the same path coverage and witnessed costs on these inputs, although their work and stop states differ; this does not establish general equivalence of tree-terminal filtering. Ordered core-query time totals are 1.416462/1.911896/1.347421/1.850084\,s for P/I/L/IL. They exclude graph loading, index construction and independent audits, and provide no formal native speedup claim.

Decision overlap is more restrictive than aggregate coverage: only 37 contexts have both an IL preferred witness and an actually attachable native no-new-cross witness whose retained ancestry does not already satisfy the preference. Of these, the alternative upper bound is lower in 34 cases, equal in two and higher in one; none has criticality at least 0.9. Comparing these upper bounds does not certify either class optimum. This result argues against continuing to optimize query precision without examining the decision interface and the connections that limit timing.

A separate retrospective check uses the current Tf final worst-path report. Its two inter-cluster connections, net 6590 pin 3 and net 5479 pin 36, have neither final guides nor occurrences in the captured guided-query population; their networks also do not occur in that population. This does not rule out indirect congestion effects. Their audited physical RR delays are 1.042804 and 3.265075\,ns. Existing same-input count-two A0/R1/A1 paths can be spliced into the current retained tree after removing only the target-exclusive chain. For net 5479, each baseline gives a 0.663513\,ns local path, but each would overuse three currently occupied unit-capacity RR nodes. All six inspected transplant proposals have capacity conflicts. The physical opportunity therefore is not yet a realizable repair, and its 2.601561\,ns local gap must not be presented as an achievable CPD reduction. Exact fixed-other-net capacity-constrained extension search is the next separately registered diagnostic; native FULL legality and STA remain necessary before any quality claim. No new native route calls were made for either offline study.
''')
main=paper/'main.tex';s=main.read_text();tag='\\input{data/actual_search_tree_discussion_v14.tex}'
assert s.count(tag)==1;s=s.replace(tag,tag+'\n\\input{data/tree_aware_query_discussion_v14.tex}');main.write_text(s)
old=paper/'data/actual_search_tree_discussion_v14.tex';s=old.read_text();s=s.replace('That next study has not been implemented or submitted.','That study is completed below as an offline factorial comparison; it has not been integrated into a native decision policy.');old.write_text(s)
claims=paper/'claims_evidence.md';s=claims.read_text();s=s.replace('已登记未实施/提交，不预告CPD收益','登记后已完成离线四臂，见C66；尚无原生消费或CPD收益')
s+='\n| C66 | 树感知查询提高部分可接入路径覆盖，但仍无决策证书且有覆盖退化 | [四臂完整审计](../tree_aware_candidate_offline_01/analysis.json)、[决策相关性](../tree_aware_candidate_offline_01/decision_relevance.json)、[成本表](data/tree_aware_query_v14.csv) | 3809上下文×P/I/L/IL，同256预算；14400独立Floyd检查/3600旧适配器控制及旧10实际focus逐字段复现。P910、IL1091固定树可接入witness，highcritical10→31；322新增/227丢失，134上界降低/61升高。四臂exact及替代支配证书均0。37双类有效witness无一highcritical；34替代UB更低不等于最优或STA证明。无native调用、无质量推广或正式提速主张 |\n'
s+='| C67 | 当前最差路径连接不在guided查询总体，强基线短路径移植受真实资源冲突限制 | [潜力诊断](../critical_path_opportunity_01/analysis.json)、[下一容量查询登记](../critical_capacity_potential_experiment_01.json) | 当前Tf两跨簇连接net6590pin3/net5479pin36均无finalguide及guidedsearch，相关net也无；不排除间接拥塞作用。后者3.265075ns RR路径可用A0/R1/A1实际suffix构造0.663513ns局部路径，但各冲突3个容量1资源；六个移植提议全部有容量冲突。保留其他分支，单目标exclusivechain剪除，物理边和prefix/占用检查；未改route，未做nativeFULL/STA。2.601561ns局部差不是可实现CPD收益，finalpath事后选样非在线算法 |\n';claims.write_text(s)
status=paper/'DEVELOPMENT_STATUS.md';s=status.read_text();status.write_text('当前状态（本段优先于下方历史状态）：树感知P/I/L/IL离线15236查询及真实RRG/上下界审计完成；P→IL可接入路径910→1091，但新增322/丢失227，无exact/支配证书。37双类有效witness无一highcritical。当前Tf最差路径两跨簇连接不在guided总体；强基线对net5479有2.601561ns局部物理差，但3资源冲突。下一为独立固定其他网络容量约束潜力诊断，已登记未实施。无新增native调用，研究active；这些结果仅本地，公开仍f7167bd。\n\n'+s)
ledger=paper/'data/evidence_v14_ledger.json';v=read(ledger)
for p in [b/'analysis.json',b/'decision_relevance.json',D/'critical_path_opportunity_01/analysis.json',register,csvpath,fragment,old]:
    v['sources_sha256'][str(p.relative_to(D))]=sha(p)
v['tree_aware_query']=dict(status='offline_audited_not_promoted',contexts=3809,queries=15236,
    fixed_extensions_P_IL=[910,1091],path_gains_losses=[322,227],runtime_exact=0,
    paired_high_criticality=0,native_route_calls=0,next_registered=register.name)
write(ledger,v)
print(dict(paired_witnesses=len(pairs),paired_high_criticality=decision['high_criticality_paired_contexts'],
    upper_comparison=dict(counts),current_critical_connections=len(potential['connections']),next=register.name))
