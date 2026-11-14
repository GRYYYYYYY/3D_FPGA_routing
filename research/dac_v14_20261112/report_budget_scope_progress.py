#!/usr/bin/env python3
"""Bind completed Tf and local-potential studies; do not run routing."""
from retained_prefix_workflow import D, read, write, sha

names = [
    'native_scope_Tf_summary_01.json',
    'current_sta_policy_native_Tf_01/initial_provenance_check.json',
    'timing_budget_ipin_reference_01/completion.json',
    'timing_budget_cbs_dev_01/completion.json',
    'finite_budget_assignment_dev_01/completion.json',
    'timing_budget_cut_certificate_01/completion.json',
    'budget_scope_larger_headroom_ref_01/completion.json',
    'budget_scope_larger_headroom_ref_01/scope_semantics_addendum.json',
    'budget_scope_larger_headroom_assignment_01/completion.json',
    'budget_scope_smaller_headroom_ref_01/completion.json',
    'budget_scope_smaller_headroom_assignment_01/completion.json',
    'source_budget_cut_certificate_01/completion.json',
    'timing_budget_matching_unit_validation_01.json',
    'timing_budget_cbs_unit_validation_01.json',
    'finite_capacity_assignment_unit_validation_01.json',
    'budget_cut_scope_alternatives_01.json',
    'budget_retained_scope_experiment_01.json',
    'current_sta_cross_circuit_spmv_experiment_01.json',
    'native_endpoint_spmv_dev_01/completion.json',
]
checked = {}
for name in names:
    obj = read(D/name)
    assert obj.get('passed', True), name
    for path, digest in obj.get('source_sha256', {}).items():
        if path not in checked:
            checked[path] = sha(path)
        assert checked[path] == digest, path
    checked[str(D/name)] = sha(D/name)
tf = read(D/names[0])['batches'][0]
rows = []
for decision in tf['decisions']:
    rows.append({k:decision[k] for k in ['policy', 'step', 'attempt', 'decision', 'comparison', 'largest_setup_losses']})
diagnostics = {}
for name in names:
    if name.endswith('/completion.json') and not name.startswith('native_endpoint'):
        obj = read(D/name)
        diagnostics[name.split('/')[0]] = {k:v for k,v in obj.items() if not isinstance(v, (dict,list))}
cut = read(D/'source_budget_cut_certificate_01/completion.json')
assert cut['source_only_cut_certified'] and len(cut['cut_agents']) > cut['cut_capacity']
assert all(q['stop'] == 0 and q['cost_s'] == q['lower_s'] for q in cut['queries'])
assert all(not q['strict_proxy_possible_avoiding_cut'] for q in cut['queries'] if q['kind']=='source_entry_cut')
assert all(q['physical_gain_s']==0 for q in cut['queries'] if q['kind']=='serial_root_only')
checked[str(D/'report_budget_scope_progress.py')] = sha(D/'report_budget_scope_progress.py')
out = dict(passed=True, research_complete=False, quality_promoted=False,
           Tf=dict(initial=tf['initial'], policies={p:{k:v for k,v in o.items() if k!='selection_history'} for p,o in tf['policies'].items()}, decisions=rows, costs=tf['costs'], child_status_counts=tf['child_status_counts']),
           diagnostics=diagnostics, source_only_cut={k:cut[k] for k in ['cut_nodes','cut_capacity','cut_agents','queries','qualification']},
           new_offline_distance_queries=330, exact_query_reuse_events=457,
           source_sha256=checked, public_snapshot='f7167bd', new_work_pushed=False,
           qualification='Only completed studies. Finite-pool failure and CBS limit are not graph infeasibility. Source-only certificate is a local fixed-terminal slack-offset result, not global STA optimality. No new native repair was launched for incompatible budget paths. Prototype costs are incremental and include rejected work; no historical U timing.',
           next_registered='current_sta_cross_circuit_spmv_experiment_01.json')
write(D/'budget_scope_progress_summary_01.json',out)
print(dict(passed=True, checked_files=len(checked), Tf_final={p:o['final']['cpd_ns'] for p,o in tf['policies'].items()}, source_only_cut=True))
