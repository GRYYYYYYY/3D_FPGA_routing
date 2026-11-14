#!/usr/bin/env python3
"""Explain the actually selected first intervention before its native outcome."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

out=D/'low_resource_first_proposal_01.json';assert not out.exists()
feedback=D/'low_resource_dual_timing_02/strict/round_000/feedback'
plan=read(feedback/'proposal/plan.json');owners=read(feedback/'owners/completion.json')
capacity=read(feedback/'capacity/analysis.json');relaxed=read(feedback/'relaxed/analysis.json')
assert all(item['passed'] for item in [plan,owners,capacity,relaxed])
assert all(sha(path)==h for path,h in plan['source_sha256'].items())
assert plan['selection']['targets']==[[47878,2]]
assert plan['repair_pins']==[[47878,2],[57399,1],[57596,1],[66543,1]]
owner=next(row for row in owners['rows'] if row['target']==[47878,2])
assert all(row['all_current_slack_margins_positive'] for row in owner['owner_release_scope'])
other=next(row for row in owners['rows'] if row['target']==[26319,1])
assert any(row['net']==26320 and not row['all_current_slack_margins_positive'] for row in other['owner_release_scope'])
write(out,dict(passed=True,source_state=plan['source_state'],proposal=plan['selection'],
    actual_selected_targets=plan['selection']['targets'],actual_repair_pins=plan['repair_pins'],
    actual_native_query_order=plan['ordered_queries'],blocked_resources=owner['blocked_resources'],
    donor_margins=[dict(net=row['net'],pins=[dict(pin=p['pin'],slack_margin_ns=p['slack_margin_to_current_worst_s']*1e9)
                                           for p in row['affected_sink_pins']]) for row in owner['owner_release_scope']],
    capacity_feasible_positive_gaps=[{k:r[k] for k in ['net','pin','improvement_ns']}
        for r in capacity['results'] if r['improvement_ns']>0],
    relaxed_positive_but_capacity_blocked=[dict(net=r['net'],pin=r['pin'],improvement_ns=r['improvement_ns'])
        for r in relaxed['results'] if r['improvement_ns']>0 and not r['rr_capacity_feasible']],
    competing_critical_owner=dict(target=other['target'],critical_owner=26320,
        reason='Primary slack-funded action list excludes this target because an affected owner connection has zero margin; a later critical-owner exchange scope may still address it.'),
    new_native_or_query_calls=0,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),
        feedback/'proposal/plan.json',feedback/'owners/completion.json',feedback/'capacity/analysis.json',feedback/'relaxed/analysis.json']},
    qualification='Actual automatic planning/ownership evidence only. No native repair outcome, acceptance, final legality or CPD gain inferred from changed plan. The original and low-resource composition experiments continue.'))
print(dict(selected=plan['selection']['targets'],repair_connections=len(plan['repair_pins']),
           capacity_free_positive=[r['net'] for r in capacity['results'] if r['improvement_ns']>0]),flush=True)
