#!/usr/bin/env python3
"""Terminal current-STA evidence and exclusive cost categories, without rerunning anything."""
import collections
import math
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from endpoint_timing_policy_streaming_v2 import compare
from run_native_scope_policy_v4 import run_dir

out = D / 'resource_first_timing_terminal_summary_01.json'
assert not out.exists()
b = D / 'resource_first_timing_resume_01/timing'
terminal = read(b / 'completion.json')
queue_terminal = read(b.parent / 'queue/completion.json')
assert terminal['passed'] and queue_terminal['passed']
assert all(sha(path) == h for path, h in terminal['source_sha256'].items())
steps = read(b / 'steps.json')
assert len(steps) == 3 and all(row['accepted'] for row in steps)
original = Path(terminal['initial_state'])
final = Path(terminal['final_state'])
av, bv = read(original / 'endpoint_vector.json'), read(final / 'endpoint_vector.json')
comparison = compare(av, bv)
finite = {k: v for k, v in av['setup'].items() if isinstance(v, (int, float)) and math.isfinite(v)}
worst = min(finite.values())
near = {k for k, v in finite.items() if v <= worst + .05 * av['cpd_s']}
costs = read(b / 'process_costs.json')
categories = collections.Counter()
for row in costs:
    tag = row['tag']
    category = ('native_transaction_coordinators_including_build_load_replace_audit_STA' if tag.endswith('_native') else
                'transaction_preparation' if tag.endswith('_prepare') else
                'current_STA_target_selection' if tag.endswith('_current_STA_selection') else
                'query_owner_dependency_and_portfolio_processes')
    categories[category] += row['complete_process_seconds']
native_details = []
for step in steps[1:]:
    tx = Path(step['evaluation']).parent
    audit = read(tx / 'current_group_audit/analysis.json')
    nested = read(tx / 'process_costs.json')
    native_details.append(dict(round=step['round'], native_transaction_seconds=audit['native_transaction_seconds'],
        connection_query_seconds=sum(q['seconds'] for q in audit['queries']), nested_processes=nested,
        timing='Nested inside the top-level native coordinator category; do not add these again. Native source observation plus separate candidate FULL/STA are older backend processes.'))
files = [Path(__file__).resolve(), b / 'completion.json', b.parent / 'queue/completion.json',
    b / 'steps.json', b / 'attempts.json', b / 'process_costs.json', D / 'resource_first_composition_01.json',
    D / 'multiobjective_archive_50/completion.json', original / 'endpoint_vector.json', final / 'endpoint_vector.json']
write(out, dict(passed=True, local_operator_stop=terminal['operator_stop'], research_goal_still_active=True,
    accepted_steps=3, attempted_proposals=terminal['attempted_proposals'], steps=steps,
    CPD_before_ns=av['cpd_s'] * 1e9, CPD_after_ns=bv['cpd_s'] * 1e9,
    actual_resources=terminal['final_resources'], whole_endpoint_comparison=comparison,
    fixed_source_near_band=dict(rule='source slack <= source worst slack +0.05*sourceCPD; diagnostic only',
        components=len(near), improved=sum(bv['setup'][k] > av['setup'][k] for k in near),
        regressed=sum(bv['setup'][k] < av['setup'][k] for k in near)),
    exclusive_resume_top_level_process_seconds=dict(categories),
    coordinator_and_unclassified_seconds=terminal['complete_current_segment_seconds'] - sum(categories.values()),
    measured_resume_segment_seconds=terminal['complete_current_segment_seconds'],
    original_interrupted_segment_seconds=read(D / 'resource_first_timing_dev_01/timing/completion.json')['complete_current_segment_seconds'],
    original_failure='transaction_preparation_failed, observer/runtime provenance incorrectly in anchor equality; source/input guards subsequently corrected in independent recovery',
    nested_native_transactions=native_details, complete_single_configuration_algorithm_seconds=None,
    source_sha256={str(path): sha(path) for path in files}, native_calls=0, query_calls=0,
    qualification='Finished registered local portfolio after3actual strictCPD/fixed-resource accepts. This is not an exhaustive timing search or overall research completion. Current static-switch reference supports prioritizing resources/runtime/other scopes instead of only more queries in this winning cone. Original failed segment, resumed segment, reused prefixes, parent/native cores and native observations remain separate; their sum is not a cold full configuration time.'))
print(dict(CPD_ns=bv['cpd_s'] * 1e9, near_components=len(near),
    setup_improved=comparison['setup_improved'], setup_regressed=comparison['setup_regressed'],
    resume_seconds=terminal['complete_current_segment_seconds'], exclusive_seconds=dict(categories)), flush=True)
