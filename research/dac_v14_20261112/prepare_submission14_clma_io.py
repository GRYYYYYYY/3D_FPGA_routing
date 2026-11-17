"""Admitted explicit-I/O result only; preserve independent-input boundaries."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,sys,fcntl
from measure_process_tree_v1 import measure
D=Path(__file__).resolve().parent;O=D/'submission_narrative_13';P=D/'submission_narrative_14';B=D/'CLMA_IO_complete_admission_01';C=D/'cp1r6_clma_io_pair_01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
 decision=read(B/'admission_decision.json');assert decision['complete_pair_admission']=='passed' and not decision['gaps'];assert decision['identical_final_working_point_including_full_vector'],'Inspect differing final outcomes before prose update'
 assert read(O/'verification.json')['passed'];assert not P.exists();P.mkdir()
 for name in ['data','supplement']:shutil.copytree(O/name,P/name,copy_function=shutil.copyfile)
 for p in O.glob('*PAIR_TABLE.md'):shutil.copyfile(p,P/p.name)
 shutil.copyfile(B/'PAIR_TABLE.md',P/'CLMA_IO_PAIR_TABLE.md')
 S=P/'supplement/CLMA_IO_complete_pair';S.mkdir()
 for root,prefix in [(B,'admission'),(D/'VTR_clma_io_input_01','input_instance')]:
  for p in root.rglob('*'):
   if not p.is_file() or p.suffix not in ['.json','.md','.log','.sdc'] or p.stat().st_size>1000000:continue
   q=S/prefix/p.relative_to(root);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 shutil.copyfile(C/'native_initial_coverage_01.json',S/'native_initial_coverage_01.json')
 files=[Path(__file__).resolve(),O/'main.tex',O/'build/main.pdf',O/'verification.json',B/'admission_decision.json',B/'pair/completion.json',D/'VTR_clma_io_input_01/registration.json',C/'native_initial_coverage_01.json']
 write(P/'edit_registration.json',dict(parent='submission_narrative_13',registered_at=datetime.now(timezone.utc).isoformat(),source_sha256={str(p):sha(p) for p in files},changes='Only explicit-I/O matched rows/coverage/abstract/applicability/conclusion; same clma circuit/layout/architecture, changed initial tree distinguished. All44 prior rows, method/prior-art/mechanism controls preserved. No unfinished s38584 result included.'))
 s=(O/'main.tex').read_text();addition=[]
 for r in decision['rows']:
  q=r['quality'];v=q['resources'];e=r['own_root_endpoints'];role='N' if r['arm']=='native' else 'D'
  addition.append(f"Clma IO CP1r6 {role}&{q['CPD_ns']:.6f}&{v['wirelength']}/{v['SB_pairs']}/{v['CB_sources']}&{r['complete_command_seconds']:.2f}&{r['sampled_PSS_GiB']:.3f}&{e['setup_improved']}/{e['setup_regressed']}/{e['hold_violation_regressions']}"+r'\\')
 anchor='\\hline\\end{tabular}\n\\end{table*}';assert s.count(anchor)==1;s=s.replace(anchor,'\n'.join(addition)+'\n'+anchor)
 a='TPU-OS adds no domain saving; elliptic, frisc and clma show common native/domain timing gains without eligible release groups.'
 b='TPU-OS adds no domain saving; elliptic, frisc and both clma constraint instances show common timing gains without eligible release groups.';assert a in s;s=s.replace(a,b)
 a='TPU-OS, CLSTM-SB, elliptic, frisc and clma are single pairs';assert a in s;s=s.replace(a,'TPU-OS, CLSTM-SB, elliptic, frisc and clma variants are single pairs')
 start=s.index('Distinct elliptic/frisc/clma circuits');end=s.index(r'\section{Mechanism Attribution',start)
 n,d=decision['rows'];cpd=n['quality']['CPD_ns'];costs=f"{n['complete_command_seconds']:.2f}/{d['complete_command_seconds']:.2f}"
 paragraph=f'''Elliptic/frisc/clma add distinct circuits and actual placements, with matched final N/D vectors. Elliptic has no crossings; frisc has no redundant nets. Clock-only clma excludes three reusable scopes via unconstrained slack. Adding preregistered 20-ns/I/O max1/min0 constraints on the same layout makes 330 pin slacks finite (101 versus 33 endpoint components), but fresh routing changes and redundancy vanishes. N/D finish at {cpd:.9f}ns/106117wire/1SB/450CB for {costs}s, without domain increment. This constraint variant adds no independent circuit/start; changed trees prevent fixed-route causal inference. Benchmark I/O settings establish no external application requirement. Original failures and rejections remain supplementary.

'''
 assert n['quality']['resources']==dict(wirelength=106117,SB_pairs=1,CB_sources=450),'Inspect changed metrics before narrative'
 s=s[:start]+paragraph+s[end:]
 s=s.replace('Elliptic/frisc/clma delimit occupancy, redundancy and constraint-coverage conditions; common timing gains add no domain benefit.', 'Elliptic/frisc/clma delimit occupancy, redundancy and timing coverage. Clma constraint variants change fresh routes; their differences do not isolate a domain effect.')
 s=s.replace('TPU-OS, elliptic, frisc and clma add no domain benefit.','TPU-OS, elliptic, frisc and clma variants add no domain benefit.')
 # Condense repeated scope/caption wording; retain numeric rows, failures and controls.
 s=s.replace('Matched complete native (N) and domain-first (D) attempts. Wire/SB/CB are occupancy; endpoints are setup better/worse and added hold violations versus each root. BNN times are two-repeat means; PSS is sampled tree GiB. Failures retain costs without quality. LSTM archival interference prevents a clean cost ratio. TPU-OS, CLSTM-SB, elliptic, frisc and clma variants are single pairs; frisc has supplementary SDC-report admission.', 'Complete native (N)/domain-first (D) pairs. Wire/SB/CB are occupancy; endpoints are setup better/worse and added hold violations versus own roots. PSS is sampled tree GiB. BNN times are two-repeat means; later variants are single pairs. Failures retain costs without quality. LSTM interference prevents a clean ratio; frisc has supplementary SDC-report admission.')
 s=s.replace('Imported controls have separate costs. Comparisons are within matched pairs; identical-tree seeds, new placements, circuits and architectures remain distinct.', 'Imported-control costs are separate. Seeds, placements, circuits and architectures are distinguished; comparisons are within matched pairs.')
 (P/'main.tex').write_text(s)
 impact=(O/'EXPERIMENT_IMPACT.md').read_text();impact=impact.replace('投稿13','投稿14').replace('保留投稿12；原42行保持，新增Clma完整配对两行及摘要/适用性/结论，主表现为44行。','保留投稿13；原44行保持，新增Clma显式I/O配对两行及对应约束覆盖说明，主表现为46行。')
 impact+='\nClma显式IO完整N/D已通过且全终态向量相同，无domain增量。330pin从未知变有限，但fresh路由树同时变化、冗余消失，不将跨SDC资源或CPD差当domain效应。新增46行不是新增独立电路；s38584只排队/输入准备，不在本稿写作收益。主稿可独立作者审阅，未来结果只影响各自表项与适用性。\n'
 (P/'EXPERIMENT_IMPACT.md').write_text(impact);(P/'build').mkdir();cmd=read(O/'build_measurement_04/registration.json')['command'];cmd=[x.replace(str(O),str(P)) for x in cmd]
 lock=(D/'critical_scope_runner.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);m=measure(cmd,P/'build_measurement');print(dict(passed=m['passed'],new_complete_rows=2,new_independent_inputs=0))
if __name__=='__main__':main()
