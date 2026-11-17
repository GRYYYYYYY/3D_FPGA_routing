"""Describe already-admitted complete trajectories; no new audit framework or search."""
import collections
import csv
import fcntl
import hashlib
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

out=D/'LSTM_admitted_mechanism_synthesis_01'
assert not out.exists()
lock=(D/'critical_scope_runner.lock').open('r');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
started=time.monotonic();out.mkdir();sources={}
def document(path,expected=None):
    p=Path(path).resolve();digest=sha(p)
    if expected is not None:assert digest==expected,p
    sources[str(p)]=digest
    return read(p)
decision=document(D/'LSTM_domain_whole_admission_03/admission_decision.json')
assert decision['domain_whole_arm_admission']==decision['complete_pair_admission']=='passed'
proofs={a:document(p) for a,p in dict(native=D/'LSTM_necessary_readonly_02/native_raw/completion.json',
                                    domain=D/'LSTM_domain_whole_admission_03/raw/completion.json').items()}
for x in proofs.values():assert x['passed'] and x['quality_admitted']
states={a:{x['state']:x for x in document(p)} for a,p in dict(
    native=D/'LSTM_necessary_readonly_02/native_raw/states.json',
    domain=D/'LSTM_domain_whole_admission_03/raw/states.json').items()}
scope_chain=document(D/'LSTM_domain_whole_admission_03/state_transition_observation.json')
rows=[];step_rows=[];phase_rows=[];features={};skips=[]
axes=['wirelength','SB_pairs','CB_sources']
for arm in ['native','domain']:
    proof=proofs[arm];flow=Path(proof['initial']['state']).parents[1];repair=flow/'resource_flow/repair'
    # initial is flow/resource_flow/initial; the parent above is flow.
    attempts=document(repair/'attempts.json');steps=document(repair/'steps.json')
    reg=document(repair/'registration.json');cap=reg['resource_limits']['wirelength']
    selection=document(repair/'round_000/selection/completion.json')
    features[arm]=dict(initial_eligible_scopes=selection['candidate_scopes'],
        multi_crossing_nets=selection['multi_crossing_nets'],minimum_margin_s=selection['minimum_margin_s'],
        fixed_resource_limits=reg['resource_limits'],fixed_CPD_s=reg['anchor']['CPD_s'])
    for attempt in attempts:
        tx=Path(attempt['transaction']);registration=document(tx/'registration.json',proof['source_sha256'][str(tx/'registration.json')])
        for role,row in attempt['roles'].items():
            if row['status']=='not_executed_domain_candidate_accepted':
                skips.append(dict(arm=arm,transaction=str(tx),role=role,status=row['status']));continue
            control=states[arm][str(tx/role)];log=Path(control['run'])/'joint_native.log'
            b=log.read_bytes();digest=hashlib.sha256(b).hexdigest();assert digest==proof['source_sha256'][str(log)]
            sources[str(log)]=digest;lines=b.decode().splitlines()
            releases=[list(map(int,line.split()[1:])) for line in lines if line.startswith('DOMAIN_RELEASE ')]
            if role=='reuse_on':
                ap=tx/'reuse_on_domain_audit.json';audit=document(ap,proof['source_sha256'][str(ap)])
                assert audit['passed'] and releases==audit['released_queries']
            else:assert not releases
            failed=row['status']=='FULL_STA_failed'
            evaluation=tx/'reuse_on_evaluation' if failed else Path(row['evaluation'])
            state=states[arm][str(evaluation)];source=states[arm][registration['roles'][role]['state']]
            if failed:
                proof_failed=document(D/'LSTM_necessary_readonly_02/domain_failed_evaluation/audit.json')
                ep=proof_failed['endpoints'];resource_accept=False;reason='Historical FULL_STA_failed; original policy never evaluated. Independent raw evidence shows wire over cap357.'
            else:
                policies=document(tx/(role+'_decisions.json'))
                ep=policies['endpoint_vector']['comparison'];resource_accept=policies['resources_under_timing']['accepted'];reason=policies['resources_under_timing']['reason']
            metrics=state['resources'];committed=attempt.get('accepted_role')==role
            assert not failed or not committed
            record=dict(id=arm+'/'+str(tx.relative_to(repair))+'/'+role,arm=arm,role=role,
                transaction=str(tx),evaluation=str(evaluation),original_status=row['status'],
                raw_route_evidence_passed=True,original_resource_policy_evaluated=not failed,
                original_resource_policy_accepted=resource_accept,original_reason=reason,
                committed=committed,CPD_ns=state['CPD_ns'],**metrics,
                wire_delta_from_root=metrics['wirelength']-proof['initial']['resources']['wirelength'],
                remaining_wire_budget_before=cap-source['resources']['wirelength'],
                over_wire_cap=max(0,metrics['wirelength']-cap),
                release_events=releases,release_event_count=len(releases),
                query_count=sum(x.startswith('QUERY ') for x in lines),
                attempt_count=sum(x.startswith('ATTEMPT ') for x in lines),
                source_resource_delta={k:metrics[k]-source['resources'][k] for k in axes},
                own_source_endpoint_summary={k:v for k,v in ep.items() if k!='changes'},
                candidate_route_body_sha256=state['route_body_sha256'])
            rows.append(record)
            if committed:step_rows.append(record)
    actual_steps=[r for r in step_rows if r['arm']==arm]
    assert len(actual_steps)==len(steps)
    for group,names in [('guided',['reuse_on']),('native_fallback',['reuse_off']),('owner',['joint_native'])]:
        chosen=[r for r in actual_steps if r['role'] in names]
        phase_rows.append(dict(arm=arm,phase=group,accepted_steps=len(chosen),
            delta={k:sum(r['source_resource_delta'][k] for r in chosen) for k in axes},
            accepted_steps_with_release=sum(bool(r['release_events']) for r in chosen),
            release_events=sum(r['release_event_count'] for r in chosen)))
    before=states[arm][document(repair/'completion.json')['final_state']]
    phase_rows.append(dict(arm=arm,phase='terminal_and_timing',accepted_steps=None,
        delta={k:proof['final']['resources'][k]-before['resources'][k] for k in axes}))
    for k in axes:
        assert sum(r['delta'][k] for r in phase_rows if r['arm']==arm)==proof['final']['resources'][k]-proof['initial']['resources'][k]

assert features['native']==features['domain']
assert len(skips)==11
domain=[r for r in rows if r['arm']=='domain'];guided=[r for r in domain if r['role']=='reuse_on']
accepted_guided=[r for r in guided if r['committed']]
tail=[r for r in guided if not r['committed']]
assert len(accepted_guided)==11 and len(tail)==16
assert all(r['over_wire_cap']>0 for r in tail)
first=[next(r for r in rows if r['arm']==a and '/round_000/candidate_00/' in r['id']) for a in ['native','domain']]
first_scope=document(D/'LSTM_first_scope_mechanism_audit_01/completion.json')
assert first_scope['rows']['native']['request_sha256']==first_scope['rows']['domain']['request_sha256']
for arm,row in zip(['native','domain'],first):
    assert {k:row[k] for k in axes}==first_scope['rows'][arm]['original_candidate_resources']
same_source_first_delta={k:first[1][k]-first[0][k] for k in axes}
write(out/'candidate_rows.json',rows);write(out/'accepted_steps.json',step_rows);write(out/'phase_deltas.json',phase_rows)
write(out/'skipped_counterfactuals.json',skips)
with (out/'candidate_rows.csv').open('w',newline='') as f:
    fields=['id','original_status','original_resource_policy_evaluated','original_resource_policy_accepted','committed','CPD_ns',*axes,'remaining_wire_budget_before','over_wire_cap','release_event_count','query_count','attempt_count']
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
summary=dict(passed=True,scope='Retrospective description of already-admitted LSTM pair; not new runs, ablations or counterfactual complete flows.',
    same_source_first_scope_delta=same_source_first_delta,initial_features=features['native'],
    executed_role_observations=len(rows),historically_legal_evaluated=sum(r['original_status']=='legal_evaluated' for r in rows),
    original_FAILED_evaluation_retained=sum(r['original_status']=='FULL_STA_failed' for r in rows),
    guided_accepted_scopes=11,guided_accepted_scopes_with_release=sum(bool(r['release_events']) for r in accepted_guided),
    guided_accepted_release_events=sum(r['release_event_count'] for r in accepted_guided),
    guided_nonaccepted_scopes=len(tail),all_nonaccepted_guided_points_over_fixed_wire_cap=True,
    original_failed_guided_role_is_not_policy_rejection=True,
    total_guided_release_events=sum(r['release_event_count'] for r in guided),
    phases=phase_rows,skipped_same_source_native_counterfactuals=11,
    missing_matched_LSTM_no_release_control=True,complete_domain_minus_native=decision['domain_minus_native'],
    complete_time_ratio=None,interference_free_time_estimate=None,
    new_native_or_STA_calls=0,new_independent_inputs=0,submission07_unchanged=True,
    no_general_mechanism_scheduler_claim=True,complete_extraction_seconds=time.monotonic()-started,
    source_sha256={**sources,str(Path(__file__).resolve()):sha(Path(__file__).resolve())})
write(out/'completion.json',summary)
print({k:v for k,v in summary.items() if k not in ['source_sha256','phases']})
print(phase_rows)
