"""Reproduce vanished-proc reads; exercise actual subreaper exit/cleanup semantics."""
import importlib.util
import os
import signal
import subprocess
import time
from pathlib import Path
from unittest.mock import patch
from retained_prefix_workflow import D, read, write, sha

root = D/'method_phase_proc_race_validation_02'
root.mkdir(exist_ok=False)
source = D/'supervise_method_phase_v2.py'
spec = importlib.util.spec_from_file_location('phase_v2', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
checks = []
for error in (FileNotFoundError, ProcessLookupError):
    with patch.object(Path, 'read_text', side_effect=error()):
        assert module.ident(os.getpid()) is None
        assert module.descendants() == {}
    checks.append(error.__name__+'_proc_reads_tolerated')
# Access errors must remain visible, not be mistaken for process termination.
with patch.object(Path, 'read_text', side_effect=PermissionError()):
    try:
        module.ident(os.getpid())
    except PermissionError:
        checks.append('permission_error_not_hidden')
    else:
        raise AssertionError('Permission error swallowed')

program = root/'fork_setsid.py'
program.write_text('''import os,sys,time
mode=sys.argv[1]
if mode=='churn':
 for _ in range(120):
  pid=os.fork()
  if pid==0: os._exit(0)
  os.waitpid(pid,0)
 sys.exit(0)
pid=os.fork()
if pid==0:
 os.setsid()
 time.sleep(.1 if mode=='clean' else 60)
 os._exit(0)
if mode=='orphan': os._exit(0)
os.waitpid(pid,0)
''')
actual = []
for mode in ['clean', 'churn', 'timeout', 'orphan', 'interrupted']:
    receipt = root/(mode+'.json')
    cmd = ['/usr/bin/python3', str(source), '--receipt', str(receipt)]
    if mode=='timeout': cmd += ['--seconds', '.3']
    cmd += ['--', '/usr/bin/python3', str(program), mode]
    with (root/(mode+'.log')).open('x') as log:
        child = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=True)
        if mode=='interrupted':
            until = time.monotonic()+5
            while not receipt.with_suffix('.active.json').exists():
                assert time.monotonic()<until
                time.sleep(.01)
            time.sleep(.1)
            child.send_signal(signal.SIGTERM)
        code = child.wait(timeout=10)
    result = read(receipt)
    assert not result['residual_descendants']
    if mode in ['clean', 'churn']:
        assert code==0 and result['passed'] and result['status']=='completed'
    else:
        assert code!=0 and not result['passed'] and result['killed_private_descendants']
    if mode=='timeout': assert result['status']=='wall_timeout'
    if mode=='orphan': assert result['status']=='live_descendant_after_root_exit'
    if mode=='interrupted': assert result['status'].startswith('Phase supervisor received signal')
    actual.append(dict(mode=mode, status=result['status'],
                       killed=len(result['killed_private_descendants'])))
write(root/'completion.json', dict(passed=True, injected_checks=checks,
    actual_process_checks=actual, native_calls_new=0,
    source_sha256={str(p):sha(p) for p in [source, Path(__file__).resolve(), program]},
    qualification='Only vanished /proc reads are tolerated. Fixed algorithms, timeout, ownership and cleanup policy unchanged. No algorithm-result or timing-equivalence claim.'))
print(dict(passed=True, injected_checks=checks, actual_process_checks=actual))
