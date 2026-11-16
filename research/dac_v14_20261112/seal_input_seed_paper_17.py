"""Seal the caption correction without changing quantitative or benefit evidence."""
import re, shutil, unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p = D/'paper'; e = D/'input_seed_paper_evidence_17'
parent_path = D/'mechanism_trigger_paper_binding_16.json'; parent = read(parent_path)
previous = Path(parent['snapshot']); source = p/'current_repair_input_seeds_17.tex'
b = p/'build_input_seeds_17'; pdf = b/(source.stem+'.pdf'); log = b/(source.stem+'.log')
target = D/'input_seed_paper_binding_17.json'; assert not target.exists()
assert sha(p/'current_repair_main.tex') == sha(previous/'current_repair_main.tex')
reg = read(e/'edit_registration.json')
assert all(sha(f)==h for f,h in reg['source_sha256'].items())
seeds = read(e/'seed_provenance.json')
assert seeds['passed'] and len(seeds['rows'])==8
assert all(sha(f)==h for f,h in seeds['source_sha256'].items())
t = source.read_text(); old = (previous/'current_repair_main.tex').read_text()
before,after = reg['changes'][0]
assert len(reg['changes'])==1 and t.count(after)==1 and t.replace(after,before)==old
assert re.findall(r'\\section\{([^}]+)\}',t)==parent['sections']
assert t.split('\\begin{document}')[0]==old.split('\\begin{document}')[0]
assert re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',t,re.S)==re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',old,re.S)
assert re.findall(r'\\bibitem\{([^}]+)\}',t)==re.findall(r'\\bibitem\{([^}]+)\}',old)
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
reader = PdfReader(pdf); assert len(reader.pages)==6
flat = unicodedata.normalize('NFKC',''.join(''.join((x.extract_text() or '').split()) for x in reader.pages))
for word in ['seedsvarybyinput','47.56%','0.797%','22.95%']:
    assert word in flat.casefold(),word
assert 'routerseed11' not in flat.casefold()
review = read(e/'visual_review.json')
assert review['passed'] and review['pages_reviewed']==6 and review['pdf_sha256']==sha(pdf)
write(e/'completion.json',dict(passed=True,pages=6,main_table_rows=43,quantitative_rows_unchanged=True,
    command_manifests=8,new_native_calls=0,new_STA_calls=0,new_independent_inputs=0,new_full_method_results=0,
    qualification='Correct blanket seed11 caption; preserve CP1r2 seed21 timeouts/no-op and Robot upstream s23 versus actual router seed11 distinction. Metadata-only, no fresh byte admission or additional benefit evidence.'))
snap = D/'paper_snapshots/current_input_seeds_20261116'; assert not snap.exists()
shutil.copytree(previous,snap)
for src,dest in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log')]:
    shutil.copy2(src,snap/dest)
shutil.copytree(e,snap/'supplement/input_seed_provenance')
for i in range(1,7):
    shutil.copy2(b/f'page{i}.png',snap/f'visual/complete_inputs_page{i}.png')
claims = read(previous/'claims_evidence.json')
claims['actual_router_seed_provenance'] = dict(status='metadata_correction_no_new_benefit_evidence',
    existing_command_manifests=8,BNN=11,Robot_SDC_upstream_s23=11,CP1r2_conv_hls=21,CP1r2_tpu_ws=21,
    new_independent_inputs=0,fresh_physical_byte_audit=False,
    evidence='supplement/input_seed_provenance/seed_provenance.json')
write(snap/'claims_evidence.json',claims)
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_input_seed_caption_correction',
    files={str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name!='snapshot_binding.json'},visual_review=review))
shutil.copy2(source,p/'current_repair_main.tex')
ledger = read(p/'data/evidence_v14_ledger.json')
ledger['sources_sha256']['paper/current_repair_main.tex']=sha(source)
write(p/'data/evidence_v14_ledger.json',ledger)
binding = parent.copy()
binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),table_rows=43,
    # Reconcile the obsolete component alias with the authoritative five scoped rows.
    scoped_component_table_rows=parent['scoped_table_rows'],
    new_complete_attempt_rows=0,new_terminal_attempt_rows=0,new_independent_inputs=0,
    new_confirmed_physical_inputs=0,newly_closed_cohort_inputs=0,visual_review=review,
    qualification='Six pages and all43quantitative rows unchanged. Existing eight command manifests correct overbroad router-seed caption; no new input, physical-byte verification, complete result, cost ratio or benefit claim.',
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,pdf,log,e/'completion.json',e/'visual_review.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']})
binding['verified_case_receipts'] = dict(parent['verified_case_receipts'],**reg['source_sha256'])
binding['main_claim_groups'] = dict(parent['main_claim_groups'],actual_input_router_seeds=['input_seed_paper_evidence_17/seed_provenance.json'])
write(target,binding)
print(dict(passed=True,pages=6,table_rows_unchanged=43,pdf=binding['pdf']))
