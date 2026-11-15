"""Read-only source/PDF/table/receipt consistency check for the current main."""
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,sha
b=read(D/'unified_archive_paper_binding_03.json');s=Path(b['snapshot'])
assert b['passed'] and len(PdfReader(b['pdf']).pages)==b['pages']==6
assert all(sha(f)==h for f,h in b['source_sha256'].items())
assert all(sha(f)==h for f,h in b['verified_case_receipts'].items())
assert all(sha(s/f)==h for f,h in read(s/'snapshot_binding.json')['files'].items())
assert sha(D/'paper/current_repair_main.tex')==sha(s/'current_repair_main.tex')
rows=read(s/'data/complete_table_rows.json');assert len(rows)==22
text=(s/'current_repair_main.tex').read_text()
for row in rows:
 line=next(x for x in text.splitlines() if x.startswith(row['label']+'&'))
 assert row.get("time_tex",f"{row['complete_seconds']:.2f}") in line
 if row['endpoint_comparison'] is None:assert '(initial fail)' in line and '&--&--&' in line;continue
 q=row['quality'];v=row['endpoint_comparison']
 for value in [f"{q['CPD_ns']:.6f}",'/'.join(str(q[k]) for k in ['wirelength','SB_pairs','CB_sources']),'/'.join(str(v[k]) for k in ['setup_improved','setup_regressed','hold_violation_regressions'])]:assert value in line
assert read(D/'paper/data/evidence_v14_ledger.json')['sources_sha256']['paper/current_repair_main.tex']==sha(s/'current_repair_main.tex')
assert b['records']==671 and b['complete_quality_configurations']==34 and b['complete_observer_measured_configurations']==33 and b['qualified_GNU_only_configurations']==1
assert '671-record archive' in text and '34 quality-complete' in text and '33 have complete observer measurements' in text
assert read(D/'multiobjective_closed_stream_quality_01/verification.json')['passed']
print(dict(archive_records=671,quality_complete=34,observer_complete=33,passed=True,pages=6,table_rows=22,initial_failure_rows=2,source_pdf_snapshot_and_primary_receipts_consistent=True,native_calls_new=0))
