"""Update only completed clma evidence in a separate author-review manuscript."""
from pathlib import Path
import json,hashlib,shutil,fcntl,sys,datetime
from measure_process_tree_v1 import measure
D=Path(__file__).resolve().parent;O=D/'submission_narrative_12';P=D/'submission_narrative_13';B=D/'CLMA_complete_admission_01';A=D/'CLMA_initial_scope_boundary_01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
 decision=read(B/'admission_decision.json');assert decision['complete_pair_admission']=='passed' and not decision['gaps'];assert read(A/'completion.json')['passed']
 assert read(O/'verification.json')['passed'];assert not P.exists()
 rows=decision['rows'];same=decision['identical_final_working_point_including_full_vector'];assert same,'Draft this different paired outcome explicitly before manuscript update'
 P.mkdir()
 for name in ['data','supplement']:shutil.copytree(O/name,P/name,copy_function=shutil.copyfile)
 for p in O.glob('*PAIR_TABLE.md'):shutil.copyfile(p,P/p.name)
 (P/'CLMA_PAIR_TABLE.md').write_bytes((B/'PAIR_TABLE.md').read_bytes())
 S=P/'supplement/CLMA_complete_pair';S.mkdir()
 for root,prefix in [(B,'admission'),(A,'initial_scope_boundary')]:
  for p in root.rglob('*'):
   if not p.is_file() or p.suffix not in ['.json','.md','.log'] or p.stat().st_size>1000000:continue
   rel=p.relative_to(root);q=S/prefix/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 source=[Path(__file__).resolve(),O/'main.tex',O/'build/main.pdf',O/'verification.json',B/'admission_decision.json',B/'pair/completion.json',A/'completion.json',A/'rows.json']
 write(P/'edit_registration.json',dict(parent='submission_narrative_12',registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256={str(p):sha(p) for p in source},changes='Only admitted clma table/coverage/abstract/applicability/conclusion; original42rows and problem/design/prior-art/mechanism controls retained. No new algorithm or success extrapolation.'))
 s=(O/'main.tex').read_text()
 old='TPU-OS adds no domain saving; elliptic and frisc have identical native/domain timing gains without eligible release groups.'
 new='TPU-OS adds no domain saving; elliptic, frisc and clma show common native/domain timing gains without eligible release groups.'
 assert old in s;s=s.replace(old,new)
 s=s.replace('elliptic and frisc include subsequent timing repair','elliptic, frisc and clma include subsequent timing repair')
 s=s.replace('TPU-OS, CLSTM-SB, elliptic and frisc are single pairs','TPU-OS, CLSTM-SB, elliptic, frisc and clma are single pairs')
 additions=[]
 for r in rows:
  q=r['quality'];e=r['own_root_endpoints'];v=q['resources'];arm='N' if r['arm']=='native' else 'D'
  additions.append(f"Clma CP1r6 {arm}&{q['CPD_ns']:.6f}&{v['wirelength']}/{v['SB_pairs']}/{v['CB_sources']}&{r['complete_command_seconds']:.2f}&{r['sampled_PSS_GiB']:.3f}&{e['setup_improved']}/{e['setup_regressed']}/{e['hold_violation_regressions']}"+r'\\')
 anchor='\\hline\\end{tabular}\n\\end{table*}'
 assert s.count(anchor)==1;s=s.replace(anchor,'\n'.join(additions)+'\n'+anchor)
 s=s.replace('TPU-OS, CLSTM-SB, elliptic and frisc pairs','TPU-OS, CLSTM-SB, elliptic, frisc and clma pairs')
 diagnosis=read(A/'completion.json')['scope_rejection_counts']
 n,d=rows
 for r in rows:
  case=Path(read(D/'cp1r6_clma_pair_01/clma_results.json')[r['arm']]['case']);assert read(case/'completion.json')['timing_accepted_steps']==5
 # State only direct observed exclusions, leaving detailed scope rows in supplement.
 why='The original screen excludes its redundant-net branches; scope-level reasons remain in the supplement.'
 if set(diagnosis)=={'no_retained_crossing_alternative'}:why='Removing either complete redundant branch leaves no retained crossing, so the sharing-domain rule admits no group.'
 elif set(diagnosis)=={'STA_or_pin_screen'}:why='The redundant-net branches fail the original current-STA pin screen.'
 paragraph=f"Elliptic, frisc and clma are distinct public sequential circuits with actual fresh Hybrid-O placements. Elliptic has no vertical occupancy; frisc has 256 CB sources but no redundant crossing nets. Clma has three redundant nets but no eligible sharing or blocked-owner group. {why} Their final native/domain vectors match. Clma's five timing accepts lower CPD by 2.2524\\% for 100 wire, with two setup improvements and no regressions; whole commands cost {n['complete_command_seconds']:.2f}/{d['complete_command_seconds']:.2f} s. Frisc/clma use clock-only20-ns SDCs, observing 886/33 clocked endpoint components; no external I/O requirement is claimed. Visited-state rejections and original report failures remain supplementary."
 start=s.index('Elliptic and frisc are distinct public sequential circuits')
 end=s.index(r'\section{Mechanism Attribution and Budget Sensitivity}',start)
 s=s[:start]+paragraph+'\n\n'+s[end:]
 s=s.replace('Elliptic lacks crossings; frisc lacks eligible redundancy despite crossings. Their native timing gains are not domain benefit.', 'Elliptic lacks crossings; frisc lacks redundancy; clma has redundant nets but no eligible sharing group. Their native timing gains add no domain benefit.')
 s=s.replace('TPU-OS, elliptic and frisc add no domain benefit.','TPU-OS, elliptic, frisc and clma add no domain benefit.')
 (P/'main.tex').write_text(s)
 impact=(O/'EXPERIMENT_IMPACT.md').read_text().replace('投稿12','投稿13').replace('保留投稿11；','保留投稿12；')
 impact+='\nClma完整N/D配对通过且最终向量一致，新增两行及适用性边界；不是新架构。3个冗余网仍无合格共享域组：'+json.dumps(diagnosis,ensure_ascii=False)+'。两臂共同原生时序收益不归于域。源回显和33个时钟端点分量限制保持，不主张外部应用I/O达标。当前确认及必要核验已终结，稿件独立作者审阅；没有未来结果前置条件。\n'
 (P/'EXPERIMENT_IMPACT.md').write_text(impact);(P/'build').mkdir()
 cmd=read(O/'build_measurement_04/registration.json')['command'];cmd=[x.replace(str(O),str(P)) for x in cmd]
 lock=(D/'critical_scope_runner.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);m=measure(cmd,P/'build_measurement');print(dict(passed=m['passed'],draft=str(P),diagnosis=diagnosis))
if __name__=='__main__':main()
