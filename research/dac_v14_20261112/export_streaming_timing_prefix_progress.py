#!/usr/bin/env python3
"""Update the focused draft with exact decoder integration and a sealed accepted prefix."""
import shutil
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
h = p / 'data/ledger_history_20261113' / ('streaming_prefix_' + str(time.time_ns()))
h.mkdir()
for name in ['current_repair_main.tex', 'claims_evidence.md', 'mechanisms_and_ablation.md', 'DEVELOPMENT_STATUS.md', 'data/evidence_v14_ledger.json']:
    target = h / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p / name, target)
assert read(D / 'endpoint_loader_streaming_integration_01/completion.json')['passed']
prefix = read(D / 'resource_first_timing_prefix_01.json')
assert prefix['passed']
f = p / 'current_repair_main.tex'
s = f.read_text()
needle = 'Equal resource shifts do not by themselves prove that the two mechanisms commute; a separately registered resource-first timing phase now tests native CPD repair under the tighter79SB/5061CB cap and the original pristine-root wire envelope.'
addition = ' Its first accepted legal transaction reduces CPD from13.607436 to13.421610 ns at2059882 wire,79 SB and5061 CB, inside the original absolute wire cap2061627. Ten setup components improve and seventeen noncritical components regress; the fixed source near-critical band has one improvement and zero regressions, with no increased hold violation. The worst endpoint stays fixed while the current winning connection set expands from ten to thirteen as tied paths appear. Subsequent targets are reselected from that new STA state. This accepted prefix is not a completed phase-order result or a new joint-frontier improvement over the existing fast point.'
assert s.count(needle) == 1
s = s.replace(needle, needle + addition)
needle = '\\section{Conclusion}'
addition = r'''\subsection{An exact streaming decoder improvement}
The previous endpoint reader retains every per-pin JSON dictionary before extracting the acceptance vector. A new independent reader parses and validates every row but retains only required endpoint/metric data. On two actual357.20 MiB source/candidate traces, old versus new loader times are11.48 versus5.10 s and10.80 versus5.31 s, with reversed measurement order between inputs. Peak process memory falls from1.73 GiB to0.18--0.21 GiB. Complete vector digests, including all52,495 setup components, endpoint/domain identities and full-precision values, are identical. No pin rows are silently skipped; a native COMPLETE pin-count check additionally detects missing rows.

Seven corruption cases are rejected, including malformed pin JSON, missing completion, duplicate or missing endpoints, nonfinite CPD, trailing data and an incomplete pin census. The real already-sealed fused candidate is successfully materialized with identical complete vectors and strict/endpoint decisions, zero new native calls and explicit same-byte physical-audit reuse. These are component memory/latency and integration results under shared server load, not complete routing-plus-repair speedups. Running timing probes retain their registered decoder/version. Complete cold fixed-policy timing remains required.

'''
assert s.count(needle) == 1
s = s.replace(needle, addition + needle)
f.write_text(s)
versions = p / 'data/manuscript_versions'
versions.mkdir(exist_ok=True)
version = versions / 'current_repair_C169.tex'
assert not version.exists()
shutil.copy2(f, version)
claims = [
    ('C168', '全精度端点解码流式化：实测组件收益与真实候选接入', 'endpoint_loader_streaming_integration_01/completion.json', '两个357MiB真实导出完整向量摘要精确一致；old约11s/new约5s，RSS约1.73GiB至0.18–0.21GiB。仍解析所有JSON，7项损坏输入拒绝，真实已封存候选接入/决策一致、0新native。只称组件收益，未切换运行中的实验或宣称全流程加速。'),
    ('C169', '资源先行后时序：首个实际接受前缀', 'resource_first_timing_prefix_01.json', '首步13.607436→13.421610ns，wire2059882、SB79/CB5061保持且原始wire cap2061627不滚动。setup10改善17非关键退化，固定源近关键12项中1改善0退化、hold无加剧；同最坏端点的winning连接10→13出现并列路径。当前STA继续选下一组，非完整轨迹/新前沿/顺序可交换结论。'),
]
with (p / 'claims_evidence.md').open('a') as out:
    for key, title, link, claim in claims:
        out.write(f'\n| {key} | {title} | [可核查证据](../{link}) | {claim} |\n')
with (p / 'mechanisms_and_ablation.md').open('a') as out:
    out.write('\nC168–C169：端点解码仍校验每行JSON、完整向量精确同值，省的是丢弃无关pin字典的驻留，不是省STA/数字精度。真实候选复用物理证据需route/graph/pack/place全相同；组件11s→5s和RSS减少不是全路由速度比。资源先行首步在79/5061紧包络内降低CPD且出现更多同endpoint并列winning连接，必须按新STA选组；17非关键setup退化只在声明的CPD/hold资源策略下接受，不能伪称endpoint-vector策略通过。\n')
f = p / 'DEVELOPMENT_STATUS.md'
f.write_text('# C168–C169：精确流式端点解码与资源先行时序首步\n\n流式解码组件约11→5s、峰值1.73GiB→0.18–0.21GiB，完整精度/身份精确相同；7损坏输入和实际candidate接入通过，0新native。运行中timing不改版本。资源先行首步已接受13.607436→13.421610ns、79SB/5061CB保持，wire2059882≤原始cap2061627，winning连接10→13要求当前STA重选；完整阶段仍在运行。短稿方法/结果/开销已同步，旧64页开发证据与所有失败保留。完整冷routing+repair时间仍未知，Goal active、无总日期/次数/矩阵停止条件，新增本地。\n\n' + f.read_text())
files = [version, D / 'endpoint_loader_streaming_validation_01/completion.json', D / 'endpoint_loader_streaming_integration_01/completion.json',
         D / 'endpoint_timing_policy_streaming_v2.py', D / 'pool_state_evaluator_v6.py', D / 'resource_first_timing_prefix_01.json',
         D / 'resource_first_timing_dev_01/queue/registration.json', D / 'candidate_full_sta_native_binding_01.json']
ledger = read(p / 'data/evidence_v14_ledger.json')
for source in files:
    ledger['sources_sha256'][str(source.relative_to(D))] = sha(source)
# The focused editable file has a versioned immutable copy for this revision.
ledger['sources_sha256'][str((p / 'current_repair_main.tex').relative_to(D))] = sha(p / 'current_repair_main.tex')
write(p / 'data/evidence_v14_ledger.json', ledger)
write(p / 'data/streaming_timing_prefix_delta_binding_01.json', dict(passed=True, claims=[r[0] for r in claims],
      sources_sha256={str(source.relative_to(D)): sha(source) for source in files}, native_calls=0,
      editable_manuscript_version=str(version.relative_to(D)),
      qualification='New complete component/parser evidence and an independently bound accepted prefix; no repeated native work for writing. Old full evidence manuscript remains as its own sealed revision. Current phase-order trajectory and full cold confirmation remain incomplete.'))
print(dict(claims=[r[0] for r in claims], ledger_sources=len(ledger['sources_sha256'])), flush=True)
