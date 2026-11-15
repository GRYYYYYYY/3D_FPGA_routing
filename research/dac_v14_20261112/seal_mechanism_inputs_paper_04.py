"""Bind conditional robot mechanism evidence; preserve measured table and old snapshots."""
import re, shutil, sys, unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p=D/'paper'; parent_path=D/'unified_archive_paper_binding_03.json'; parent=read(parent_path)
previous=Path(parent['snapshot']); assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
source=p/'current_repair_mechanism_inputs_04.tex'; build=p/'build_mechanism_inputs_04'
pdf=build/'current_repair_mechanism_inputs_04.pdf'; log=p/'build_mechanism_inputs_04.log'
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
text=source.read_text(); oldtext=(previous/'current_repair_main.tex').read_text()
assert re.findall(r'\\section\{([^}]+)\}',text)==parent['sections']
assert text.split('\\begin{document}')[0]==oldtext.split('\\begin{document}')[0]
reader=PdfReader(pdf); assert len(reader.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
for word in ['671-record','34quality-complete','33havecompleteobservermeasurements','qualifiedGNU-timeonly','22.95%','47.56%','0.797%','source-cut','owner-scopegainsonrobotarenotclaimed']:
    assert word in flat,word
rows=read(previous/'data/complete_table_rows.json'); assert len(rows)==22
for row in rows:
    assert next(x for x in text.splitlines() if x.startswith(row['label']+'&'))==next(x for x in oldtext.splitlines() if x.startswith(row['label']+'&'))
sys.path.insert(0,str(p/'tools/pdf_review')); import pymupdf
newpdf=pymupdf.open(pdf); oldpdf=pymupdf.open(parent['pdf'])
changed=[i+1 for i in range(6) if newpdf[i].get_pixmap().samples!=oldpdf[i].get_pixmap().samples]
assert changed==[2,3,4]
receipts=parent['verified_case_receipts'].copy()
new_receipts=['robot_release_capacity_cut_01/completion.json','robot_current_owner_screen_01/completion.json','structural_input_screen_01/completion.json']
for name in new_receipts:
    f=D/name; r=read(f); assert r['passed'] and r['native_calls_new']==0
    assert all(sha(s)==h for s,h in r['source_sha256'].items())
    assert all(sha(f.parent/s)==h for s,h in r['artifact_sha256'].items())
    receipts[str(f)]=sha(f)
assert all(sha(f)==h for f,h in receipts.items())
snap=D/'paper_snapshots/current_mechanism_inputs_20261115'; assert not snap.exists()
shutil.copytree(previous,snap)
for src,name in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log')]:
    shutil.copy2(src,snap/name)
for i in changed: shutil.copy2(build/f'page{i}.png',snap/f'visual/mechanism_page{i}.png')
for directory in ['structural_input_screen_01','robot_release_capacity_cut_01','robot_current_owner_screen_01']:
    dest=snap/'supplement'/directory; dest.mkdir()
    for f in (D/directory).glob('*.json'): shutil.copy2(f,dest/f.name)
checks=parent['main_claim_groups'].copy()
checks['robot_conditional_domain_obstruction']=['robot_release_capacity_cut_01/completion.json','robot_release_capacity_cut_01/cuts.json']
checks['robot_current_owner_proposals_only']=['robot_current_owner_screen_01/completion.json']
claims=read(previous/'claims_evidence.json'); claims['main_claim_groups']=checks
claims['mechanism_input_scope']=dict(new_native_calls=0,new_full_method_outcomes=0,structural_inputs=6,legal_historical_roots=5,initial_failure_roots=1,
    robot_domain_obstructions=2,robot_slack_eligible_owner_proposals=16,
    qualification='Conditional fixed-outside-owner/domain proof; no-release ablation and actual robot owner transaction remain unexecuted. Structural opportunities are not algorithm outcomes or unseen holdout results.')
write(snap/'claims_evidence.json',claims)
visual='Changed pages2/3/4 inspected at1.5x: legible, no clipping; pages1/5/6 raster-exact. Historical contact images remain historical; mechanism_page images are current. No font/margin/table/figure-population change.'
files={str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name!='snapshot_binding.json'}
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_mechanism_input_update',files=files,visual_review=visual))
shutil.copy2(source,p/'current_repair_main.tex')
ledger=read(p/'data/evidence_v14_ledger.json'); ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source); write(p/'data/evidence_v14_ledger.json',ledger)
binding={k:v for k,v in parent.items() if k not in ['source_sha256','qualification','visual_review','snapshot','pdf','main_claim_groups','verified_case_receipts']}
binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),main_claim_groups=checks,verified_case_receipts=receipts,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),source,pdf,log,parent_path,snap/'snapshot_binding.json',snap/'claims_evidence.json']},
    visual_review=visual,new_independent_inputs=0,new_native_calls=0,complete_research=False,
    qualification='Two mechanism paragraphs replaced. Exact robot retained domains and external capacity owners establish conditional obstruction; release and coordination remain distinct. Original selector finds current-margin proposals, not native feasibility or gains. Six pages/22 measured rows/671 observations/34 quality configurations unchanged; complete confirmation remains pending.')
write(D/'mechanism_inputs_paper_binding_04.json',binding)
print(dict(passed=True,pages=6,table_rows=22,changed_pages=changed,pdf=binding['pdf']))
