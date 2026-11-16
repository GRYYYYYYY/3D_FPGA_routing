"""Seal objective-specific mechanism claims with unchanged quantitative main table."""
import re,shutil,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';e=D/'mechanism_trigger_paper_evidence_16';parent_path=D/'cohort_mechanism_paper_binding_15.json';parent=read(parent_path)
previous=Path(parent['snapshot']);source=p/'current_repair_mechanism_triggers_16.tex';b=p/'build_mechanism_triggers_16'
pdf=b/'current_repair_mechanism_triggers_16.pdf';log=b/'current_repair_mechanism_triggers_16.log';target=D/'mechanism_trigger_paper_binding_16.json';assert not target.exists()
assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
reg=read(e/'edit_registration.json');assert all(sha(f)==h for f,h in reg['source_sha256'].items())
t=source.read_text();old=(previous/'current_repair_main.tex').read_text();restored=t
for before,after in reversed(reg['changes']):assert restored.count(after)==1;restored=restored.replace(after,before)
assert restored==old
assert re.findall(r'\\section\{([^}]+)\}',t)==parent['sections']
assert t.split('\\begin{document}')[0]==old.split('\\begin{document}')[0]
assert re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',t,re.S)==re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',old,re.S)
assert re.findall(r'\\bibitem\{([^}]+)\}',t)==re.findall(r'\\bibitem\{([^}]+)\}',old)
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
reader=PdfReader(pdf);assert len(reader.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((x.extract_text() or '').split()) for x in reader.pages))
for word in ['all48initialcandidaterecords','AllnineBNN','zeroreleaseevents','47.56%','0.797%','22.95%']:assert word in flat,word
review=read(e/'visual_review.json');assert review['passed'] and review['pages_reviewed']==6 and review['pdf_sha256']==sha(pdf)
write(e/'completion.json',dict(passed=True,pages=6,main_table_rows=43,quantitative_rows_unchanged=True,new_native_calls=0,new_independent_inputs=0,new_full_method_results=0,main_edits=3,
    qualification='Clarify resource-vs-timing owner triggers, fixed timing-envelope context and actual guided-release coverage; draft triage remains uninstalled/unconfirmed.'))
snap=D/'paper_snapshots/current_mechanism_triggers_20261116';assert not snap.exists();shutil.copytree(previous,snap)
for src,dest in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log')]:shutil.copy2(src,snap/dest)
shutil.copytree(e,snap/'supplement/mechanism_trigger_clarification')
for folder in ['mechanism_selection_evidence_01','release_coverage_01','mechanism_triage_validation_02']:
    shutil.copytree(D/folder,snap/'supplement'/folder,ignore=shutil.ignore_patterns('__pycache__'))
shutil.copy2(D/'recommend_current_mechanisms_v1.py',snap/'supplement/mechanism_triage_validation_02/recommend_current_mechanisms_v1.py')
for i in range(1,7):shutil.copy2(b/f'page{i}.png',snap/f'visual/complete_inputs_page{i}.png')
claims=read(previous/'claims_evidence.json')
claims['objective_specific_mechanism_triggers']=dict(status='development_hypothesis_not_installed_or_confirmed',
    resources='Avoidable crossing excess/capacity certificate and eligible target+owner slack cuts; no positive CPD witness required.',
    timing='Positive physical delay witness with actual same-witness capacity conflict before owner expansion.',
    budget_counterexample='Same initial SB-only tree and identical48candidate records, same resource caps;1.00/1.02CPD limits lead to0/4 extra domain SB savings versus native.',
    complete_configuration_contexts=10,declared_physical_identities=9,new_independent_inputs=0,
    evidence=['mechanism_selection_evidence_01/completion.json','mechanism_triage_validation_02/completion.json'])
claims['resource_release_event_coverage']=dict(all_executed_guided_roles_covered=True,BNN_roles=9,BNN_events=0,robot_roles=3,robot_events=5,
    flag_off_whole_flow_counterfactual=False,evidence='release_coverage_01/completion.json')
write(snap/'claims_evidence.json',claims)
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_objective_specific_mechanism_claims',
    files={str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name!='snapshot_binding.json'},visual_review=review))
shutil.copy2(source,p/'current_repair_main.tex');ledger=read(p/'data/evidence_v14_ledger.json');ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source);write(p/'data/evidence_v14_ledger.json',ledger)
binding=parent.copy();receipts=parent['verified_case_receipts'].copy();receipts.update(reg['source_sha256'])
binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),table_rows=43,
    new_complete_attempt_rows=0,new_terminal_attempt_rows=0,new_independent_inputs=0,new_confirmed_physical_inputs=0,newly_closed_cohort_inputs=0,
    verified_case_receipts=receipts,visual_review=review,
    qualification='Six pages and all43quantitative rows unchanged; correct objective-specific owner trigger wording and attribute release only to observed events. Same-start SB timing-envelope counterexample included. Pure development triage uninstalled; no new experiment, cost ratio or independent confirmation.',
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,pdf,log,e/'completion.json',e/'visual_review.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']})
binding['main_claim_groups']=dict(parent['main_claim_groups'],objective_specific_mechanism_context=['mechanism_selection_evidence_01/completion.json','mechanism_triage_validation_02/completion.json'],actual_release_coverage=['release_coverage_01/completion.json'])
write(target,binding);print(dict(passed=True,pages=6,table_rows_unchanged=43,pdf=binding['pdf']))
