"""Seal a narrower prior-art statement and bound contribution map, no new result."""
import re, shutil, unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p=D/'paper';e=D/'sharing_prior_art_paper_evidence_18';parent_path=D/'input_seed_paper_binding_17.json';parent=read(parent_path)
previous=Path(parent['snapshot']);source=p/'current_repair_sharing_prior_art_18.tex';b=p/'build_sharing_prior_art_18'
pdf=b/(source.stem+'.pdf');log=b/(source.stem+'.log');target=D/'sharing_prior_art_paper_binding_18.json'
assert not target.exists() and sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
reg=read(e/'edit_registration.json');assert all(sha(f)==h for f,h in reg['source_sha256'].items())
scope=read(e/'evidence_scope_bindings.json');assert scope['passed'] and all(sha(f)==h for f,h in scope['source_sha256'].items())
t=source.read_text();old=(previous/'current_repair_main.tex').read_text();before,after=reg['changes'][0]
assert len(reg['changes'])==1 and t.count(after)==1 and t.replace(after,before)==old
assert re.findall(r'\\section\{([^}]+)\}',t)==parent['sections']
assert t.split('\\begin{document}')[0]==old.split('\\begin{document}')[0]
assert re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',t,re.S)==re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',old,re.S)
assert re.findall(r'\\bibitem\{([^}]+)\}',t)==re.findall(r'\\bibitem\{([^}]+)\}',old)
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
reader=PdfReader(pdf);assert len(reader.pages)==6
flat=unicodedata.normalize('NFKC',''.join(''.join((x.extract_text() or '').split()) for x in reader.pages)).casefold()
for word in ['negotiatedsame-netsharing','uncongestedcriticalconnections','seedsvarybyinput','47.56%','0.797%','22.95%']:
    assert word in flat,word
review=read(e/'visual_review.json');assert review['passed'] and review['pages_reviewed']==6 and review['pdf_sha256']==sha(pdf)
write(e/'completion.json',dict(passed=True,pages=6,main_table_rows=43,quantitative_rows_unchanged=True,
    references_unchanged=9,new_native_calls=0,new_STA_calls=0,new_independent_inputs=0,new_full_method_results=0,
    qualification='Acknowledge existing negotiated same-net sharing and uncongested critical rerouting. Supplement compares prior primitives and actual attribution controls; no cross-paper numeric ranking or new benefit claim.'))
snap=D/'paper_snapshots/current_sharing_prior_art_20261116';assert not snap.exists();shutil.copytree(previous,snap)
for src,dest in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log')]:
    shutil.copy2(src,snap/dest)
shutil.copytree(e,snap/'supplement/sharing_prior_art')
for i in range(1,7):shutil.copy2(b/f'page{i}.png',snap/f'visual/complete_inputs_page{i}.png')
shutil.copy2(b/'contact.png',snap/'visual/contact.png')
claims=read(previous/'claims_evidence.json')
claims['negotiated_sharing_prior_art']=dict(status='acknowledged_prior_ingredients_not_new_benefit',
    prior_ingredients=['Current timing','Same-net sharing','Uncongested critical-connection rerouting','Incremental repair'],
    local_comparison='Retained cross-layer permission domains, per-net actual-failure release, matched owner coordination and fixed whole-candidate envelopes.',
    external_router_reproduced=False,cross_paper_numeric_rank=False,new_independent_inputs=0,
    evidence=['supplement/sharing_prior_art/sources.json','supplement/sharing_prior_art/contribution_comparison.md','supplement/sharing_prior_art/evidence_scope_bindings.json'])
write(snap/'claims_evidence.json',claims)
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_sharing_prior_art_clarification',
    files={str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name!='snapshot_binding.json'},visual_review=review))
shutil.copy2(source,p/'current_repair_main.tex');ledger=read(p/'data/evidence_v14_ledger.json')
ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source);write(p/'data/evidence_v14_ledger.json',ledger)
binding=parent.copy();binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),table_rows=43,
    new_complete_attempt_rows=0,new_terminal_attempt_rows=0,new_independent_inputs=0,new_confirmed_physical_inputs=0,
    newly_closed_cohort_inputs=0,visual_review=review,
    qualification='Six pages,43quantitative rows and9references unchanged. Acknowledge negotiated same-net sharing and critical-connection rerouting as prior art; bind supplement attribution/comparison scopes. No new native/STA work, independent evidence, external router comparison, time ratio or benefit claim.',
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,pdf,log,e/'completion.json',e/'visual_review.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']})
binding['verified_case_receipts']=dict(parent['verified_case_receipts'],**reg['source_sha256'],**scope['source_sha256'])
binding['main_claim_groups']=dict(parent['main_claim_groups'],negotiated_sharing_prior_art=['sharing_prior_art_paper_evidence_18/sources.json','sharing_prior_art_paper_evidence_18/contribution_comparison.md','sharing_prior_art_paper_evidence_18/evidence_scope_bindings.json'])
write(target,binding);print(dict(passed=True,pages=6,table_rows_unchanged=43,pdf=binding['pdf']))
