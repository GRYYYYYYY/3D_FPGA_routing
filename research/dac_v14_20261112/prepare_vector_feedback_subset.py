#!/usr/bin/env python3
"""Derive a new scope from rejected same-state evidence, not historical winners."""
import hashlib
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from critical_action_patterns import patterns,evaluate
from current_proposal_portfolio import request_text
from run_native_scope_policy_v4 import run_dir
import json

b=D/'vector_feedback_subset_01';b.mkdir(exist_ok=False)
actor=D/'low_resource_dual_timing_02/endpoint';terminal=read(actor/'completion.json')
assert terminal['passed'] and terminal['accepted_steps']==0
attempts=read(actor/'attempts.json');row=next(r for r in attempts if r['proposal']=='all_positive_combined')
state=Path(row['before_state']);assert not row['accepted'] and Path(terminal['initial_state'])==state
tx=Path(row['evaluation']).parent;audit_path=tx/'current_group_audit/analysis.json';audit=read(audit_path);assert audit['passed']
feedback=actor/'round_000/feedback';base=read(feedback/'proposal/plan.json');cone=read(feedback/'cone.json')
assert base['passed'] and cone['passed'] and Path(base['source_state'])==state
assert Path(cone['source_state'])==state
bad={(r['net'],r['pin']) for r in audit['changed_delays'] if r['after_s']>r['before_s']}
improved={(r['net'],r['pin']) for r in audit['changed_delays'] if r['after_s']<r['before_s']}
actions=base['actions'];safe=[i for i,a in enumerate(actions)
    if tuple(a['target']) in improved and not (set(map(tuple,a['donors']))&bad)]
assert safe
profile=evaluate(patterns(cone,actions),actions,safe)
pins=set(map(tuple,profile['repair_pins']));targets={tuple(actions[i]['target']) for i in safe}
sta={}
for line in (run_dir(state)/'native_sta_frontier.jsonl').open():
    r=json.loads(line)
    if r.get('type')=='pin' and (r['net'],r['pin']) in pins:
        sta[r['net'],r['pin']]=r
        if len(sta)==len(pins):break
assert sta.keys()==pins
ordered=sorted(targets,key=lambda key:(sta[key]['setup_slack_s'],key))+sorted(pins-targets)
files=[Path(__file__).resolve(),actor/'completion.json',actor/'attempts.json',audit_path,
    feedback/'proposal/plan.json',feedback/'cone.json',state/'completion.json',state/'endpoint_vector.json',
    run_dir(state)/'native_sta_frontier.jsonl',D/'critical_action_patterns.py',D/'current_proposal_portfolio.py']
plan=dict(passed=True,source_state=str(state),actions=[actions[i] for i in safe],
    selection=dict(status='same_state_rejected_candidate_feedback_subset',targets=sorted(targets),
        fraction=base['selection']['fraction'],profile=profile,
        rule='Keep targets that improved in the rejected aggregate and remove every action with an observed delay-increasing donor. Preserve the source; do not transplant a later accepted state.'),
    ordered_queries=[dict(net=n,pin=p,raw_criticality=sta[n,p]['setup_criticality_raw']) for n,p in ordered],
    repair_pins=sorted(pins),source_sha256={str(path):sha(path) for path in files},native_calls=0,accepted=False,
    qualification='New current-source feedback intervention. Observed aggregate donor monotonicity is only a proposal heuristic; occupancy/order can change in this smaller transaction. Fresh native whole replacement, FULL/STA, same full-vector rule and absolute caps are mandatory. No tolerance or near-endpoint relaxation.')
body=request_text(plan);digest=hashlib.sha256(body.encode()).hexdigest()
old_requests={}
for path in actor.glob('round_000/*portfolio*/portfolio.json'):
    for item in read(path)['proposals']:old_requests[item['request_sha256']]=item['name']
assert digest not in old_requests,'Already evaluated exact source/request; reuse instead of repeating'
write(b/'plan.json',plan)
write(b/'completion.json',dict(passed=True,source_state=str(state),selected_action_ids=safe,
    targets=sorted(targets),repair_pins=sorted(pins),observed_delay_increasing_connections=sorted(bad),
    predicted_current_path_profile=profile,new_request_sha256=digest,not_in_previous_exact_menu=True,
    native_calls=0,route_calls=0,source_sha256={str(b/'plan.json'):sha(b/'plan.json')},
    qualification='Mechanism-based scope preparation only. It separates harmful donors from small gains hidden by tied paths. Does not prove actual vector/CPD improvement or legal capacity after regrouping.'))
print(dict(targets=sorted(targets),repair_connections=len(pins),profile=profile),flush=True)
