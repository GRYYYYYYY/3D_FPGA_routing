"""Append one fixed reduction pair after the existing domain engineering arm."""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

root = D / 'portable_reduction_pair_01'
plan = read(root / 'plan.json')
q = root / 'queue'
q.mkdir(exist_ok=False)
lock = (q / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
bound = {str(root / 'plan.json'): sha(root / 'plan.json'),
         str(Path(__file__).resolve()): sha(Path(__file__).resolve())}
write(q / 'registration.json', dict(**process_identity(os.getpid()), source_sha256=bound,
    fixed_order=plan['fixed_order'], qualification='Single owner; admission and native execution remain deferred until all existing registered work.'))
try:
    predecessor = Path(plan['predecessor'])
    identity = read(predecessor / 'registration.json')
    while not (predecessor / 'completion.json').exists():
        actual = process_identity(identity['pid'])
        assert actual and actual['state'] != 'Z' and actual['start_ticks'] == identity['start_ticks'], 'Predecessor missing without terminal receipt; reconcile descendants'
        write(q / 'status.json', dict(status='waiting_for_registered_domain_engineering_arm', predecessor=str(predecessor)))
        time.sleep(15)
    prior = read(predecessor / 'completion.json')
    assert prior['passed'] and prior['status'] == 'registered_domain_engineering_terminal'
    whole = read(Path(plan['whole_method_prerequisite']) / 'completion.json')
    assert whole['passed'] and whole['status'] == 'registered_whole_method_execution_terminal', 'Portable whole-method prerequisite failed; roles remain unexecuted'
    serial = (D / 'critical_scope_runner.lock').open('r')
    write(q / 'status.json', dict(status='waiting_for_shared_serial_slot'))
    fcntl.flock(serial, fcntl.LOCK_EX)
    assert all(sha(path) == digest for path, digest in bound.items())
    assert all(sha(path) == digest for path, digest in plan['source_sha256'].items())
    for stage, script in [('admitting_inputs', 'admit_portable_reduction_pair_01.py'),
                          ('running', 'run_portable_reduction_pair_01.py')]:
        with (q / (stage + '.log')).open('x') as log:
            child = subprocess.Popen([sys.executable, str(D / script)], stdout=log, stderr=subprocess.STDOUT)
            write(q / 'status.json', dict(status=stage, **process_identity(child.pid)))
            code = child.wait()
        assert code == 0, stage + ' requires reconciliation; no automatic repeat'
    assert read(root / 'comparison.json')['passed']
    write(q / 'completion.json', dict(passed=True, status='registered_pair_terminal',
        source_sha256=bound, comparison=str(root / 'comparison.json'),
        qualification='Both roles accounted for, including failed/no-gain/worse outcomes; not a research stopping condition.'))
    write(q / 'status.json', dict(status='terminal'))
except Exception as error:
    write(q / 'completion.json', dict(passed=False, status='reconciliation_required', error=repr(error), source_sha256=bound))
    write(q / 'status.json', dict(status='reconciliation_required', error=repr(error)))
    raise
