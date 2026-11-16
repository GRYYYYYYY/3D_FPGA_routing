"""Seal actual owner/input-contract evidence into a reviewed six-page snapshot."""
import re,shutil,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';e=D/'owner_contract_paper_evidence_09';parent_path=D/'qualified_complete_paper_binding_08.json';parent=read(parent_path);previous=Path(parent['snapshot']);source=p/'current_repair_owner_contract_09.tex';build=p/'build_owner_contract_09';pdf=build/'current_repair_owner_contract_09.pdf';log=build/'current_repair_owner_contract_09.log'
assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
reg=read(e/'edit_registration.json');assert all(sha(f)==h for f,h in reg['source_sha256'].items())
t=source.read_text();old=(previous/'current_repair_main.tex').read_text()
assert t.split('\\begin{document}')[0]==old.split('\\begin{document}')[0]
assert re.findall(r'\\section\{([^}]+)\}',t)==parent['sections']
assert re.findall(r'\\bibitem\{([^}]+)\}',t)==re.findall(r'\\bibitem\{([^}]+)\}',old)
assert re.findall(r'\\begin\{figure\*\}.*?\\end\{figure\*\}',t,re.S)==re.findall(r'\\begin\{figure\*\}.*?\\end\{figure\*\}',old,re.S)
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
legacy=read(previous/'data/complete_table_rows.json');assert len(legacy)==22
for row in legacy:
 assert next(x for x in t.splitlines() if x.startswith(row['label']+'&'))==next(x for x in old.splitlines() if x.startswith(row['label']+'&'))
for label in ['BNN terminal N','Robot SDC N','Robot SDC D','Attention N (initial fail)','Attention D (initial fail)']:
 assert next(x for x in t.splitlines() if x.startswith(label+'&'))==next(x for x in old.splitlines() if x.startswith(label+'&'))
rows=[x for x in t.splitlines() if '&' in x and x.endswith(('\\\\','\\\\\\hline')) and not x.startswith('Circuit/role')];assert len(rows)==33,len(rows)
reader=PdfReader(pdf);assert len(reader.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
for token in ['7351.26','498.00','504.09','794.67','792.69','47.56%','0.797%','22.95%','155.10','107.00','106.48','102.93','102.90','CP1']:
 assert token in flat,token
review=read(e/'visual_review.json');assert review['passed'] and review['pages_reviewed']==6 and review['pdf_sha256']==sha(pdf)
receipts=parent['verified_case_receipts'].copy();receipts.update(reg['source_sha256']);assert all(sha(f)==h for f,h in receipts.items())
assert read(D/'confirmation_release_cp1_01/completion.json')['full_method_source_and_rules_frozen']
assert read(D/'robot_owner_scope_pair_01/verification.json')['passed']
write(e/'completion.json',dict(passed=True,pages=6,complete_attempt_rows=31,initial_routing_failures=4,input_loading_failures=4,scoped_rows=2,source_sha256=reg['source_sha256'],new_native_calls=0,old_development_reclassified=False))
snap=D/'paper_snapshots/current_owner_contract_20261116';assert not snap.exists();shutil.copytree(previous,snap)
for src,dest in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log')]:shutil.copy2(src,snap/dest)
shutil.copytree(e,snap/'supplement/owner_contract')
for i in range(1,7):shutil.copy2(build/f'page{i}.png',snap/f'visual/complete_inputs_page{i}.png')
for n in ['input_failure_rows','scoped_component_rows','moved_composition_row']:write(snap/f'data/{n}.json',read(e/f'{n}.json'))
claims=read(previous/'claims_evidence.json');claims['owner_contract_update']=dict(source_and_rules_frozen=True,independent_confirmation_results=False,positive_integrated_owner_reentry=False,positive_integrated_timing_feedback=False,old_runs_reclassified=False,owner_scope='Robot unrestricted/no-release pair:31 setup improvements,0regressions,12 extra wire/1CB; shared imported155.10s; fixed-resource rejects both. Scope effect, not domain benefit.',input_failures='Four pre-routing input interpretation failures retained, corrected development pairs queued.',source_archive='Public source omits vendored dependencies; full local relocated bundle validated. External binaries and physical inputs remain explicit.')
write(snap/'claims_evidence.json',claims)
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_owner_contract_update',files={str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name!='snapshot_binding.json'},visual_review=review))
shutil.copy2(source,p/'current_repair_main.tex');ledger=read(p/'data/evidence_v14_ledger.json');ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source);write(p/'data/evidence_v14_ledger.json',ledger)
binding=parent.copy();binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),table_rows=33,complete_configuration_table_rows=31,scoped_component_table_rows=2,table_initial_failure_rows=4,table_input_loading_failure_rows=4,new_native_calls_during_paper_update=0,new_complete_attempt_rows=4,verified_case_receipts=receipts,visual_review=review,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,pdf,log,e/'completion.json',e/'edit_registration.json',e/'visual_review.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']},qualification='Fixed prospective CP1 source is not completed independent confirmation. Shared imported owner contrast isolates scope and trades resources for endpoints. Input-loading failures are not routing failures. Historical evidence and cost denominators preserved.')
write(D/'owner_contract_paper_binding_09.json',binding);print(dict(passed=True,pages=6,rows=33,pdf=binding['pdf']))
