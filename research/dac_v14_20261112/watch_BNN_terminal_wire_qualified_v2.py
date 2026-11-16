"""Wait on the real recovery owner, then audit under the shared serial lock."""
import fcntl, os, subprocess, sys, time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

root = D/'BNN_terminal_wire_qualified_comparison_02'; plan = read(root/'plan.json')
q = root/'analysis'; q.mkdir(exist_ok=False)
owner = (q/'owner.lock').open('w'); fcntl.flock(owner, fcntl.LOCK_EX|fcntl.LOCK_NB)
bound = {**plan['source_sha256'], str(root/'plan.json'):sha(root/'plan.json')}
assert read(D/'BNN_terminal_wire_qualified_comparison_validation_02.json')['passed']
prior = Path(plan['recovery_queue']); reg = read(prior/'registration.json')
write(q/'registration.json', dict(**process_identity(os.getpid()), source_sha256=bound,
    prerequisite_owner=dict(pid=reg['pid'],start_ticks=reg['start_ticks']), native_calls=0,
    executes_existing_results_only=True, uses_shared_serial_slot=True))
try:
    while not (prior/'completion.json').exists():
        live = process_identity(reg['pid'])
        assert live and live['state'] != 'Z' and live['start_ticks'] == reg['start_ticks'], 'Original recovery owner missing without terminal receipt'
        write(q/'status.json', dict(status='waiting_for_original_terminal_wire_completion'))
        time.sleep(30)
    serial = (D/'critical_scope_runner.lock').open('r')
    while True:
        try:
            fcntl.flock(serial,fcntl.LOCK_EX|fcntl.LOCK_NB); break
        except BlockingIOError:
            write(q/'status.json', dict(status='waiting_for_shared_serial_slot')); time.sleep(30)
    assert all(sha(f) == h for f,h in bound.items())
    write(q/'status.json', dict(status='comparing_completed_configuration'))
    with (q/'comparison.log').open('x') as log:
        code = subprocess.run([sys.executable,str(D/'compare_BNN_terminal_wire_qualified_v2.py')],stdout=log,stderr=subprocess.STDOUT).returncode
    assert code == 0 and read(root/'completion.json')['passed']
    write(q/'completion.json',dict(passed=True,status='readonly_comparison_terminal',native_calls=0,source_sha256=bound))
    write(q/'status.json',dict(status='terminal',passed=True))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),native_calls=0,source_sha256=bound))
    write(q/'status.json',dict(status='reconciliation_required',error=repr(error)))
    raise
