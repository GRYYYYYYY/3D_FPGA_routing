"""Integrate the actually closed same-role BNN engineering observation."""
import re
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

p = D/'paper'
parent_path = D/'complete_tradeoff_paper_binding_10.json'
parent = read(parent_path)
previous = Path(parent['snapshot'])
r = D/'complete_BNN_domain_engineering_01'
c = r/'bnn_domain_closed_stream'
e = D/'BNN_engineering_paper_evidence_11'
assert not e.exists()
assert not (D/'BNN_engineering_paper_binding_11.json').exists()
assert sha(p/'current_repair_main.tex') == sha(previous/'current_repair_main.tex')
actual, comparison, equivalent, queue = [read(f) for f in [c/'completion.json', r/'comparison.json', r/'domain_downstream_equivalence.json', r/'queue/completion.json']]
assert actual['passed'] and comparison['passed'] and queue['passed']
assert comparison['same_role_execution_exact']
assert equivalent['initial']['full_endpoint_vector_exact'] and equivalent['final']['full_endpoint_vector_exact']
assert not comparison['optimized_pair_cost_ratio_established']
assert not comparison['stable_interleaved_timing_complete']
assert actual['complete_wall_seconds'] == comparison['actual_complete_seconds']
assert actual['resources'] == dict(wirelength=2061417, SB_pairs=43, CB_sources=5060)
assert comparison['complete_endpoint_comparisons']['historical_domain']['setup_regressed'] == 0
assert comparison['complete_endpoint_comparisons']['historical_domain']['setup_improved'] == 0
e.mkdir()
old = (previous/'current_repair_main.tex').read_text()
historical_row = 'BNN cold D&13.228146&2061417/43/5060&9754.31&11.063&547/820/0\\\\'
assert old.count(historical_row) == 1
row = f"BNN stream D&{actual['CPD_ns']:.6f}&2061417/43/5060&{actual['complete_wall_seconds']:.2f}&{actual['sampled_tree_PSS_peak_kib']/1048576:.3f}&547/820/0" + r'\\'
anchor = r'BNN stream N&13.228146&2059631/82/5062&7247$^{*}$&--&14/17/0\\'
assert old.count(anchor) == 1
new = old.replace(anchor, anchor+'\n'+row)
new = new.replace('The first 31 rows', 'The first 32 rows')
start = new.index('Single-pass indexing preserves all BNN graph payloads')
end = new.index('\n\nIn the original BNN pair', start)
paragraph = r'''Single-pass indexing preserves BNN graph payloads, downstream states, requests and native work at 7463.17 versus 7933.25 s. Adding same-flow metadata and streaming parsing preserves native execution at 7247 s (original integer-second GNU-time); its observer/PSS loss and brief overlap remain. The same engineering changes now preserve all original domain states, requests, native work, graph payloads and full endpoint vectors at 9116.40 versus 9754.31 s: 637.92 s (6.54\%) less in this single observation. Sampled peak PSS is 11.067 GiB with 28 missing observations. These same-input engineering results establish behavior preservation, not statistical acceleration or a new optimized domain/native ratio. The original matched 22.95\% overhead remains; stable symmetric interleaved timing is pending.'''
# Keep the table and prose rounded from the same measured receipt.
paragraph = paragraph.replace('11.067', f"{actual['sampled_tree_PSS_peak_kib']/1048576:.3f}")
new = new[:start]+paragraph+new[end:]
assert 'Nine new complete attempts and two scoped rows' in new
new = new.replace('Nine new complete attempts and two scoped rows', 'Ten new complete attempts and two scoped rows')
source = p/'current_repair_BNN_engineering_11.tex'
source.write_text(new)
write(e/'complete_engineering_row.json', dict(label='BNN stream D', quality=dict(actual['resources'], CPD_ns=actual['CPD_ns']),
    complete_seconds=actual['complete_wall_seconds'], PSS_peak_kib=actual['sampled_tree_PSS_peak_kib'],
    missing_memory_observations=actual['missing_memory_observations'], own_root_endpoints=dict(setup_improved=547,setup_regressed=820,hold_violation_regressions=0),
    endpoint_count_derivation='Historical complete domain row; actual initial and final full vectors independently verified exact by the closed comparator.',
    same_role_seconds_difference=comparison['descriptive_same_role_seconds_difference'],
    same_role_percent_difference=comparison['descriptive_same_role_percent_difference'],
    new_independent_inputs=0, new_optimized_pair_ratio=False))
sources = [parent_path, source, Path(__file__).resolve(), c/'completion.json', c/'measurement/completion.json', c/'metadata_consumers.json',
    r/'comparison.json', r/'domain_downstream_equivalence.json', r/'queue/completion.json', r/'queue/results.json',
    e/'complete_engineering_row.json']
write(e/'edit_registration.json', dict(parent=str(parent_path), source=str(source), new_complete_attempt_rows=1,
    complete_attempt_rows=32, scoped_rows=2, new_independent_inputs=0, native_calls_during_edit=0,
    source_sha256={str(f):sha(f) for f in sources},
    qualification='Actual same-input full engineering execution. Original historical pair and figure retained; no new independent confirmation or causal/statistical timing claim.'))
print(dict(source=str(source), new_table_row=row))
