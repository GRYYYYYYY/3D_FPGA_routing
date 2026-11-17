"""Add the admitted s38417 pair to a protected separate submission draft."""
from pathlib import Path
from datetime import datetime,timezone
import fcntl,hashlib,json,shutil
from measure_process_tree_v1 import measure
D=Path(__file__).resolve().parent;O=D/'submission_narrative_15';P=D/'submission_narrative_16';B=D/'S38417_complete_admission_01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
d=read(B/'admission_decision.json');assert d['complete_pair_admission']=='passed' and not d['gaps'] and d['identical_final_working_point_including_full_vector'];assert read(O/'verification.json')['passed'] and not P.exists()
assert all(sha(p)==h for p,h in d['source_sha256'].items())
P.mkdir()
for n in ['data','supplement']:shutil.copytree(O/n,P/n,copy_function=shutil.copyfile)
for p in O.glob('*PAIR_TABLE.md'):shutil.copyfile(p,P/p.name)
shutil.copyfile(B/'PAIR_TABLE.md',P/'S38417_PAIR_TABLE.md');S=P/'supplement/S38417_complete_pair';S.mkdir()
for p in B.rglob('*'):
 if p.is_file() and p.suffix in ['.json','.md','.log'] and p.stat().st_size<1000000:
  q=S/p.relative_to(B);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
sources=[Path(__file__).resolve(),O/'main.tex',O/'build/main.pdf',O/'verification.json',B/'admission_decision.json',B/'pair/completion.json',D/'VTR_s38417_input_01/completion.json',D/'cp1r6_s38417_pair_01/NATIVE_INITIAL_TRANSACTION_OBSERVATION.json']
write(P/'edit_registration.json',dict(parent='submission_narrative_15',registered_at=datetime.now(timezone.utc).isoformat(),source_sha256={str(p):sha(p) for p in sources},scope='Only admitted s38417 pair and related abstract, table, applicability, conclusion; preserve prior48 rows and method/prior-art/controls. Distinct circuit, same architecture family. No universal gain or external application claim.'))
s=(O/'main.tex').read_text();addition=[]
for r in d['rows']:
 q=r['quality'];v=q['resources'];e=r['own_root_endpoints'];arm='N' if r['arm']=='native' else 'D';addition.append(f"S38417 CP1r6 {arm}&{q['CPD_ns']:.6f}&{v['wirelength']}/{v['SB_pairs']}/{v['CB_sources']}&{r['complete_command_seconds']:.2f}&{r['sampled_PSS_GiB']:.3f}&{e['setup_improved']}/{e['setup_regressed']}/{e['hold_violation_regressions']}"+r'\\')
anchor='\\hline\\end{tabular}\n\\end{table*}';assert s.count(anchor)==1;s=s.replace(anchor,'\n'.join(addition)+'\n'+anchor)
a='TPU-OS adds no domain saving; elliptic, frisc, clma and s38584 show common timing gains without eligible release groups.'
b='TPU-OS adds no domain saving; elliptic, frisc, clma and s38584 show common timing gains without eligible release groups. S38417 has eligible groups but no domain increment.'
assert s.count(a)==1;s=s.replace(a,b)
a='BNN, LSTM, TPU-OS, CLSTM-SB, elliptic, frisc, clma and s38584 include timing repair;';b='BNN, LSTM, TPU-OS, CLSTM-SB, elliptic, frisc, clma, s38584 and s38417 include timing repair;';assert s.count(a)==1;s=s.replace(a,b)
anchor=r'\section{Mechanism Attribution and Budget Sensitivity}';assert s.count(anchor)==1
s=s.replace(anchor,'S38417 has two screened sharing groups; native already removes both initial SBs. Both complete flows reach identical quality and endpoint vectors, with no domain increment. Whole commands cost 535.29/535.07 s (single pair).\n\n'+anchor)
a='TPU-OS, elliptic, frisc, clma variants and s38584 add no domain benefit.';b='TPU-OS, elliptic, frisc, clma variants, s38584 and s38417 add no domain benefit.';assert s.count(a)==1;s=s.replace(a,b)
(P/'main.tex').write_text(s)
(P/'EXPERIMENT_IMPACT.md').write_text('# 投稿16：已核验范围与未来证据影响\n\n投稿15保留；新增两行 s38417 完整配对并更新摘要、适用性和结论。相同架构族上的不同公开电路与真实布局，两臂算一个输入；明确 20 ns 和 I/O 为基准 SDC。两个筛选组不保证增量：native 已在初始事务释放两个 SB，最终两臂质量及全端点向量相同。完整命令及只读验证费用分列，单次 N/D 不当统计计时。\n\nBNN、LSTM、机制控制、四档代价和全部负结果保持；LSTM 归档干扰不推算干净时间，CLSTM 历史恢复仍在补充材料。后续独立输入只影响对应主表、适用性、摘要和结论；端点、完整费用及失败须通过既有准入后才能计入。当前稿件可独立作者审阅，研究继续。\n')
(P/'build').mkdir();cmd=read(O/'build_measurement/registration.json')['command'];cmd=[x.replace(str(O),str(P)) for x in cmd]
lock=(D/'critical_scope_runner.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);m=measure(cmd,P/'build_measurement');print(dict(passed=m['passed'],draft=str(P),new_distinct_circuits=1))
