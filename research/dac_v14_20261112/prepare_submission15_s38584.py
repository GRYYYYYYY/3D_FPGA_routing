"""Create a separate draft only after actual complete s38584 pair admission."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,sys,fcntl
from measure_process_tree_v1 import measure
D=Path(__file__).resolve().parent;O=D/'submission_narrative_14';P=D/'submission_narrative_15';B=D/'S38584_complete_admission_01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
d=read(B/'admission_decision.json');assert d['complete_pair_admission']=='passed' and not d['gaps'];assert d['identical_final_working_point_including_full_vector'],'Different paired result requires separate explicit interpretation'
assert read(O/'verification.json')['passed'] and not P.exists();P.mkdir()
for n in ['data','supplement']:shutil.copytree(O/n,P/n,copy_function=shutil.copyfile)
for p in O.glob('*PAIR_TABLE.md'):shutil.copyfile(p,P/p.name)
shutil.copyfile(B/'PAIR_TABLE.md',P/'S38584_PAIR_TABLE.md');S=P/'supplement/S38584_complete_pair';S.mkdir()
for p in B.rglob('*'):
 if p.is_file() and p.suffix in ['.json','.md','.log'] and p.stat().st_size<1000000:
  q=S/p.relative_to(B);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
sources=[Path(__file__).resolve(),O/'main.tex',O/'build/main.pdf',O/'verification.json',B/'admission_decision.json',B/'pair/completion.json',D/'VTR_s38584_input_01/completion.json']
write(P/'edit_registration.json',dict(parent='submission_narrative_14',registered_at=datetime.now(timezone.utc).isoformat(),source_sha256={str(p):sha(p) for p in sources},scope='Only admitted distinct s38584 pair, applicability and conclusion; preserve all prior46 result rows and method/prior-art/controls. No universal gain or external application claim.'))
s=(O/'main.tex').read_text();addition=[]
for r in d['rows']:
 q=r['quality'];v=q['resources'];e=r['own_root_endpoints'];arm='N' if r['arm']=='native' else 'D';addition.append(f"S38584 CP1r6 {arm}&{q['CPD_ns']:.6f}&{v['wirelength']}/{v['SB_pairs']}/{v['CB_sources']}&{r['complete_command_seconds']:.2f}&{r['sampled_PSS_GiB']:.3f}&{e['setup_improved']}/{e['setup_regressed']}/{e['hold_violation_regressions']}"+r'\\')
anchor='\\hline\\end{tabular}\n\\end{table*}';assert s.count(anchor)==1;s=s.replace(anchor,'\n'.join(addition)+'\n'+anchor)
a='TPU-OS adds no domain saving; elliptic, frisc and both clma constraint instances show common timing gains without eligible release groups.';b='TPU-OS adds no domain saving; elliptic, frisc, clma and s38584 show common timing gains without eligible release groups.';assert a in s;s=s.replace(a,b)
s=s.replace('TPU-OS, elliptic, frisc and clma variants add no domain benefit.','TPU-OS, elliptic, frisc, clma variants and s38584 add no domain benefit.')
anchor=r'\section{Mechanism Attribution and Budget Sensitivity}';assert s.count(anchor)==1
n,z=d['rows'];paragraph=f"S38584 is a distinct public register-rich circuit with a fresh placement and explicit benchmark clock/I/O. No initial redundant crossing group qualifies; both complete at {n['quality']['CPD_ns']:.9f} ns with {n['quality']['resources']['wirelength']} wire/{n['quality']['resources']['SB_pairs']} SB/{n['quality']['resources']['CB_sources']} CB and identical endpoint vectors. Their whole commands cost {n['complete_command_seconds']:.2f}/{z['complete_command_seconds']:.2f} s. This is one matched input, not a new architecture or interleaved speedup."
s=s.replace(anchor,paragraph+'\n\n'+anchor);s=s.replace('TPU-OS, CLSTM-SB, elliptic, frisc and clma variants','TPU-OS, CLSTM-SB, elliptic, frisc, clma variants and s38584')
(P/'main.tex').write_text(s);(P/'EXPERIMENT_IMPACT.md').write_text((O/'EXPERIMENT_IMPACT.md').read_text().replace('投稿14','投稿15').replace('未来显式SDC输入应先修复新版本契约的报告字段，不重跑本次已完成算法来补报告','CP1r6已独立修正报告字段并通过测试；原Frisc失败保持，不重跑已完成算法')+'\nS38584是新公开电路及真实布局，同既有架构族；匹配终态向量相同，无domain增量。基准SDC不代表外部应用要求。新两行已通过全部准入，原46行与投稿14保持。\n');(P/'build').mkdir()
cmd=read(O/'build_measurement_03/registration.json')['command'];cmd=[x.replace(str(O),str(P)) for x in cmd]
lock=(D/'critical_scope_runner.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);m=measure(cmd,P/'build_measurement');print(dict(passed=m['passed'],draft=str(P),new_distinct_circuits=1))
