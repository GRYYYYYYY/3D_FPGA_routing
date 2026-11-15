"""Read-only current C221 manuscript, exact claim lineage and immutable artifact check."""
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
b=read(D/'R1_native_closure_paper_binding_01.json')
assert b['passed'] and b['pages']==6 and b['records']==578
assert b['claims']==read(D/'joint_owner_escape_paper_binding_01.json')['claims']+['C221']
assert len(set(b['claims']))==len(b['claims']) and 'C197' in b['claims']
assert all(sha(f)==h for f,h in b['source_sha256'].items())
a=Path(b['archive']);c=read(a/'completion.json');assert c['records']==578
assert all(sha(a/f)==h for f,h in c['artifact_sha256'].items())
v=read(a/'verification.json');assert v['passed'] and v['terminal_checkpoint_not_duplicated'] and v['new_materialized_states']==2
assert read(D/'multiobjective_R1_joint_owner_escape_01/verification.json')['actual_escape_transfer']==dict(node=3507189,from_owner=62707,to_target=31767,fixed_sinks_exact=True)
controls=read(D/'closed_seed_transfer_eight_roles_01.json');assert controls['successfully_closed_menus']==8
projection=read(D/'paper/data/joint_quality_projection_binding_33.json');points=read(a/'points.json')
for label,name in [('R1 native seed terminal','bnn_R1'),('Tf native seed terminal','bnn_Tf')]:
 state=controls['matched_own_current_pairs'][name]['native']['final_state']
 row=next(p for p in points if p.get('state')==state)
 assert projection['selected_records'][label]==row['id']
assert read(D/'multiobjective_closed_Tf_native_01/verification.json')['passed']
s=Path(b['snapshot']);assert all(sha(s/f)==h for f,h in read(s/'snapshot_binding.json')['files'].items())
assert sha(D/'paper/current_repair_main.tex')==sha(s/'current_repair_main.tex')
r=PdfReader(b['pdf']);assert len(r.pages)==6
text=unicodedata.normalize('NFKC',''.join(''.join((p.extract_text() or '').split()) for p in r.pages))
assert all(t in text or (any(c.isalpha() for c in t) and t.replace('-','') in text.replace('-','')) for t in b['numerical_text_checks'])
assert read(D/'paper/data/evidence_v14_ledger.json')['sources_sha256']['paper/current_repair_main.tex']==sha(s/'current_repair_main.tex')
print(dict(passed=True,paper_pages=6,records=578,claim_lineage_exact=True,source_pdf_snapshot_consistent=True,native_calls_new=0),flush=True)
