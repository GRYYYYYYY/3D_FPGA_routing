#!/usr/bin/env python3
"""Add sealed automatic transfer and isolated order sensitivity without attributing it to I/O."""
import shutil
import time
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
proof = read(D / 'fused_eltwise_order_mechanism_01.json')
assert proof['passed'] and all(sha(path)==digest for path,digest in proof['source_sha256'].items())
history = p/'data/ledger_history_20261113'/('serialization_mechanism_'+str(time.time_ns()))
history.mkdir()
for name in ['current_repair_main.tex','claims_evidence.md','mechanisms_and_ablation.md','DEVELOPMENT_STATUS.md','data/evidence_v14_ledger.json']:
    target=history/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p/name,target)
f=p/'current_repair_main.tex'
s=f.read_text()
needle=r'\subsection{Capacity feedback changes the domain decision}'
assert s.count(needle)==1
addition=r'''\subsection{Automatic transfer exposes retained-tree order sensitivity}
A new compact/fused automatic actor from the same pristine eltwise A0 root reaches6.018101129 ns,217050 wire,26 SB and968 CB under unrestricted native repair. Its own-current paired-domain branch instead reaches217191 wire,24 SB and965 CB at the same CPD:141 additional wire units buy two fewer SB and three fewer CB. Both trajectories exhaust their registered current rank-window menu, with one and two accepts respectively. Unlike the old pilot, the new actor has no two-accept local cap. Their complete imported-state workflows are117.15 and118.13 s in this cohort; these are neither cold routing times nor repeated formal timing results. Both use five native children, but fewer child processes do not imply fewer STA evaluations because fused transactions also reobserve restored source. The broader BNN native/paired continuation remains in progress, so historical fixed-prefix points are not declared converged method results.

The23-wire improvement over the older217214-wire guided endpoint has a different cause from reduced graph output. First-step trees and complete endpoint vectors agree, and both second-step request/domain files are identical. Only network6719 changes in the second guided candidate. A same-binary intervention runs the old canonical source, the native-serialized source, and a native source with only6719 restored to canonical branch order. The resulting complete candidate trees and full native endpoint vectors match the old, new and old reference respectively; all pass native FULL/freshSTA and exact source recovery. Retained seed contents agree while their traversal order differs. This establishes search-choice sensitivity to serialization order; it does not prove equal weighted path costs or a particular heap-tie mechanism. Ordered route bytes therefore remain part of search/cache identity. Topology and current timing equivalence alone do not establish equivalent future searches. Confirmation must freeze a traversal policy and give native/domain controls the same policy, rather than crediting this difference to guide scoring or I/O optimization.

'''
s=s.replace(needle,addition+needle)
f.write_text(s)
version=p/'data/manuscript_versions/current_repair_C172.tex'
assert not version.exists()
shutil.copy2(f,version)
claim='C172'
with (p/'claims_evidence.md').open('a') as out:
    out.write('\n| C172 | 融合自动资源流程迁移与保留树序列化敏感性 | [机制与三臂证据](../fused_eltwise_order_mechanism_01.json) | eltwise原生217050/26SB/968CB与paired217191/24SB/965CB均6.018101ns，额外141wire换2SB/3CB。两actor分别1/2接受并耗尽当前menu，117.15/118.13s仅导入状态工作流。相对旧217214少23wire，三臂old/native/仅6719改序准确回到old/new/old，保留seed内容相同顺序不同；不归因于新引导、图文本或已证明等代价heap tie。确认须固定并共享遍历策略，缓存保留精确有序route身份。最初standalone adapter漏建输出目录失败、修复02后3臂通过，原失败成本保留。BNN新延续尚待actor终封。 |\n')
with (p/'mechanisms_and_ablation.md').open('a') as out:
    out.write('\nC172：只有第二步ON的net6719出现差异，OFF及首步ON/OFF实际树和向量相同；当前物理拓扑/完整STA相同不代表未来原生查询语义相同。KEEP seed值的多重集相同、顺序改变，old/new/局部swap三臂准确复现两端点，所以23wire归因于保留树遍历/搜索选择敏感性，尚未证明具体同代价tie。后续可比较全局固定canonical/native/确定性seed策略，在相同selector/scope/机会的native与domain分支均使用同一策略，不能逐电路挑序。原source/candidate精确路由SHA继续作为查询cache身份；order-insensitive tree helper只用于物理等价审查，不能作为搜索重用许可。\n')
status=p/'DEVELOPMENT_STATUS.md'
status.write_text('# C172：自动迁移与保留树顺序的因果局部对照\n\n新Eltwise native/paired两actor已终封，6.018101ns下217050/26/968与217191/24/965，均来自自动原生起点。新paired比旧217214少23wire，经三臂仅6719改序局部干预复现old/new/old，属于serialization/seed遍历影响，不是图文本优化带来的数学质量提升。source树/完整向量等价不允许忽略有序路由缓存身份。档案52现295观测；新BNN无两步前缀上限的own-current原生/配对轨迹继续，未终封私有prefix不作正式点。后续归档单owner队列已登记，强A0/R1/U/Tf始终留在联合人口。所有计时分层、Goal active、新增本地未推送。\n\n'+status.read_text())
files=[version,D/'fused_eltwise_order_mechanism_01.json',D/'serialization_order_diagnostic_02/completion.json',
    D/'serialization_order_diagnostic_01/failure.json',D/'run_serialized_order_native_analysis_v2.py',
    D/'multiobjective_archive_52/completion.json',D/'multiobjective_tradeoff_summary_24.json',
    D/'fused_resource_development_01/eltwise_A0_native_only_K8/completion.json',
    D/'fused_resource_development_01/eltwise_A0_feedback_K8/completion.json',
    D/'export_policy_native_binding_01.json',D/'fused_resource_archive_queue_01/registration.json']
ledger=read(p/'data/evidence_v14_ledger.json')
for path in files:ledger['sources_sha256'][str(path.relative_to(D))]=sha(path)
ledger['sources_sha256']['paper/current_repair_main.tex']=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
write(p/'data/serialization_mechanism_delta_binding_01.json',dict(passed=True,claims=[claim],
    source_sha256={str(path):sha(path) for path in files},manuscript_version=str(version),native_calls=0,
    qualification='Only new sealed actor/causal-diagnostic reconciliation. Existing main/native stages unmodified; no completed experiments rerun for writing. BNN continuation and full cold confirmation remain independent outstanding work.'))
print(dict(claims=[claim],ledger_sources=len(ledger['sources_sha256'])),flush=True)
