"""Seal the reviewed six-page cohort/mechanism manuscript and evidence map."""
import re,shutil,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';e=D/'cohort_mechanism_paper_evidence_15'
parent_path=D/'CP1r2_pair_paper_binding_14.json';parent=read(parent_path);previous=Path(parent['snapshot'])
source=p/'current_repair_cohort_mechanism_15.tex';build=p/'build_cohort_mechanism_15'
pdf=build/'current_repair_cohort_mechanism_15.pdf';log=build/'current_repair_cohort_mechanism_15.log'
target=D/'cohort_mechanism_paper_binding_15.json';assert not target.exists()
assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
reg=read(e/'edit_registration.json');assert all(sha(f)==h for f,h in reg['source_sha256'].items())
t=source.read_text();old=(previous/'current_repair_main.tex').read_text()
assert t.split('\\begin{document}')[0]==old.split('\\begin{document}')[0]
assert re.findall(r'\\section\{([^}]+)\}',t)==parent['sections']
assert re.findall(r'\\bibitem\{([^}]+)\}',t)==re.findall(r'\\bibitem\{([^}]+)\}',old)
assert re.findall(r'\\includegraphics[^\n]+',t)==re.findall(r'\\includegraphics[^\n]+',old)
table=lambda x:re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',x,re.S)[0]
reduced=table(t)
for row in reg['added_rows']:assert row in reduced;reduced=reduced.replace(row+'\n','') if row+'\n' in reduced else reduced.replace(row,'')
assert reduced.replace('\n\\hline','\\hline')==table(old).replace('\\\\\\hline','\\\\\n\\hline').replace('\n\\hline','\\hline')
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
reader=PdfReader(pdf);assert len(reader.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((x.extract_text() or '').split()) for x in reader.pages))
for token in ['1904.67','1906.23','251140/9/654','251160/9/653','194.52','47.56%','0.797%','22.95%']:
    assert token in flat,token
review=read(e/'visual_review.json');assert review['passed'] and review['pages_reviewed']==6 and review['pdf_sha256']==sha(pdf)
write(e/'completion.json',dict(passed=True,pages=6,main_table_rows=43,terminal_attempt_rows=36,
    infrastructure_grouped_rows=2,scoped_rows=5,unchanged_old_rows=38,
    added_initial_timeouts=2,added_scoped_union_arms=3,new_independent_physical_inputs=0,
    newly_closed_cohort_inputs=2,source_sha256=reg['source_sha256']))
snap=D/'paper_snapshots/current_cohort_mechanism_20261116';assert not snap.exists();shutil.copytree(previous,snap)
for src,dest in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log')]:shutil.copy2(src,snap/dest)
shutil.copytree(e,snap/'supplement/cohort_and_robot_mechanism')
for i in range(1,7):shutil.copy2(build/f'page{i}.png',snap/f'visual/complete_inputs_page{i}.png')
claims=read(previous/'claims_evidence.json')
claims['CP1r2_conv_hls_pair']['limits']='Fixed-menu no-op, not global optimality or speedup; TPU cohort now closed with initial execution timeouts. Positive integrated benefits remain pending.'
claims['CP1r2_closed_cohort']=dict(registered_inputs=2,roles=4,matched_legal_inputs=1,legal_roles=2,
    initial_execution_timeouts=2,no_legal_quality_for_timeout=True,
    evidence='cp1r2_cross_circuit_cohort_01/terminal_evidence_01/completion.json')
claims['robot_union_fixed_scope']=dict(source='251161/10/653',native='251140/9/654',domain_release='251160/9/653',
    CPD_ns=13.354624073258492,domain_without_release='exact_rollback',
    resource_policy=dict(native=False,domain_release=True),endpoint_policy=dict(native=True,domain_release=False),
    setup_changes=dict(native=[240,0,0],domain_release=[240,32,0]),shared_imported_seconds=194.52237720787525,
    no_actor_commit=True,complete_controller_benefit=False,evidence='robot_union_mechanism_02/verification_v2.json')
claims['robot_p1_owner_reentry']=dict(verified_automatic_commits=4,wire_delta=68,CB_delta=-4,
    CPD_unchanged=True,existing_reload_vector_exact=True,full_method_complete=False,
    evidence='robot_owner_reentry_audit_02/completion.json')
write(snap/'claims_evidence.json',claims)
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_closed_cohort_and_mechanism',files={str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name!='snapshot_binding.json'},visual_review=review))
shutil.copy2(source,p/'current_repair_main.tex')
ledger=read(p/'data/evidence_v14_ledger.json');ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source);write(p/'data/evidence_v14_ledger.json',ledger)
binding=parent.copy();receipts=parent['verified_case_receipts'].copy();receipts.update(reg['source_sha256'])
binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),table_rows=43,
    complete_configuration_table_rows=36,new_terminal_attempt_rows=2,scoped_table_rows=5,
    new_independent_inputs=0,new_confirmed_physical_inputs=0,newly_closed_cohort_inputs=2,
    verified_case_receipts=receipts,visual_review=review,
    qualification='Closed fixed-version cohort: one legal no-op physical pair, one initial-timeout pair. Same-source robot three-arm union distinguishes domain resource tradeoff and failure-release enablement; four automatic owner commits verified only on partial development path. Historical complete BNN costs retained; no universal/controller superiority.',
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,pdf,log,e/'completion.json',e/'edit_registration.json',e/'visual_review.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']})
binding['main_claim_groups']=dict(parent['main_claim_groups'],closed_fixed_cohort=['cp1r2_cross_circuit_cohort_01/terminal_evidence_01/completion.json'],union_mechanism=['robot_union_mechanism_02/verification_v2.json'],partial_owner_reentry=['robot_owner_reentry_audit_02/completion.json'])
write(target,binding);print(dict(passed=True,pages=6,main_rows=43,pdf=binding['pdf']))
