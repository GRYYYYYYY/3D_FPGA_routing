"""Seal the six-page manuscript with two actual, explicitly scoped native outcomes."""
import re
import shutil
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
parent_path = D / 'routing_position_paper_binding_05.json'
parent = read(parent_path)
previous = Path(parent['snapshot'])
assert sha(p/'current_repair_main.tex') == sha(previous/'current_repair_main.tex')
evidence = D/'native_ablation_paper_evidence_06'
reg = read(evidence/'edit_registration.json')
assert all(sha(f) == h for f, h in reg['source_sha256'].items())
source = p/'current_repair_native_ablation_06.tex'
build = p/'build_native_ablation_06'
pdf = build/'current_repair_native_ablation_06.pdf'
log = p/'build_native_ablation_06.log'
text = source.read_text()
old = (previous/'current_repair_main.tex').read_text()
assert text.split('\\begin{document}')[0] == old.split('\\begin{document}')[0]
assert re.findall(r'\\section\{([^}]+)\}', text) == parent['sections']
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error', log.read_text())
assert re.findall(r'\\bibitem\{([^}]+)\}', text) == re.findall(r'\\bibitem\{([^}]+)\}', old)
rows = read(previous/'data/complete_table_rows.json')
assert len(rows) == 22
for row in rows:
    assert next(x for x in text.splitlines() if x.startswith(row['label']+'&')) == next(x for x in old.splitlines() if x.startswith(row['label']+'&'))
for environment in ['figure', 'figure\\*']:
    pattern = r'\\begin\{' + environment + r'\}.*?\\end\{' + environment + r'\}'
    assert re.findall(pattern, text, re.S) == re.findall(pattern, old, re.S)
reader = PdfReader(pdf)
assert len(reader.pages) == 6
flat = unicodedata.normalize('NFKC', ''.join(''.join((page.extract_text() or '').split()) for page in reader.pages))
for word in ['217.95', '29.24', '2059607/82/5062', 'rollback', '34predictedconnectiondelays',
             '22.95%', '47.56%', '0.797%', '10308.49']:
    assert word in flat, word
assert 'firstconnectionafternineattempts' in flat
assert 'remainsqueued' not in flat
receipts = parent['verified_case_receipts'].copy()
for f in [D/'BNN_wire_timing_native_validation_01/verification.json',
          D/'BNN_wire_timing_native_validation_01/candidate_evaluation/completion.json',
          D/'BNN_wire_timing_native_validation_01/measurement/completion.json',
          D/'BNN_wire_timing_native_validation_01/actual_prediction_checks.json',
          D/'robot_domain_release_ablation_01/verification.json',
          D/'robot_domain_release_ablation_01/transaction/completion.json',
          D/'query_reduction_resource_dev_01/bnn_A0_paired/completion.json']:
    receipts[str(f)] = sha(f)
assert all(sha(f) == h for f, h in receipts.items())
snap = D/'paper_snapshots/current_native_ablation_20261116'
assert not snap.exists()
shutil.copytree(previous, snap)
for src, name in [(source,'current_repair_main.tex'), (pdf,'build/current_repair_main.pdf'), (log,'build/build.log')]:
    shutil.copy2(src, snap/name)
for i in range(1,7):
    shutil.copy2(build/f'page{i}.png', snap/f'visual/native_ablation_page{i}.png')
shutil.copytree(evidence, snap/'supplement/native_ablation')
shutil.copy2(evidence/'scoped_component_rows.json', snap/'data/scoped_component_rows.json')
claims = read(previous/'claims_evidence.json')
claims['unconfirmed'] = [s for s in claims['unconfirmed'] if s not in ['robot release ablation','BNN composed candidate FULL_STA']]
claims['scoped_native_outcomes'] = dict(composition='legal accepted fixed three-net candidate,2setup improvements/0regressions/0increased hold violations;34exact delay predictions',
    robot_no_release='Same23-connection request fails on first connection;9attempts;source bytes/full vector restored',
    receipts=[str(D/'BNN_wire_timing_native_validation_01/verification.json'),str(D/'robot_domain_release_ablation_01/verification.json')],
    actual_new_native_experiments=2, new_independent_inputs=0, new_complete_method_outcomes=0,
    complete_configuration_costs_attached=False, archive_counts_include_these_rows=False)
claims['mechanism_input_scope']['qualification'] = 'Conditional fixed-outside-owner/domain proof now accompanied by actual same-source no-release failure and exact rollback. Actual robot owner transaction remains pending. Structural opportunities and same-root ablations are not independent inputs or complete-method outcomes.'
claims['mechanism_input_scope']['new_native_calls'] = 2
claims['grouping_development'] = dict(receipt=str(D/'query_reduction_resource_dev_01/bnn_A0_paired/completion.json'),
    imported_seconds=10308.489168014377, complete_cold_seconds=None, statistical_speedup=False,
    interpretation='Does not establish a cost benefit over historical K8; do not promote heuristic into registered dev03.')
write(snap/'claims_evidence.json', claims)
visual = 'All6pages visually inspected at1.3x. Unified table has22unchanged full-flow rows and2separately labelled scoped components; no clipped text, overflow or missing references. Fonts/margins and both figures unchanged. native_ablation_page1--6 are current renders; older images remain historical.'
files = {str(f.relative_to(snap)):sha(f) for f in snap.rglob('*') if f.is_file() and f.name != 'snapshot_binding.json'}
write(snap/'snapshot_binding.json', dict(status='immutable_six_page_native_ablation_update',files=files,visual_review=visual))
shutil.copy2(source,p/'current_repair_main.tex')
ledger = read(p/'data/evidence_v14_ledger.json')
ledger['sources_sha256']['paper/current_repair_main.tex'] = sha(source)
write(p/'data/evidence_v14_ledger.json',ledger)
binding = {k:v for k,v in parent.items() if k not in ['source_sha256','qualification','visual_review','snapshot','pdf']}
binding.update(snapshot=str(snap),pdf=str(snap/'build/current_repair_main.pdf'),table_rows=24,
    complete_configuration_table_rows=22,scoped_component_table_rows=2,table_failed_scoped_rows=1,
    new_native_calls=2,new_independent_inputs=0,verified_case_receipts=receipts,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,pdf,log,evidence/'edit_registration.json',
        evidence/'scoped_component_rows.json',snap/'snapshot_binding.json',snap/'claims_evidence.json']},
    visual_review=visual,qualification='Two actual scoped native outcomes integrated, with imported costs explicitly separated from22full-flow rows. '
        'Historical671-record archive,34quality-complete configurations and33+1measurement counts unchanged and labelled historical. '
        'Native no-release failure is operational; separate capacity proof provides conditional infeasibility. '
        'No owner-scope gain, new independent input, complete-method universal benefit, interleaved speedup or confirmation freeze inferred.')
write(D/'native_ablation_paper_binding_06.json',binding)
print(dict(passed=True,pages=6,full_flow_rows=22,scoped_rows=2,pdf=binding['pdf']))
