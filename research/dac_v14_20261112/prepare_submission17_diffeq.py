"""Add the admitted diffeq P1 pair to a protected separate submission draft."""
from pathlib import Path
from datetime import datetime,timezone
import fcntl,hashlib,json,shutil
from measure_process_tree_v1 import measure
D=Path(__file__).resolve().parent;O=D/'submission_narrative_16';P=D/'submission_narrative_17';B=D/'DIFFEQ_P1FIX_complete_admission_01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
d=read(B/'admission_decision.json');assert d['complete_pair_admission']=='passed' and not d['gaps'] and d['identical_final_working_point_including_full_vector'];assert read(O/'verification.json')['passed'] and not P.exists();assert all(sha(p)==h for p,h in d['source_sha256'].items());assert all(r['own_root_endpoints']['setup_improved']==r['own_root_endpoints']['setup_regressed']==r['own_root_endpoints']['hold_violation_regressions']==0 for r in d['rows'])
selection=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/cp1r6_diffeq_p1fix_pair_01/diffeq_p1fix/native/flow/resource_flow/repair/round_000/selection/completion.json');owner=selection.parent.parent/'owner_selection/completion.json';s0=read(selection);o0=read(owner);assert s0['passed'] and s0['multi_crossing_nets']==s0['candidate_scopes']==0 and o0['passed'] and o0['eligible_joint_groups']==0
P.mkdir()
for n in ['data','supplement']:shutil.copytree(O/n,P/n,copy_function=shutil.copyfile)
for p in O.glob('*PAIR_TABLE.md'):shutil.copyfile(p,P/p.name)
shutil.copyfile(B/'PAIR_TABLE.md',P/'DIFFEQ_P1_PAIR_TABLE.md');S=P/'supplement/DIFFEQ_P1_complete_pair';S.mkdir()
for p in B.rglob('*'):
 if p.is_file() and p.suffix in ['.json','.md','.log'] and p.stat().st_size<1000000:
  q=S/p.relative_to(B);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
T=P/'supplement/DIFFEQ_P1_input_history';T.mkdir()
history=[D/'VTR_diffeq_p1_input_01/queue/completion.json',D/'VTR_diffeq_p1_input_02/queue/completion.json',D/'VTR_diffeq_p1_input_03/completion.json',D/'diffeq_p1_native_import_probe_02/completion.json',D/'confirmation_release_cp1r6_p1flags_01/completion.json',D/'cp1r6_diffeq_p1_pair_01/PRECHECK_FAILURE.json']
for i,p in enumerate(history):shutil.copyfile(p,T/f'{i:02d}_{p.parent.name}_{p.name}')
sources=[Path(__file__).resolve(),O/'main.tex',O/'build/main.pdf',O/'verification.json',B/'admission_decision.json',B/'pair/completion.json',D/'VTR_diffeq_p1_input_03/completion.json',D/'confirmation_release_cp1r6_p1flags_01/completion.json',selection,owner,*history]
write(P/'edit_registration.json',dict(parent='submission_narrative_16',registered_at=datetime.now(timezone.utc).isoformat(),source_sha256={str(p):sha(p) for p in sources},scope='Only admitted diffeq P1 pair and related abstract, table, applicability, conclusion; preserve prior50 rows and method/prior-art/controls. Independent circuit and actual P1 placement, same architecture family. Parser-only version; no universal gain or external application claim.'))
s=(O/'main.tex').read_text();addition=[]
for r in d['rows']:
 q=r['quality'];v=q['resources'];e=r['own_root_endpoints'];arm='N' if r['arm']=='native' else 'D';addition.append(f"Diffeq P1 {arm}&{q['CPD_ns']:.6f}&{v['wirelength']}/{v['SB_pairs']}/{v['CB_sources']}&{r['complete_command_seconds']:.2f}&{r['sampled_PSS_GiB']:.3f}&{e['setup_improved']}/{e['setup_regressed']}/{e['hold_violation_regressions']}"+r'\\')
anchor='\\hline\\end{tabular}\n\\end{table*}';assert s.count(anchor)==1;s=s.replace(anchor,'\n'.join(addition)+'\n'+anchor)
a='S38417 has eligible groups but no domain increment.';b='S38417 has eligible groups but no domain increment; diffeq P1 has no eligible group and both routes remain unchanged.';assert s.count(a)==1;s=s.replace(a,b)
a='elliptic, frisc, clma, s38584 and s38417 include timing repair;';b='elliptic, frisc, clma, s38584, s38417 and diffeq P1 include timing repair;';assert s.count(a)==1;s=s.replace(a,b)
a='Its whole commands cost 535.29/535.07 s (single pair). Original failures remain supplementary.';b='Its commands cost 535.29/535.07 s. Diffeq P1 has 327 CB but no eligible group; both flows retain the full root vector at 56.74/56.97 s. Single-pair costs are descriptive. Original failures remain supplementary.';assert s.count(a)==1;s=s.replace(a,b)
a='Elliptic/frisc/clma/s38417 delimit occupancy, redundancy, timing coverage and available native opportunities.';b='Elliptic/frisc/clma/s38417/diffeq delimit occupancy, redundancy, timing coverage and native opportunities.';assert s.count(a)==1;s=s.replace(a,b)
a='TPU-OS, elliptic, frisc, clma variants, s38584 and s38417 add no domain benefit.';b='TPU-OS, elliptic, frisc, clma variants, s38584, s38417 and diffeq add no domain benefit.';assert s.count(a)==1;s=s.replace(a,b)
(P/'main.tex').write_text(s);(P/'EXPERIMENT_IMPACT.md').write_text((O/'EXPERIMENT_IMPACT.md').read_text().replace('投稿16','投稿17')+'\nDiffeq P1完整配对通过：新公开电路、真实分区布局，同架构族；原树327 CB但无合格组，两臂原树与全端点向量均保持，domain无增量。独立解析兼容包只识别实际P1无参开关，其余确认规则不变；两次输入准备失败和预检拒绝保留。此结果更新主表、摘要、适用性和结论，不推断其他输入。\n');(P/'build').mkdir();cmd=read(O/'build_measurement_02/registration.json')['command'];cmd=[x.replace(str(O),str(P)) for x in cmd]
lock=(D/'critical_scope_runner.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);m=measure(cmd,P/'build_measurement');print(dict(passed=m['passed'],draft=str(P),new_distinct_circuits=1))
