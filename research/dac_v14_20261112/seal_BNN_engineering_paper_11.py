"""Seal six reviewed pages against the actually completed engineering receipt."""
import re, shutil, unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p = D/'paper'; e = D/'BNN_engineering_paper_evidence_11'
parent_path = D/'complete_tradeoff_paper_binding_10.json'
parent = read(parent_path); previous = Path(parent['snapshot'])
source = p/'current_repair_BNN_engineering_11.tex'
build = p/'build_BNN_engineering_11'
pdf = build/'current_repair_BNN_engineering_11.pdf'
log = build/'current_repair_BNN_engineering_11.log'
binding_path = D/'BNN_engineering_paper_binding_11.json'
assert not binding_path.exists()
assert sha(p/'current_repair_main.tex') == sha(previous/'current_repair_main.tex')
reg = read(e/'edit_registration.json')
assert all(sha(f) == h for f,h in reg['source_sha256'].items())
t = source.read_text(); old = (previous/'current_repair_main.tex').read_text()
assert t.split('\\begin{document}')[0] == old.split('\\begin{document}')[0]
assert re.findall(r'\\section\{([^}]+)\}', t) == parent['sections']
assert re.findall(r'\\bibitem\{([^}]+)\}', t) == re.findall(r'\\bibitem\{([^}]+)\}', old)
for kind in ['figure', 'figure*']:
    pattern = r'\\begin\{'+re.escape(kind)+r'\}.*?\\end\{'+re.escape(kind)+r'\}'
    assert re.findall(pattern,t,re.S) == re.findall(pattern,old,re.S)
old_table = re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',old,re.S)
new_table = re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',t,re.S)
assert len(old_table) == len(new_table) == 1
new_row = next(line for line in t.splitlines() if line.startswith('BNN stream D&'))
assert new_table[0].replace(new_row+'\n','') == old_table[0]
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error', log.read_text())
reader = PdfReader(pdf); assert len(reader.pages) == 6
flat = unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
for token in ['9116.40','637.92','6.54%','11.067','47.56%','0.797%','22.95%','CP1']:
    assert token in flat, token
review = read(e/'visual_review.json')
assert review['passed'] and review['pages_reviewed'] == 6 and review['pdf_sha256'] == sha(pdf)
row = read(e/'complete_engineering_row.json')
comparison = read(D/'complete_BNN_domain_engineering_01/comparison.json')
assert row['complete_seconds'] == comparison['actual_complete_seconds']
assert round(row['same_role_seconds_difference'],2) == -637.92
assert round(row['same_role_percent_difference'],2) == -6.54
write(e/'completion.json',dict(passed=True,pages=6,complete_attempt_rows=32,scoped_rows=2,
    total_table_rows=34,unchanged_old_table_rows=33,new_complete_attempt_rows=1,
    new_independent_inputs=0,new_native_calls_during_paper_edit=0,
    historical_matched_pair_overhead_preserved=True,optimized_pair_ratio_established=False,
    source_sha256=reg['source_sha256']))
snap = D/'paper_snapshots/current_BNN_engineering_20261116'
assert not snap.exists()
shutil.copytree(previous,snap)
for src,dest in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log')]:
    shutil.copy2(src,snap/dest)
shutil.copytree(e,snap/'supplement/BNN_engineering')
shutil.copy2(e/'complete_engineering_row.json',snap/'data/BNN_engineering_row.json')
for i in range(1,7): shutil.copy2(build/f'page{i}.png',snap/f'visual/complete_inputs_page{i}.png')
claims = read(previous/'claims_evidence.json')
claims['BNN_engineering_completion'] = dict(whole_seconds=row['complete_seconds'],
    same_role_execution_exact=True, new_independent_inputs=0, CP1_changed=False,
    complete_receipt='complete_BNN_domain_engineering_01/bnn_domain_closed_stream/completion.json',
    comparison='complete_BNN_domain_engineering_01/comparison.json',
    claim='Same-input domain behavior preserved with a descriptively lower complete time; stable interleaved native/domain timing pending.',
    limits='No causal or statistical speedup, optimized pair ratio, independent input or integrated-controller superiority claim.')
write(snap/'claims_evidence.json',claims)
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_BNN_engineering_completion',
    files={str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name!='snapshot_binding.json'},visual_review=review))
shutil.copy2(source,p/'current_repair_main.tex')
ledger = read(p/'data/evidence_v14_ledger.json')
ledger['sources_sha256']['paper/current_repair_main.tex'] = sha(source)
write(p/'data/evidence_v14_ledger.json',ledger)
receipts = parent['verified_case_receipts'].copy(); receipts.update(reg['source_sha256'])
binding = parent.copy()
binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),table_rows=34,
    complete_configuration_table_rows=32,new_complete_attempt_rows=1,
    new_independent_inputs=0,verified_case_receipts=receipts,visual_review=review,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,pdf,log,
        e/'completion.json',e/'edit_registration.json',e/'visual_review.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']},
    qualification='Closed same-role complete BNN engineering evidence. One new complete execution, zero new independent inputs. Original historical pair and paired figure unchanged; no optimized ratio or statistical acceleration. CP1 unchanged.')
binding['main_claim_groups'] = dict(parent['main_claim_groups'], BNN_domain_engineering_same_behavior=['complete_BNN_domain_engineering_01/comparison.json'])
write(binding_path,binding)
print(dict(passed=True,pages=6,table_rows=34,pdf=binding['pdf']))
