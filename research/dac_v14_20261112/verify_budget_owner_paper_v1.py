"""Read-only verification of the current C223 manuscript and bound case receipts."""
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,sha
b=read(D/'budget_owner_paper_binding_01.json')
assert b['passed'] and b['claims']==read(D/'transfer_index_paper_binding_01.json')['claims']+['C223']
assert len(set(b['claims']))==len(b['claims']) and 'C197' in b['claims']
assert all(sha(f)==h for f,h in b['source_sha256'].items())
assert all(sha(f)==h for f,h in b['verified_case_receipts'].items())
s=Path(b['snapshot']);assert all(sha(s/f)==h for f,h in read(s/'snapshot_binding.json')['files'].items())
assert sha(D/'paper/current_repair_main.tex')==sha(s/'current_repair_main.tex')
r=PdfReader(b['pdf']);assert len(r.pages)==b['pages']==6
t=unicodedata.normalize('NFKC',''.join(''.join((p.extract_text() or '').split()) for p in r.pages)).replace('-','')
assert all(k.replace('-','') in t for k in b['numerical_text_checks'])
assert read(D/'paper/data/evidence_v14_ledger.json')['sources_sha256']['paper/current_repair_main.tex']==sha(s/'current_repair_main.tex')
v=read(D/'paper/current_visual_review_C223.json')
assert v['passed'] and v['pdf_sha256']==sha(b['pdf']) and v['source_sha256']==sha(s/'current_repair_main.tex')
assert sha(v['rendered_contact'])==v['rendered_contact_sha256']
print(dict(passed=True,pages=6,claim='C223',source_pdf_snapshot_consistent=True,cited_case_receipts_unchanged=True,native_calls_new=0),flush=True)
