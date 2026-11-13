#!/usr/bin/env python3
"""Synthetic mechanism interpretation tests, not native trace validation."""
import json
import math
from analyze_retained_prefix_costs import summarize, distribution


def fixture(plan, accepted):
    lines = [f'H3D_PREFIX_TABLE plan={plan} net=7 leaves=1 candidates=6 unit_seconds=1e-10']
    for entry in [10,20,30,40,50,60]:
        owned = entry != 60
        children = [] if entry in [50,60] else [(entry+1,3e-9,0)]
        if entry == 10:
            children.append((entry+2,5e-9,1))
        for child,delay,expand in children:
            lines.append(f'H3D_PREFIX_EXIT plan={plan} net=7 entry={entry} exit={child} component=4 parent_switch=2 tdel_seconds={delay} r_upstream=2 c_downstream=1e-15 re_expand={expand}')
        prefix = f'H3D_PREFIX_ENTRY plan={plan} net=7 entry={entry} owned={int(owned)} retained_exits={len(children)} source_known={int(entry==10)} source_units=5 opening_units=21 occupancy={2 if entry==20 else int(owned)} capacity=1 acc_cost=1 pres_fac=2'
        lines.append(prefix + (' tdel_seconds=2e-9 r_upstream=1 c_downstream=1e-15 re_expand=1' if owned else ' tdel_seconds=nan r_upstream=nan c_downstream=nan re_expand=0'))
        view = int(entry != 40)
        reachable = entry in [10,20]
        for child,delay,expand in children:
            lines.append(f'H3D_PREFIX_REACH plan={plan} net=7 pin=3 entry={entry} exit={child} sink_view={view} reaches={int(reachable)}')
        best = '3e-9' if reachable else 'nan'
        lines.append(f'H3D_PREFIX_PAIR plan={plan} net=7 pin=3 entry={entry} sink_view={view} reachable_exits={len(children) if reachable else 0} expandable_exits={int(entry==10)} best_exit_tdel_seconds={best} branch_units=2 prior={int(entry==20)} proposed={int(entry==10)}')
    lines.append(f'H3D_PREFIX_DECISION plan={plan} net=7 accepted={accepted} old_cost=20 new_cost=19.5')
    return lines

r = summarize(fixture(1,0)+fixture(2,1))
assert len(r['candidate_events']) == 12
first = r['candidate_events'][0]
assert not first['accepted'] and first['proposed']
assert math.isclose(first['best_reachable_exit_seconds'],3e-9)
assert math.isclose(first['best_expandable_reachable_exit_seconds'],5e-9)
assert first['fastest_reachable_is_not_expandable']
assert math.isclose(first['direct_expandable_minus_best_reachable_seconds'],2e-9)
assert math.isclose(first['entry_tree_minus_source_units'],15)
assert first['opening_non_source_units'] == 16
assert [x['state'] for x in r['candidate_events'][:6]] == [
    'reachable_expandable_child','reachable_child_none_expandable',
    'crossing_child_not_reaching','crossing_child_view_unknown',
    'owned_no_crossing_child','not_owned']
assert r['candidate_events'][1]['entry_overused']
assert r['candidate_events'][1]['best_expandable_reachable_exit_seconds'] is None
assert r['candidate_events'][5]['entry_tree_minus_source_units'] is None
assert r['strata']['accepted=0 proposed=1 source_measured=1']['candidate_events'] == 1
assert r['strata']['accepted=1 proposed=1 source_measured=1']['candidate_events'] == 1
assert r['strata']['accepted=1 proposed=0 source_measured=0']['nets'] == 1
assert distribution([]) == dict(count=0,minimum=None,median=None,maximum=None)
assert distribution([3,1,2,4])['median'] == 2.5
json.dumps(r,allow_nan=False)
for text in [
    '\n'.join(fixture(1,0)).replace('unit_seconds=1e-10','unit_seconds=0'),
    '\n'.join(fixture(1,0)).replace('unit_seconds=1e-10','unit_seconds=nan'),
    '\n'.join(fixture(1,0)).replace('source_units=5','source_units=-1'),
]:
    try:
        summarize(text.splitlines())
    except AssertionError:
        pass
    else:
        raise AssertionError('invalid physical unit/cost accepted')
print('PASS six ownership/reach/expansion states, faster nonexpandable exit, accepted/rejected separation, measured/estimated separation, finite JSON, empty strata and three malformed unit/cost cases; synthetic only')
