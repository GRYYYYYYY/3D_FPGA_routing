"""Run one separately registered explicit-domain intervention in the serial slot."""
import fcntl, os, subprocess, sys
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

root = D / 'R1_owner_release_joint_probe_01'
plan = read(root / 'plan.json')
q = root / 'queue'
q.mkdir(exist_ok=False)
lock = (q / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
files = [Path(__file__).resolve(), root / 'plan.json', root / 'prepared_transaction_registration.json',
         D / 'crossing_source_stage_01/build_verification.json', *map(Path, plan['prepared_files'])]
hashes = {str(f): sha(f) for f in files}
write(q / 'registration.json', dict(pid=os.getpid(), start_ticks=process_identity(os.getpid())['start_ticks'],
      source_sha256=hashes, qualification=plan['qualification']))
assert read(D / 'R1_whole_net_residual_probe_01/queue/completion.json')['passed']
assert read(D / 'complete_serial_source_snapshot_01/queue/completion.json')['passed']
write(q / 'status.json', dict(status='waiting_for_current_serial_owner_to_release_slot',
      qualification='Fresh BNN complete pair and checkpoint recovery02 retain their registered ownership; this independent two-role joint probe waits on the same serial slot.'))
serial = (D / 'critical_scope_runner.lock').open('r')
fcntl.flock(serial, fcntl.LOCK_EX)
assert all(sha(f) == h for f, h in hashes.items())
tx = root / 'transaction'
tx.mkdir()
(tx / 'registration.json').write_bytes((root / 'prepared_transaction_registration.json').read_bytes())
with (q / 'transaction.log').open('w') as log:
    child = subprocess.Popen([sys.executable, str(D / 'run_joint_crossing_source_transactions_v2.py'),
                              '--batch', str(tx)], stdout=log, stderr=subprocess.STDOUT)
    write(q / 'status.json', dict(status='running', phase='joint_owner_release_native_and_target_CB_domain',
          pid=child.pid, start_ticks=process_identity(child.pid)['start_ticks']))
    code = child.wait()
passed = code == 0 and (tx / 'completion.json').exists() and read(tx / 'completion.json')['passed']
write(q / 'completion.json', dict(passed=passed, returncode=code, transaction=str(tx),
      source_sha256=hashes, qualification=plan['qualification']))
write(q / 'status.json', dict(status='terminal', passed=passed))
print(dict(passed=passed, transaction=str(tx)), flush=True)
