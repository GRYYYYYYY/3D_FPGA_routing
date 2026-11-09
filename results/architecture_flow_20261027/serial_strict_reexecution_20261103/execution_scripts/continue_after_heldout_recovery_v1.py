#!/usr/bin/env python3
"""Wait for the exact recovery owner, then finish registered research stages.

This coordinator ends at review, never at a claim of scientific completion.
"""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from flatland_benchmark import BASE, read
from lazagna_common import ROOT, sha256, utc, write_json
import continue_strict_study as original
import run_flatland_evaluation_import_fix_v1 as evaluation

SCRIPTS = Path(__file__).resolve().parent
HELDOUT_COUNT = 168
STAGES = [
    ('width300', ['run_flatland_evaluation_import_fix_v1.py', '--phase', 'width300', '--workers', '1']),
    ('serial', ['run_flatland_serial_candidate.py']),
    ('balance', ['run_flatland_balance_sensitivity.py']),
    ('evaluation_analysis', ['analyze_flatland_evaluation.py']),
    ('serial_analysis', ['analyze_flatland_serial_candidate.py']),
    ('balance_analysis', ['analyze_flatland_balance_sensitivity.py']),
    ('figures', ['render_flatland_figures.py']),
    ('report', ['render_flatland_report.py']),
    ('paired_width', ['run_paired_width_diagnostic.py']),
    ('paired_width_analysis', ['analyze_paired_width_diagnostic.py']),
]


def heldout_gate():
    """Account for every planned case, including failed routes and placements."""
    jobs = [j for j in read(BASE / 'evaluation_jobs.json')['jobs'] if j['phase'] == 'heldout']
    assert len(jobs) == HELDOUT_COUNT
    names = set()
    for job in jobs:
        name = f"heldout_{job['circuit']}_s{job['seed']}_{job['family']}_w{job['width']}"
        assert name not in names
        names.add(name)
        directory = BASE / 'evaluation_cases' / name
        result = read(directory / 'result.json')
        assert result['status'] == 'completed' and result['job'] == job, name
        assert set(result['flows']) == set(job['roles']), name
        for flow, arms in job['roles'].items():
            row = result['flows'][flow]
            if row['status'] == 'placement_failed':
                assert set(row['unattempted_roles']) == set(arms), name
                receipt = read(BASE / 'runs' / row['receipt'] / 'manifest.json')
                assert receipt['status'] in ('failed', 'timeout'), name
                continue
            assert row['status'] == 'completed' and set(row['roles']) == set(arms), name
            unique = set(row['roles'].values())
            audit = read(directory / (flow + '_audit_summary.json'))
            assert audit['passed'] and row['registered_roles'] == len(arms), name
            assert row['unique_runs'] == len(unique) == audit['registered_route_count'], name
            assert row['legal_runs'] == audit['legal_count'] == len(audit['legal']), name
            assert row['failed_runs'] == audit['failed_count'] == len(audit['failed']), name
            assert audit['legal_count'] + audit['failed_count'] == len(unique), name
            audited_names = [r['name'] for r in audit['legal'] + audit['failed']]
            assert len(audited_names) == len(set(audited_names)) and set(audited_names) == unique, name
    return len(names)


def recovery_gate():
    queue = read(BASE / 'heldout_disk_recovery_queue_v2' / 'state.json')
    assert queue['status'] == 'heldout_recovery_complete'
    expected = {'heldout_lstm_s21_sb_w100', 'heldout_lstm_s21_hybrid_o_w100'}
    assert set(queue['completed']) == expected
    for name in expected:
        d = BASE / 'evaluation_cases' / name
        r = d / 'recovery_disk_reserve_v2'
        assert read(r / 'input_integrity.json')['passed'], name
        assert read(r / 'recovered_result.json') == read(d / 'result.json'), name
    folder = BASE / 'evaluation_invocations'
    invocation = read(folder / 'heldout_unstarted_recovery_v1_1.json')
    registration = folder / 'heldout_unstarted_recovery_v1_1_registration.json'
    assert invocation['registration_sha256'] == sha256(registration)
    assert not invocation['unstarted_jobs']
    assert len(invocation['results']) == invocation['planned_cases'] == 78
    assert all(r['status'] == 'completed' for r in invocation['results'])
    assert read(folder / 'heldout_unstarted_recovery_v1_1_input_integrity.json')['passed']
    return heldout_gate()


def execute_stages(directory, bindings, state, completed):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(SCRIPTS) + os.pathsep + str(ROOT / 'scripts')
    env['PYTHONUNBUFFERED'] = '1'
    for label, args in STAGES:
        original.verify(bindings)
        original.quiescent()
        evaluation.require_disk_space()
        cmd = [sys.executable, str(SCRIPTS / args[0]), *args[1:]]
        state('running_stage', stage=label, command=cmd)
        with (directory / (label + '.log')).open('x') as log:
            subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        completed.append(label)
        state('stage_completed', stage=label)


def main(pid, start_ticks):
    lock = (BASE / 'post_heldout_continuation.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert original.identity(pid) == start_ticks, 'Recovery owner is not live with the registered identity'
    command = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    assert any(x.endswith(b'/queue_heldout_disk_recovery_v2.py') for x in command)
    for name in ('serial_protocol.json', 'partition_balance_sensitivity_jobs.json',
                 'evaluation_analysis', 'serial_analysis', 'balance_analysis', 'figures',
                 'report.html', 'paired_width_jobs.json', 'paired_width_analysis'):
        assert not (BASE / name).exists(), f'Existing downstream output requires review: {name}'
    assert not any((BASE / 'evaluation_cases').glob('width300_*'))
    directory = BASE / 'post_heldout_continuation_v1'
    directory.mkdir(exist_ok=False)
    bindings = dict(read(BASE / 'strict_continuation' / 'registration.json')['source_and_protocol_sha256'])
    files = {SCRIPTS / args[0] for _, args in STAGES}
    files.update([Path(__file__), SCRIPTS / 'queue_heldout_disk_recovery_v2.py',
                  SCRIPTS / 'recover_evaluation_case_v2.py', SCRIPTS / 'recover_unstarted_heldout_v1.py',
                  BASE / 'heldout_disk_recovery_queue_v2' / 'registration.json',
                  BASE / 'evaluation_jobs.json', BASE / 'selected_configs.json',
                  BASE / 'paired_width_diagnostic_protocol.json',
                  BASE / 'evaluation_invocations' / 'heldout_unstarted_recovery_v1_1_registration.json'])
    original.verify(bindings)
    bindings.update({str(p): sha256(p) for p in files})
    write_json(directory / 'registration.json', dict(utc=utc(), owner_pid=pid,
        owner_start_ticks=start_ticks, stages=STAGES, source_and_protocol_sha256=bindings,
        workers=1, reason='Continue after preserved disk-space recovery; original inputs, parameters and scientific acceptance remain unchanged.',
        terminal='awaiting_scientific_and_integrity_closure'))
    completed = []

    def state(status, **fields):
        write_json(directory / 'state.json', dict(utc=utc(), supervisor_pid=os.getpid(),
            status=status, completed_stages=completed, **fields))

    try:
        state('waiting_recovery_owner', owner_pid=pid, owner_start_ticks=start_ticks)
        while original.identity(pid) == start_ticks:
            time.sleep(30)
        strict_lock = (BASE / 'strict_continuation.lock').open('a')
        fcntl.flock(strict_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        original.verify(bindings)
        original.training_gate()
        original.quiescent()
        count = recovery_gate()
        write_json(directory / 'heldout_gate.json', dict(utc=utc(), passed=True, cases=count,
            qualification='All planned terminal records accounted, including route failures; full input checks remain in the analysis and final integrity review.'))
        execute_stages(directory, bindings, state, completed)
        state('awaiting_scientific_and_integrity_closure', report=str(BASE / 'report.html'),
              paired_width_analysis=str(BASE / 'paired_width_analysis' / 'summary.json'))
    except BaseException as error:
        state('needs_diagnosis', error=str(error), traceback=traceback.format_exc())
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner-pid', type=int, required=True)
    parser.add_argument('--owner-start-ticks', type=int, required=True)
    args = parser.parse_args()
    main(args.owner_pid, args.owner_start_ticks)
