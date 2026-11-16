"""Seal six reviewed pages with one complete prospectively fixed no-op input."""
import re
import shutil
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';e=D/'CP1r2_pair_paper_evidence_14'
parent_path=D/'runtime_recovery_paper_binding_13.json';parent=read(parent_path)
previous=Path(parent['snapshot']);source=p/'current_repair_CP1r2_pair_14.tex'
build=p/'build_CP1r2_pair_14';pdf=build/'current_repair_CP1r2_pair_14.pdf';log=build/'current_repair_CP1r2_pair_14.log'
target=D/'CP1r2_pair_paper_binding_14.json';assert not target.exists()
assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
reg=read(e/'edit_registration.json');assert all(sha(f)==h for f,h in reg['source_sha256'].items())
t=source.read_text();old=(previous/'current_repair_main.tex').read_text()
assert t.split('\\begin{document}')[0]==old.split('\\begin{document}')[0]
assert re.findall(r'\\section\{([^}]+)\}',t)==parent['sections']
assert re.findall(r'\\bibitem\{([^}]+)\}',t)==re.findall(r'\\bibitem\{([^}]+)\}',old)
assert re.findall(r'\\includegraphics[^\n]+',t)==re.findall(r'\\includegraphics[^\n]+',old)
table=lambda x:re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',x,re.S)[0]
rows=read(e/'paired_rows.json')['rows'];assert table(t).replace('\n'.join(rows)+'\n','')==table(old)
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
reader=PdfReader(pdf);assert len(reader.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((x.extract_text() or '').split()) for x in reader.pages))
for token in ['505.17','500.90','14.351002','84291/0/37','CP1r2','47.56%','0.797%','22.95%']:
    assert token in flat,token
review=read(e/'visual_review.json');assert review['passed'] and review['pages_reviewed']==6 and review['pdf_sha256']==sha(pdf)
write(e/'completion.json',dict(passed=True,pages=6,main_table_rows=38,
    complete_attempt_rows=34,infrastructure_grouped_rows=2,scoped_rows=2,
    unchanged_old_rows=36,new_complete_method_outputs=2,new_confirmed_physical_inputs=1,
    positive_mechanism_confirmation=False,source_sha256=reg['source_sha256']))
snap=D/'paper_snapshots/current_CP1r2_pair_20261116';assert not snap.exists();shutil.copytree(previous,snap)
for src,dest in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log')]:shutil.copy2(src,snap/dest)
shutil.copytree(e,snap/'supplement/CP1r2_conv_hls_pair')
for i in range(1,7):shutil.copy2(build/f'page{i}.png',snap/f'visual/complete_inputs_page{i}.png')
claims=read(previous/'claims_evidence.json');claims['CP1r2_conv_hls_pair']=dict(
    complete_verified_arms=2,independent_confirmed_physical_inputs=1,
    initial_route_and_full_vectors_matched=True,quality_gain=False,
    endpoint_changes=0,native_seconds=505.16725363209844,domain_seconds=500.89671114459634,
    mechanism='18 current critical-connection queries have zero physical improvement with fixed or relaxed capacity; capacity conflicts alone do not motivate timing owner expansion.',
    limits='Fixed-menu no-op, not global optimality or statistical speedup; remaining tpu input and positive integrated benefits pending.',
    evidence='cp1r2_cross_circuit_cohort_01/conv_hls_comparison.json')
write(snap/'claims_evidence.json',claims)
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_first_CP1r2_pair',files={str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name!='snapshot_binding.json'},visual_review=review))
shutil.copy2(source,p/'current_repair_main.tex')
ledger=read(p/'data/evidence_v14_ledger.json');ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source);write(p/'data/evidence_v14_ledger.json',ledger)
binding=parent.copy();receipts=parent['verified_case_receipts'].copy();receipts.update(reg['source_sha256'])
binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),table_rows=38,
    complete_configuration_table_rows=34,new_complete_attempt_rows=2,
    new_confirmed_physical_inputs=1,verified_case_receipts=receipts,visual_review=review,
    qualification='First complete prospectively frozen conv_hls pair confirms fixed-menu no-op on one distinct known physical input. Native/domain roots and final full endpoints match. Original historical BNN quality/cost claims retained; positive integrated benefits and full cohort pending.',
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,pdf,log,e/'completion.json',e/'edit_registration.json',e/'visual_review.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']})
binding['main_claim_groups']=dict(parent['main_claim_groups'],first_complete_prospective_no_op=['cp1r2_cross_circuit_cohort_01/conv_hls_comparison.json'])
write(target,binding);print(dict(passed=True,pages=6,main_rows=38,pdf=binding['pdf']))
