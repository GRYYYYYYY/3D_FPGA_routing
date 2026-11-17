"""Update only admitted release attribution; preserve the complete result table."""
from pathlib import Path
import json,hashlib,shutil,datetime,fcntl,sys
from measure_process_tree_v1 import measure
D=Path(__file__).resolve().parent;O=D/'submission_narrative_11';P=D/'submission_narrative_12';B=D/'LSTM_release_ablation_01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
x=read(B/'decision.json');assert x['passed'] and x['release_necessary_for_this_registered_search_completion']
assert read(O/'verification.json')['passed'];assert sha(O/'build/main.pdf')=='88261b66ffd489e8cb1e19bb8818ed3a58a884b2fa07b2b4cbb69da3a2c0d877'
P.mkdir(exist_ok=False)
for name in ['data','supplement']:shutil.copytree(O/name,P/name,copy_function=shutil.copyfile)
for p in O.glob('*PAIR_TABLE.md'):shutil.copyfile(p,P/p.name)
write(P/'edit_registration.json',dict(registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent='submission_narrative_11',changes='Only abstract release sentence, mechanism table/paragraph, conclusions and evidence scope; all42 complete rows, problem/design/prior-art, four-strength cost comparison unchanged.',source_sha256={str(p):sha(p) for p in [O/'main.tex',O/'build/main.pdf',O/'verification.json',B/'decision.json',Path(__file__).resolve()]}))
S=P/'supplement/LSTM_release_ablation';S.mkdir()
for rel in ['plan.json','preflight.json','source_preflight.json','adapter.diff','decision.json','verification.json','RESULT.md','queue/completion.json','queue/execution_receipt.json','measurement/completion.json','verification_measurement/completion.json','transaction/completion.json','transaction/process_costs.json','transaction/reuse_on_domain_audit.json','transaction/reuse_on_audit/analysis.json','transaction/reuse_on/runs/state/joint_native.log','transaction/reuse_on/runs/state/vertical_domain.log']:
 q=S/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(B/rel,q)
s=(O/'main.tex').read_text()
a='Endpoint regressions remain explicit.';b='Endpoint regressions remain explicit. One matched LSTM ablation shows release enabling group completion.';assert s.count(a)==1;s=s.replace(a,b)
a='Domain obstruction & Robot fixed 25-connection scope: no-release rolls back; release gives 9 SB/653 CB; unrestricted gives 9 SB/654 CB and violates the 653-CB cap. Release restores feasibility under guidance.'
b='Domain obstruction & Robot and one matched LSTM group roll back without release and complete with release. LSTM retains the identical search prefix before relaxation; this isolates completion of that group, not the complete 70-SB difference.'
assert s.count(a)==1;s=s.replace(a,b)
a='A separate robot control multiplies cross-layer congestion cost'
b='The earliest accepted LSTM group with release provides a second fixed-scope ablation. Disabling only release preserves all eight requests, domains, native options and the search prefix. Nine constrained attempts fail on one connection; no-release completes five of eight queries and rolls back. The reused release result saves eight SB for 206 wire at equal CPD/CB, with three setup improvements and five regressions. The new component costs 214.45 s, plus 1.48 s independent checking. This retrospective control isolates group completion, not the whole 70-SB difference.\n\n'+a
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace('Robot/R1 controls distinguish guidance, release and coordination;', 'Robot/LSTM/R1 controls distinguish guidance, release and coordination;')
(P/'main.tex').write_text(s)
impact=(O/'EXPERIMENT_IMPACT.md').read_text().replace('投稿11','投稿12').replace('保留投稿10；','保留投稿11；').replace('新增Frisc完整补充准入行和对应摘要/适用性/结论。','完整42行主表保持；新增LSTM单组释放消融及对应摘要/机制表/结论。')
impact+='\nLSTM首次接受且有释放的8请求组，关闭释放后5/8完成并回滚；开启释放既有结果8/8完成，少8SB、多206线长，同CPD/CB，setup3改善/5退化。实际命令、域及释放前日志一致，只有失败释放开关不同。该项局部反事实缺口已闭合；全部LSTM收益中释放所占比例与完整no-release控制器费用仍未知，不作为本稿前置条件。新组件214.452907秒与独立核验1.481365秒分别列账，完整主表费用不改。\n'
(P/'EXPERIMENT_IMPACT.md').write_text(impact)
(P/'LSTM_RELEASE_RESULT.md').write_text((B/'RESULT.md').read_text())
cmd=read(O/'build_measurement/registration.json')['command'];cmd=[x.replace(str(O),str(P)) for x in cmd]
lock=(D/'critical_scope_runner.lock').open('r');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
m=measure(cmd,P/'build_measurement');print(dict(build_passed=m['passed'],seconds=m['complete_command_wall_seconds']))
