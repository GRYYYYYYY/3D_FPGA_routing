"""Replay actual policy choices; check rejection/failure paths before native execution."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from resource_policy_scheduling_v1 import execution_order,accepted_resource_role,skip_optional_native

roots=[D/n for n in ['complete_serial_seed_policy_dev_01/native_seed_paired/flow/repair',
    'complete_serial_seed_policy_dev_01/delay_seed_native/flow/repair',
    'complete_serial_seed_policy_dev_01/delay_seed_paired/flow/repair',
    'stable_seed_transfer_dev_01/eltwise_A0_paired','stable_seed_transfer_dev_01/bnn_A0_paired',
    'stable_seed_transfer_recovery_01/bnn_R1_paired','stable_seed_transfer_recovery_02/bnn_Tf_paired']]
out=D/'lazy_resource_scheduling_validation_01'
assert not (out/'completion.json').exists()
if out.exists():assert not list(out.iterdir()), 'An earlier empty read-only attempt may be resumed'
out.mkdir(exist_ok=True)
files=[Path(__file__).resolve(),D/'resource_policy_scheduling_v1.py'];rows=[]
for actor in roots:
    closed=read(actor/'completion.json');assert closed['passed']
    for f,h in closed['source_sha256'].items():assert sha(f)==h
    files += [actor/'completion.json',actor/'attempts.json']
    for attempt in read(actor/'attempts.json'):
        tx=Path(attempt['transaction']) if 'transaction' in attempt else actor/f"round_{attempt['round']:03d}"/f"candidate_{attempt['candidate_rank']:02d}"
        roles=read(tx/'registration.json')['roles']
        if 'pair' in attempt:
            observed={}
            for name,row in attempt['pair'].items():
                decision=read(tx/(name+'_decisions.json'))
                assert row['status']==decision['status']
                if row['status']=='legal_evaluated':
                    assert row['accepted']==decision['accepted']==decision['decision']['accepted']
                    observed[name]=dict(row,policies=dict(resources_under_timing=decision['decision']))
                else:observed[name]=row
                files.append(tx/(name+'_decisions.json'))
        else:observed=read(tx/'progress.json')
        assert all(r['status'] in ['legal_evaluated','transaction_failed_rolled_back'] for r in observed.values())
        expected=next((name for name in ['reuse_on','reuse_off'] if observed.get(name,{}).get('status')=='legal_evaluated' and observed[name]['policies']['resources_under_timing']['accepted']),None)
        computed={};skipped=[]
        for name in execution_order(roles):
            if skip_optional_native(name,computed):skipped.append(name)
            else:computed[name]=observed[name]
        assert accepted_resource_role(computed)==expected
        if expected:assert attempt['committed_evaluation']==observed[expected]['evaluation']
        else:assert not attempt.get('committed_evaluation')
        rows.append(dict(transaction=str(tx),winner=expected,executed_roles=list(computed),optional_native_skipped=bool(skipped)))
        files.append(tx/'registration.json')
        if (tx/'progress.json').exists():files.append(tx/'progress.json')

# An accepted ON must be a complete legal candidate. Rejection, failed search,
# or execution errors cannot be used as an acceptance shortcut.
def legal(value):return dict(status='legal_evaluated',policies=dict(resources_under_timing=dict(accepted=value)))
guards=[]
for status in ['transaction_failed_rolled_back','native_or_candidate_audit_failed','FULL_STA_failed','running']:
    row=dict(status=status,policies=dict(resources_under_timing=dict(accepted=True)))
    assert not skip_optional_native('reuse_off',{'reuse_on':row});guards.append(status)
for on in [legal(False),dict(status='transaction_failed_rolled_back')]:
    assert not skip_optional_native('reuse_off',{'reuse_on':on})
    assert accepted_resource_role({'reuse_on':on,'reuse_off':legal(True)})=='reuse_off'
assert skip_optional_native('reuse_off',{'reuse_on':legal(True)})
assert not skip_optional_native('reuse_on',{'reuse_on':legal(True)})
write(out/'completion.json',dict(passed=True,native_calls_new=0,actual_scope_replays=len(rows),
    optional_native_controls_not_needed=sum(r['optional_native_skipped'] for r in rows),
    actual_ON_reject_or_fail_windows=sum(r['executed_roles']==['reuse_on','reuse_off'] for r in rows),
    actual_OFF_fallback_winners=sum(r['winner']=='reuse_off' and 'reuse_on' in r['executed_roles'] for r in rows),
    invalid_acceptance_shortcuts_rejected=guards,all_existing_policy_choices_preserved=True,rows=rows,
    source_sha256={str(f):sha(f) for f in files},
    qualification='Recorded current-source decisions replayed without predicting runtime or fabricating omitted OFF candidates. Domain-first accepted winner is unchanged; actual native reexecution and complete flow remain required. Guard/fallback unit cases are separate from observed trajectory windows and are not additional benchmark samples. All prior matched native/domain controls remain archived.'))
print(dict(passed=True,scopes=len(rows),optional_controls=sum(r['optional_native_skipped'] for r in rows)),flush=True)
