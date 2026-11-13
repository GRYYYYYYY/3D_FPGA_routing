#!/usr/bin/env python3
"""Single owner waits for both evidence seals and the ordinary VPR slot limit."""
from pathlib import Path
import fcntl, hashlib, json, os, socket, subprocess, time

D = Path(__file__).resolve().parent
R = D.parents[1]
deps = ['target_reuse_expansion_dev_01', 'persistent_view_dev_01']
runner = D / 'run_persistent_expansion.py'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ticks(pid): return Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()[19]
def write(name, value):
    p = D / name
    t = p.with_suffix('.tmp')
    t.write_text(json.dumps(value, indent=2) + '\n')
    t.replace(p)
def live():
    result = []
    for p in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            a = p.read_bytes().split(b'\0')[0].decode()
            if a.startswith(str(D) + '/') and a.endswith('/bin/vpr'): result.append(int(p.parent.name))
        except (OSError, UnicodeError): pass
    return result

lock = (D / 'persistent_expansion_queue.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
owners = {}
for name in deps:
    if not (D / name / 'completion.json').exists():
        pid = json.loads((D / name / 'registration.json').read_text())['pid']
        owners[name] = dict(pid=pid, start_ticks=ticks(pid))
identity = dict(pid=os.getpid(), start_ticks=ticks(os.getpid()), host=socket.gethostname(),
                dependencies=owners, runner_sha256=sha(runner),
                binary_sha256=sha(D / 'persistent_query_candidate_01/bin/vpr'),
                policy='Both E expansion and P exact-view confirmation must finish and seal, then <=2 live VPR. P-only eltwise/bnn transfer, exact views, no feedback/timing guide.64GiB/1800s/disk80GiB,max3VPR; no formal speedup assumption.')
write('persistent_expansion_queue_identity.json', identity)
while True:
    complete = {n: (D / n / 'completion.json').exists() for n in deps}
    processes = live()
    write('persistent_expansion_queue_state.json', dict(status='waiting_for_both_seals_and_slot', dependencies=complete, live_vpr=processes, observed_at=time.time()))
    if all(complete.values()) and len(processes) <= 2: break
    for name, done in complete.items():
        if done: continue
        owner = owners[name]
        try: assert ticks(owner['pid']) == owner['start_ticks']
        except (OSError, AssertionError):
            write('persistent_expansion_queue_state.json', dict(status='dependency_terminal_without_completion_requires_diagnosis', dependency=name))
            raise SystemExit(2)
    time.sleep(20)
for name in deps: assert json.loads((D / name / 'input_seal.json').read_text())['passed']
for circuit in ['spmv', 'softmax']:
    assert json.loads((D / 'persistent_view_dev_01/runs' / f'{circuit}_O/optimization_equivalence.json').read_text())['passed']
assert sha(runner) == identity['runner_sha256']
assert sha(D / 'persistent_query_candidate_01/bin/vpr') == identity['binary_sha256']
with (D / 'persistent_expansion_registered.log').open('x') as log:
    p = subprocess.Popen([str(R / '.venv-lazagna/bin/python'), str(runner), '--out', 'persistent_expansion_dev_01'], cwd=R, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    write('persistent_expansion_queue_state.json', dict(status='running_pilot', pilot_pid=p.pid, pilot_start_ticks=ticks(p.pid), started_at=time.time()))
    code = p.wait()
write('persistent_expansion_queue_state.json', dict(status='pilot_terminal', returncode=code, finished_at=time.time()))
