"""Replace only six proven-unexecuted waiting owners; preserve the live BNN chain."""
import os,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from confirmation_priority_waiter_guard_02 import check

root=D/'confirmation_priority_handoff_04';plan=read(root/'plan.json');validation=read(root/'validation.json')
assert validation['passed'] and not (root/'completion.json').exists()
assert all(sha(p)==h for p,h in validation['source_sha256'].items())
assert all(sha(p)==h for p,h in plan['protected_source_sha256'].items())
active=plan['active_predecessor_identity'];actual=process_identity(active['pid']);assert actual and actual['state']!='Z' and actual['start_ticks']==active['start_ticks']
assert not (Path(plan['active_predecessor'])/'completion.json').exists()
for path,row in plan['revisions'].items():assert sha(path)==row['sha256']
supp_active=plan['active_supplemental_identity'];observed=process_identity(supp_active['pid']);assert observed and observed['start_ticks']==supp_active['start_ticks'] and observed['state']!='Z'
fds=[];stopped=[];terminated=[];launched=[];phase='preflight'
try:
    # Open stable kernel process handles, then recheck the exact registration,
    # command, waiting status, absence of children and absence of method output.
    for node in plan['stages']:
        check(node);fd=os.pidfd_open(node['pid']);check(node);fds.append((node,fd))
    phase='quiescing_unexecuted_waiters'
    for node,fd in fds:
        check(node);signal.pidfd_send_signal(fd,signal.SIGSTOP);stopped.append((node,fd))
    deadline=time.monotonic()+10
    for node,fd in stopped:
        while True:
            p=process_identity(node['pid']);assert p and p['start_ticks']==node['start_ticks']
            if p['state'] in ['T','t']:break
            assert time.monotonic()<deadline;time.sleep(.02)
        check(node,require_running=False)
    write(root/'quiesced_waiters.json',dict(passed=True,owners=[dict(batch=n['batch'],pid=n['pid'],start_ticks=n['start_ticks'],no_children=True,no_method_output=True) for n,fd in stopped],active_CP1r3_untouched=True))
    phase='terminating_superseded_waiters'
    for node,fd in stopped:
        signal.pidfd_send_signal(fd,signal.SIGTERM);signal.pidfd_send_signal(fd,signal.SIGCONT)
    deadline=time.monotonic()+10
    for node,fd in stopped:
        while True:
            p=process_identity(node['pid'])
            if not p or p['state']=='Z' or p['start_ticks']!=node['start_ticks']:break
            assert time.monotonic()<deadline;time.sleep(.02)
        terminated.append(node['batch'])
    # These are explicit cancellation receipts, never successful predecessor or
    # historical experiment completions. Original registrations remain intact.
    phase='recording_unexecuted_cancellations'
    for node,fd in stopped:
        q=Path(node['old_queue']);assert not (q/'completion.json').exists()
        write(q/'completion.json',dict(passed=False,status='superseded_before_execution_for_confirmation_priority',
            reason='Remaining raw admission now follows original-check replay before historical recovery; this development waiter had no children or method output.',
            replacement_queue=node['new_queue'],handoff_plan=str(root/'plan.json'),native_calls_new=0,
            algorithm_or_input_changes=False,old_pid=node['pid'],old_start_ticks=node['start_ticks'],old_registration_sha256=node['old_registration_sha256'],
            is_experiment_completion=False,is_successful_predecessor=False))
        write(q/'status.json',dict(status='superseded_unexecuted_waiter',replacement_queue=node['new_queue'],native_calls_new=0))
    phase='starting_priority_owners'
    supplementary=Path(plan['supplemental_wrapper']);sq=D/'CP1r3_raw_admission_01/queue_priority_04'
    assert sha(supplementary)==plan['supplemental_sha256'] and not sq.exists()
    with (root/'supplemental_owner.log').open('x') as log:
        sp=subprocess.Popen([sys.executable,'-B',str(supplementary)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    until=time.monotonic()+30
    while not (sq/'registration.json').exists():
        assert sp.poll() is None and time.monotonic()<until;time.sleep(.05)
    sr=read(sq/'registration.json');actual=process_identity(sr['pid'])
    assert actual and actual['state']!='Z' and actual['start_ticks']==sr['start_ticks']
    write(root/'supplemental_owner.json',dict(queue=str(sq),**actual))
    for node in plan['stages']:
        q=Path(node['new_queue']);assert not q.exists()
        with (Path(node['old_queue']).parent/'priority_04_owner.log').open('x') as log:
            child=subprocess.Popen([sys.executable,'-B',node['wrapper']],stdout=log,stderr=subprocess.STDOUT,
                start_new_session=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        deadline=time.monotonic()+30
        while not (q/'registration.json').exists():
            assert child.poll() is None,(node['batch'],'Replacement startup failed')
            assert time.monotonic()<deadline,(node['batch'],'Replacement registration missing');time.sleep(.05)
        reg=read(q/'registration.json');p=process_identity(reg['pid'])
        assert p and p['state']!='Z' and p['start_ticks']==reg['start_ticks']
        assert str(root/'plan.json') in reg['source_sha256'] and reg['source_sha256'][str(root/'plan.json')]==sha(root/'plan.json')
        launched.append(dict(batch=node['batch'],queue=str(q),pid=reg['pid'],start_ticks=reg['start_ticks'],predecessor=node['predecessor']))
    assert len(launched)==len(terminated)==4
    assert all(sha(p)==h for p,h in plan['protected_source_sha256'].items())
    for path,row in plan['revisions'].items():assert sha(path)==row['sha256']
    write(root/'completion.json',dict(passed=True,status='confirmation_priority_handoff_applied',
        old_unexecuted_owners_cancelled=terminated,new_owners=launched,active_CP1r3_order_unchanged=True,
        confirmation_protocol_inputs_and_method_rules_unchanged=True,historical_completion_fabricated=False,
        native_calls_by_handoff=0,source_sha256=validation['source_sha256'],research_complete=False))
    print(dict(passed=True,replaced_waiters=4,raw_admission_immediately_after_supplement=True,native_calls_by_handoff=0))
except Exception as error:
    # Before termination, return any stopped owner to its previous wait. After
    # termination, preserve the exact partial handoff for explicit reconciliation.
    if phase=='quiescing_unexecuted_waiters':
        for node,fd in stopped:
            try:signal.pidfd_send_signal(fd,signal.SIGCONT)
            except ProcessLookupError:pass
    write(root/'failure.json',dict(passed=False,phase=phase,error=repr(error),terminated=terminated,launched=launched,no_native_retry=True))
    raise
finally:
    for node,fd in fds:os.close(fd)
