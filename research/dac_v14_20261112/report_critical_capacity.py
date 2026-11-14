#!/usr/bin/env python3
"""Close the feasible repair diagnostic; register a state-dependent intervention."""
import csv
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

b = D/'critical_capacity_potential_01'
n = D/'critical_repair_validation_01'
a, done, migration = [read(p) for p in [b/'analysis.json',n/'completion.json',n/'path_migration_analysis.json']]
assert all(v['passed'] for v in [a,done,migration])
assert done['native_analysis_calls']==2 and done['route_search_calls']==0
assert len(migration['changed_physical_sink_delays'])==1
paper = D/'paper'
register = D/'current_sta_repair_experiment_01.json'
assert not register.exists()
write(register,dict(status='registered_selector_implemented_queries_not_submitted',
    hypothesis='Re-selecting repair targets from the current STA state can address critical-path migration that limits a successful one-connection repair.',
    evidence='One capacity-feasible repair shortened net5479/pin36 by1.955259ns, but FULL/STA CPD improved only0.00419ns and the worst path moved to bram_select[6] -> bram_rdata_ext[60]. All23905 sink physical delays were compared; only the repaired connection changed.',
    input_run=str(n/'runs/eltwise_layer_R'),
    input_policy='This first development state is a diagnostic repaired Tf route. Use only its current STA/route/occupancy to select next targets; no hardcoded net/pin list or A0/R1 oracle suffix. A successful continuation is not a fair final algorithm comparison until the same procedure is applied from matched A0/R1/Tf initial states.',
    implementation=dict(selector='select_current_critical_targets.py::select', query='critical_capacity_adapter.h::query_critical_capacity',
        route_transaction='Refactor audited target-exclusive-chain removal and isolated route serialization into reusable helpers. Retain input route, proposed route and accepted-state pointer separately.',
        native_consumer='Unchanged VPR route-file load, FULL legality and full STA before acceptance; later in-process integration targets route.cpp post-legal/best-state handling. This prototype is an external repair stage, not yet an in-process router.'),
    factors=['Frozen initial worst-path target set versus re-selection from each accepted state.',
        'One-target repair versus sequential current-path repairs; use native STA after each proposal.',
        'Worst-path only versus near-critical path union is a later separate selection factor.',
        'Full-device search is explicit; compare with native-domain restricted search before attributing benefit to selection alone.'],
    query_policy='For each current-path target, prune only its exclusive chain; reuse immutable graph and capacities, rebuild ownership/tree-prefix state from current accepted route. First query fixed-other-net free capacity; use a relaxed reference only to diagnose absence of feasible improvement. Rank admissible proposals by physical path reduction, deterministic net/pin tie-break. A fixed-tree prefix is charged once.',
    acceptance='First pilot accepts only nativeFULL-legal proposals with strictly smaller reported CPD and unchanged other sink physical delays on the verified zero-RC graph. Keep full STA reports and all rejected proposals. If equal-CPD near-critical ties block useful progress, design a separate no-worse-WNS/TNS or path-vector acceptance factor; do not silently change this rule.',
    discriminants=['Further CPD gain after re-selection supports path-migration-aware intervention; compare against frozen targets with the same work opportunity.',
        'No feasible shorter extension with a large relaxed gap motivates bounded coordinated reroute or retained-subtree replacement.',
        'Shorter extensions but unchanged CPD motivate a near-critical-set objective/acceptance test, not neighboring guide-weight tuning.',
        'Same-scope A0/R1 gain equally or more: retain improvement as a general post-route stage, make no Tf-specific advantage claim.',
        'Runtime dominated by repeated graph load/STA: prototype cost must be reported, then evaluate persistent/in-process integration.'],
    metrics=['all statuses including failed/timeout/missing', 'per-circuit matched CPD and tails', 'native FULL and STA',
        'actual SB/CB resources', 'accepted/rejected target and path migration', 'native original iteration count',
        'query/preparation/planning time', 'entire initial-route-plus-repair wall time'],
    per_process_limits=dict(timeout_seconds=1800,query_memory_bytes=24*1024**3,native_memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    scope_limits='No total research call/date/matrix cap. A per-invocation repair/work budget and no-gain exit bound a method invocation only, never the overall research goal.',
    source_sha256={str(p):sha(p) for p in [n/'completion.json',n/'path_migration_analysis.json',b/'analysis.json',D/'select_current_critical_targets.py']}))

csvpath=paper/'data/critical_capacity_v14.csv'
with csvpath.open('w') as f:
    writer=csv.writer(f);writer.writerow(['net','pin','fixed_other_capacity','current_ns','reference_ns','gain_ns','expansions','core_seconds','capacity_feasible'])
    for r in a['results']:
        writer.writerow([r['net'],r['pin'],r['mode'],r['current_physical_seconds']*1e9,r['physical_seconds']*1e9,r['improvement_ns'],r['expansions'],r['query_seconds'],r['rr_capacity_feasible']])
fragment=paper/'data/critical_capacity_discussion_v14.tex'
fragment.write_text(r'''A subsequent full-device reference search separates physical opportunity from fixed-other-net capacity feasibility. After pruning only the target-exclusive chain, the reverse query terminates at retained-tree anchors and charges their physical prefix once. It admits any physical crossing count and excludes retained IPIN/SINK nodes as anchors. Thus it is an exact local zero-RC graph reference, not a claim about the historical native bounding box, queued seeds, or global routing/STA optimum. The capacity adapter passes 2,000 independent forward-Floyd comparisons on 1,000 random directed graphs (751 reachable and 1,249 unreachable cases). Physical RRG edges, all 1,028,568 RR capacities, ownership and preserved branches are independently checked.

For net 6590 pin 3, the relaxed reference is 0.856978\,ns, while the fixed-other-net optimum equals the current 1.042804\,ns. For net 5479 pin 36, the relaxed reference is 0.663513\,ns and the capacity-feasible reference is 1.309816\,ns, versus the current 3.265075\,ns. The latter establishes a candidate improvement of 1.955259\,ns within the stated local model. Fixed-capacity query core times are 0.008217 and 0.064732\,s; these exclude graph loading, preparation and validation.

The shorter net 5479 witness is then serialized into an isolated route copy. Two unchanged-VPR analysis-only loads compare the original and repaired routes using identical packed/place/RRG inputs, switch-ID verification, native FULL checks and full STA. Both pass. Independent physical-delay comparison covers 23,905 sink connections: only net 5479 pin 36 changes; all other net traces are identical. Whole-design CPD improves only from 6.20812 to 6.20393\,ns (0.067492\%), as the worst path moves from bram\_select[7] to bram\_rdata\_ext[15], to bram\_select[6] to bram\_rdata\_ext[60]. This supports feasible local repair and critical-path migration, not a 1.955259\,ns CPD gain. The repaired CPD remains worse than the matched count-two A0/R1 result of 6.01810\,ns.

Planar wirelength remains 228,420, but occupied SB pairs increase from 118 to 119 and CB crossing output sources from 955 to 956. Analysis-only process times are 8.586962 and 9.784481\,s; they are load/check/STA costs, not full route-process timings or a formal speed comparison. There are two new native analysis calls and zero new route-search calls. A reporting-wrapper path error occurred after both native processes completed; a separate recovery uses the exact graph from their manifests, with no native reruns. Original failures and recovery evidence are retained.

The next registered intervention selects targets from each accepted state's STA, rather than retaining the original worst-path targets. It preserves a transactional best route and native legality/STA acceptance. Worst-path versus near-critical-set selection, fixed versus refreshed targets, and full-device versus native-domain search are distinct factors. Matched A0/R1/Tf must receive the same post-route repair opportunity before any method-quality claim; this retrospective single-circuit repair is not a promoted online algorithm.
''')
main=paper/'main.tex';s=main.read_text();tag='\\input{data/tree_aware_query_discussion_v14.tex}';assert s.count(tag)==1
main.write_text(s.replace(tag,tag+'\n\\input{data/critical_capacity_discussion_v14.tex}'))
old=paper/'data/tree_aware_query_discussion_v14.tex';s=old.read_text()
s=s.replace('Exact fixed-other-net capacity-constrained extension search is the next separately registered diagnostic; native FULL legality and STA remain necessary before any quality claim.', 'The separately registered capacity-constrained reference and native FULL/STA intervention are completed in the following study; these transplant proposals themselves remain infeasible.')
old.write_text(s)
claims=paper/'claims_evidence.md';s=claims.read_text()
s+='\n| C68 | 固定其他网络容量下仍有可行关键连接缩短空间 | [容量参考](../critical_capacity_potential_01/analysis.json)、[完整查询数据](data/critical_capacity_v14.csv) | 零RC全设备固定保留树模型，2000独立Floyd比较；net6590无容量可行收益，net5479由3.265075到1.309816ns。只对该局部模型exact，非历史BB/heap或全局STA界 |\n'
s+='| C69 | 原生合法局部修复仅带来小幅CPD收益，最差路径发生迁移 | [原生FULL/STA](../critical_repair_validation_01/completion.json)、[路径迁移及23905连接核对](../critical_repair_validation_01/path_migration_analysis.json)、[下一实验](../current_sta_repair_experiment_01.json) | 两analysis-only加载均合法；仅net5479pin36物理延迟改变，CPD6.20812→6.20393ns，仍劣于强A0/R1的6.01810；SB118→119/CB955→956，线长不变。8.586962/9.784481s为加载检查STA进程，非完整路由计时。包装器路径错误在native完成后独立恢复，零重跑。未推广为通用新方法 |\n'
claims.write_text(s)
status=paper/'DEVELOPMENT_STATUS.md';status.write_text('当前状态（优先于历史）：固定容量最短扩展与原生FULL/STA验证完成；net5479局部缩短1.955259ns，CPD仅改善0.00419ns且最差路径迁移。强A0/R1仍更好，未推广。下一为当前STA驱动的事务式修复，通用目标选择器已实施，后续查询尚未提交。2个analysis-only调用，0个新route-search调用；研究active，新增仅本地。\n\n'+status.read_text())
ledger=paper/'data/evidence_v14_ledger.json';v=read(ledger)
for p in [b/'analysis.json',b/'unit_validation.json',n/'completion.json',n/'path_migration_analysis.json',n/'input_seal.json',n/'independent_native_analysis_audit.json',register,csvpath,fragment,old]:
    v['sources_sha256'][str(p.relative_to(D))]=sha(p)
v['critical_capacity_repair']=dict(status='feasible_single_connection_diagnostic_not_promoted',native_analysis_calls=2,route_search_calls=0,cpd_ns=[6.20812,6.20393],local_gain_ns=1.955259065766768,checked_sink_connections=23905,next_registered=register.name)
write(ledger,v)
report=dict(passed=True,status='capacity_reference_and_native_intervention_verified',research_complete=False,quality_promoted=False,
    local_reference=a['results'],native_observations=done['observations'],path_migration=str(n/'path_migration_analysis.json'),
    interpretation='A physically shorter capacity-feasible connection exists and nativeFULL/STA realizes it, but another path limits CPD. Prioritize state-dependent critical/near-critical repair; do not infer useful algorithm quality from query coverage alone.',
    updated_utc=datetime.now(timezone.utc).isoformat(),native_analysis_calls=2,route_search_calls=0,
    source_sha256={str(p.relative_to(D)):sha(p) for p in [Path(__file__),b/'analysis.json',n/'completion.json',n/'path_migration_analysis.json',n/'input_seal.json',register]},
    public_snapshot='f7167bd1fbeb267d7ffc02766eeb2e5966aec387',this_followup_pushed=False)
write(D/'critical_capacity_repair_summary_01.json',report)
print(dict(status=report['status'],cpd_ns=[6.20812,6.20393],next=register.name))
