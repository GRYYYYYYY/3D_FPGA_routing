#!/usr/bin/env python3
"""Reject corrupted retained-prefix records; synthetic schema checks, not native validation."""
from analyze_retained_prefix import parse_trace
from retained_prefix_workflow import original_records

BASE = """H3D_PREFIX_TABLE plan=1 net=7 leaves=1 candidates=3 unit_seconds=1e-10
H3D_PREFIX_EXIT plan=1 net=7 entry=10 exit=11 component=4 parent_switch=2 tdel_seconds=3e-9 r_upstream=2 c_downstream=1e-15 re_expand=1
H3D_PREFIX_ENTRY plan=1 net=7 entry=10 owned=1 retained_exits=1 source_known=1 source_units=5 opening_units=21 occupancy=1 capacity=1 acc_cost=1 pres_fac=2 tdel_seconds=2e-9 r_upstream=1 c_downstream=1e-15 re_expand=1
H3D_PREFIX_ENTRY plan=1 net=7 entry=20 owned=1 retained_exits=0 source_known=0 source_units=6 opening_units=22 occupancy=1 capacity=1 acc_cost=1 pres_fac=2 tdel_seconds=2e-9 r_upstream=1 c_downstream=1e-15 re_expand=1
H3D_PREFIX_ENTRY plan=1 net=7 entry=30 owned=0 retained_exits=0 source_known=0 source_units=7 opening_units=23 occupancy=0 capacity=1 acc_cost=1 pres_fac=2 tdel_seconds=nan r_upstream=nan c_downstream=nan re_expand=0
H3D_PREFIX_REACH plan=1 net=7 pin=3 entry=10 exit=11 sink_view=1 reaches=1
H3D_PREFIX_PAIR plan=1 net=7 pin=3 entry=10 sink_view=1 reachable_exits=1 expandable_exits=1 best_exit_tdel_seconds=3e-9 branch_units=2 prior=1 proposed=1
H3D_PREFIX_PAIR plan=1 net=7 pin=3 entry=20 sink_view=1 reachable_exits=0 expandable_exits=0 best_exit_tdel_seconds=nan branch_units=3 prior=0 proposed=0
H3D_PREFIX_PAIR plan=1 net=7 pin=3 entry=30 sink_view=1 reachable_exits=0 expandable_exits=0 best_exit_tdel_seconds=nan branch_units=4 prior=0 proposed=0
H3D_PREFIX_DECISION plan=1 net=7 accepted=0 old_cost=20 new_cost=19.5
H3D_PREFIX_SKIP plan=2 net=8 reason=no_eligible_pins
"""
r = parse_trace(BASE.splitlines())
assert r['accepted_plans'] == 0 and r['skipped_plans'] == 1
assert r['counters']['owned_candidate_events'] == 2
assert r['counters']['retained_crossing_candidate_events'] == 1
assert r['counters']['retained_reachable_candidate_events'] == 1
assert r['leaf_events'] == r['leaves_with_retained_reachable_option'] == 1
bad = [
    BASE.replace('retained_exits=1', 'retained_exits=0'),
    BASE.replace('reachable_exits=1', 'reachable_exits=0'),
    BASE.replace('best_exit_tdel_seconds=3e-9', 'best_exit_tdel_seconds=2e-9'),
    BASE.replace('owned=0 retained_exits=0', 'owned=1 retained_exits=0'),
    BASE.replace('accepted=0', 'accepted=2'),
    BASE.replace('plan=2 net=8', 'plan=3 net=8'),
    BASE.replace('H3D_PREFIX_DECISION plan=1 net=7 accepted=0 old_cost=20 new_cost=19.5\n', ''),
    BASE + 'H3D_PREFIX_EXIT plan=1 net=7 entry=99 exit=98 component=4 parent_switch=2 tdel_seconds=3e-9 r_upstream=2 c_downstream=1e-15 re_expand=1\n',
]
for text in bad:
    try:
        parse_trace(text.splitlines())
    except (AssertionError, KeyError):
        pass
    else:
        raise AssertionError('Accepted corrupted trace')
assert original_records(['H3D_PLAN planning_seconds=1 plans=4']) == original_records(['H3D_PLAN planning_seconds=2 plans=4'])
assert original_records(['H3D_DELAY_INIT unit_seconds=1e-10']) != original_records(['H3D_DELAY_INIT unit_seconds=2e-10'])
assert original_records(['H3D_UNKNOWN physical_seconds=1e-10']) != original_records(['H3D_UNKNOWN physical_seconds=2e-10'])
print('PASS one synthetic mixed-ownership/rejected-plan example, eight corruption cases and physical-unit-preserving time normalization; native tests pending')
