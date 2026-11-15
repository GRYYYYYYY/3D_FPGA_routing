"""Read-only source/PDF/table/receipt consistency check for the current main."""
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,sha
b=read(D/'unified_structure_paper_binding_01.json');s=Path(b['snapshot'])
assert b['passed'] and len(PdfReader(b['pdf']).pages)==b['pages']==6
assert all(sha(f)==h for f,h in b['source_sha256'].items())
assert all(sha(f)==h for f,h in b['verified_case_receipts'].items())
assert all(sha(s/f)==h for f,h in read(s/'snapshot_binding.json')['files'].items())
assert sha(D/'paper/current_repair_main.tex')==sha(s/'current_repair_main.tex')
rows=read(s/'data/complete_table_rows.json');assert len(rows)==21
text=(s/'current_repair_main.tex').read_text()
for row in rows:
 line=next(x for x in text.splitlines() if x.startswith(row['label']+'&'))
 assert f"{row['complete_seconds']:.2f}" in line
 if row['endpoint_comparison'] is None:assert '(initial fail)' in line and '&--&--&' in line;continue
 q=row['quality'];v=row['endpoint_comparison']
 for value in [f"{q['CPD_ns']:.6f}",'/'.join(str(q[k]) for k in ['wirelength','SB_pairs','CB_sources']),'/'.join(str(v[k]) for k in ['setup_improved','setup_regressed','hold_violation_regressions'])]:assert value in line
assert read(D/'paper/data/evidence_v14_ledger.json')['sources_sha256']['paper/current_repair_main.tex']==sha(s/'current_repair_main.tex')
print(dict(passed=True,pages=6,table_rows=21,initial_failure_rows=2,source_pdf_snapshot_and_primary_receipts_consistent=True,native_calls_new=0))
