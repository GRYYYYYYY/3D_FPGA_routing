"""Single owner for the missing complete domain engineering arm; no retries."""
import fcntl, os, subprocess, sys, time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

root = D/'complete_BNN_domain_engineering_01'; plan = read(root/'plan.json')
q = root/'queue'; q.mkdir(exist_ok=False)
lock = (q/'owner.lock').open('w'); fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
bound = {**plan['source_sha256'], str(root/'plan.json'):sha(root/'plan.json')}
write(q/'registration.json', dict(**process_identity(os.getpid()), source_sha256=bound,
    fixed_order=plan['fixed_order'], qualification=plan['qualification']))
try:
    prior = Path(plan['predecessor']); identity = read(prior/'registration.json')
    while not (prior/'completion.json').exists():
        live = process_identity(identity['pid'])
        assert live and live['state'] != 'Z' and live['start_ticks'] == identity['start_ticks'], 'Predecessor missing without terminal receipt; reconcile descendants'
        write(q/'status.json', dict(status='waiting_for_registered_robot_p1_pair', predecessor=str(prior)))
        time.sleep(15)
    terminal = read(prior/'completion.json')
    assert terminal['passed'] and terminal['status'] == 'registered_pair_terminal', 'Predecessor requires reconciliation; domain arm remains unexecuted'
    serial = (D/'critical_scope_runner.lock').open('r')
    write(q/'status.json', dict(status='waiting_for_shared_serial_slot'))
    fcntl.flock(serial, fcntl.LOCK_EX)
    assert all(sha(f) == h for f,h in bound.items())
    config = read(plan['config'])
    assert all(sha(f) == h for f,h in config['input_sha256'].items())
    write(root/'admission.json', dict(passed=True, complete_input_seals_verified=True,
        native_calls_before_admission=0, source_sha256=bound))
    case = root/'bnn_domain_closed_stream'; case.mkdir(); (case/'queue').mkdir()
    (case/'config.json').write_bytes(Path(plan['config']).read_bytes())
    command = [sys.executable, str(D/'measure_process_tree_v1.py'), '--output', str(case/'measurement'),
        '--', sys.executable, str(D/'run_complete_resource_timing_joint_stream_v1.py'),
        '--config', plan['config'], '--output', str(case/'flow')]
    with (q/'measured_command.log').open('x') as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        child_identity = process_identity(child.pid)
        write(case/'queue/registration.json', dict(**child_identity, command=command, source_sha256=bound))
        write(q/'status.json', dict(status='running', case=case.name, **child_identity))
        code = child.wait()
    measurement = read(case/'measurement/completion.json') if (case/'measurement/completion.json').exists() else None
    flow = read(case/'flow/completion.json') if (case/'flow/completion.json').exists() else None
    command_ok = bool(code == 0 and measurement and measurement['passed'] and flow and flow['passed'])
    verification_ok = False; verify_code = None
    if command_ok:
        write(q/'status.json', dict(status='verifying_complete_case', case=case.name))
        with (q/'case_verification.log').open('x') as log:
            verify_code = subprocess.run([sys.executable, str(D/'verify_complete_resource_timing_joint_stream_v1.py'),
                '--root', str(case)], stdout=log, stderr=subprocess.STDOUT).returncode
        verification_ok = bool(verify_code == 0 and (case/'completion.json').exists() and read(case/'completion.json')['passed'])
    result = dict(passed=command_ok and verification_ok, command_passed=command_ok,
        verification_passed=verification_ok, returncode=code, verification_returncode=verify_code,
        failure_stage=None if command_ok and verification_ok else 'readonly_case_verification' if command_ok else 'measured_command')
    write(q/'results.json', {case.name:result})
    write(q/'status.json', dict(status='comparing_actual_domain_execution', case=case.name))
    with (q/'comparison.log').open('x') as log:
        compare_code = subprocess.run([sys.executable, str(D/'compare_BNN_domain_engineering_01.py')],
            stdout=log, stderr=subprocess.STDOUT).returncode
    assert compare_code == 0 and read(root/'comparison.json')['passed'], 'Comparison requires reconciliation; no retry'
    write(q/'completion.json', dict(passed=True, status='registered_domain_engineering_terminal',
        execution_all_legal=result['passed'], results={case.name:result},
        comparison=str(root/'comparison.json'), source_sha256=bound,
        qualification='Accounting terminal, including any failed or divergent outcome; not completion of the research goal.'))
    write(q/'status.json', dict(status='terminal', passed=True, execution_all_legal=result['passed']))
except Exception as error:
    write(q/'completion.json', dict(passed=False, status='reconciliation_required', error=repr(error), source_sha256=bound))
    write(q/'status.json', dict(status='reconciliation_required', error=repr(error)))
    raise
