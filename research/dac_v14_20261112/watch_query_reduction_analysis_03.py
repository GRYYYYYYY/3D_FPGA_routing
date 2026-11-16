"""Single read-only comparison owner; preserve all existing native queue owners."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

root = D / 'query_reduction_resource_dev_01'
out = root / 'analysis_03'
out.mkdir(exist_ok=False)
owner_lock = (out / 'owner.lock').open('w')
fcntl.flock(owner_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
script = D / 'compare_query_reduction_terminal_03.py'
files = [Path(__file__).resolve(), script, root / 'queue/registration.json',
         D / 'query_reduction_completed_comparison_02/completion.json',
         D / 'query_reduction_terminal_03_validation.json']
assert read(files[-1])['passed']
bindings = {str(p): sha(p) for p in files}
reg = read(root / 'queue/registration.json')
write(out / 'registration.json', dict(pid=os.getpid(), start_ticks=process_identity(os.getpid())['start_ticks'],
    prerequisite_owner=dict(pid=reg['pid'], start_ticks=reg['start_ticks']), source_sha256=bindings,
    native_calls=0, executes_existing_results_only=True, uses_shared_serial_slot=True))
while not (root / 'queue/completion.json').exists():
    p = process_identity(reg['pid'])
    if not p or p['state'] == 'Z' or p['start_ticks'] != reg['start_ticks']:
        write(out / 'completion.json', dict(passed=False, status='predecessor_missing_without_terminal', native_calls=0))
        raise SystemExit(1)
    write(out / 'status.json', dict(status='waiting_for_registered_query_reduction_terminal'))
    time.sleep(30)
# CPU-heavy audit hashes and endpoint parsing must not overlap measured native flows.
serial = (D / 'critical_scope_runner.lock').open('r')
while True:
    try:
        fcntl.flock(serial, fcntl.LOCK_EX | fcntl.LOCK_NB)
        break
    except BlockingIOError:
        write(out / 'status.json', dict(status='waiting_for_shared_serial_slot'))
        time.sleep(30)
assert all(sha(p) == h for p, h in bindings.items())
write(out / 'status.json', dict(status='comparing_sealed_results'))
with (out / 'comparison.log').open('w') as log:
    code = subprocess.run([sys.executable, str(script)], stdout=log, stderr=subprocess.STDOUT).returncode
write(out / 'completion.json', dict(passed=code == 0, returncode=code, source_sha256=bindings, native_calls=0))
write(out / 'status.json', dict(status='terminal', passed=code == 0))
