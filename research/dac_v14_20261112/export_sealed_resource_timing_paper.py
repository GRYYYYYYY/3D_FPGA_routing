#!/usr/bin/env python3
"""Sealed resource cohort, two actual timing accepts and native consumer evidence."""
import shutil
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';resource=read(D/'fused_resource_development_01/bnn_A0_feedback_K8/completion.json')
first=read(D/'low_resource_timing_accept_01.json');second=read(D/'low_resource_timing_accept_02.json')
consumer=read(D/'native_census_state_evaluator_validation_01/completion.json')
assert all(x['passed'] for x in [resource,first,second,consumer])
assert resource['accepted_steps']==9 and resource['final_resources']['SB_pairs']==43
assert read(D/'native_resource_nonempty_selection_01/completion.json')['passed']
archive=D/'multiobjective_low_resource_timing_02';assert read(archive/'completion.json')['records']==332
plot=p/'data/joint_quality_projection_binding_06.json';assert read(plot)['passed']
history=p/'data/ledger_history_20261113'/('sealed_resource_timing_'+str(time.time_ns()));history.mkdir()
for name in ['current_repair_main.tex','claims_evidence.md','mechanisms_and_ablation.md','DEVELOPMENT_STATUS.md','data/evidence_v14_ledger.json']:
    target=history/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p/name,target)
f=p/'current_repair_main.tex';s=f.read_text()
s=s.replace('data/joint_quality_projection_05.pdf','data/joint_quality_projection_06.pdf')
old='Archive52 snapshot plus all nine sealed extended-native BNN observations, on one physical-input identity, including A0/R1/U/Tf and repairs. The ongoing paired trajectory is excluded until its final context seal. Duplicate quality tuples are collapsed.'
new='Archive332 contains219 BNN observations on one physical-input identity, including strong A0/R1/U/Tf, all sealed resource trajectories and the registered two-accept timing prefix. Duplicate quality tuples are collapsed to123 plotted coordinates.'
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('A0 native K8 &13.607436&2059563&86&5062', 'A0 native K8 (end) &13.607436&2059591&82&5062')
s=s.replace('A0 guided K8 &13.607436&2059842&79&5061', 'A0 guided K8 (end) &13.607436&2061353&43&5060')
needle='R1 selective release &13.228146&2069104&72&5071'
assert s.count(needle)==1
s=s.replace(needle,'Resource/timing (2) &13.413972&2061297&45&5060\\\\\n'+needle)
start=s.index('The new unrestricted native BNN resource actor completes five automatic accepts')
end=s.index(r'\subsection{Automatic transfer exposes retained-tree order sensitivity}',start)
s=s[:start]+r'''The completed native-order resource cohort ends at13.607436067 ns for both own-current branches. The unrestricted control makes five accepts, using2059591 wire,82 SB and5062 CB. The paired domain/failure-release branch makes nine accepts, using2061353 wire,43 SB and5060 CB. Its additional1762 wire units buy39 fewer SB and two fewer CB. Both exhaust their registered current menus; historical two-accept points are prefixes, not native resource bounds. Native and paired workflows cost2061.28 and7293.64 s and create nine and nineteen native children respectively. The paired branch pays its additional searches; these imported-state measurements are not equal-compute or cold whole-configuration timing.

A separately registered composition freezes the earlier seven-accept45-SB/5060-CB resource prefix. Exact current-cone diagnosis finds five optimistic source-only distance gaps, reusing seven references and querying three missing inputs. Actual capacity checks leave only one positive single-connection gap; the larger gains require owner release. The current selector chooses47878/pin2 plus three slack-bearing donors. Native complete replacement and FULL/STA reduce CPD to13.421610490 ns, spend40 wire units and preserve45 SB/5060 CB. Ten setup components improve and seventeen regress, with no increased hold violation. The fixed source near-critical band has one improvement and no regression. The critical endpoint stays unchanged, while its winning cone gains three routed connections. A second freshly selected transaction reaches13.413972155 ns and2061297 wire, with eleven setup improvements and no regressions. These locally input-sealed states extend the collected quality frontier; the whole timing trajectory remains active. The first is rejected by the fixed full-vector policy, whereas the second is admissible from that strict successor. The independently initialized vector branch cannot borrow that successor after divergence.

'''.replace('\n+','\n')+s[end:]
s=s.replace('The broader BNN native/paired continuation remains in progress, so historical fixed-prefix points are not declared converged method results.',
    'BNN resource trajectories are now sealed separately; their native controls also continue beyond historical prefixes.')
s=s.replace('It awaits actual client validation and does not select historical policies separately per circuit.',
    'Actual client validation passes and automatic transfer is running; policies are not selected separately by circuit history.')
start=s.index('The fused candidate implementation passes ten small native jobs')
end=s.index('\n\nCurrent evidence has several practical limits.',start)
s=s[:start]+r'''The fused candidate implementation passes ten native regression jobs and actual BNN resource/timing transactions against separate same-binary candidate LOAD/FULL/STA. Candidate and restored-source receipts remain distinct. Preserved decoder/admission failures and recovery work stay in the detailed evidence; no tolerance or borrowed timing is introduced. Each full graph echo costs753.92 MiB and each frontier357.20 MiB, repeated for source, candidate and restored source. Optional graph-text export passes ten tiny jobs and two BNN paired transactions with exact native search, route, frontier and recovery identity. Timing-cone selection still requires full output. Full versus compact requests are86.73/67.90 s for the timing case and90.21/70.66 s for the resource case, with reversed measurement order. Compact mode omits about2.21 GiB of unused graph text while keeping full frontiers, native FULL and fresh STA. These are single paired component measurements, with startup and validation-only LOADs separately accounted, not repeated cold timing. Earlier timing recovery costs1793.82 s, split into894.94 s of query/dependency/portfolio work,834.50 s of native coordination and49.76 s of preparation; its interrupted predecessor remains separate.

The new45-SB timing composition further exposes integration cost: its first committed round has843.38 s of completed top-level child work, with a0.667 s native repair core nested inside transaction coordination and206.49 s of complete candidate analysis/materialization. These nested figures are not added together or presented as complete single-configuration time.'''.replace('\n+','\n')+s[end:]
old='These counts carry native assurance; independent physical verification remains separate. Fixed seed/census controls enter environment and cache identity. Actual client validation and automatic shadow transfer remain pending. The faster count consumer requires implementation and measurement; no full-algorithm speedup is claimed. Detailed validation failures and recovery costs remain in the evidence record.'
new='These counts carry explicit native assurance. Actual client validation passes, including frozen-control and exact-cache checks. A new consumer defers complete independent physical audit during private acceptance and requires it for the selected final state; other private states cannot borrow that proof. Two actual sealed-worker replays match full vectors and all resource fields, reject seven invalid/premature-publication cases, and preserve candidate menus, including nonempty four-candidate sources. Private materialization takes1.34/1.19 s versus7.06/6.97 s for per-candidate independent audit; the selected final independent audit costs5.57 s. These sequential component measurements do not establish full-algorithm speedup. A separate registered live trajectory comparison retains identical selection, search and acceptance.'
assert s.count(old)==1;s=s.replace(old,new)
f.write_text(s);version=p/'data/manuscript_versions/current_repair_C181.tex';assert not version.exists();shutil.copy2(f,version)
claims=[('C179','45SB下两次真实时序接受与完整向量退化','low_resource_timing_accept_02.json',
    '固定此前7接受45SB/5060CB输入：13.607436→13.421610→13.413972ns，wire2061265→2061305→2061297。第一步目标47878/p2+3donor，setup10改善17退化、hold违例0，固定near12中1改善0退化；端点未迁移，winning cone增加3连接。第二步11改善0退化，两policy均可接受该strict当前状态，但独立次级分支不得跳过第一次拒绝。局部FULL/物理/input seal已通过，完整轨迹未结束。'),
    ('C180','完整own-current资源对照与联合档案','multiobjective_low_resource_timing_02/completion.json',
    'native5接受82SB/5062CB/2059591，paired9接受43SB/5060CB/2061353，同13.607436ns；差1762wire换39SB/2CB。导入流程2061.28/7293.64s，native children9/19，非等compute或冷时间。归并档案329再加3个独立封存观察=332；BNN219观测123质量坐标，强A0/R1/U/Tf共同前沿。45SB组合prefix不是43SB最终资源起点，不串批次或拼时间。'),
    ('C181','原生计数私有接受与所选最终独立审查接口','native_census_state_evaluator_validation_01/completion.json',
    'v8/state_resource_assurance实际2worker replay通过：完整vector/所有计数字段相符，不制造independent_audit，7负例包括提前发布/借别的state最终proof/无finalstate。来源非空4候选两个接口一致。私有物化1.34/1.19s对独立7.06/6.97s、最终独立5.57s，为组件串行观测非全算法加速；完整live等价性owner已登记待direct-scope predecessor终封。')]
with (p/'claims_evidence.md').open('a') as out:
    for key,title,link,claim in claims:out.write(f'\n| {key} | {title} | [证据](../{link}) | {claim} |\n')
with (p/'mechanisms_and_ablation.md').open('a') as out:
    out.write('\nC179–C181：完整资源cohort43SB已终封并进入外部强基线联合档案。冻结此前7步45SB输入的strict组合已两接受，CPD13.413972且SB45/CB5060保持；只代表该注册prefix，不挪用43SB起点。第一步full setup向量17退化但固定near12零退化，提示全setup-Pareto可能阻止有价值的donor余量使用；保留当前两策略不改规则，之后可独立研究固定near集合+受控donor预算，不能把新规则混入当前批。v8快计数consumer实际回放/非空selector通过，final独立proof只证本state；真实live4case等价性尚待结果。\n')
status=p/'DEVELOPMENT_STATUS.md';status.write_text('# C179–C181：43SB资源终封、45SB真实时序组合、快计数接受接口\n\n联合档案332观测，含强基线与全部封存资源/seed及新增局部时序接受。完整原生5步82SB，对应paired9步43SB/5060CB，同CPD；导入开销和额外native搜索均保留。两次strict时序接受从注册45SB prefix到13.413972ns，不是从最终43SB点起步；完整strict/vector流程继续，不能合并接续两条状态。原生计数consumer真实2receipt/7负例及非空4候选验证通过，完整live等价性单owner等待前置批次。完整冷时间、全体策略与跨电路确认未完成，Goal active，无总次数/日期/矩阵/作者终止，新增本地未推送。\n\n'+status.read_text())
files=[version,D/'low_resource_timing_accept_01.json',D/'low_resource_timing_accept_02.json',
    D/'fused_resource_development_01/bnn_A0_feedback_K8/completion.json',D/'multiobjective_merged_seed_resource_01/completion.json',
    archive/'completion.json',archive/'composition_summary.json',plot,
    D/'seed_census_client_validation_01/completion.json',D/'native_census_state_evaluator_validation_01/completion.json',
    D/'resource_assurance_selector_validation_01/completion.json',D/'native_resource_nonempty_selection_01/completion.json',
    D/'pool_state_evaluator_v8.py',D/'state_resource_assurance.py',D/'run_native_census_resource_repair.py',
    D/'native_census_resource_equivalence_01/queue/registration.json']
ledger=read(p/'data/evidence_v14_ledger.json')
for path in files:ledger['sources_sha256'][str(path.relative_to(D))]=sha(path)
ledger['sources_sha256']['paper/current_repair_main.tex']=sha(f);write(p/'data/evidence_v14_ledger.json',ledger)
write(p/'data/sealed_resource_timing_delta_binding_01.json',dict(passed=True,claims=[c[0] for c in claims],
    source_sha256={str(path):sha(path) for path in files},manuscript_version=str(version),new_native_calls_in_export=0,
    qualification='New sealed resource/local timing/consumer evidence only. Full trajectories, live fast-consumer equivalence, cold complete timing and broad frozen confirmation are not inferred.'))
print(dict(claims=[c[0] for c in claims],ledger_sources=len(ledger['sources_sha256'])),flush=True)
