#!/usr/bin/env python3
"""Report actual coordinated gains and register a separate plateau-policy test."""
import csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

transaction=read(D/'coordinated_repair_01/analysis.json')
coordinated=read(D/'coordinated_native_01/completion.json')
follow=read(D/'postcoordination_path_analysis_01.json')
assert transaction['passed'] and transaction['all_sinks_restored'] and coordinated['passed'] and coordinated['accepted'] and follow['passed']
tf=follow['arms']['Tf']['completion'];r1=follow['arms']['R1']['completion']
assert tf['passed'] and tf['accepted'] and r1['passed'] and not r1['accepted']
assert r1['before_cpd_ns']==r1['after_cpd_ns']
assert len(r1['physical_change']['changed'])==1 and all(r['after_ns']<r['before_ns'] for r in r1['physical_change']['changed'])
for arm in ['Tf','A0','R1']:
    doc=read(D/f'postcoordination_{arm}_queries_01/analysis.json');assert doc['passed']
    assert all(sha(p)==h for p,h in doc['source_sha256'].items())
assert all(sha(p)==h for p,h in transaction['source_sha256'].items())
nextfile=D/'postroute_plateau_policy_experiment_01.json';assert not nextfile.exists()
write(nextfile,dict(status='registered_not_implemented_not_submitted',
    question='Does a strictly improving connection-delay vector allow safe progress across a tied critical-path plateau that strictCPD acceptance rejects?',
    evidence='StrongR1 net6590pin4 is shortened by0.185825799ns with all other23904 sink physical delays unchanged, nativeFULL passed, reported CPD remains6.01810ns and sTNS remains-33483.7ns. Worst-path start changes frombram_select[7] tobram_select[6]. Therefore even strictTNS improvement would reject this observed first plateau step.',
    arms=['Strict:existing R1 candidate remains rejected; immutable completed control reused.',
        'Plateau branch:allow this existing complete legal route as a branch state only when fullSTA CPD/setup/hold WNS/TNS do not worsen, every audited sink physical delay is nonincreasing and at least one strictly decreases. Then reselect targets from that state and attempt further free-capacity repairs.'],
    start_state=str(D/'native_reconvergence_eltwise_dev_01/runs/eltwise_layer_R1'),
    reusable_first_candidate=str(D/'postcoordination_R1_native_01/runs/eltwise_layer_R'),
    existing_rejection_preserved=True,
    scope='First acceptance-factor experiment on verified zero-RC graph with single-connection repairs. This componentwise guard does not admit the coordinated transaction, whose blocker delays include regressions. Nonzero-RC/load changes require a different fully validated delay comparison.',
    implementation=['Keep strict and plateau accepted-state pointers separate; never rewrite old completion or frozen routes.',
        'Use generic currentSTA selection and the same exact fixed-tree free-capacity query, deterministic proposal ordering and nativeFULL/STA.',
        'Guard all sink connections, not only selected ones; log equal-reported-CPD steps, route resources and complete cost. Track route hashes and strict delay-vector descent to detect cycles.',
        'A locally accepted plateau step is not a demonstrated CPD benefit. Evaluate whether later steps actually reduce finalCPD or stall; preserve the original best state and alternate branch states.'],
    discriminants=['Later CPD drops after previously rejected zero-CPD-gain steps: supports multi-path plateau handling.',
        'No further free-capacity gain: diagnose resource/tree coupling on current tied paths, rather than pretending the first step already improved quality.',
        'Unacceptable runtime/resources or no robust final gain: change selection/coordinate tied connections and retain costs.'],
    matched_policy_followup='After selecting a stable policy, apply the same selection/acceptance/scope/coordinated-fallback/work budget from frozen matched count-two A0/R1/Tf initial states. CurrentTf has already received three interventions; its6.01928ns is not superior to6.01810ns baselines or an equal-opportunity method comparison.',
    overhead_followup='Prototype loads static graph for each attachment and repeats externalSTA. Measure complete cost; consider a persistent graph/query worker or in-process integration only with equivalent decisions and native validation.',
    budgets='Bound each invocation/process and retain all statuses. No global research date, call-count or fixed-matrix stopping rule.',
    per_process_limits=dict(timeout_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    source_sha256={str(p):sha(p) for p in [D/'postcoordination_path_analysis_01.json',D/'postcoordination_R1_native_01/completion.json',D/'postcoordination_R1_native_01/physical_change_audit.json',D/'coordinated_native_01/completion.json',D/'postcoordination_reference_experiment_01.json']}))

rows=[]
for arm,doc,b in [('Tf_coord',coordinated,D/'coordinated_native_01'),('Tf_next',tf,D/'postcoordination_Tf_native_01'),('R1_next',r1,D/'postcoordination_R1_native_01')]:
    after=Path(doc['candidate_run']);before=Path(doc['input_run'])
    metrics=read(after/'independent_audit.json')['physical_metrics'];old_metrics=read(before/'independent_audit.json')['physical_metrics']
    rows.append(dict(arm=arm,status='legal',accepted=doc['accepted'],cpd_before_ns=doc['before_cpd_ns'],cpd_after_ns=doc['after_cpd_ns'],
        analysis_process_seconds=doc['process_seconds'],changed_sink_count=len(doc['physical_change']['changed']),
        resources_before=old_metrics,resources_after=metrics,completion=str(b/'completion.json')))
summary=dict(passed=True,status='coordinated_native_gain_and_followup_sealed_not_promoted',native_analysis_calls=3,route_search_calls=0,
    status_counts=dict(legal=3,failed=0,timeout=0,missing=0),accepted=2,rejected_for_no_CPD_gain=1,queries=24,
    observations=rows,coordinated_target_physical_gain_ns=0.3792905989286055,
    coordinated_blocker_connections_restored=10,coordinated_affected_nets=4,
    coordinated_preparation_seconds=transaction['build_process_seconds'],
    coordinated_query_core_seconds=sum(q['core_seconds'] for q in transaction['queries']),
    coordinated_query_process_seconds=sum(q['process_seconds'] for q in transaction['queries']),
    latest_Tf_accepted_cpd_ns=tf['after_cpd_ns'],original_Tf_cpd_ns=6.20812,strong_A0_R1_cpd_ns=6.01810,
    Tf_improvement_from_original_percent=(1-tf['after_cpd_ns']/6.20812)*100,
    Tf_remaining_gap_to_strong_baseline_ns=tf['after_cpd_ns']-6.01810,
    qualification='Three nativeanalysis interventions, not fullrouteprocess samples or method promotion. Tf trajectory has prior repair opportunities; matched whole-policy A0/R1/Tf validation and formal timing remain required. R1 tie changes the worst-path start without reported CPD/TNS improvement.',
    next_registered=nextfile.name,public_snapshot='f7167bd1fbeb267d7ffc02766eeb2e5966aec387',this_followup_pushed=False,
    source_sha256={str(p.relative_to(D)):sha(p) for p in [D/'coordinated_repair_01/analysis.json',D/'coordinated_native_01/completion.json',D/'postcoordination_path_analysis_01.json',D/'postcoordination_Tf_native_01/completion.json',D/'postcoordination_R1_native_01/completion.json',nextfile]})
write(D/'coordinated_repair_summary_01.json',summary)
paper=D/'paper';csvpath=paper/'data/coordinated_repair_v14.csv'
with csvpath.open('w') as f:
    w=csv.writer(f);w.writerow(['arm','status','accepted','CPD_before_ns','CPD_after_ns','changed_sinks','analysis_process_seconds','SB_after','CB_after','planar_wirelength_after'])
    for r in rows:
        p=r['resources_after'];w.writerow([r['arm'],r['status'],r['accepted'],r['cpd_before_ns'],r['cpd_after_ns'],r['changed_sink_count'],r['analysis_process_seconds'],p['sb_pairs_used'],p['cb_crossing_output_sources_used'],p['planar_wirelength_excluding_sb_half_nodes']])
fragment=paper/'data/coordinated_repair_discussion_v14.tex'
fragment.write_text(r'''A bounded coordinated transaction realizes the previously blocked critical witness. It reserves the target suffix, removes the blocker subtrees serving the ten affected sinks, and retains all paths to unaffected sinks. Blocker networks and sinks are processed in ascending ID/pin order; each attachment uses the current occupancy and recomputed retained-tree prefixes. A failed attachment would discard the transaction. The tree operations pass 1,000 randomized independent path-preservation, ancestry, pruning and attachment checks. All ten attachments succeed, and 91 new directed edges are checked against the original RRG. Unrelated network traces are unchanged and all terminals are restored before native analysis.

The unchanged VPR binary passes native FULL legality and full STA. CPD improves from 6.20393 to 6.09618\,ns (1.736802\%); setup TNS improves from $-35113.1$ to $-35066.8$\,ns. The target RR delay decreases by 0.379291\,ns. Eleven sink delays change: eight decrease and three increase, including blocker degradations of approximately 0.274651, 0.646302 and 0.460476\,ns. Thus final acceptance is based on the whole-design STA result, not target improvement alone. Occupied SB pairs increase from 119 to 128, CB crossing output sources from 956 to 959, and planar wirelength from 228,420 to 228,481. The worst path moves to bram\_select[4] to bram\_wdata\_c\_5\_ext[53]. This is a feasible coordinated improvement on one current state, not a globally optimal or promoted method.

Prototype construction takes 48.047812\,s including preparation and physical audits. Its ten query cores sum to 5.395719\,s; the ten complete query processes sum to 13.894189\,s, including repeated static-graph loading. The native analysis process takes 8.915268\,s. These are nested or distinct stage measurements as stated, not additive core/parent timers, not full initial-route process measurements, and not a formal native speed comparison. Persistent graph reuse and in-process integration remain engineering work rather than claimed speedups.

The next current-STA free-capacity probe is applied to the repaired Tf state and to the matched strong A0/R1 states. Packed netlist, placement and RRG digests match, but the route states and prior repair opportunities differ. The four Tf targets contain one positive witness (net 7647 pin 56, 0.662117\,ns local gain); A0's five targets contain none; R1's five contain one (net 6590 pin 4, 0.185826\,ns local gain). Both positive proposals pass native FULL/STA. Tf improves further from 6.09618 to 6.01928\,ns and is accepted. R1 stays at 6.01810\,ns and is rejected by the registered strict-CPD rule, despite only its target physical delay decreasing. R1's reported setup TNS also stays at $-33483.7$\,ns while the worst-path start moves from bram\_select[7] to bram\_select[6], exposing a tied-path plateau rather than evidence that the physical repair did not happen.

The Tf trajectory now improves 3.041823\% from its frozen 6.20812\,ns state but remains 0.00118\,ns worse than the strong A0/R1 CPD. Its final SB/CB counts are 129/960 and planar wirelength is 228,483; method superiority is not established. This stage performs 24 new queries and three legal native analysis calls, with two accepted interventions and one legal strict-CPD rejection. A separate acceptance-factor experiment is registered: permit a zero-CPD-gain single-connection step only when all audited sink physical delays are nonincreasing with at least one strict decrease and native setup/hold metrics do not worsen, then test whether subsequent steps reduce CPD. Existing strict-policy evidence remains immutable. This zero-RC componentwise condition does not automatically apply to coordinated trades, nonzero-RC loading, or broader timing objectives. Equal-opportunity complete-policy A0/R1/Tf comparisons are still required.
''')
main=paper/'main.tex';s=main.read_text();tag='\\input{data/current_sta_repair_discussion_v14.tex}';assert s.count(tag)==1
main.write_text(s.replace(tag,tag+'\n\\input{data/coordinated_repair_discussion_v14.tex}'))
old=paper/'data/current_sta_repair_discussion_v14.tex';s=old.read_text();s=s.replace('Thus the next intervention must examine coordinated repair and shared-subtree handling rather than just refreshing a single target or increasing its query budget.','The following intervention therefore examines coordinated repair and shared-subtree handling rather than just refreshing a single target or increasing its query budget.');old.write_text(s)
claims=paper/'claims_evidence.md';s=claims.read_text()
s+='\n| C72 | 协调恢复共享阻塞子树实现合法CPD改善 | [事务构造](../coordinated_repair_01/analysis.json)、[原生FULL/STA](../coordinated_native_01/completion.json)、[成本和资源](data/coordinated_repair_v14.csv) | 3阻塞网10汇全部重接，1000随机树验证，91真实新边检查；4网11汇延迟改变含3退化，其余网络不变。CPD6.20393→6.09618ns，sTNS改善；SB119→128/CB956→959，线长+61。构造48.047812s含审计，querycore5.395719s包含于queryprocess13.894189s，analysis8.915268s，非正式完整路由计时 |\n'
s+='| C73 | 后续单连接修复继续降低Tf，但R1暴露关键路径持平台阶 | [后续STA与路径](../postcoordination_path_analysis_01.json)、[汇总](../coordinated_repair_summary_01.json)、[独立接受准则实验](../postroute_plateau_policy_experiment_01.json) | Tf6.09618→6.01928ns，仍差强A0/R1的6.01810，资源129SB/960CB；R1目标缩短0.185826ns且其他23904汇不变，但CPD/TNS持平、最差起点迁移，按旧strictCPD规则拒绝。当前阶段24新queries/3legalnativeanalysis，2接受1合法拒绝，非等完整修复机会或方法推广。下一单独验证全汇物理延迟向量不退化的plateau分支，不能自动应用于有退化的协调事务 |\n';claims.write_text(s)
status=paper/'DEVELOPMENT_STATUS.md';status.write_text('当前状态（优先于历史）：协调事务10汇重接且nativeFULL/STA通过，Tf6.20393→6.09618；新STA单连接再改善到6.01928，仍差强A0/R1的6.01810。R1合法局部缩短但CPD/TNS持平且最差起点迁移，strictCPD拒绝保留。当前轮24新查询/3legalanalysis，未推广，额外开销和资源明确记录。下一plateau接受准则实验已登记未实施，随后统一A0/R1/Tf完整策略比较；研究active，新内容仅本地。\n\n'+status.read_text())
ledger=paper/'data/evidence_v14_ledger.json';v=read(ledger)
files=[D/'coordinated_repair_summary_01.json',D/'coordinated_repair_01/analysis.json',D/'coordinated_repair_01/unit_validation.json',D/'coordinated_native_01/completion.json',D/'postcoordination_path_analysis_01.json',nextfile,csvpath,fragment,old]
files += [D/f'postcoordination_{a}_queries_01/analysis.json' for a in ['Tf','A0','R1']]
for p in files:v['sources_sha256'][str(p.relative_to(D))]=sha(p)
v['coordinated_repair']=dict(status=summary['status'],queries=24,native_analysis_calls=3,all_legal=True,accepted=2,latest_Tf_CPD_ns=tf['after_cpd_ns'],strong_A0_R1_CPD_ns=6.01810,next_registered=nextfile.name)
write(ledger,v)
print(dict(status=summary['status'],latest_Tf=tf['after_cpd_ns'],R1_rejected_CPD_tie=True,next=nextfile.name),flush=True)
