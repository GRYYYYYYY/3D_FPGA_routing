#!/usr/bin/env python3
"""Update the focused manuscript with verified mechanisms and explicit pending transfer."""
import shutil
import time
from retained_prefix_workflow import D,read,write,sha

p=D/'paper'
native=read(D/'BNN_extended_native_menu_01.json')
seed=read(D/'repair_seed_order_mechanism_01.json')
census=read(D/'native_resource_census_eltwise_02/completion.json')
assert all(item['passed'] for item in [native,seed,census])
assert seed['single_source_resource_policy']['accepted']
history=p/'data/ledger_history_20261113'/('stable_seed_census_'+str(time.time_ns()))
history.mkdir()
for name in ['current_repair_main.tex','claims_evidence.md','mechanisms_and_ablation.md','DEVELOPMENT_STATUS.md','data/evidence_v14_ledger.json']:
    target=history/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p/name,target)
f=p/'current_repair_main.tex';s=f.read_text()
needle=r'\subsection{Automatic transfer exposes retained-tree order sensitivity}'
assert s.count(needle)==1
addition=r'''\subsection{Extending the native control changes the comparison}
The new unrestricted native BNN resource actor completes five automatic accepts, ending at13.607436067 ns,2059591 wire,82 SB and5062 CB. Its first two accepted states match the previous native pilot; the next three reduce SB from86 to84,83 and82. Relative to pristine strong A0 this endpoint spends24 wire units and saves twelve SB at unchanged CPD. It is a stronger own-current native control, not a guided contribution. Historical86-SB/two-accept points remain fixed-prefix observations. The paired native-order continuation and its final joint archive are separate active owners; the registered menu is not an exhaustive resource optimum.

'''
s=s.replace(needle,addition+needle)
needle=r'\subsection{Capacity feedback changes the domain decision}'
assert s.count(needle)==1
addition=r'''\subsection{An explicit seed policy removes the observed ambiguity}
A new independent implementation orders eligible repair seeds either by RR ID or by native physical delay followed by RR ID; the default keeps native depth-first order. It preserves seed membership, native primary cost formulas, physical delays and capacity/domain checks. In six actual eltwise source-by-policy transactions, both explicit policies produce identical complete candidate trees, endpoint vectors and real sink-cost traces from the canonical and native-serialized sources. RR-ID order yields217214 wire; physical-delay/RR-ID order yields217183, with24 SB,965 CB and unchanged6.018101129 ns CPD. The latter is eight wire units below the native-serialized result and thirty-one below the old canonical result, and passes the stated resource-under-timing rule. It remains a fixed-source development transaction rather than an automatic pristine-root method score.

Instrumentation reads actual finite sink labels before native path-cost reset. All lookahead factors are zero in these repair queries. Three later cost rows differ between the original source representations, including pressure retries; thus the whole difference is not established to be a set of equal-cost heap ties. Twelve native regression jobs and six tiny preset-plus-subsequent-search jobs validate default compatibility, eligible seed content, real FULL/freshSTA, independent candidate LOAD and restored source. A new independent development batch fixes one physical-delay/RR-ID policy globally for both native/domain controls from pristine A0/R1/Tf roots. It awaits actual client validation and does not select historical policies separately per circuit.

'''
s=s.replace(needle,addition+needle)
needle=r'\section{Conclusion}'
assert s.count(needle)==1
addition=r'''\subsection{Native counting targets measured validation overhead}
The completed extended native BNN imported-state workflow costs2061.28 s. Native worker requests account for572.64 s; candidate materialization/physical audit, transaction reconstruction and tree-equivalence checks account for543.80,330.43 and136.65 s. These exclusive categories explain why reducing graph text alone does not resolve prototype overhead. A new opt-in C++ census counts actual planar wire, globally occupied SB pairs and CB output sources, per-net occupancies and crossing edge kinds from actual route trees. In source/candidate/restored and ordinary-input observations, every count matches an independent physical audit. Counter on/off preserves ordered route bodies, complete native frontiers and seed/cost traces; an additional same-binary candidate LOAD independently passes physical and timing checks.

This is explicitly native assurance, not an independent audit renamed as a census. The first comparison script incorrectly included private placement paths in serialized file headers; recovery reuses both valid native workers and compares exact ordered bodies while binding placement bytes/IDs. Failures and segment costs remain separate. Fixed per-pool seed/census controls enter environment and cache identity. Actual pool/client validation is queued after the existing cohort; a later shadow transfer retains all Python audits. A faster count consumer and final independent validation policy still require implementation and measurement, so no full-algorithm speedup is claimed.

'''
s=s.replace(needle,addition+needle)
f.write_text(s)
version=p/'data/manuscript_versions/current_repair_C175.tex'
assert not version.exists();shutil.copy2(f,version)
claims=[
    ('C173','更充分原生对照及实际开销分布','BNN_extended_native_menu_01.json','5次自动接受到82SB/5062CB、2059591wire、13.607436ns；比根+24wire/−12SB。旧两步86SB不是收敛最强对照。2061.28s仅导入流程，native请求572.64s，候选物理/重建/树检查543.80/330.43/136.65s，均嵌套或互斥标签分明。配对仍独立续跑。'),
    ('C174','显式seed策略、源序列化不变性与真实cost','repair_seed_order_mechanism_01.json','6臂与6独立LOAD/物理审查：RR-ID/延迟后RR-ID均使source表示不变，后者217183wire/24SB/965CB、6.018101ns，比native保序少8wire，比canonical少31。12tiny+6preset真实验证通过。三行后续cost不同，不能称整体已证同代价heap tie；cost读真实rr_node_route_inf而非返回对象未填字段。尚非完整算法/逐电路选点。'),
    ('C175','实际原生资源census与快接口前置验证','native_resource_census_eltwise_02/completion.json','source/candidate/restored/plain-input全部wire/SB/CB/occupancy/crossing种类与独立审查一致；counter toggle保有序body/全STA/seed/cost，独立LOAD再查通过。私有文件头路径比较错误保留，恢复只新2native+复用2，不拼完整时间。显式native assurance不冒充独立audit；新client实测及全Python审查shadow队列已登记，快accept消费者尚未实现。'),
]
with (p/'claims_evidence.md').open('a') as out:
    for key,title,link,claim in claims:out.write(f'\n| {key} | {title} | [可核查证据](../{link}) | {claim} |\n')
with (p/'mechanisms_and_ablation.md').open('a') as out:
    out.write('\nC173–C175：强化native-only后5步82SB，旧2步86SB不能作永久充分对照。全局种子顺序策略显式化后同物理源表示给出相同树/向量/cost；delay/RR在单固定源217183wire，须从pristine A0/R1/Tf自动迁移并共享policy给原生与domain控制，不能逐电路挑历史最优。原生Dijkstra(no lookahead)cost3行随后状态变，排除“所有差异都已证纯等代价tie”的过强说法。验证开销约一半来自Python重建/物理/树检查；native census只作read-only native assurance先同独立审查shadow，快消费者仍未实现。\n')
status=p/'DEVELOPMENT_STATUS.md'
status.write_text('# C173–C175：强化原生对照、显式seed和原生计数前置验证\n\n封存native BNN5接受82SB/5062CB、2059591wire、13.607436ns；paired原版本继续，归档/归并单owner等待。6臂seed策略验证表示不变，单源delay/RR候选217183wire/24/965，资源策略接受但不是完整自动算法。C++计数器与完整独立资源审查相符，2新worker+2封存复用纠正header误比较；不冒充独立审查、不宣称完整速度。新actual client验证与全局固定delay/RR从pristine A0/R1/Tf的8actor shadow迁移已登记，原批次不改，快消费者待实现。主档案52=295观测，另有6新诊断观测的301记录分支，终封归并已登记。Goal active，无总日期/调用/固定矩阵停止，新增本地未推送。\n\n'+status.read_text())
files=[version,D/'BNN_extended_native_menu_01.json',D/'repair_seed_order_mechanism_01.json',
    D/'repair_seed_order_native_binding_01.json',D/'repair_seed_order_tiny_01/completion.json',
    D/'repair_seed_order_eltwise_01/completion.json',D/'fused_preset_tiny_01/completion.json',
    D/'native_resource_census_eltwise_01/failure.json',D/'native_resource_census_eltwise_02/completion.json',
    D/'native_resource_census_stage_01/binding.json',D/'native_resources_from_receipt.py',
    D/'seed_census_client_validation_01/registration.json',D/'stable_seed_transfer_dev_01/queue/registration.json',
    D/'multiobjective_seed_order_diag_01/completion.json',D/'merge_seed_resource_archive_queue_01/registration.json']
ledger=read(p/'data/evidence_v14_ledger.json')
for path in files:ledger['sources_sha256'][str(path.relative_to(D))]=sha(path)
ledger['sources_sha256']['paper/current_repair_main.tex']=sha(f)
write(p/'data/evidence_v14_ledger.json',ledger)
write(p/'data/stable_seed_census_delta_binding_01.json',dict(passed=True,claims=[row[0] for row in claims],
    source_sha256={str(path):sha(path) for path in files},manuscript_version=str(version),native_calls=0,
    qualification='New verified result/implementation/precondition delta only. Branch archives and queued transfer are explicit; whole automatic sorted-policy transfer, fast consumer and full cold confirmation are not silently completed.'))
print(dict(claims=[row[0]for row in claims],ledger_sources=len(ledger['sources_sha256'])),flush=True)
