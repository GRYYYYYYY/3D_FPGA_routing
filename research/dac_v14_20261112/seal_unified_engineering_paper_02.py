"""Seal the six-page main with one qualified complete engineering result."""
import re,shutil,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
p=D/'paper';parent_path=D/'unified_structure_paper_binding_01.json';parent=read(parent_path)
assert sha(p/'current_repair_main.tex')==sha(Path(parent['snapshot'])/'current_repair_main.tex')
source=p/'current_repair_unified_engineering_02.tex';pdf=p/'build_unified_engineering_02/current_repair_unified_engineering_02.pdf';log=p/'build_unified_engineering_02.log'
text=source.read_text();sections=re.findall(r'\\section\{([^}]+)\}',text);assert sections==parent['sections']
assert text.split('\\begin{document}')[0]==(p/'current_repair_main.tex').read_text().split('\\begin{document}')[0]
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
r=PdfReader(pdf);assert len(r.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in r.pages))
for word in ['7247','216/686','PSSisunavailable','22.95%','47.56%','0.797%','534','803','658','33successful']:assert word in flat,word
table=D/'unified_main_table_evidence_02';proof=read(table/'completion.json');assert proof['passed'] and proof['rows']==22
assert all(sha(f)==h for f,h in proof['source_sha256'].items()) and sha(table/'rows.json')==proof['artifact_sha256']['rows.json']
rows=read(table/'rows.json')
for row in rows:
    line=next(x for x in text.splitlines() if x.startswith(row['label']+'&'))
    assert row.get('time_tex',f"{row['complete_seconds']:.2f}") in line
    if row['endpoint_comparison'] is None:assert '(initial fail)' in line;continue
    q=row['quality'];v=row['endpoint_comparison']
    for value in [f"{q['CPD_ns']:.6f}",'/'.join(str(q[k]) for k in ['wirelength','SB_pairs','CB_sources']),'/'.join(str(v[k]) for k in ['setup_improved','setup_regressed','hold_violation_regressions'])]:assert value in line
checks=parent['main_claim_groups'].copy();checks['engineering_closed_stream_qualified_whole_invocation']=['orphaned_BNN_quality_analysis_02/completion.json','orphaned_BNN_engineering_comparison_01/completion.json','unified_main_table_evidence_02/completion.json']
checks['confirmation_integration_still_pending'] += ['current_owner_transaction_validation_01/completion.json','unified_resource_noop_preflight_01/completion.json','unified_input_integration_01/preflight.json']
receipts=parent['verified_case_receipts'].copy()
for name in checks['engineering_closed_stream_qualified_whole_invocation']+checks['confirmation_integration_still_pending']:
    f=D/name;assert read(f)['passed'];receipts[str(f)]=sha(f)
assert all(sha(f)==h for f,h in receipts.items())
snap=D/'paper_snapshots/current_unified_engineering_20261115';snap.mkdir(exist_ok=False)
files={};previous=Path(parent['snapshot'])
for src,name in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log'),(p/'IEEEtran.cls','IEEEtran.cls'),
    (p/'data/joint_quality_projection_34.pdf','data/joint_quality_projection_34.pdf'),(p/'data/joint_quality_projection_binding_34.json','data/joint_quality_projection_binding_34.json'),
    (p/'visual_unified_engineering_02/contact.png','visual/contact.png'),(p/'visual_unified_engineering_02/page4.png','visual/table_page.png'),
    (table/'rows.json','data/complete_table_rows.json'),(D/'orphaned_BNN_engineering_comparison_01/completion.json','supplement/closed_stream_engineering.json'),
    (D/'query_reduction_timing_qualification_01/completion.json','supplement/queue_timing_qualification.json'),
    (previous/'supplement/historical_claims_evidence.md','supplement/historical_claims_evidence.md'),
    (previous/'supplement/historical_main_C223_corrected.tex','supplement/historical_main_C223_corrected.tex'),
    (previous/'supplement/audit_notes.tex','supplement/audit_notes.tex')]:
    dest=snap/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);files[name]=sha(dest)
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_engineering_update',files=files))
claims=read(previous/'claims_evidence.json');claims['main_claim_groups']=checks
claims['new_engineering_cost_scope']='Original full-command GNU-time seconds with observer loss and brief overlap; no complete PSS or statistical speedup.'
write(snap/'claims_evidence.json',claims)
shutil.copy2(source,p/'current_repair_main.tex')
ledger=read(p/'data/evidence_v14_ledger.json');ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source);write(p/'data/evidence_v14_ledger.json',ledger)
binding=dict(passed=True,pages=6,sections=sections,records=658,complete_configurations=33,archive_scope='Frozen archive658 unchanged; newly verified stream full-quality configuration not yet incorporated.',
    figure_archive_records=640,table_rows=22,table_failed_initial_rows=2,table_observer_missing_rows=1,snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),
    main_claim_groups=checks,verified_case_receipts=receipts,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),source,pdf,log,parent_path,table/'completion.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']},
    visual_review='Six-page contact and full-resolution table page inspected; unchanged fonts/margins, no clipping/overfull or unresolved references; missing PSS and GNU-time star visible.',
    new_independent_inputs=0,new_complete_engineering_quality_results=1,complete_research=False,
    qualification='One verified same-input engineering control integrated in the unified main table and cost discussion. Original observer loss and timing precision retained, not promoted to statistical acceleration or new matched-arm overhead. Main remains six pages; historical recovery detail is in supplement.')
write(D/'unified_engineering_paper_binding_02.json',binding)
print(dict(passed=True,pages=6,rows=22,missing_PSS_rows=1,pdf=binding['pdf']))
