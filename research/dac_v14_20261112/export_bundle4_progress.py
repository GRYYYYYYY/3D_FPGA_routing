#!/usr/bin/env python3
"""Add sealed whole-bundle evidence and its controlled contribution to the paper."""
import shutil,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';h=p/'data/ledger_history_20261113'/('bundle4_'+str(time.time_ns()));h.mkdir()
for n in ['main.tex','claims_evidence.md','mechanisms_and_ablation.md','DEVELOPMENT_STATUS.md','data/evidence_v14_ledger.json']:
 target=h/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p/n,target)
s=read(D/'R1_fast_bundle4_resource_summary_01.json');m=read(D/'R1_fast_bundle4_mechanism_01.json');archive=read(D/'multiobjective_archive_37/completion.json');assert s['passed']and m['passed']and archive['passed'];tex=p/'data/bundle4_resource_v14.tex';assert not tex.exists();tex.write_text(r'''\subsection{Whole-bundle resource improvement and controlled attribution}
The K4 distinct-net resource trajectory has now completed with actor-final input, context and cache seals. From the same automatically obtained R1 fast root, two accepted whole transactions preserve exact CPD13.228145689936355 ns and finish at2069048 wire,79 SB and5071 CB. Relative to the root this is168 additional wire units, seven fewer SB and one fewer CB. All candidates receive real replacement, independent capacity/scope/domain checks and complete native FULL/STA. The joint archive now contains222 observations. The low-wire A0 state and low-SB R1 states remain external alternatives rather than being collapsed to a single winner or a method-only frontier.

\begin{table}[t]
\centering\scriptsize
\caption{K4 controls from each own-current state; exact CPD is constant throughout. OFF and ON have identical cut scope/order and native search costs.}
\begin{tabular}{lrrr}
\hline
State & Wire & SB & CB\\
\hline
R1 fast root &2068880&86&5072\\
First OFF &2068908&83&5072\\
First ON,committed &2069004&83&5071\\
Second OFF &2069000&80&5071\\
Second ON,committed &2069048&79&5071\\
\hline
\end{tabular}
\end{table}
The first automatic bundle selects31972/pin8,21922/pin4,21927/pin5 and21946/pin1. Unrestricted native repair already removes three SB. ON additionally removes one CB at96 extra wire units relative to OFF; that first ON candidate regresses one setup component, still4.869294 ns above the current worst. After commit, current resources and complete STA are used to rerank. The second bundle changes to7031/pin9,77160/pin3,53191/pin23 and3914/pin13605. Its OFF removes three more SB from the accepted current state; ON removes four, spending48 additional wire units relative to that OFF candidate. Both second candidates improve three setup components, regress none, and introduce no hold-violation regression. Their selection and outcomes were not obtained by carrying the initial target list forward.

The final selected worst endpoint, all winning arrival-cone nodes/edges and ten winning routed-connection identities exactly match the root. Counts within50/100/200/500/1000 ps of the worst setup value remain4/4/5/10/77. Thus this resource trajectory has no observed critical-path migration. It demonstrates resource improvement within an exact timing envelope, not strict CPD improvement or endpoint-wide dominance over every initial state. The final K4 state and the earlier single-cut paired state are alternatives: K4 uses six fewer SB but sixty more wire units, at the same CPD/CB. Against the native-only single-cut state, K4 saves five SB and one CB but spends160 more wire units. These distinctions keep both old and new legal Pareto tradeoffs in the archive.

The complete imported-state paired workflow is1198.820 s. It executes four candidate FULL/STA validations and nine native children including input observations and repair workers. Search cores total9.017 s, nested inside371.064 s of native child lifetimes. Sequential outer phase sums are510.142 s for candidate pooled FULL/STA/materialization,191.823 s for native-worker requests,156.187 s for transaction audits,83.789 s for worker materialization,56.285 s for selection and22.200 s for domain audits; initialization, initial observation and final seals account for the remainder. These levels are not additive across nesting boundaries. K4 validates more cuts per complete candidate gate, but its workload/policy differs from the single-cut native-only and older paired workflows. This is mechanism and cost evidence, not a formally rotated speedup or complete cold routing-plus-repair timing result. Initial routing, cache construction and all reused historical creation remain separate unknown configuration costs.

\paragraph{Next combination based on the improved strong native root.}
A read-only screen of the completed lower-wire strong-A0 timing state finds60 current sharing scopes. Its first K4 window is21922/pin4,62976/pin27,21927/pin5 and21946/pin1; all four have current setup margin above10.553678 ns. Structural removal potential is not feasible savings or a guarantee of unchanged final timing. An independent registered K4 native-only/paired diagnostic starts from this same sealed algorithmically obtained13.228146 ns state, with exact root CPD/SB/CB and a fixed0.1\% wire allowance. Each policy reranks from its own accepted state; the initial read-only selection is reused with exact input binding rather than rerun for reporting. It uses the released single-native-process diagnostic lane while the original K8 and later native-first owners keep their versions and rules. Real feasibility, complete replacement, physical/FULL/STA and final budget acceptance remain mandatory; outcomes are pending. This combination does not require resource selection alone to improve CPD before it may follow a timing improvement.
''')
main=p/'main.tex';t=main.read_text();needle=r'\input{data/strong_start_tradeoffs_terminal_v14.tex}';assert t.count(needle)==1;t=t.replace(needle,needle+'\n'+r'\input{data/bundle4_resource_v14.tex}');t=t.replace('a crossing-domain trajectory trades one SB and one CB for108 wire units.','a four-net bundle trajectory trades seven SB and one CB for168 wire units.');main.write_text(t)
claims=[('C150','K4完整封存：同精确CPD减少7SB/1CB，逐态原生控制隔离贡献','R1_fast_bundle4_mechanism_01.json','R1快速根13.228145689936355ns，final2069048wire/79SB/5071CB，+168wire/−7SB/−1CB。首轮OFF已减3SB，ON额外−1CB/+96wire；后轮ON较OFF额外−1SB/+48wire。关键锥完全不变；不是新搜索原语或所有资源全胜。'),('C151','完整K4研究流程开销与验证摊薄','R1_fast_bundle4_resource_summary_01.json','1198.820s导入态双臂流程；4候选FULLSTA、9native children、core9.017s嵌于child371.064s。规划56.285s，主要成本仍是完整状态/审计/STA；不同K/策略/后端不作正式速度比，冷完整单配置成本未知。'),('C152','强A0低线长快速态上的资源组合潜力与独立登记','strong_A0_fast_resource_screen_01/completion.json','0native/route的现有状态筛查得60scope，K4最小时序余量10.553678ns，仅是结构筛查。初筛报告字段名修复精确复用已完成选择，未重跑。后续native-only/paired独立同根各自当前态；原K8/native-first保留，组合结果待验证。')]
with (p/'claims_evidence.md').open('a')as f:
 for key,title,link,claim in claims:f.write(f'\n| {key} | {title} | [可核查证据](../{link}) | {claim} |\n')
with (p/'mechanisms_and_ablation.md').open('a')as f:f.write('\nC150–C152：K4两轮同源OFF/ON表明资源scope/当前调度已有收益，域限制额外给出首轮CB与后轮SB节省。ON总收益不能全归新原语。4条候选FULLSTA覆盖8个提交cut，开销仍由完整审计/状态占主导；必须等native-first各自轨迹验证是否值得为额外资源质量执行ON。强A0 timing→resource独立同根对照已启动，不要求各模块独立改善CPD，最终budget/FULLSTA仍统一验证。\n')
f=p/'DEVELOPMENT_STATUS.md';f.write_text('# C150–C152：K4减少7SB/1CB与强A0组合验证\n\nK4两步完整封存13.228145689936355ns/2069048wire/79SB/5071CB，关键锥不变，1198.820s是导入态配对流程。档案37=222观察；原K8继续，native-first仍等待，强A0低线长快速态K4独立原生/配对实验已启动，结果未知。新内容本地，Goal active。\n\n'+f.read_text())
files=[tex,D/'R1_fast_bundle4_mechanism_01.json',D/'R1_fast_bundle4_resource_summary_01.json',D/'multiobjective_archive_37/completion.json',D/'multiobjective_tradeoff_summary_15.json',D/'R1_fast_bundle4_final_cone_01.json',D/'strong_A0_fast_resource_screen_01/completion.json',D/'strong_A0_fast_resource_dev_01/queue/registration.json',D/'run_serial_current_resource_repair.py',D/'run_serial_resource_transactions.py'];ledger=read(p/'data/evidence_v14_ledger.json')
for f in files:ledger['sources_sha256'][str(f.relative_to(D))]=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger);write(p/'data/bundle4_delta_binding_01.json',dict(passed=True,claims=[x[0]for x in claims],sources_sha256={str(f.relative_to(D)):sha(f)for f in files},native_calls=0,archive_records=archive['records'],qualification='Only new sealed bundle result/cone/control/cost evidence and explicitly pending independent combination. No full historical replay/audit or duplicated completed native experiment.'))
print(dict(sources=len(ledger['sources_sha256']),claims=[x[0]for x in claims]),flush=True)
