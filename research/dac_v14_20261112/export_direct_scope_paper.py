#!/usr/bin/env python3
"""Add a verified engineering delta, without promoting private route prefixes."""
import shutil
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';proof=read(D/'direct_native_transaction_validation_01/completion.json')
assert proof['passed'] and proof['cases']==6 and proof['native_calls']==0
history=p/'data/ledger_history_20261113'/('direct_scope_'+str(time.time_ns()));history.mkdir()
for name in ['current_repair_main.tex','claims_evidence.md','mechanisms_and_ablation.md','DEVELOPMENT_STATUS.md','data/evidence_v14_ledger.json']:
    target=history/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p/name,target)
f=p/'current_repair_main.tex';s=f.read_text();needle=r'\section{Conclusion}';assert s.count(needle)==1
s=s.replace(needle,r'''\subsection{Direct audit avoids another candidate serialization}
An independent checker now consumes the actual native candidate rather than reconstructing another route and subsequently comparing its trees. It checks source/request receipts, restored timing exports, terminal mappings, retained edges, untouched networks, logged replacement nodes, graph edges and complete capacity. Six predetermined sealed accepted or legal-rejected transactions reproduce the original scope and switch-delay checks; six corruption guards also pass with zero new native calls. Two BNN replays take21.53 and20.79 s, whereas historical reconstruction records take34.73 and35.68 s; these are separate component measurements, not a paired speedup. Full physical/resource and domain audits remain enabled. Forced-path reservations are outside this API. A registered independent automatic-trajectory comparison must pass before integrated equivalence or runtime benefit is claimed.

'''+needle);f.write_text(s)
version=p/'data/manuscript_versions/current_repair_C176.tex';assert not version.exists();shutil.copy2(f,version)
with (p/'claims_evidence.md').open('a') as out:
    out.write('\n| C176 | 直接实际候选scope审查的工程证据 | [六事务和损坏对照](../direct_native_transaction_validation_01/completion.json) | 预定first/last封存事务复用，无新增VPR；scope/query/attempt/物理switch-delay变化一致、完整capacity检查、6损坏拒绝。BNN21.53/20.79s对旧历史34.73/35.68s不作正式匹配速度结论。forced reservation未支持；完整自动轨迹等价性仍待实际队列结果，物理/domain/FULLSTA全保留。 |\n')
with (p/'mechanisms_and_ablation.md').open('a') as out:
    out.write('\nC176：将重建候选+实际树二次比较替换成直接实际候选scope/edge/capacity检查，保持有序native输出原字节、selector/search/acceptance不变；物理拓扑等价仅用于scope，不能替代search/cache身份。六真实封存事务+六损坏对照通过；新完整自动trajectory工程对照从同global-seed A0 native/paired起点出发，逐步目标/接受/有序树/完整向量及最终独立指标均须匹配。仍保留完整独立物理/domain/native-counter shadow审查；不是快速计数accept消费者或正式完整加速。\n')
status=p/'DEVELOPMENT_STATUS.md';status.write_text('# C176：直接实际候选scope审查，完整集成仍待验证\n\n六封存事务+六损坏检查通过，无新VPR。新独立完整工程等价性owner已登记，待原global-seed cohort结束后运行，原实验输入/接受规则不改。BNN7接受45SB/5060CB仅私有prefix，未终封、不进入主图/最终方法分数。Goal active；未推送。\n\n'+status.read_text())
files=[version,D/'direct_native_transaction_audit.py',D/'validate_direct_native_transaction_audit.py',
    D/'direct_native_transaction_validation_01/registration.json',D/'direct_native_transaction_validation_01/completion.json',
    D/'direct_scope_actor_preparation_01.json',D/'run_direct_scope_shadow_resource_repair.py',
    D/'direct_scope_resource_equivalence_02/queue/registration.json']
ledger=read(p/'data/evidence_v14_ledger.json')
for path in files:ledger['sources_sha256'][str(path.relative_to(D))]=sha(path)
ledger['sources_sha256']['paper/current_repair_main.tex']=sha(f);write(p/'data/evidence_v14_ledger.json',ledger)
write(p/'data/direct_scope_delta_binding_01.json',dict(passed=True,claims=['C176'],
    source_sha256={str(path):sha(path) for path in files},manuscript_version=str(version),
    native_calls=0,qualification='Verified direct-scope engineering delta only. Private paired prefixes excluded; full integrated equivalence/cold speedup unproven.'))
print(dict(claim='C176',ledger_sources=len(ledger['sources_sha256'])),flush=True)
