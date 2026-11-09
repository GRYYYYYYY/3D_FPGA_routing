#!/usr/bin/env python3
"""Advance registered stages after the identified training owner finishes."""
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


STAGES = [
    ('selection', ['select_flatland_configs.py']),
    ('training_analysis', ['analyze_flatland_training.py']),
    ('heldout', ['run_flatland_evaluation.py', '--phase', 'heldout', '--workers', '6']),
    ('width300', ['run_flatland_evaluation.py', '--phase', 'width300', '--workers', '6']),
    ('serial', ['run_flatland_serial.py']),
    ('balance', ['run_flatland_balance_sensitivity.py']),
    ('evaluation_analysis', ['analyze_flatland_evaluation.py']),
    ('serial_analysis', ['analyze_flatland_serial.py']),
    ('balance_analysis', ['analyze_flatland_balance_sensitivity.py']),
    ('figures', ['render_flatland_figures.py']),
    ('report', ['render_flatland_report.py']),
]


def process_identity(pid):
    try:
        text = Path(f'/proc/{pid}/stat').read_text()
        fields = text[text.rindex(')') + 2:].split()
        if fields[0] == 'Z':
            return None
        return int(fields[19])  # Linux /proc stat field 22, process start ticks.
    except FileNotFoundError:
        return None


def verify_bindings(bindings):
    for path, digest in bindings.items():
        assert sha256(path) == digest, f'Registered source/input changed: {path}'


def training_gate():
    protocol = read(BASE / 'benchmark_protocol.json')
    total = 0
    for circuit in protocol['training']:
        for family in protocol['architectures']:
            d = BASE / 'training_cases' / f'{circuit}_{family}'
            result = read(d / 'result.json')
            audit = read(d / 'audit_summary.json')
            assert result['status'] == 'completed', f'Training diagnosis needed: {d}'
            assert audit['passed'] and audit['registered_route_count'] == 33
            assert result['registered_routes'] == 33
            assert result['legal_routes'] == audit['legal_count'] == len(audit['legal'])
            assert result['failed_routes'] == audit['failed_count'] == len(audit['failed'])
            assert audit['legal_count'] + audit['failed_count'] == 33
            total += 33
    assert total == 594
    for stem in ('eltwise_layer_spmv', 'attention_layer_softmax', 'bnn_gemm_layer'):
        d = BASE / 'training_invocations'
        invocation = read(d / (stem + '.json'))
        assert all(r['status'] == 'completed' for r in invocation['results'])
        assert read(d / (stem + '_input_integrity.json'))['passed']
    assert read(BASE / 'p1_training_preflight_state.json')['status'] == 'passed'
    assert read(BASE / 'p1_training_partition_weight_review.json')['status'] == 'resolved'


def quiescent():
    active = []
    for p in (BASE / 'runs').glob('*/manifest.json'):
        if read(p)['status'] in ('starting', 'running'):
            active.append(p.parent.name)
    assert not active, f'Previous study processes still unresolved: {active}'


def main(pid, start_ticks):
    directory = BASE / 'registered_study_continuation_20261029'
    lock = (BASE / 'registered_study_continuation.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    directory.mkdir(exist_ok=False)
    state_path = directory / 'state.json'
    completed = []

    def state(status, **fields):
        write_json(state_path, dict(utc=utc(), supervisor_pid=os.getpid(),
            status=status, completed_stages=completed, **fields))

    try:
        assert process_identity(pid) == start_ticks, 'Training owner identity changed before registration'
        command = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        assert any(arg.endswith(b'/run_flatland_training.py') or arg == b'scripts/run_flatland_training.py' for arg in command)
        assert b'bnn' in command and b'gemm_layer' in command
        for name in ('selected_configs.json', 'evaluation_jobs.json', 'serial_protocol.json',
                     'partition_balance_sensitivity_jobs.json', 'report.html'):
            assert not (BASE / name).exists(), f'Existing downstream artifact needs review: {name}'
        for name in ('training_analysis', 'evaluation_analysis', 'serial_analysis', 'balance_analysis', 'figures'):
            assert not (BASE / name).exists(), f'Existing downstream output needs review: {name}'
        bindings = dict(read(BASE / 'training_jobs.json')['source_sha256'])
        script_names = {args[0] for _, args in STAGES}
        script_names.update(['continue_flatland_registered_study.py', 'flatland_statistics.py',
            'analyze_flatland_diagnostics.py', 'check_flatland_partition_balance.py',
            'lazagna_common.py', 'run_vpr.py', 'validate_lazagna_vtr9_pilot.py'])
        bindings.update({str(ROOT / 'scripts' / name): sha256(ROOT / 'scripts' / name) for name in script_names})
        for name in ('benchmark_protocol.json', 'training_jobs.json', 'capacity_selection.json',
                     'execution_resource_amendment.json', 'partition_balance_sensitivity_protocol.json',
                     'p1_training_preflight_state.json', 'p1_training_partition_weight_review.json'):
            bindings[str(BASE / name)] = sha256(BASE / name)
        verify_bindings(bindings)
        write_json(directory / 'registration.json', dict(utc=utc(), training_owner_pid=pid,
            training_owner_start_ticks=start_ticks, source_and_protocol_sha256=bindings,
            stages=STAGES, contract='One continuation owner; wait for exact training owner; '
            'require all training cases and input seals; preserve registered failures; '
            'stop on any command or evidence error; no automatic retry or goal-completion claim.'))
        while process_identity(pid) == start_ticks:
            state('waiting_training_owner', training_owner_pid=pid, training_owner_start_ticks=start_ticks)
            time.sleep(30)
        verify_bindings(bindings)
        training_gate()
        for label, args in STAGES:
            verify_bindings(bindings)
            quiescent()
            if label == 'heldout':
                summary = read(BASE / 'training_analysis/summary.json')
                assert summary['status'] == 'all_registered_training_attempts_accounted'
                assert summary['registered_attempts'] == len(summary['observations']) == 594
                selection = read(BASE / 'selected_configs.json')
                assert selection['status'] == 'frozen_before_heldout'
            command = [sys.executable, str(ROOT / 'scripts' / args[0]), *args[1:]]
            state('running_stage', stage=label, command=command)
            with (directory / (label + '.log')).open('x') as stream:
                subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
            completed.append(label)
            state('stage_completed', stage=label)
        state('registered_artifacts_ready_for_scientific_and_integrity_closure',
              report=str(BASE / 'report.html'))
    except BaseException as error:
        state('needs_diagnosis', error=str(error), traceback=traceback.format_exc())
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--training-pid', required=True, type=int)
    parser.add_argument('--training-start-ticks', required=True, type=int)
    args = parser.parse_args()
    main(args.training_pid, args.training_start_ticks)
