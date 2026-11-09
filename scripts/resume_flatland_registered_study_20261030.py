#!/usr/bin/env python3
"""Evidence-gated continuation after loss of the Oct29 observation owners.

Preserve terminal solves and frozen sources. Recover only the one independently
documented successful child; recompute interrupted audits, never solver attempts.
"""
import argparse
import datetime
import fcntl
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys
import traceback

import continue_flatland_registered_study as original
import flatland_benchmark as study
import flatland_experiment_io as io
from lazagna_common import ROOT, sha256, utc, write_json
from run_vpr import parse_metrics
from validate_lazagna_vtr9_pilot import placements

BASE = study.BASE
DIRECTORY = BASE / 'owner_recovery_20261030'
OLD = BASE / 'registered_study_continuation_20261029'
RECOVER = 'heldout_clstm_like.large_s21_sb_n80_w100_p1_delay_c6'


def idle():
    found = []
    for p in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            args = p.read_bytes().split(b'\0')
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        if any(Path(os.fsdecode(a)).name in {
            'vpr', 'run_flatland_training.py', 'run_flatland_evaluation.py',
            'run_flatland_serial.py', 'run_flatland_balance_sensitivity.py',
            'continue_flatland_registered_study.py'} for a in args if a):
            found.append(str(p.parent))
    assert not found, ('Active experiment owner or solver', found)


def locks(names):
    result = []
    for name in names:
        f = (BASE / name).open('a')
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result.append(f)
    return result


def preflight():
    assert not DIRECTORY.exists(), 'Preserve existing recovery; diagnose before another attempt'
    DIRECTORY.mkdir()
    idle()
    held = locks(['evaluation_runner.lock', 'training_runner.lock', 'serial_runner.lock'])
    bindings = study.read(OLD / 'registration.json')['source_and_protocol_sha256']
    original.verify_bindings(bindings)
    original.training_gate()
    old_state = study.read(OLD / 'state.json')
    assert old_state['completed_stages'] == ['selection', 'training_analysis']
    assert old_state['stage'] == 'heldout'
    assert study.read(BASE / 'selected_configs.json')['status'] == 'frozen_before_heldout'
    summary = study.read(BASE / 'training_analysis/summary.json')
    assert summary['registered_attempts'] == len(summary['observations']) == 594
    assert summary['status'] == 'all_registered_training_attempts_accounted'
    plan = study.read(BASE / 'evaluation_jobs.json')
    assert plan['selection_sha256'] == sha256(BASE / 'selected_configs.json')
    expected, records = {}, {}

    def require(p, digest=None):
        p = str(Path(p).resolve())
        if p in expected and digest is not None:
            assert expected[p] in (None, digest), p
        if p not in expected or digest is not None:
            expected[p] = digest

    for p, h in bindings.items():
        require(p, h)
    for p in [Path(__file__), OLD / 'state.json', OLD / 'registration.json',
              BASE / 'selected_configs.json', BASE / 'evaluation_jobs.json',
              BASE / 'training_analysis/summary.json']:
        require(p)
    pending = []
    for d in sorted((BASE / 'runs').glob('heldout_*')):
        m = study.read(d / 'manifest.json')
        require(d / 'manifest.json')
        if m['status'] in ('starting', 'running'):
            pending.append(d.name)
        for p, info in m['shared_inputs'].items():
            assert io.identity(p) == tuple(info['stat_identity']), p
            require(p, info['sha256'])
        for name, info in m.get('outputs', {}).items():
            require(d / name, info['sha256'])
        for p in d.iterdir():
            if p.is_file() and p.name in ('packed.net', 'placed.place', 'routed.route',
                'stdout.log', 'time.txt', 'pair_check.json', 'placement_check.json', 'independent_audit.json'):
                require(p)
    assert pending == [RECOVER], pending
    d = BASE / 'runs' / RECOVER
    m = study.read(d / 'manifest.json')
    assert not Path(f"/proc/{m['supervisor_pid']}").exists()
    assert not Path(f"/proc/{m['process_group_id']}").exists()
    timing = (d / 'time.txt').read_text()
    assert re.search(r'^\s*Exit status: 0\s*$', timing, re.M)
    log = (d / 'stdout.log').read_text()
    metrics = parse_metrics(log)
    assert 'VPR succeeded' in log and metrics['native_full_check_passed'] and metrics['routing_success_reported']
    elapsed = re.search(r'Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): ([\d:.]+)', timing).group(1)
    seconds = 0.0
    for component in elapsed.split(':'):
        seconds = 60 * seconds + float(component)
    assert seconds < m['timeout_seconds']
    source = d.with_name(RECOVER.rsplit('_delay_c6', 1)[0] + '_place')
    assert sha256(d / 'packed.net') == sha256(source / 'packed.net')
    assert placements(d / 'placed.place') == placements(source / 'placed.place')
    partial = []
    for d in sorted((BASE / 'evaluation_cases').iterdir()):
        if (d / 'result.json').exists():
            assert study.read(d / 'result.json')['status'] == 'completed'
        else:
            partial.append(d.name)
        for p in d.iterdir():
            assert p.is_file()
            require(p)
    for i, (p, h) in enumerate(expected.items(), 1):
        before = io.identity(p)
        digest = sha256(p)
        assert before == io.identity(p), p
        assert h is None or digest == h, p
        records[p] = dict(sha256=digest, stat_identity=before)
        if i % 40 == 0:
            print('recovery input verification', i, '/', len(expected), flush=True)
    write_json(DIRECTORY / 'preflight.json', dict(utc=utc(), passed=True,
        source_sha256=sha256(__file__), files=records, partial_cases=partial,
        recover_run=RECOVER, recovered_wall_seconds=seconds, recovered_metrics=metrics,
        original_owner_status='PIDs and unified handles missing; all study locks free; no solver found',
        termination_cause='Unknown; no inference from missing owner',
        recovery_policy='No solver rerun, no retuning, no changed budget. Preserve original running receipt; '
            'derive child exit from GNU time and VPR output; archive incomplete case/audit metadata before rebuilding audits.',
        wall_time_qualification='GNU time child wall duration, not original Python supervisor duration; '
            'heldout parallel runtimes are not speedup measurements.'))
    print('recovery preflight passed', flush=True)
    return held


def resume():
    idle()
    held = locks(['evaluation_runner.lock', 'training_runner.lock', 'serial_runner.lock'])
    check = study.read(DIRECTORY / 'preflight.json')
    assert check['passed'] and check['source_sha256'] == sha256(__file__)
    assert not (DIRECTORY / 'recovery_applied.json').exists()
    for p, info in check['files'].items():
        assert io.identity(p) == tuple(info['stat_identity']), p
    bindings = study.read(OLD / 'registration.json')['source_and_protocol_sha256']
    original.verify_bindings(bindings)
    original.training_gate()
    archive = DIRECTORY / 'archive'
    archive.mkdir()
    d = BASE / 'runs' / RECOVER
    shutil.copy2(d / 'manifest.json', archive / 'original_running_manifest.json')
    m = study.read(d / 'manifest.json')
    m.update(status='completed', returncode=0, metrics=check['recovered_metrics'],
        finish_utc=datetime.datetime.fromtimestamp((d / 'time.txt').stat().st_mtime, datetime.timezone.utc).isoformat(),
        wall_seconds=check['recovered_wall_seconds'],
        recovery=dict(utc=utc(), preflight=str(DIRECTORY / 'preflight.json'),
            original_receipt=str(archive / 'original_running_manifest.json'),
            finish_time_source='GNU time output mtime; reconstructed, not original supervisor timestamp',
            wall_seconds_source='GNU time elapsed child wall duration', solver_reexecuted=False))
    m['outputs'] = {name: dict(sha256=check['files'][str(d / name)]['sha256'], bytes=(d / name).stat().st_size)
                    for name in ['packed.net', 'placed.place', 'routed.route', 'stdout.log', 'time.txt']}
    source = d.with_name(RECOVER.rsplit('_delay_c6', 1)[0] + '_place')
    write_json(d / 'manifest.json', m)
    write_json(d / 'pair_check.json', dict(utc=utc(), passed=True,
        checks=dict(packed_identical=True, placement_identical=True), source=str(source),
        recovered_after_owner_loss=True))
    archived = []
    for case in check['partial_cases']:
        directory = BASE / 'evaluation_cases' / case
        job = study.read(directory / 'registration.json')
        ctx = study.context(job['circuit'], job['family'], job['seed'], job['width'])
        for flow in job['roles']:
            for run in (BASE / 'runs').glob(study.prefix(ctx, job['phase'], flow) + '_*'):
                p = run / 'independent_audit.json'
                if p.exists():
                    target = archive / 'partial_run_audits' / run.name / p.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    p.rename(target)
                    archived.append(str(target))
        target = archive / 'partial_cases' / case
        target.parent.mkdir(parents=True, exist_ok=True)
        directory.rename(target)
        archived.append(str(target))
    write_json(DIRECTORY / 'recovery_applied.json', dict(utc=utc(), solver_reruns=0,
        recovered_run=RECOVER, archived=archived, frozen_source_changes=0,
        core_policy='RLIMIT_CORE soft=0 inherited; same as Oct29 execution amendment'))
    for f in held:
        f.close()
    completed = ['selection', 'training_analysis']
    def state(status, **fields):
        write_json(DIRECTORY / 'state.json', dict(utc=utc(), supervisor_pid=os.getpid(),
            status=status, completed_stages=completed, **fields))
    try:
        for label, args in original.STAGES[2:]:
            original.verify_bindings(bindings)
            original.quiescent()
            command = [sys.executable, str(ROOT / 'scripts' / args[0]), *args[1:]]
            state('running_stage', stage=label, command=command)
            with (DIRECTORY / (label + '.log')).open('x') as stream:
                subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
            completed.append(label)
            state('stage_completed', stage=label)
        state('registered_artifacts_ready_for_scientific_and_integrity_closure')
    except BaseException as error:
        state('needs_diagnosis', error=str(error), traceback=traceback.format_exc())
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['preflight', 'resume'])
    args = parser.parse_args()
    owner = locks(['registered_study_continuation.lock'])
    resource.setrlimit(resource.RLIMIT_CORE, (0, resource.getrlimit(resource.RLIMIT_CORE)[1]))
    if args.mode == 'preflight':
        preflight()
    else:
        resume()
