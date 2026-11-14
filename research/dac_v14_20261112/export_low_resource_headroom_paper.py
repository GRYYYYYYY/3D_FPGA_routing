#!/usr/bin/env python3
"""Reconcile current-cone headroom and bounded vector semantics as diagnostic evidence."""
import shutil
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';diag=read(D/'low_resource_timing_headroom_04/completion.json')
assert diag['passed'] and diag['reused_queries']==7 and diag['new_queries']==3
positive=[r for r in diag['rows'] if r['potential_ns']>0];assert len(positive)==5
assert read(D/'explicit_envelope_timing_policy_validation_01.json')['passed']
history=p/'data/ledger_history_20261113'/('low_resource_headroom_'+str(time.time_ns()));history.mkdir()
for name in ['current_repair_main.tex','claims_evidence.md','mechanisms_and_ablation.md','DEVELOPMENT_STATUS.md','data/evidence_v14_ledger.json']:
    target=history/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p/name,target)
f=p/'current_repair_main.tex';s=f.read_text()
old='Anchors do not roll forward, so a tolerance cannot accumulate timing degradation.'
assert s.count(old)==1
s=s.replace(old,'The new bounded vector variant additionally enforces the strict timing control\'s immutable wire/SB/CB limits. Anchors do not roll forward, and no tolerance can accumulate timing degradation.')
s=s.replace('Forced-target-path timing transactions remain outside that validated scope.','Large CPD-changing forced-path transactions remain outside that validated scope.')
start=s.index('From the fast A0 state, unrestricted K8 resource repair reaches86 SB')
end=s.index('\n\nThe resulting four quality coordinates',start)
s=s[:start]+r'''From fast A0, historical unrestricted K8 reaches86 SB at2059603 wire; guided K8 spends279 more wire for seven fewer SB and one fewer CB at the same CPD. Corresponding pristine-root two-accept resource prefixes preserve the slower13.607436 ns CPD and use forty fewer wire units. They are fixed historical opportunities, not converged native bounds. A separately sealed resource-first timing phase starts from79SB/5061CB, keeps these vertical caps and the original root wire envelope, and automatically reaches13.421610,13.413972 and13.228146 ns. The last repair expands a current critical-owner dependency to nine networks and twelve connections: one noncritical connection spends about1.114955 ns of route margin while a critical connection saves about0.185826 ns. Strict CPD accepts it; the endpoint-vector control rejects a setup regression. Across this phase eleven setup components improve and seventeen regress, with no increased hold violation; the fixed source near-critical band has one improvement and no regression. The final current-state portfolio has no further admissible proposal.'''+s[end:]
needle=r'\subsection{Automatic transfer exposes retained-tree order sensitivity}'
assert s.count(needle)==1
addition=r'''A separate current-cone diagnostic uses a legal45-SB/5060-CB resource prefix at13.607436 ns. Five of ten winning-cone routed connections retain optimistic source-only switch-distance gaps: two0.185825799 ns and three0.007639001 ns. Seven exact references are reused and only three absent queries run. These paths relax capacity, sharing and retained branches; their sum is not a feasible CPD gain. Same-root strict and resource-bounded vector branches are active composition diagnostics, not final method scores.

'''
s=s.replace(needle,addition+needle)
old='Strong BNN A0/R1 roots additionally allow eight native convergence attempts with a1.01 reconvergence threshold.'
assert s.count(old)==1
s=s.replace(old,old+' BNN has no supplied SDC: native default constraints use one ideal ap\_clk domain, zero input/output delay and zero setup/hold constraints; exact constraint echoes are bound.')
f.write_text(s);version=p/'data/manuscript_versions/current_repair_C178.tex';assert not version.exists();shutil.copy2(f,version)
claims=[('C177','低资源状态的当前关键路径改善潜力','low_resource_timing_headroom_04/completion.json',
    '45SB/5060CB注册私有合法prefix：当前精确max-arrival cone1端点/10连接，5项源-only潜力，2×0.185825799ns和3×0.007639001ns；严格复用7项，仅新增3项8.83s。全精度FULL/STA向量等值；先前未开echo、旧cache选错和cache缺失均保留，138.44/138.08s两次分析分段，不拼完整算法时间。乐观路径放松容量/共享/保留树，不相加作可实现CPD下降。'),
    ('C178','固定资源下严格与端点向量策略的独立实现','explicit_envelope_timing_policy_validation_01.json',
    '7个已有真实状态策略对照及9类负例通过，无新路由；存在严格拒绝而次级接受的合法native82SB终点，尚非自动首步或后续CPD收益证据。独立v4继承v3物理problem identity修复，双策略同45SB/5060CB/2061627wire绝对预算，继承完整SDC/domain/endpoint身份，逐步重新选目标，无epsilon/滚动容差。当前真实dual_timing_02队列运行，未完成。')]
with (p/'claims_evidence.md').open('a') as out:
    for key,title,link,claim in claims:out.write(f'\n| {key} | {title} | [证据](../{link}) | {claim} |\n')
with (p/'mechanisms_and_ablation.md').open('a') as out:
    out.write('\nC177–C178：45SB合法注册prefix的current winning cone仍有5条正源-only静态距离gap；与快13.228ns终点10项全零gap不同，支持同资源下原生current-STA修复，而非只扩大同一查询预算。7严格命中+3缺失查询，反向证据去虚拟anchor后核真实正向边；不可当可行路由或CPD总收益。双策略从同一全精度STA/端点/SDC和2061627wire/45SB/5060CB启动；strict参考原规则，次级增加完整setup向量Pareto且CPD非退化。分叉后各自选当前目标，严格同源同请求时才复用native结果，研究工作流/分支导入开销均不代替完整单配置时间。\n')
status=p/'DEVELOPMENT_STATUS.md';status.write_text('# C177–C178：低资源后的时序潜力与双接受策略\n\n45SB/5060CB注册诊断prefix不是资源actor最终分数；该actor原版本继续并观察到后续44SB。current-cone10连接中5项正乐观gap，7复用+3新查询；完整native观察两段及审查错误保留，未反复跑已成功native/query。双策略原生composition诊断已启动，同绝对资源上限，当前还无接受结果，不预告CPD提升。Goal active，新内容本地未推送。\n\n'+status.read_text())
files=[version,D/'low_resource_timing_headroom_01/failure.json',D/'low_resource_timing_headroom_01/full_observation/completion.json',
    D/'low_resource_timing_headroom_02/failure.json',D/'low_resource_timing_headroom_02/full_observation/completion.json',
    D/'low_resource_timing_headroom_03/failure.json',D/'low_resource_timing_headroom_04/completion.json',
    D/'low_resource_timing_headroom_04/reuse_receipts.json',D/'low_resource_timing_headroom_04/new_queries.log',
    D/'explicit_envelope_timing_policy.py',D/'explicit_envelope_timing_policy_validation_01.json',
    D/'explicit_endpoint_portfolio_preparation_01.json',D/'run_independent_critical_portfolio_v4.py',
    D/'low_resource_dual_timing_01/queue/completion.json',D/'low_resource_dual_timing_02/queue/registration.json']
ledger=read(p/'data/evidence_v14_ledger.json')
for path in files:ledger['sources_sha256'][str(path.relative_to(D))]=sha(path)
ledger['sources_sha256']['paper/current_repair_main.tex']=sha(f);write(p/'data/evidence_v14_ledger.json',ledger)
write(p/'data/low_resource_headroom_delta_binding_01.json',dict(passed=True,claims=[c[0] for c in claims],
    source_sha256={str(path):sha(path) for path in files},manuscript_version=str(version),
    new_native_calls_in_export=0,qualification='Diagnostic/current implementation delta. No final resource/dual-strategy result, new global CPD point or complete algorithm time inferred.'))
print(dict(claims=[c[0] for c in claims],ledger_sources=len(ledger['sources_sha256'])),flush=True)
