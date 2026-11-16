"""Seal the six-page failure-aware manuscript against actual interrupted receipts."""
import re
import shutil
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';e=D/'runtime_recovery_paper_evidence_13'
parent_path=D/'proc_race_paper_binding_12.json';parent=read(parent_path)
previous=Path(parent['snapshot']);source=p/'current_repair_runtime_recovery_13.tex'
build=p/'build_runtime_recovery_13';pdf=build/'current_repair_runtime_recovery_13.pdf'
log=build/'current_repair_runtime_recovery_13.log'
target=D/'runtime_recovery_paper_binding_13.json';assert not target.exists()
assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
reg=read(e/'edit_registration.json');assert all(sha(f)==h for f,h in reg['source_sha256'].items())
text=source.read_text();old=(previous/'current_repair_main.tex').read_text()
assert text.split('\\begin{document}')[0]==old.split('\\begin{document}')[0]
assert re.findall(r'\\section\{([^}]+)\}',text)==parent['sections']
assert re.findall(r'\\bibitem\{([^}]+)\}',text)==re.findall(r'\\bibitem\{([^}]+)\}',old)
assert re.findall(r'\\includegraphics[^\n]+',text)==re.findall(r'\\includegraphics[^\n]+',old)
old_table=re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',old,re.S)[0]
new_table=re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',text,re.S)[0]
rows=read(e/'failure_groups.json')['rows']
old_rows=read(D/'proc_race_paper_evidence_12/interrupted_rows.json')['rows']
assert new_table.replace('\n'.join(rows),'\n'.join(old_rows))==old_table
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
reader=PdfReader(pdf);assert len(reader.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
for token in ['6147.85','346.66','103.04','185.03','47.56%','0.797%','22.95%','CP1r2','9116.40']:
    assert token in flat,token
review=read(e/'visual_review.json');assert review['passed'] and review['pages_reviewed']==6 and review['pdf_sha256']==sha(pdf)
actual=dict(attempts=[a for g in read(e/'failure_groups.json')['groups'] for a in g['attempts']])
receipts=e/'receipts';receipts.mkdir()
index=[]
for row in actual['attempts']:
    folder=receipts/(row['input']+'_'+row['arm']);folder.mkdir()
    for kind in ['measurement','failure_trace']:
        original=Path(row[kind]);copy=folder/('measurement.json' if kind=='measurement' else 'failure_trace.log')
        shutil.copy2(original,copy);assert sha(copy)==sha(original)
        index.append(dict(original=str(original),copy=str(copy.relative_to(e)),sha256=sha(copy)))
write(e/'receipt_index.json',index)
write(e/'completion.json',dict(passed=True,pages=6,total_table_rows=36,
    complete_attempt_rows=32,interrupted_attempt_rows=5,pre_native_launch_failure_rows=4,infrastructure_grouped_rows=2,scoped_rows=2,
    unchanged_old_table_rows=34,new_complete_method_outputs=0,
    initial_legal_observations_only=True,original_BNN_cost_claims_preserved=True,
    source_sha256=reg['source_sha256']))
snap=D/'paper_snapshots/current_runtime_recovery_20261116';assert not snap.exists()
shutil.copytree(previous,snap)
for src,dest in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log')]:shutil.copy2(src,snap/dest)
shutil.copytree(e,snap/'supplement/runtime_recovery')
for i in range(1,7):shutil.copy2(build/f'page{i}.png',snap/f'visual/complete_inputs_page{i}.png')
claims=read(previous/'claims_evidence.json')
claims['runtime_infrastructure_failures']=dict(attempted_arms=9,complete_quality_results=0,pre_VPR_launch_failures=4,
    initial_legal_arms=5,original_receipts_preserved=True,
    attribution='Infrastructure failure, not scientific no-gain or congestion.',
    confirmation='CP1r2 preserves algorithms/rules; executable guard and vanished-proc handling verified before re-registration. Full confirmation remains pending.',
    evidence=['execution_reconciliation_20261116_01/completion.json','CP1r1_packaging_failure_01/completion.json'])
write(snap/'claims_evidence.json',claims)
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_runtime_recovery_evidence',
    files={str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name!='snapshot_binding.json'},visual_review=review))
shutil.copy2(source,p/'current_repair_main.tex')
ledger=read(p/'data/evidence_v14_ledger.json');ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source);write(p/'data/evidence_v14_ledger.json',ledger)
binding=parent.copy();all_receipts=parent['verified_case_receipts'].copy();all_receipts.update(reg['source_sha256'])
binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),table_rows=36,
    complete_configuration_table_rows=32,interrupted_attempt_rows=5,new_complete_attempt_rows=0,
    new_independent_inputs=0,verified_case_receipts=all_receipts,visual_review=review,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,pdf,log,e/'completion.json',e/'edit_registration.json',e/'visual_review.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']},
    qualification='Nine infrastructure attempts grouped in main table, all individual actual costs retained supplementary with no complete quality. Corrected-input initial legality verified; fixed CP1r2 confirmation pending. Original historical paired benefit/cost claims unchanged.')
binding['main_claim_groups']=dict(parent['main_claim_groups'],runtime_failure_accounting=['execution_reconciliation_20261116_01/completion.json','CP1r1_packaging_failure_01/completion.json'])
write(target,binding)
print(dict(passed=True,pages=6,rows=36,pdf=binding['pdf']))
