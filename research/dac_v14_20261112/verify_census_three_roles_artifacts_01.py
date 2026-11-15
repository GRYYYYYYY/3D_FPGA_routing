"""Read-only replay of current paper/snapshot and archive artifact bindings."""
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, sha

binding = read(D / 'census_three_roles_paper_binding_01.json')
assert binding['passed'] and binding['pages'] == 6 and binding['records'] == 495
for p, h in binding['source_sha256'].items():
    assert sha(p) == h, p
archive = Path(binding['archive'])
receipt = read(archive / 'completion.json')
assert receipt['passed'] and receipt['records'] == 495
for p, h in receipt['artifact_sha256'].items():
    assert sha(archive / p) == h, p
snapshot = Path(binding['snapshot'])
for p, h in read(snapshot / 'snapshot_binding.json')['files'].items():
    assert sha(snapshot / p) == h, p
assert sha(D / 'paper/current_repair_main.tex') == sha(snapshot / 'current_repair_main.tex')
pdf = PdfReader(binding['pdf'])
assert len(pdf.pages) == 6
text = ''.join(''.join(p.extract_text() or '' for p in pdf.pages).split())
assert all(t in text for t in binding['numerical_text_checks'])
ledger = read(D / 'paper/data/evidence_v14_ledger.json')
assert ledger['sources_sha256']['paper/current_repair_main.tex'] == sha(snapshot / 'current_repair_main.tex')
print(dict(passed=True, archive_records=495, paper_pages=6,
           source_pdf_snapshot_consistent=True, native_calls=0), flush=True)
