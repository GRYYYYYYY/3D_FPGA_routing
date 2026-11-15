"""Bind the current six-page main to separately enumerated quality and cost coverage."""
import re,shutil,sys,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';parent_path=D/'unified_engineering_paper_binding_02.json';parent=read(parent_path)
previous=Path(parent['snapshot']);assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
source=p/'current_repair_unified_archive_03.tex';build=p/'build_unified_archive_03'
pdf=build/'current_repair_unified_archive_03.pdf';log=p/'build_unified_archive_03.log'
archive=D/'multiobjective_closed_stream_quality_01';verified=read(archive/'verification.json')
assert verified['passed'] and verified['records']==671 and verified['complete_quality_configurations']==34
assert verified['complete_observer_measured_configurations']==33 and verified['qualified_GNU_only_configurations']==1
assert all(sha(archive/n)==h for n,h in read(archive/'completion.json')['artifact_sha256'].items())
text=source.read_text();assert re.findall(r'\\section\{([^}]+)\}',text)==parent['sections']
assert text.split('\\begin{document}')[0]==(p/'current_repair_main.tex').read_text().split('\\begin{document}')[0]
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
reader=PdfReader(pdf);assert len(reader.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
for word in ['671-record','34quality-complete','33havecompleteobservermeasurements','qualifiedGNU-timeonly','7247','22.95%','47.56%','0.797%']:
    assert word in flat,word
rows=read(previous/'data/complete_table_rows.json');assert len(rows)==22
oldtext=(previous/'current_repair_main.tex').read_text()
for row in rows:
    line=next(x for x in text.splitlines() if x.startswith(row['label']+'&'))
    assert line==next(x for x in oldtext.splitlines() if x.startswith(row['label']+'&'))
sys.path.insert(0,str(p/'tools/pdf_review'));import pymupdf
newpdf=pymupdf.open(pdf);oldpdf=pymupdf.open(parent['pdf'])
assert all(newpdf[i].get_pixmap().samples==oldpdf[i].get_pixmap().samples for i in range(5))
snap=D/'paper_snapshots/current_unified_archive_20261115';assert not snap.exists()
shutil.copytree(previous,snap)
for src,name in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log'),
    (build/'page6.png','visual/archive_page6.png'),(archive/'complete_configuration_inventory.json','supplement/current_complete_configuration_inventory.json'),
    (archive/'added_observations.json','supplement/closed_stream_actual_states.json'),
    (archive/'verification.json','supplement/current_archive_verification.json')]:
    dest=snap/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
# Old contact/table visuals remain valid for pages 1--5 only; page6 has its own review.
checks=parent['main_claim_groups'].copy();checks['archive_counts']=['multiobjective_closed_stream_quality_01/verification.json']
receipts=parent['verified_case_receipts'].copy()
receipts[str(archive/'verification.json')]=sha(archive/'verification.json')
assert all(sha(f)==h for f,h in receipts.items())
claims=read(previous/'claims_evidence.json');claims['main_claim_groups']=checks
claims['archive_count_scope']=dict(records=671,quality_complete_configurations=34,observer_complete_configurations=33,qualified_GNU_only_configurations=1,independent_new_inputs=0)
write(snap/'claims_evidence.json',claims)
files={str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name!='snapshot_binding.json'}
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_archive_scope_update',files=files,
    visual_review='Pages1--5 raster-exact to previous verified PDF; updated page6 inspected at2x, no clipping or overflow. Inherited contact is historical; visual/archive_page6.png is current.'))
shutil.copy2(source,p/'current_repair_main.tex')
ledger=read(p/'data/evidence_v14_ledger.json');ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source);write(p/'data/evidence_v14_ledger.json',ledger)
binding=dict(passed=True,pages=6,sections=parent['sections'],records=671,complete_configurations=34,
    complete_quality_configurations=34,complete_observer_measured_configurations=33,qualified_GNU_only_configurations=1,
    archive_scope='34 actual complete-quality configurations;33 have original observer-complete measurements;1 has qualified original GNU-time only.',
    figure_archive_records=640,table_rows=22,table_failed_initial_rows=2,table_observer_missing_rows=1,
    snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),main_claim_groups=checks,verified_case_receipts=receipts,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),source,pdf,log,parent_path,archive/'completion.json',archive/'verification.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']},
    visual_review='Firstfivepagesrasterexact;updatedsixthpagevisuallyreviewed.Nochangedfonts,margins,tablevaluesorfigurepopulation.',
    new_independent_inputs=0,new_native_calls=0,complete_research=False,
    qualification='Completed stream actual states incorporated into canonical archive; main count paragraph now distinguishes complete quality from measurement coverage. No missing observer receipt reconstructed, no new matched-arm timing/independent-input/algorithm benefit claim. Historical figure remains explicitly frozen.')
write(D/'unified_archive_paper_binding_03.json',binding)
print(dict(passed=True,pages=6,archive_records=671,complete_quality=34,observer_complete=33,table_rows=22,pdf=binding['pdf']))
