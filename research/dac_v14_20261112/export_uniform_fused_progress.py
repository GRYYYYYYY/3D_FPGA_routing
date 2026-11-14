#!/usr/bin/env python3
"""Sync current results, relaxed potential and verified actual-candidate integration into both drafts."""
import shutil
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
h = p / 'data/ledger_history_20261113' / ('uniform_fused_' + str(time.time_ns()))
h.mkdir()
for name in ['main.tex', 'current_repair_main.tex', 'claims_evidence.md', 'mechanisms_and_ablation.md', 'DEVELOPMENT_STATUS.md', 'data/evidence_v14_ledger.json']:
    target = h / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p / name, target)
assert read(D / 'candidate_full_sta_native_binding_01.json')['passed']
assert read(D / 'full_root_timing_potential_02/completion.json')['all_source_root_distances_equal_current']
assert read(D / 'uniform_feedback_resource_dev_01/queue/completion.json')['passed']
assert read(D / 'multiobjective_archive_47/completion.json')['records'] == 282
f = p / 'current_repair_main.tex'
s = f.read_text()
s = s.replace('This integration has passed small-graph equivalence tests; representative large materialization and independent LOAD checks are separately registered.',
    'This integration has passed small-graph tests and the actual BNN resource transaction: dedicated candidate exports exactly equal a separate same-binary LOAD/FULL/STA, independent physical/scope checks pass, and source recovery is exact. CPD-changing or forced-path timing transactions remain outside that validated scope.')
old = 'Large actual-candidate physical/materialization checks and separate native LOAD controls remain pending in the registered queue.'
new = 'The BNN actual-candidate physical/materialization checks and separate same-binary native LOAD controls now pass. Two Python comparison/admission errors are preserved: endpoint tuple/list representation and applying a six-digit printed-source CPD check to a full-precision candidate metric. Recovery reuses the sealed native worker and passed transaction/domain audits with zero new repair searches, then executes two new independent validation-only LOAD jobs. No physical or STA tolerance is introduced.'
assert old in s
s = s.replace(old, new)
needle = 'Their extra validation-only jobs must not be counted as algorithm work or removed from the reported validation workflow.'
s = s.replace(needle, needle + ' The new fused kernel COMPLETE interval is28.757 s and includes its candidate observer; connection QUERY intervals sum to7.859 s. The372.048 s recovery segment reuses native creation from a prior attempt and includes new controls, so it is neither a fresh complete algorithm time nor a speedup measurement. A measured I/O target is also apparent: each full timing-graph echo is753.92 MiB and each native frontier357.20 MiB, repeated for source, candidate and restored source. A subsequent resource-only export-level experiment may omit an unused graph dump while preserving actual FULL/STA and complete endpoint/per-pin precision; that optimization is not yet implemented or timed.')
f.write_text(s)
tex = p / 'data/uniform_fused_v14.tex'
assert not tex.exists()
tex.write_text(r'''\subsection{Uniform pristine-root K8 and actual-candidate integration}
The original uniform resource cohort is now fully sealed. Both circuits use the same K8 cap, current ranking, fixed root CPD, root-wire plus0.1\% envelope and nonincreasing vertical objectives. Strong native BNN A0 starts at13.607436066820355ns/2059567wire/94SB/5062CB. Native-only K8 preserves CPD, reduces wire by four units and SB by eight, ending2059563/86/5062. Paired K8 reaches2059842/79/5061 at unchanged CPD, spending275 wire for15SB and1CB. These slower states retain a forty-wire advantage over corresponding timing-first resource endpoints; they are not discarded simply for failing to beat the fast CPD. They are developmental policy outcomes, not per-circuit historical best selection.

Eltwise native K8 reaches6.018101128546505ns/217050wire/26SB/968CB; paired K8 reaches217214/24/965 at the same CPD. The latter saves one SB versus old paired K4 with all other quality coordinates equal. Its actual domain groups have six then three networks and never release a failed domain, so this transfer gain is attributed to grouping/domain choice, not fallback. Native-only later legal resource regressions are recorded rather than committed. The archive now has282 legal observations, not282 independent configurations; its full matched-input quality projections retain strong A0/R1/U/Tf and different opportunities explicitly. A focused current-repair manuscript is maintained beside this chronological evidence draft.

\paragraph{A broader timing-potential reference.}
The existing fast-A0 current winning-cone portfolio had zero positive retained-prefix gain even without background occupancy. Source-root-only queries remove every shared-prefix restriction as well. Seven changed queries are newly solved and three identical queries exactly reused; all ten source-root relaxed distances equal the current static-switch distances. Every reverse witness is converted to and independently checked against actual forward RRG edges, excluding the artificial terminal. An initial audit-orientation mistake is preserved and corrected with zero repeated queries. This is an exact reference in the verified zero-RC switch-delay relaxation, not a global native-STA optimum or a research stop. It weakens the basis for merely increasing these same timing-query budgets at this state.

\paragraph{Actual candidate FULL/STA in one native worker.}
The independent callback installs complete candidate copies, performs native FULL, constructs fresh candidate STA and exports a dedicated actual route/vector. Original trees, sink lookups, occupancy, route digest and output hooks are restored; original FULL/STA is observed again. Ten tiny native jobs pass, including separate candidate LOAD equality and failure isolation. The BNN resource candidate also passes full physical/retained-scope checks and exact whole-route structure equivalence to the prior72SB reference; candidate native exports equal a separate same-binary LOAD/FULL/STA and original source exports are exact after restoration and in a following independent child. The successful materializer uses a distinct installed-candidate receipt and never relabels source timing as candidate timing.

Two failed Python admission stages are retained. Version01 compared tuple endpoint IDs against their JSON list form, then its empty-state cleanup masked that assertion; all numeric source fields and source-restored exports actually agreed. Version02 still applied an old six-significant-digit printed-source check to the new explicit full-precision candidate metric, so a valid candidate was stopped before its physical audit. Version03 normalizes endpoint identities, preserves an empty state list and separates printed-source consistency from actual candidate-vector identity. It exactly reuses the completed sealed native worker and already passed transaction/domain audits, performs no new repair search and then runs two independent validation-only LOAD jobs. All final context/input/cache seals pass. No tolerance or synthetic CPD rounding enters acceptance.

Fused COMPLETE time is28.757s including its candidate observer; connection QUERY components total7.859s. Neither is the earlier callback-free search core. The372.048s recovery segment includes materialization, fresh controls and sealing but reuses a prior worker; original native creation and failed Python stages stay separately recorded. It is not cold full routing-plus-repair time or a speedup. The full timing echo is753.92MiB and native frontier357.20MiB per state, repeated across source/candidate/restored views. Conditional resource-only graph-dump export is a subsequent measured hypothesis, not an implemented omission of native STA.

\paragraph{Independent composition diagnostic.}
The completed automatic resource-first BNN endpoint supplies the next registered timing state:79SB/5061CB remain hard caps, while wire is capped at2061627 from the original pristine root's0.1\% envelope. It is not inflated by restarting that percentage at the resource successor. The timing selector reselects from its own current STA and requires strict CPD improvement after every complete accepted transaction. This diagnoses phase order with the already automatic first phase reused; it is not a manual accepted timing prefix, a frozen confirmation score or a new complete cold timing measurement. The overall research remains active.
''')
f = p / 'main.tex'
s = f.read_text()
assert s.count(r'\section{Conclusion}') == 1
f.write_text(s.replace(r'\section{Conclusion}', r'\input{data/uniform_fused_v14.tex}' + '\n\n' + r'\section{Conclusion}'))
claims = [
    ('C164', '统一原生起点K8的真实质量取舍', 'uniform_feedback_resource_dev_01/queue/completion.json', '四actor完整通过。BNN native同CPD少4wire/8SB；paired同CPD+275wire/−15SB/−1CB；Eltwise paired24SB较旧K4再少1且CPD/wire/CB相同。未触发域释放，不归因fallback；原生对照和退化拒绝均保留。'),
    ('C165', '源根放松排查当前公共前缀潜力', 'full_root_timing_potential_02/completion.json', '七项新语义查询、三项严格匹配复用。十个当前最坏连接在无保留前缀/无占用下距离仍等于现状；真实前向边独立验证。旧反向/虚拟边审计解释已纠正、0重复查询；仅静态开关放松参考，非全局STA最优证明。'),
    ('C166', '同worker真实候选FULL/STA大图集成通过', 'candidate_full_sta_native_binding_01.json', '实际候选与独立同binary LOAD的全部导出精确一致，原树/占用/输出hook/源向量恢复及物理scope检查通过。源与候选receipt明确；两次Python guard错误保留，复用已封存worker及通过审计、0重复repair，新做2个验证LOAD。fused COMPLETE28.757含observer，QUERY7.859，恢复段372.048不作冷速度比。'),
    ('C167', '资源先行后时序的固定绝对资源包络', 'resource_first_timing_dev_01/queue/registration.json', '先行阶段来自pristine强A0自动K8，不手工注入timing前缀。后续当前STA选择，严格CPD接受，SB79/CB5061不增，wire2061627锚原始根而非滚动0.1%。独立开发中，尚无完成/确认/冷计时主张。'),
]
with (p / 'claims_evidence.md').open('a') as out:
    for key, title, link, claim in claims:
        out.write(f'\n| {key} | {title} | [可核查证据](../{link}) | {claim} |\n')
with (p / 'mechanisms_and_ablation.md').open('a') as out:
    out.write('\nC164–C167：统一K8从原生pristine根出现“不降CPD但更省资源”的实际点；native-only本身有收益，paired多省SB/CB但可多wire。Eltwise未触发fallback，不能混淆分组/域与失败释放贡献。fast最坏连接解除全部prefix后proxy距离仍等于现状，不再单靠加查询预算。新fused真实STA/独立LOAD通过；CPD变更/强制路径事务仍需后续覆盖。COMPLETE含candidate observer，恢复段复用历史worker不伪造完整冷时间。资源先行→时序以原始wire绝对预算及更紧79/5061垂直预算验证组合，不要求各模块单独改善CPD。\n')
f = p / 'DEVELOPMENT_STATUS.md'
f.write_text('# C164–C167：统一原生根资源取舍、源根潜力与实际候选STA集成\n\n最新档案47=282合法观察，失败另列。current_repair_main.tex是问题—机制—整体结果—Pareto—消融—开销主线短稿；main.tex保留完整开发证据，旧conclusion84wire已纠正为当前强A0 native8序列40wire。原快照均保留。\n统一K8四actor完整通过，BNN/eltwise都有CPD持平的资源取舍；源根诊断十个当前最坏连接在更宽放松下距离仍等于现状。真实candidate同worker FULL/新STA/恢复及独立LOAD大图通过；两个Python检查错误保留且0重复repair恢复，输入态/验证段/核心分开，冷完整时间仍未知。资源先行后timing当前STA实验正在执行，固定79SB/5061CB与原始wire上限2061627，不重新抬高包络。导出I/O优化只有测量依据和后续假设，尚未实现。Goal active，新增本地未推送。\n\n' + f.read_text())
files = [tex, p / 'current_repair_main.tex', p / 'data/joint_quality_projection_binding_02.json',
         D / 'multiobjective_archive_47/completion.json', D / 'multiobjective_tradeoff_summary_21.json',
         D / 'common_resource_budget_slices_07.json', D / 'uniform_feedback_resource_dev_01/queue/completion.json',
         D / 'full_root_timing_potential_02/completion.json', D / 'candidate_full_sta_native_binding_01.json',
         D / 'candidate_full_sta_cost_semantics_01.json', D / 'resource_first_timing_dev_01/queue/registration.json',
         D / 'resource_only_export_optimization_hypothesis_01.json']
ledger = read(p / 'data/evidence_v14_ledger.json')
for f in files:
    ledger['sources_sha256'][str(f.relative_to(D))] = sha(f)
write(p / 'data/evidence_v14_ledger.json', ledger)
write(p / 'data/uniform_fused_delta_binding_01.json', dict(passed=True, claims=[r[0] for r in claims], archive_records=282,
      sources_sha256={str(f.relative_to(D)): sha(f) for f in files}, native_calls=0,
      qualification='New completed quality/actual-native evidence and source-root diagnostic. Focused manuscript keeps actual contribution and limitations separate from historical appendices. Pending phase-order and export-level studies explicitly excluded from completed results; no repeat of old experiments to write this update.'))
print(dict(claims=[r[0] for r in claims], sources=len(ledger['sources_sha256'])), flush=True)
