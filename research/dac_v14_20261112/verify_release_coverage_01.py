"""Account every executed guided resource role, so missing audits cannot mean zero."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
root=D/'release_coverage_01';assert not root.exists();root.mkdir()
matrix=D/'mechanism_selection_evidence_01/pairs.json';rows=read(matrix);sources=[Path(__file__).resolve(),matrix];result=[]
for row in rows:
    actor=Path(row['domain']['actor']);done=read(actor/'completion.json');assert done['passed']
    sources += [actor/'completion.json',actor/'attempts.json']
    expected=set();events=0;queries=0;release_enabled_roles=0;roles=0
    for attempt in read(actor/'attempts.json'):
        tx=Path(attempt['transaction']);reg=read(tx/'registration.json');progress=read(tx/'progress.json')
        sources += [tx/'registration.json',tx/'progress.json']
        for name,r in reg['roles'].items():
            if not r.get('crossing_reuse_enabled'):continue
            status=progress[name]['status'];assert status in ['legal_evaluated','transaction_failed_rolled_back'],status
            audit=tx/(name+'_domain_audit.json');a=read(audit);assert a['passed'] and a['enabled']
            expected.add(str(audit.resolve()));sources.append(audit);roles+=1
            released=a.get('released_queries')
            if r.get('domain_failure_release'):
                assert released is not None,'Missing release trace audit cannot imply zero'
                release_enabled_roles+=1;events+=len(released)
            else:assert not released
            if 'queries' in r:queries+=len(r['queries'])
    observed={str(p.resolve()) for p in actor.glob('round_*/candidate_*/reuse_on_domain_audit.json')}
    assert expected==observed,(row['label'],expected^observed)
    assert events==row['domain']['observed_released_queries']
    result.append(dict(label=row['label'],guided_resource_roles=roles,release_enabled_roles=release_enabled_roles,
        registered_guided_connections=queries,audited_released_queries=events,all_executed_guided_roles_covered=True,
        zero_means_no_observed_release_event=True,not_a_flag_off_counterfactual=True))
by={x['label']:x for x in result}
assert by['BNN']['guided_resource_roles']==9 and by['BNN']['audited_released_queries']==0
assert by['Robot']['audited_released_queries']==5
write(root/'rows.json',result)
write(root/'completion.json',dict(passed=True,resource_configuration_contexts=10,all_executed_guided_roles_covered=True,
    BNN_resource_guided_roles=9,BNN_audited_release_events=0,robot_audited_release_events=5,
    new_native_calls=0,new_independent_inputs=0,source_sha256={str(p):sha(p) for p in sorted(set(sources))},
    qualification='Existing complete resource trajectories only. Every actual guided role has its passed domain/release audit; unavailable audit fields never become zero events. Counts describe executed mechanisms, not a new release-off whole-flow counterfactual or new independent trial. Registered connections are not attempt counts, total router calls or savings estimates.'))
print(dict(passed=True,BNN_guided_roles=9,BNN_release_events=0,robot_release_events=5))
