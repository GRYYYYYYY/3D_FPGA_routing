"""Seal only the built and visually reviewed six-page complete-input manuscript."""
import re
import shutil
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p = D/'paper'
parent_path = D/'complete_input_paper_binding_07.json'
parent = read(parent_path)
previous = Path(parent['snapshot'])
assert sha(p/'current_repair_main.tex') == sha(previous/'current_repair_main.tex')
e = D/'qualified_complete_paper_evidence_08'
reg = read(e/'edit_registration.json')
assert all(sha(f) == h for f,h in reg['sources_sha256'].items())
source = p/'current_repair_qualified_inputs_08.tex'
build = p/'build_qualified_inputs_08'
pdf = build/'current_repair_qualified_inputs_08.pdf'
log = build/'current_repair_qualified_inputs_08.log'
old = (previous/'current_repair_main.tex').read_text()
text = source.read_text()
assert text.split('\\begin{document}')[0] == old.split('\\begin{document}')[0]
assert re.findall(r'\\section\{([^}]+)\}', text) == parent['sections']
assert re.findall(r'\\bibitem\{([^}]+)\}', text) == re.findall(r'\\bibitem\{([^}]+)\}', old)
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error', log.read_text())
for environment in ['figure','figure\\*']:
    pattern = r'\\begin\{' + environment + r'\}.*?\\end\{' + environment + r'\}'
    assert re.findall(pattern,text,re.S) == re.findall(pattern,old,re.S)
legacy = read(previous/'data/complete_table_rows.json')
assert len(legacy) == 22
for row in legacy:
    assert next(x for x in text.splitlines() if x.startswith(row['label']+'&')) == next(x for x in old.splitlines() if x.startswith(row['label']+'&'))
reader = PdfReader(pdf)
assert len(reader.pages) == 6
flat = unicodedata.normalize('NFKC',''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
for token in ['7351.26','498.00','504.09','794.67','792.69','10972','47.56%','0.797%','22.95%','231overusednodes','104s','101.43s']:
    assert token in flat,token
review = read(e/'visual_review.json')
assert review['passed'] and review['pages_reviewed'] == 6 and review['pdf_sha256'] == sha(pdf)
receipts = parent['verified_case_receipts'].copy()
for f in [e/'completion.json',e/'rows.json',D/'unified_input_integration_01/comparison.json',
          D/'attention_initial_failure_pair_01/completion.json',
          D/'complete_BNN_terminal_wire_flow_01/bnn_native_terminal_wire/completion.json',
          D/'standalone_native_observation_equivalence_01/completion.json',
          D/'confirmation_input_inventory_01/completion.json',
          D/'BNN_terminal_wire_qualified_comparison_02/completion.json',
          D/'standalone_whole_method_check_01/completion.json']:
    receipts[str(f)] = sha(f)
assert all(sha(f) == h for f,h in receipts.items())
transaction_check = D/'standalone_transaction_native_check_01/completion.json'
if 'A known R1 owner transaction also reproduces' in text:
    assert read(transaction_check)['passed']
    receipts[str(transaction_check)] = sha(transaction_check)
snap = D/'paper_snapshots/current_qualified_inputs_20261116'
assert not snap.exists()
shutil.copytree(previous,snap)
for src,dest in [(source,'current_repair_main.tex'),(pdf,'build/current_repair_main.pdf'),(log,'build/build.log')]:
    shutil.copy2(src,snap/dest)
shutil.copytree(e,snap/'supplement/qualified_complete_inputs')
for i in range(1,7):shutil.copy2(build/f'page{i}.png',snap/f'visual/complete_inputs_page{i}.png')
write(snap/'data/new_complete_input_rows.json',read(e/'rows.json'))
claims = read(previous/'claims_evidence.json')
claims['complete_input_update'] = dict(
    audit=str(e/'completion.json'),new_complete_attempts=5,new_legal_outputs=3,new_initial_failures=2,
    new_BNN_independent_inputs=0,robot_input='Known different actual placement plus declared SDC; one within-input N/D pair, not a placement-only causal control.',
    robot_result='Identical roots and final endpoints; zero accepted resource/owner/timing changes. Lower-CPD proposal exceeds fixed resource budgets.',
    attention_result='Both initial routes fail; 200 iterations and231 overused nodes; no legal repair input.',
    full_controller_frozen=False,statistical_speedup=False,historical_archive_counts_updated=False,
    BNN_qualified_baseline_comparison='Actual shared-prefix equivalence passed;24wire saved and2setup improvements/0regressions. GNU7351vs7247s,+104s; old observer/PSS loss and overlap preserved.',
    standalone_whole_method='Actual existing tiny input whole flow passed outside project;101.434s,0accepted resource/owner/timing steps. Not independent evidence or broad mechanism-path confirmation.')
write(snap/'claims_evidence.json',claims)
files = {str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name != 'snapshot_binding.json'}
write(snap/'snapshot_binding.json',dict(status='immutable_six_page_complete_input_update',files=files,visual_review=review))
shutil.copy2(source,p/'current_repair_main.tex')
ledger = read(p/'data/evidence_v14_ledger.json')
ledger['sources_sha256']['paper/current_repair_main.tex'] = sha(source)
write(p/'data/evidence_v14_ledger.json',ledger)
binding = {k:v for k,v in parent.items() if k not in ['source_sha256','qualification','visual_review','snapshot','pdf','new_native_calls','new_independent_inputs']}
binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),table_rows=29,
    complete_configuration_table_rows=27,scoped_component_table_rows=2,table_initial_failure_rows=4,
    new_native_calls_during_paper_update=0,new_complete_attempt_rows=5,
    verified_case_receipts=receipts,visual_review=review,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,pdf,log,e/'completion.json',e/'edit_registration.json',e/'visual_review.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']},
    qualification='Complete own-output cost and full own-root endpoints for3legal results plus2failed attempts. Historical archive counts unchanged. Known physical input differences and declared benchmark SDC do not establish unseen generalization, external application timing, frozen full-controller confirmation or causal acceleration.')
write(D/'qualified_complete_paper_binding_08.json',binding)
print(dict(passed=True,pages=6,complete_attempt_rows=27,scoped_rows=2,pdf=binding['pdf']))
