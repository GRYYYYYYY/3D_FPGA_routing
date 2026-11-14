#!/usr/bin/env python3
"""Add completed automatic release and exact workload costs without rerouting."""
import shutil
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
history = p / 'data/ledger_history_20261113' / ('automatic_release_' + str(time.time_ns()))
history.mkdir()
for name in ['main.tex', 'claims_evidence.md', 'mechanisms_and_ablation.md', 'DEVELOPMENT_STATUS.md', 'data/evidence_v14_ledger.json']:
    target = history / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p / name, target)
mechanism = read(D / 'automatic_domain_release_mechanism_01.json')
band = read(D / 'automatic_domain_release_endpoint_band_01.json')
assert mechanism['passed'] and band['passed']
tex = p / 'data/automatic_release_v14.tex'
assert not tex.exists()
tex.write_text(r'''\subsection{Automatic per-net release: completed native validation}
The independent automatic release build and validation have now completed. Eight tiny native children confirm unchanged default OFF/ON/failure results, guided-failure recovery with exactly the free native trees, distinct feedback request identity and a following default request unaffected in the same parent. On the actual BNN eight-cut scope, all eight domains are initially active; the native worker itself releases31767/pin1 after the guided search fails. Earlier restored trees and their occupancy are retained. Seven networks stay guided. The actual serialized candidate route and every fixed endpoint setup/hold component exactly match the prior selective-domain reference, with native FULL, physical/resource/domain audits, candidate fresh STA and final input/cache/context seals passed. The result remains13.228145689936355 ns,2069104 wire,72 SB and5071 CB. This is automatic recovery of the known resource point, not an additional independent frontier point.

The whole transaction is accepted under the registered resource-under-timing rule. Strict CPD rejects it, while endpoint-vector acceptance improves nine setup components with zero setup regressions and no increased hold violation. The worst endpoint identity is unchanged. In a fixed diagnostic source band of setup slack within0.05 times source CPD of the worst source slack, all23 components stay exact. Thus this step reduces actual resource occupancy and improves noncritical components without reducing the currently near-critical bottlenecks. Equality of endpoint values alone is not used to claim identical internal winning paths or future CPD benefit. The band is descriptive; it is not an acceptance tolerance and cannot accumulate CPD degradation.

The complete imported-state validation workflow is287.624 s, including source/native worker113.480 s, source materialization21.221 s, actual transaction audit41.032 s, domain audit10.984 s, candidate FULL/STA/materialization65.870 s, final context seal14.856 s and20.182 s of registration/context/miscellaneous work. Native repair core is6.693 s, nested within the worker rather than additive. Source/candidate native children account for43.712/37.073 s within these stages. No cold initial route is included. This run uses an exact sealed physical reference for the matching candidate, so neither its comparison with339.716 s of the earlier diagnostic nor its6.693 s core is advertised as a whole-algorithm speedup.

A subsequent independent cohort uses K8, the same0.1\% root-wire envelope and exact root-CPD cap from pristine strong native A0 starts for both eltwise and BNN. It compares native-only trajectories with paired automatic-feedback trajectories; each branch reselects after its own commits. No release network or accepted repair prefix is injected. These are prospective development probes; their still-running states are not included as completed quality points or timing results in this table. The two-step local probe is not an overall research stopping condition.
''')
main = p / 'main.tex'
s = main.read_text()
needle = r'\input{data/selective_frontier_v14.tex}'
assert s.count(needle) == 1
main.write_text(s.replace(needle, needle + '\n' + r'\input{data/automatic_release_v14.tex}'))
with (p / 'claims_evidence.md').open('a') as out:
    out.write('\n| C163 | 自动按网释放复现真实资源点并完整计费 | [原生机制与代价](../automatic_domain_release_mechanism_01.json)、[端点带宽诊断](../automatic_domain_release_endpoint_band_01.json) | 全8域起步，自动仅释放31767p1，保留前序占用及其余7域；route/full-vector与先前7域点精确一致，FULLSTA/最终封存通过。资源策略接受、strict拒绝、端点策略9改善零退化接受；源定义近关键23分量均不变。287.624s输入态流程、core6.693s嵌套，非冷速度提升或新前沿点。独立原生起点统一K8迁移队列后续运行。 |\n')
with (p / 'mechanisms_and_ablation.md').open('a') as out:
    out.write('\nC163：自动仅释放失败net，不重做前五个成功恢复；同实际route/完整向量复现72SB点，说明手工release list不是取得该点的必要接口。与free74SB形成+64wire/−2SB取舍。九端点改善都不在固定源近关键23分量内，不能据此称后续CPD必改进。完整输入态流程287.624s，主要为源构建/观察、audit和候选FULLSTA；core6.693s为嵌套分量。真实初始routing+repair冷时间未知。\n')
f = p / 'DEVELOPMENT_STATUS.md'
f.write_text('# C163：自动失败释放已完整通过，统一起点K8后续已启动\n\n新C++ kernel/queue与Python pool默认关闭；tiny 8-child兼容/恢复、BNN真实替换/FULLSTA/最终封存通过。自动起步8域仅释放31767p1，复现合法72SB点；strict拒绝、端点9改善零退化接受，固定源近关键23项不变。287.624s为输入态流程，非冷完整算法时间。后续uniform_feedback_resource_dev_01从pristine strong-native eltwise/BNN A0根运行同K8 native-only及paired-feedback，独立自当前态选择。Goal active，全部新增本地。\n\n' + f.read_text())
files = [tex, D / 'automatic_domain_release_mechanism_01.json', D / 'automatic_domain_release_endpoint_band_01.json',
         D / 'automatic_domain_release_dev_01/completion.json', D / 'domain_failure_release_stage_01/native_validation_binding_01.json',
         D / 'domain_failure_release_tiny_01/completion.json', D / 'domain_failure_release_validation_queue_01/completion.json',
         D / 'uniform_feedback_resource_dev_01/queue/registration.json']
ledger = read(p / 'data/evidence_v14_ledger.json')
for f in files:
    ledger['sources_sha256'][str(f.relative_to(D))] = sha(f)
write(p / 'data/evidence_v14_ledger.json', ledger)
write(p / 'data/automatic_release_delta_binding_01.json', dict(passed=True, claims=['C163'],
      archive_records=264, sources_sha256={str(f.relative_to(D)): sha(f) for f in files},
      native_calls=0, qualification='Actual completed automatic native integration and workload costs; subsequent prospective queue explicitly excluded from completed QoR or timing. No repeated native runs to update the draft.'))
print(dict(claims=['C163'], ledger_sources=len(ledger['sources_sha256'])), flush=True)
