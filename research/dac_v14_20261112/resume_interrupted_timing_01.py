"""Recover the registered serial timing chain without changing its scientific policy."""
import fcntl
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

old = D/'completed_resource_timing_dev_01/queue'
registration = read(old/'registration.json')
assert process_identity(registration['pid']) is None
old_lock = (old/'owner.lock').open('r')
fcntl.flock(old_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
phase = read(old/'status.json')
assert process_identity(phase['pid']) is None
assert phase['case'] == 'paired' and phase['phase'] == 'timing'
assert not (old/'completion.json').exists()
assert all(sha(p) == h for p, h in registration['source_sha256'].items())
for case in registration['cases'].values():
    assert all(sha(p) == h for p, h in case['source_sha256'].items())
prior = old.parent/'paired'
assert read(old.parent/'native/completion.json')['passed']
saved = read(prior/'resume_state.json')
current = Path(saved['current_state'])
assert read(current/'completion.json')['passed'] and read(current/'input_seal.json')['passed']
assert all(sha(p) == h for p, h in read(prior/'registration.json')['source_sha256'].items())
q = D/'completed_resource_timing_recovery_01/queue'
q.mkdir(parents=True, exist_ok=False)
lock = (q/'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
output = q.parent/'paired'
command = list(phase['command'])
command[0] = sys.executable
command[command.index('--batch')+1] = str(output)
command += ['--resume-from', str(prior)]
write(q/'registration.json', dict(pid=os.getpid(), start_ticks=process_identity(os.getpid())['start_ticks'],
    hostname=socket.gethostname(), cases=registration['cases'], original_owner=str(old),
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),old/'registration.json',
        prior/'registration.json',prior/'resume_state.json',prior/'steps.json',current/'input_seal.json']},
    command=command, recovery_from_saved_accepts=len(read(prior/'steps.json')),
    policy_and_inputs_unchanged=True, interruption_cause='unknown; recorded owner and child absent; exclusive owner lock acquired',
    complete_single_configuration_algorithm_seconds=None,
    qualification='Independent recovery segment; completed native case and three paired accepts reused. Interrupted attempts and costs retained; missing elapsed intervals remain unknown. No fresh routing root or budget reset.'))
started=time.monotonic()
with (q/'paired_resume.log').open('w') as log:
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    write(q/'status.json',dict(status='running',case='paired',phase='resume_timing',pid=process.pid,
        start_ticks=process_identity(process.pid)['start_ticks'],command=command))
    code=process.wait()
receipt=output/'completion.json'
passed=code==0 and receipt.exists() and read(receipt)['passed']
write(q/'completion.json',dict(passed=passed, original_native_receipt=str(old.parent/'native/completion.json'),
    paired_recovery_receipt=str(receipt), returncode=code,
    complete_recovery_segment_seconds=time.monotonic()-started,
    complete_single_configuration_algorithm_seconds=None,
    original_interrupted_segment=str(prior), unknown_interrupted_elapsed_time=True,
    qualification='Scientific decisions retain the registered policy. This segment is not cold configuration timing.'))
write(q/'status.json',dict(status='terminal',passed=passed))
