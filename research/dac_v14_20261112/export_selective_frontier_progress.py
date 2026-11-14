#!/usr/bin/env python3
"""Publish completed tradeoffs and causal partial-domain evidence into the live draft."""
import shutil
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
h = p / 'data/ledger_history_20261113' / ('selective_frontier_' + str(time.time_ns()))
h.mkdir()
for n in ['main.tex', 'claims_evidence.md', 'mechanisms_and_ablation.md', 'DEVELOPMENT_STATUS.md', 'data/evidence_v14_ledger.json']:
    target = h / n
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p / n, target)
archive = read(D / 'multiobjective_archive_44/completion.json')
assert archive['passed'] and archive['records'] == 264
assert read(D / 'A0_K8_final_critical_structure_02.json')['passed']
assert read(D / 'A0_joint_K8_endpoint_acceptance_01.json')['passed']
assert read(D / 'failure_feedback_domain_dev_02/completion.json')['passed']
tex = p / 'data/selective_frontier_v14.tex'
assert not tex.exists()
tex.write_text(r'''\section{Current timing--resource results and mechanism controls}
This section supersedes earlier development snapshots for current frontier membership. Older recorded points, pending-at-the-time statements and negative attempts remain historical evidence, rather than new independent algorithm configurations. The archive has264 legal observations, including repeated states and reobservations. Initial-guide A0/R1/U/Tf cohorts retain their own versions, convergence and timing identities; none is silently combined with a later repair core to fabricate a complete algorithm point. Resource rows below use actual planar wire, SB pairs and CB output sources, not guide recommendations or an inferred area/power estimate.

\subsection{Joint results, external baselines and retained alternatives}
\begin{table}[h]
\centering\caption{BNN quality observations on the same physical inputs. ``A0 fast'' starts after three automatically selected strict timing repairs of the strong native A0 route. Subsequent rows have explicitly different roots or repair opportunities; this is a descriptive quality comparison, not an equal-compute superiority result.}
\label{tab:current-joint-frontier}
\small
\begin{tabular}{lrrrr}\hline
State & CPD(ns) & Wire & SB & CB\\\hline
Strong native A0 &13.607436&2059567&94&5062\\
Strong native R1 &13.421610&2068908&86&5072\\
A0 fast/native K8 &13.228146&2059603&86&5062\\
A0 fast/paired K8 &13.228146&2059882&79&5061\\
R1 fast/paired K8 &13.228146&2069040&74&5071\\
R1 partial domain &13.228146&2069104&72&5071\\\hline
\end{tabular}
\end{table}
The A0-fast native-only K8 trajectory retains exact13.228145689936355 ns CPD and ends at2059603 wire,86 SB and5062 CB. Compared with the strong native A0 starting route, it uses36 more wire units, eight fewer SB and unchanged CB, with2.787376\% lower CPD. Its paired K8 counterpart spends279 more wire units for seven fewer SB and one fewer CB, at identical CPD. Thus the domain mechanism offers a measurable resource tradeoff beyond an equal-selector unrestricted native control, without being universally superior. Both branches reselect from their own committed state after divergence. The final complete winning critical cones, fan-in values and critical connection identities remain unchanged during this resource phase; flat CPD does not mean the resource change failed to execute.

The native-only A0-fast K8 result quality-dominates the earlier resource-only A0 K4 state (13.607436 ns,2059667 wire,86 SB,5062 CB), as well as both A0-fast K4 final states. Those older states cease being independent quality-frontier corners. The slower native-first A0 state (13.607436 ns,2059583 wire,88 SB,5062 CB) still has a lower-wire tradeoff and is not discarded solely for its CPD. The A0-fast paired K8 state quality-dominates the strong native R1 row in all four quality coordinates. This does not establish method superiority at matched total opportunities or complete runtime. Older Rq/reassignment alternatives with CB5060 or5059 retain a lower-CB option. The archive includes external strong A0/R1 states; it is not an internal-method-only Pareto display.

Under the strong A0 CB cap and forty wire units of headroom, the best observed fast timing has86 SB. With0.1\% wire headroom the observed minimum is79 SB. Under the different R1 wire/CB envelope the observed minimum is72 SB. These are empirical budget slices of collected states, not mathematical bounds, uniformly selected confirmation results or a per-circuit history-best algorithm score. Missing complete runtime keeps219 observations provisionally retained; quality domination alone cannot certify five-dimensional domination when comparable complete time is absent.

\subsection{Mechanism intervention: release one capacity-incompatible domain}
The previous all-eight-domain failure at31767/pin1 motivated a new independent intervention from its exact same sealed source, scope, raw criticalities, native binary and query order. The old failed search and unrestricted control are reused as evidence. Releasing only the certified blocked network, with seven other domains retained, restores all eight connections and passes real replacement, independent scope/edge/capacity checks, native FULL, fresh STA and final context seals. The result is13.228145689936355 ns,2069104 wire,72 SB and5071 CB. Relative to the same-source unrestricted fallback it saves two SB for64 wire units, with unchanged CPD and CB. Relative to its79-SB source it saves seven SB for56 wire units. This is actual feasibility and a distinct joint quality point, beyond the earlier necessary infeasibility certificate; it does not show that the two saved SB reduce CPD.

The next independent implementation releases a domain automatically when its native guided search cannot produce a capacity-feasible branch, resets search costs and retries just that network while preserving prior successful restorations. Search failure triggers release; absent a separate reachability certificate it is not described as proof that no path exists. Its build and tiny/large matched validation are distinct from the completed quality observation above. Default native search, real physical delay, complete-transaction capacity and final native FULL/STA remain mandatory. A failed whole transaction retains its original state.

\subsection{Combination contribution and cross-circuit transfer}
The first native-only A0 K8 commit produces exactly the route and full endpoint setup/hold vectors of the two-step native-only K4 final state. The first K4 step is endpoint-vector-flat and rejected by that policy; the whole K8 group improves one setup component with no regressions and is accepted, while strict CPD still rejects it. One candidate FULL/STA gate replaces two at this common state. This supports testing complete groups without requiring every intermediate component to improve CPD or even the endpoint vector. It is evidence from the already-fast diagnostic source; it does not establish that an independent pristine-root endpoint policy reaches it or that a plateau step enables later CPD improvement.

On eltwise, the strong native A0 source is6.018101128546505 ns,217065 wire,30 SB,968 CB. Paired K4 ends at the same CPD,217214 wire,25 SB,965 CB; native-first K4 ends at217181 wire,26 SB,965 CB. The latter spends33 fewer wire units but one more SB, so scheduling changes the tradeoff rather than preserving every outcome. Its first unrestricted result (217050 wire,27 SB,968 CB) already quality-dominates the source. Later unrestricted rejection genuinely invokes the guided alternative.

On SPMV, paired and native-first R1 K1 produce a byte-identical legal route and exact endpoint vectors at7.045986460951781 ns,148605 wire,zero SB,967 CB. This saves twelve wire units and one SB relative to its R1 root, but the strong A0 remains better in CPD and wire with the same vertical counts. This is a retained, explicitly baseline-dominated development result, not evidence of cross-circuit superiority. Eight-cut uniform selection and equal-opportunity multi-circuit confirmation remain subsequent work; K1/K4/K8 results cannot be labeled one fixed configuration.

\subsection{Full-cost accounting and current limitations}
The two-step A0-fast native-only K8 imported-state workflow takes829.329 s and its paired counterpart1248.263 s. The paired workflow makes three new native requests and exactly reuses one sealed unrestricted request; reused creation cost is not borrowed. Eltwise paired/native-first workflows take128.696/99.813 s; SPMV takes59.399/37.181 s and four/three native children. Those runs differ in work, state reuse or concurrent load and are not formal cold complete-algorithm speedups. The selective-domain intervention takes339.716 s including construction, audits, replacement, STA and final seals, but excluding creation of its pre-existing source. The previous R1 K8 total includes its failed request:18.699 s of native search core versus1057.993 s of imported research workflow. Neither is full routing-plus-repair single-configuration time. That cold complete time is still unknown; no U historical time or sum of unrelated stage histories fills it.

Loaded post-legal contexts reconstruct actual occupancy and current native STA, but do not restore the original route run's accumulated PathFinder congestion-price history. The matched restricted/unrestricted repair controls share this fresh loaded context. Porting to a running router must state whether that history is preserved or reset and test the choice. This limitation is distinct from true physical Tdel, actual resource counts or the legality of already validated repairs. Before confirmation, freeze circuit-independent selection/strategy parameters and compare strong A0/R1/native repairs with the same search domain, target rule, allowed tree scope and acceptance opportunities. No fixed matrix or design-budget endpoint is an end condition for the overall research goal.
''')
main = p / 'main.tex'
s = main.read_text()
old = 'A subsequent two-transaction native resource phase preserves CPD, removes six SB for sixteen further wire units, and improves one setup component without regressions.'
new = 'Subsequent K8 resource refinement preserves CPD: unrestricted native search reaches86 SB at2059603 wire, while retained-crossing domains reach79 SB and5061 CB at2059882 wire. A selective failure-domain release from an R1-fast state reaches72 SB at2069104 wire, exposing an explicit resource tradeoff.'
assert old in s
s = s.replace(old, new)
s = s.replace(r'\section{Experimental Setup}', r'\input{data/selective_frontier_v14.tex}' + '\n\n' + r'\section{Experimental Setup}')
s = s.replace(r'\section{Results}', r'\section{Frozen Initial-Guide Results}')
problem = r'''\paragraph{Current multiobjective repair problem.}
Among legal final routes, retain nondominated CPD, planar wire, actual SB/CB and comparable complete algorithm time. A branch can separately use strict CPD improvement, fixed-resource timing improvement or resource improvement under an explicit timing envelope. The latter two define design tradeoffs rather than a universal requirement to beat every strong A0 CPD. Intermediate private states may spend slack or resources when a mechanism-backed whole combination is checked and accepted atomically. Native FULL and fresh physical STA govern final acceptance; exact fixed endpoint vectors are evaluated only within the same constraints and endpoint identities. Frozen initial-guide experiments below remain separate from post-legal development.

'''
s = s.replace(r'\section{Method}', problem + r'\section{Method}')
main.write_text(s)
claims = [
    ('C159', '强A0 fast K8联合前沿与旧状态重判', 'strong_A0_paired_K8_summary_01.json', '同CPD下native-only2059603/86/5062与paired2059882/79/5061互不支配；旧慢A0 K4被质量支配，低wire native-first/低CB Rq仍保留。冷完整时间缺失，不作五维或同机会优越声明。'),
    ('C160', '完整组合可被端点策略接受而首个分步被拒', 'A0_joint_K8_endpoint_acceptance_01.json', 'K8首步与两步K4实际route/full-vector完全相同；首K4端点持平拒绝，K8一项setup改善零退化接受，strictCPD拒绝。已快起点诊断，非原始起点策略确认或后续CPD使能证明。'),
    ('C161', '按失败网络释放域获得真实合法取舍点', 'failure_feedback_domain_dev_02/completion.json', '相同源/8cut/native核/顺序，仅31767解除、其余7域保留：13.228145689936355ns/2069104wire/72SB/5071CB；较原生自由回退−2SB/+64wire。真实替换/FULLSTA/封存通过；339.716s是输入态研究流程，非冷完整算法。'),
    ('C162', '跨电路与native-first不等价控制', 'resource_schedule_cohort_binding_01.json', 'Eltwise节约SB/CB但native-first与paired取舍不同；SPMV route/vector完全相同但仍被强A0支配。机会/原生调用与流程时间分列，不以不同工作量流程比称正式加速。'),
]
with (p / 'claims_evidence.md').open('a') as f:
    for key, title, link, claim in claims:
        f.write(f'\n| {key} | {title} | [可核查证据](../{link}) | {claim} |\n')
with (p / 'mechanisms_and_ablation.md').open('a') as f:
    f.write('\nC159–C162：同scope unrestricted与domain可推进不同资源坐标，非只比旧R1；组合不要求每分步CPD/端点改善。必要性容量证书之后已有7域真实合法72SB点，自动fallback是独立后续实现。资源阶段关键锥不变以A0_K8_final_critical_structure_02为准；01的int/string比较误报已被纠正，无重跑native。loaded context未保存旧PathFinder累积价格历史，不能称完整当前router状态复用。跨电路SPMV仍被强A0支配，完整冷时间未知。\n')
status = p / 'DEVELOPMENT_STATUS.md'
status.write_text('# C159–C162：强基线联合前沿、选择性域释放与迁移控制\n\n档案44=264合法观察；219完整时间待定。新主结果位于selective_frontier_v14.tex，旧分节是历史封存记录。A0 fast K8形成86SB/低wire与79SB/低CB取舍；R1按网释放72SB真实通过。Eltwise有资源收益，SPMV仍被强A0支配。自动native failure-release独立构建/验证队列运行；原批次均完整保留。Goal active，无日期/次数/矩阵总停止条件，新增均本地未推送。\n\n' + status.read_text())
files = [tex, D / 'multiobjective_archive_44/completion.json', D / 'multiobjective_tradeoff_summary_20.json',
         D / 'common_resource_budget_slices_06.json', D / 'strong_A0_native_only_K8_summary_01.json',
         D / 'strong_A0_paired_K8_summary_01.json', D / 'A0_K8_final_critical_structure_02.json',
         D / 'A0_joint_K8_endpoint_acceptance_01.json', D / 'resource_schedule_cohort_binding_01.json',
         D / 'failure_feedback_domain_dev_02/completion.json', D / 'failure_feedback_domain_dev_02/round_000/candidate_00/partial_domain_decisions.json',
         D / 'failure_feedback_domain_dev_02/round_000/candidate_00/partial_domain_domain_audit.json',
         D / 'domain_failure_release_preparation_01.json', D / 'domain_failure_release_validation_queue_01/registration.json']
ledger = read(p / 'data/evidence_v14_ledger.json')
for f in files:
    ledger['sources_sha256'][str(f.relative_to(D))] = sha(f)
write(p / 'data/evidence_v14_ledger.json', ledger)
write(p / 'data/selective_frontier_delta_binding_01.json', dict(passed=True, claims=[c[0] for c in claims],
      archive_records=264, sources_sha256={str(f.relative_to(D)): sha(f) for f in files},
      native_calls=0, qualification='Completed quality and mechanism evidence with pending independent automatic implementation explicitly separated. Historical records preserved; no repeated full experiments to fill the manuscript.'))
print(dict(claims=[c[0] for c in claims], sources=len(ledger['sources_sha256'])), flush=True)
