"""Seal six pages of matched cost evidence, with unchanged contribution scope."""
import re
import shutil
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
e = D / 'balanced_cost_paper_evidence_19'
parent_path = D / 'sharing_prior_art_paper_binding_18.json'
parent = read(parent_path)
previous = Path(parent['snapshot'])
source = p / 'current_repair_balanced_cost_19.tex'
build = p / 'build_balanced_cost_19_r2'
pdf = build / 'current_repair_balanced_cost_19.pdf'
log = build / 'current_repair_balanced_cost_19.log'
target = D / 'balanced_cost_paper_binding_19.json'
assert not target.exists() and sha(p / 'current_repair_main.tex') == sha(previous / 'current_repair_main.tex')
registration = read(e / 'edit_registration.json')
assert all(sha(f) == h for f, h in registration['source_sha256'].items())
scope = read(e / 'cost_matching_scope.json')
assert scope['passed'] and scope['all_matching_gates_passed']
assert all(sha(f) == h for f, h in scope['source_sha256'].items())
text = source.read_text()
old = (previous / 'current_repair_main.tex').read_text()
restored = text
assert len(registration['changes']) == 7
for before, after in reversed(registration['changes']):
    assert restored.count(after) == 1
    restored = restored.replace(after, before)
assert restored == old, 'Only the seven recorded cost/count/figure-scope edits are allowed'
assert text.split('\\begin{document}')[0] == old.split('\\begin{document}')[0]
assert re.findall(r'\\section\{([^}]+)\}', text) == parent['sections']
assert text[text.index('\\begin{thebibliography}'):]==old[old.index('\\begin{thebibliography}'):]
assert len([line for line in text.splitlines() if line.count('&') == 5 and not line.startswith('Circuit/role')]) == 42
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error', log.read_text())
reader = PdfReader(pdf)
assert len(reader.pages) == 6
flat = unicodedata.normalize('NFKC', ''.join(''.join((x.extract_text() or '').split()) for x in reader.pages)).casefold()
for phrase in ['24.91%', '22.95%', '1.24796/1.25026', '7308.61/9129.25',
               'negotiatedsame-netsharing', 'uncongestedcriticalconnections', 'originalcoldpair', '47.56%', '0.797%']:
    assert phrase in flat, phrase
review = read(e / 'visual_review.json')
assert review['passed'] and review['pages_reviewed'] == 6 and review['pdf_sha256'] == sha(pdf)
write(e / 'completion.json', dict(
    passed=True, pages=6, table_rows=42, terminal_display_rows=35, represented_terminal_attempts=37,
    repeated_measurements=4, balanced_summary_rows=2, moved_historical_engineering_rows=3,
    historical_rows_and_all_failures_retained=True, references=9,
    prior_art_and_contribution_boundaries_unchanged=True, source_preamble_and_mechanisms_unchanged=True,
    new_native_or_STA_calls=0, new_independent_inputs=0, new_CP1r3_results=0,
    historical_archive_counts_unchanged=True, paper_build_receipts=[str(build / 'build_receipt.json')],
    qualification='Matched whole-command overhead and same-input reproducibility only. Means summarize two successful fully matched runs per arm, not independent circuits or invented configurations. Prior-art, mechanism attribution, generality limits and all failures remain. Earlier engineering rows are retained in the supplement.'))
snapshot = D / 'paper_snapshots/current_balanced_cost_20261116'
assert not snapshot.exists()
shutil.copytree(previous, snapshot)
for src, dest in [(source, 'current_repair_main.tex'), (pdf, 'build/current_repair_main.pdf'), (log, 'build/build.log')]:
    shutil.copy2(src, snapshot / dest)
shutil.copytree(e, snapshot / 'supplement/balanced_cost')
for i in range(1, 7):
    shutil.copy2(build / f'page{i}.png', snapshot / f'visual/complete_inputs_page{i}.png')
shutil.copy2(build / 'contact.png', snapshot / 'visual/contact.png')
claims = read(previous / 'claims_evidence.json')
claims['unconfirmed'] = [x for x in claims['unconfirmed'] if x != 'symmetric interleaved engineering runtime']
claims['unconfirmed'].append('causal or statistical engineering speedup')
claims['BNN_engineering_completion']['claim'] = 'Historical single-run behavior preservation; subsequent balanced timing is separately verified, not a causal speedup against older observations.'
claims['BNN_engineering_completion']['superseded_pending_timing_by'] = 'balanced_complete_cost_repeats'
claims['complete_pair_figure_update']['BNN_time_scope'] = 'Original cold matched pair,22.95percent; new balanced mean overhead24.91percent is separate and explicitly identified in the caption.'
claims['balanced_complete_cost_repeats'] = dict(
    status='four_original_whole_commands_and_all_matching_gates_passed', independent_new_inputs=0,
    native_mean_seconds=7308.614699278027, domain_mean_seconds=9129.245384229347,
    ratio_of_means=1.249107492987853, pair_ratios=scope['paired_ratios'],
    historical_22_95_percent_retained=True, statistical_speedup=False,
    evidence=['supplement/balanced_cost/cost_matching_scope.json', 'supplement/balanced_cost/whole_costs.csv'],
    terminal_table_display_rows=35, represented_terminal_attempts=37,
    prior_art_and_contribution_boundaries_unchanged=True, new_CP1r3_outcomes=0)
write(snapshot / 'claims_evidence.json', claims)
write(snapshot / 'snapshot_binding.json', dict(status='immutable_six_page_matched_complete_cost_update',
    files={str(f.relative_to(snapshot)): sha(f) for f in snapshot.rglob('*') if f.is_file() and f.name != 'snapshot_binding.json'},
    visual_review=review))
shutil.copy2(source, p / 'current_repair_main.tex')
ledger = read(p / 'data/evidence_v14_ledger.json')
ledger['sources_sha256']['paper/current_repair_main.tex'] = sha(source)
ledger['sources_sha256']['balanced_cost_paper_evidence_19/cost_matching_scope.json'] = sha(e / 'cost_matching_scope.json')
write(p / 'data/evidence_v14_ledger.json', ledger)
binding = parent.copy()
binding.update(snapshot=str(snapshot), pdf=str(snapshot / 'build/current_repair_main.pdf'),
    table_rows=42, complete_configuration_table_rows=35, represented_terminal_attempts=37,
    table_observer_missing_rows=0, new_complete_attempt_rows=2, new_terminal_attempt_rows=2,
    new_actual_complete_measurements=4, moved_historical_engineering_rows=3,
    new_independent_inputs=0, new_confirmed_physical_inputs=0, newly_closed_cohort_inputs=0,
    visual_review=review, prior_art_and_contribution_boundaries_unchanged=True,
    qualification='Six pages,42displayed rows and9unchanged references. Four same-input full repetitions enter as two timing summaries; three older engineering rows move intact to the supplement. Full matching permits descriptive complete cost ratios, not statistical speedup, independent-input evidence or broader algorithm superiority. Paper18 prior-art/contribution and historical22.95percent remain.',
    source_sha256={str(f): sha(f) for f in [Path(__file__).resolve(), parent_path, source, pdf, log,
        e / 'edit_registration.json', e / 'completion.json', e / 'visual_review.json',
        snapshot / 'snapshot_binding.json', snapshot / 'claims_evidence.json']})
binding['verified_case_receipts'] = dict(parent['verified_case_receipts'], **registration['source_sha256'], **scope['source_sha256'])
binding['main_claim_groups'] = dict(parent['main_claim_groups'],
    balanced_complete_cost_repeats=['BNN_interleaved_timing_03/comparison.json',
        'BNN_timing03_balanced_receipt_01/completion.json', 'balanced_cost_paper_evidence_19/cost_matching_scope.json'])
write(target, binding)
print(dict(passed=True, pages=6, table_rows=42, actual_balanced_measurements=4,
           new_independent_inputs=0, pdf=binding['pdf']))
