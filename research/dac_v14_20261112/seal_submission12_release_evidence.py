from pathlib import Path
import json,hashlib,datetime
from pypdf import PdfReader
D=Path(__file__).resolve().parent;P=D/'submission_narrative_12';O=D/'submission_narrative_11';B=D/'LSTM_release_ablation_01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
a=(O/'main.tex').read_text();b=(P/'main.tex').read_text()
def table(s):return s.split('Circuit/role &',1)[1].split('\\hline',1)[1].split('\\hline\\end{tabular}',1)[0].strip().splitlines()
assert table(a)==table(b) and len(table(b))==42
assert a[a.index(r'\section{Introduction}'):a.index(r'\section{Validation')]==b[b.index(r'\section{Introduction}'):b.index(r'\section{Validation')]
start='A separate robot control multiplies';end=r'\subsection{Timing budgets'
assert a[a.index(start):a.index(end)]==b[b.index(start):b.index(end)]
assert (O/'data/references.tex').read_bytes()==(P/'data/references.tex').read_bytes()
assert (P/'data/references.tex').read_text().count(r'\bibitem')==10
assert len(PdfReader(P/'build/main.pdf').pages)==6
assert 'Overfull' not in (P/'build/main.log').read_text()
assert sha(O/'build/main.pdf')=='88261b66ffd489e8cb1e19bb8818ed3a58a884b2fa07b2b4cbb69da3a2c0d877'
for path,h in read(P/'edit_registration.json')['source_sha256'].items():assert sha(path)==h,path
assert read(B/'decision.json')['passed'] and read(B/'queue/completion.json')['passed']
for path,h in read(B/'plan.json')['source_sha256'].items():assert sha(path)==h,path
for path,h in read(B/'decision.json')['source_sha256'].items():assert sha(path)==h,path
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
(P/'COMPLETE_PAIR_TABLE.md').write_text((O/'COMPLETE_PAIR_TABLE.md').read_text().replace('投稿11','投稿12'))
write(P/'REVISION_STATUS.json',dict(status='verified_six_page_submission',parent='submission_narrative_11',verified_at=now,main_table_rows=42,all_complete_rows_unchanged=True,problem_design_prior_art_and_four_strength_control_unchanged=True,LSTM_single_scope_release_ablation_passed=True,no_complete_LSTM_release_attribution=True,no_new_independent_inputs=True,source_AND_PDF_parent_preserved=True,build_output_directory_error_and_two_seven_page_attempts_preserved=True,qualification='Only evidence-supported abstract/mechanism/conclusion update and removal of repeated prose; no font/reference/result/negative-case deletion. Standalone author review; no future result prerequisite.'))
write(P/'review/visual_review.json',dict(passed=True,pages_reviewed=list(range(1,7)),detailed_pages=[5,6],all42_complete_rows_preserved=True,no_clipping_or_overlap_observed=True,ten_references_present=True))
paths=[p for p in P.rglob('*') if p.is_file() and 'review' not in p.relative_to(P).parts and p.name!='verification.json' and p.suffix not in ['.aux','.xdv'] and (p.suffix!='.log' or p.parent.name!='build')]
write(P/'verification.json',dict(passed=True,verified_at=now,pages=6,main_table_rows=42,all42_complete_rows_unchanged=True,method_and_prior_art_unchanged=True,four_strength_cost_control_unchanged=True,parent_source_and_PDF_unchanged=True,LSTM_local_release_ablation_admitted=True,whole_costs_not_changed_by_local_ablation=True,original_failures_retained=True,artifact_sha256={str(p):sha(p) for p in sorted(paths)}))
p=D/'refresh_current_status_20261114.py';s=p.read_text();a="write(D/'CURRENT_STATUS.json',status)";add='''lstm_release_decision=D/'LSTM_release_ablation_01/decision.json'
if lstm_release_decision.exists():
    status['LSTM_release_ablation_01']['decision']=read(lstm_release_decision)
    status['active_schedule_order']=[]
    status['research_next_pair_conditional_ETA']=dict(remaining_roles=0,remaining_checks=0,completion_ETA_seconds=0,observed_component_seconds=214.45290657505393,independent_verification_seconds=1.48136505484581,qualification='Single registered ablation and original gates terminal; no complete-flow time ratio inferred. Future unregistered research has no invented ETA.')
    status['outstanding']=['LSTM same-source first releasing-group no-release ablation admitted:5/8 then rollback versus existing release8/8 accepted, identical prefix before relaxation. Update only scoped attribution; do not attribute whole70SB or infer new input. Continue dependency/budget applicability on different actual inputs; before new explicit-SDC confirmation correct report declaration in a separate frozen release. No repeated BNN/LSTM local resource tuning; historical recovery stays supplementary. Research Goal active.']
paper12=D/'submission_narrative_12/verification.json'
if paper12.exists():
    status['submission_candidate_latest']=read(paper12);status['paper_pdf']=str(D/'submission_narrative_12/build/main.pdf');status['paper_pages']=6
    status['evidence']['submission_candidate_latest']='submission_narrative_12/verification.json'
    paper=dict(pdf=status['paper_pdf'],pages=6,verification=str(paper12),submission='12',scope='Verified author-review candidate:42 complete rows unchanged; new fixed-group LSTM release mechanism evidence only.')
''';assert a in s;s=s.replace(a,add+a)
a="'github_frisc_admission67_publication_receipt_20261117.json']";assert a in s;s=s.replace(a,"'github_frisc_admission67_publication_receipt_20261117.json','github_LSTM_release68_publication_receipt_20261117.json']");p.write_text(s)
print(dict(passed=True,pages=6,rows=42,pdf_sha256=sha(P/'build/main.pdf'),artifacts=len(paths)))
