"""Integrate verified whole costs; preserve paper18 prior-art and claim boundaries."""
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
e = D / 'balanced_cost_paper_evidence_19'
parent_path = D / 'sharing_prior_art_paper_binding_18.json'
parent = read(parent_path)
previous = Path(parent['snapshot']) / 'current_repair_main.tex'
assert not e.exists()
assert sha(p / 'current_repair_main.tex') == sha(previous)
receipt_path = D / 'BNN_timing03_balanced_receipt_01/completion.json'
receipt = read(receipt_path)
assert receipt['passed'] and receipt['paired_cost_observation_available']
assert receipt['independent_new_inputs'] == 0
assert all(sha(f) == h for f, h in receipt['source_sha256'].items())
comparison_path = D / 'BNN_interleaved_timing_03/comparison.json'
comparison = read(comparison_path)
assert comparison['paired_cost_observation_available']
assert all(r['same_role_exact'] and all(g['byte_exact'] for g in r['graph_payloads'])
           and r['own_root_endpoints']['compatible'] for r in comparison['rows'].values())
assert all(x['matched_initial_state'] and x['endpoint_comparison_available'] for x in comparison['pairs'])
old = previous.read_text()
changes = []


def replace(before, after):
    global old
    assert old.count(before) == 1, before
    changes.append([before, after])
    old = old.replace(before, after)


replace('Matched complete BNN flows reach 13.228146 ns in 7933.25/9754.31 s:',
        r'Symmetric N/D/D/N repeats reach 13.228146 ns with native/domain mean complete times 7308.61/9129.25 s (24.91\% overhead):')
replace('N/D: native/domain-first. Hybrid-O except eltwise topology rows; seeds vary by input.',
        'N/D: native/domain-first. Balanced rows: two complete repeats per arm, mean time and maximum sampled PSS. Hybrid-O except eltwise topology rows; seeds vary by input.')
historical = [line for line in old.splitlines() if line.startswith(('BNN index N&', 'BNN stream N&', 'BNN stream D&'))]
assert len(historical) == 3
rows = []
for role in ['native', 'domain']:
    selected = [r for r in receipt['rows'] if r['arm'].startswith(role + '_')]
    assert len(selected) == 2
    quality = comparison['rows'][role + '_0']['quality']
    assert quality == comparison['rows'][role + '_1']['quality']
    own = comparison['rows'][role + '_0']['own_root_endpoints']
    assert own == comparison['rows'][role + '_1']['own_root_endpoints']
    rows.append('BNN balanced ' + ('N' if role == 'native' else 'D') +
                f"&{quality['CPD_ns']:.6f}&{quality['wirelength']}/{quality['SB_pairs']}/{quality['CB_sources']}" +
                f"&{receipt[role + '_mean_seconds']:.2f}&{max(r['sampled_tree_PSS_peak_kib'] for r in selected)/1024**2:.3f}" +
                f"&{own['setup_improved']}/{own['setup_regressed']}/{own['hold_violation_regressions']}" + r'\\')
replace('\n'.join(historical), '\n'.join(rows))
replace('Table~\\ref{tab:completecost} retains 36 terminal attempts (four routing failures, four loading failures, two initial execution timeouts), nine infrastructure failures in two grouped rows, and five scoped components.',
        'Table~\\ref{tab:completecost} has 35 terminal rows representing 37 attempts, including four routing failures, four loading failures, two initial timeouts and four balanced repeats in two summary rows. Nine infrastructure failures remain in two grouped rows, plus five scoped components. Three earlier BNN engineering rows move intact to the supplement.')
before = ('Single-pass indexing preserves BNN graph payloads, states, requests and native work at 7463.17 versus 7933.25 s. '
          'Metadata reuse/streaming preserves native execution at 7247 s (qualified GNU-time; observer/PSS lost, brief overlap). '
          'The same changes preserve domain states, requests, work and full vectors at 9116.40 versus 9754.31 s, '
          r'a descriptive 637.92-s/6.54\% reduction; sampled PSS is 11.067 GiB with 28 missing observations. '
          'This establishes behavior preservation, not statistical acceleration or an optimized N/D ratio. '
          r'Original matched overhead remains 22.95\%; symmetric interleaving is running.')
after = (r'Behavior-preserving indexing/streaming observations, including the qualified 7247-s GNU-time run, remain supplementary. '
         r'With identical engineering, serial N/D/D/N gives mean complete times 7308.61/9129.25 s: ratio 1.24911, or 24.91\% domain overhead. '
         r'Paired ratios are 1.24796/1.25026. Same-role trajectories, full requests, native work and six actual graph payloads match; '
         r'paired fresh roots/full endpoint vectors match, with compatible final endpoint comparisons. '
         r'Missing memory observations are 22/28/27/29 in registered order. Four whole repeats add no independent input. '
         r'Two observations per arm on a shared host with uncontrolled OS caches support descriptive costs only. '
         r'The original 22.95\% overhead is retained as a separate historical observation; no component times are summed or observer CPU subtracted.')
replace(before, after)
replace('Fourteen later terminal attempts, nine infrastructure failures and five scoped components lie outside those counts.',
        'Fourteen later terminal attempts, four balanced timing repeats, nine infrastructure failures and five scoped components lie outside those counts.')
replace('Each panel has its own scale; lower is better for that metric. Nine development configuration pairs are not nine independent inputs;',
        'Each panel has its own scale; lower is better for that metric. The BNN bar uses the original cold pair; balanced repeats are reported separately. Nine development configuration pairs are not nine independent inputs;')
e.mkdir()
source = p / 'current_repair_balanced_cost_19.tex'
assert not source.exists()
source.write_text(old)
shutil.copy2(D / 'BNN_timing03_balanced_receipt_01/whole_costs.csv', e / 'whole_costs.csv')
write(e / 'historical_engineering_rows.json', dict(rows=historical, retained_parent=str(parent_path),
      removed_from_main_not_discarded=True, costs_and_observer_qualifications_unchanged=True))
write(e / 'cost_matching_scope.json', dict(
    passed=True, registered_order=receipt['registered_order'], rows=receipt['rows'], pairs=receipt['pairs'],
    paired_ratios=receipt['pair_domain_over_native_ratios'], ratio_of_arm_means=receipt['ratio_of_arm_means'],
    all_matching_gates_passed=True, independent_new_inputs=0, historical_22_95_percent_retained=True,
    prior_art_and_contribution_boundaries_unchanged=True,
    new_CP1r3_outcomes_in_paper=0, external_router_comparison_added=False,
    statistical_speedup_established=False, whole_costs_are_not_component_sums=True,
    source_sha256={str(f): sha(f) for f in [receipt_path, comparison_path,
        D / 'BNN_timing03_balanced_claim_binding_01.json']}))
assert len(changes) == 7
restored = source.read_text()
for before, after in reversed(changes):
    assert restored.count(after) == 1
    restored = restored.replace(after, before)
assert restored == previous.read_text()
def table_rows(text):
    return [line for line in text.splitlines() if line.count('&') == 5 and not line.startswith('Circuit/role')]
assert len(table_rows(previous.read_text())) == 43 and len(table_rows(source.read_text())) == 42
write(e / 'edit_registration.json', dict(
    registered_at=datetime.now(timezone.utc).isoformat(), parent=str(parent_path), source=str(source),
    changes=changes, previous_table_rows=43, new_table_rows=42, terminal_display_rows=35,
    represented_terminal_attempts=37, balanced_summary_rows=2, actual_balanced_measurements=4,
    moved_historical_engineering_rows=3, new_independent_inputs=0, new_native_or_STA_calls=0,
    prior_art_and_contribution_text_unchanged=True, canonical_source_not_yet_promoted=True,
    source_sha256={str(f): sha(f) for f in [Path(__file__).resolve(), parent_path, previous,
        source, e / 'cost_matching_scope.json', e / 'historical_engineering_rows.json', e / 'whole_costs.csv']}))
print(dict(source=str(source), changed_passages=len(changes), table_rows=42,
           new_independent_inputs=0, canonical_promoted=False))
