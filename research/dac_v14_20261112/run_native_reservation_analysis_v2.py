#!/usr/bin/env python3
"""Evaluate an immutable current/candidate route once with native endpoint STA.

An identical-route observation reuses the source physical audit. A replacement
receives its own independent physical/capacity audit after native FULL/STA.
Acceptance is deliberately a separate policy decision.
"""
import argparse
import fcntl
import os
from pathlib import Path
import shutil
import sys
import time
from retained_prefix_workflow import D, read, write, sha, require_formal_terminal, route_body
from endpoint_timing_policy import load

ROOT = D.parents[1]
OLD = ROOT / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0] = [str(OLD / 'execution_scripts'), str(ROOT / 'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--candidate-route', type=Path)
    parser.add_argument('--trace-off', action='store_true')
    parser.add_argument('--native-cases', type=Path)
    parser.add_argument('--reserve-targets', type=Path)
    parser.add_argument('--objective',choices=['weighted_soft','weighted_capacity','physical_soft','physical_capacity'],default='weighted_soft')
    parser.add_argument('--pressure-start',type=float,default=1.)
    args = parser.parse_args()
    started = time.monotonic()
    require_formal_terminal()
    lock = (D / 'critical_scope_runner.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    source, b = args.source.resolve(), args.batch.resolve()
    stage = D / 'native_reservation_stage_03'
    binding = read(stage / 'binding.json')
    assert sha(stage / 'bin/vpr') == binding['binary_sha256']
    manifest = read(source / 'manifest.json')
    assert manifest['status'] == 'completed' and manifest['metrics']['native_full_check_passed']
    assert read(source / 'independent_audit.json')['audit']['passed']
    route = args.candidate_route.resolve() if args.candidate_route else source / 'routed.route'
    observation = sha(route) == sha(source / 'routed.route')
    graph = Path(manifest['command'][manifest['command'].index('--read_rr_graph') + 1])
    assert sha(graph) == manifest['shared_inputs'][str(graph)]['sha256']
    b.mkdir(exist_ok=False)
    (b / 'bin').mkdir()
    shutil.copy2(stage / 'bin/vpr', b / 'bin/vpr')
    shutil.copy2(OLD / 'runtime_dependency_binding.json', b / 'runtime_dependency_binding.json')
    files = [Path(__file__), D / 'endpoint_timing_policy.py', D / 'native_endpoint_vector_experiment_01.json',
             stage / 'binding.json', source / 'manifest.json', source / 'routed.route', source / 'packed.net',
             source / 'placed.place', source / 'independent_audit.json', route, graph, b / 'bin/vpr']
    if args.native_cases:
        files.append(args.native_cases.resolve())
    if args.reserve_targets:
        assert args.native_cases
        files.append(args.reserve_targets.resolve())
    hashes = {str(p): sha(p) for p in files}
    write(b / 'registration.json', dict(status='registered_before_native', source=str(source), candidate_route=str(route),
          observation_only=observation, trace_off=args.trace_off, reserve_targets=None if not args.reserve_targets else str(args.reserve_targets.resolve()), source_sha256=hashes,
          pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
          native_analysis_calls_planned=1, route_search_calls=0,
          limits=dict(timeout_seconds=1800, memory_bytes=64*1024**3, disk_reserve_bytes=80*1024**3)))
    io.BASE = b
    io.ADDRESS_SPACE_BYTES = 64 * 1024**3
    for p, h in hashes.items():
        io.frozen_hash(p, h)
    rd = b / 'runs/state'
    rd.mkdir(parents=True)
    for name in ['packed.net', 'placed.place']:
        shutil.copy2(source / name, rd / name)
    shutil.copy2(route, rd / 'routed.route')
    before = {n: sha(rd / n) for n in ['packed.net', 'placed.place', 'routed.route']}
    write(rd / 'pair_check.json', dict(passed=True, checks={n: sha(rd/n) == sha(source/n) for n in ['packed.net', 'placed.place']},
          scope='Exact packing and placement; input route frozen within this evaluation.'))
    cmd = list(manifest['command'])
    cmd[0] = str(b / 'bin/vpr')
    if '--route' in cmd:
        cmd.remove('--route')
    assert '--analysis' in cmd and '--route' not in cmd
    cmd[cmd.index('--timing_report_npaths') + 1] = '10'
    if '--verify_route_file_switch_id' not in cmd:
        cmd += ['--verify_route_file_switch_id', 'on']
    else:
        cmd[cmd.index('--verify_route_file_switch_id') + 1] = 'on'
    for option, name in [('--net_file', 'packed.net'), ('--place_file', 'placed.place'), ('--route_file', 'routed.route')]:
        cmd[cmd.index(option) + 1] = str(rd / name)
    env = {'VPR_H3D_MODE': 'off', 'VPR_JOINT_NATIVE_RESERVE_TARGETS': '', 'VPR_JOINT_NATIVE_RESERVE_OUTPUT': ''}
    if args.reserve_targets:
        env['VPR_JOINT_NATIVE_RESERVE_TARGETS']=str(args.reserve_targets.resolve())
        env['VPR_JOINT_NATIVE_RESERVE_OUTPUT']=str(rd/'pending_reservations.log')
    if not args.trace_off:
        env['VPR_H3D_FINAL_STA_TRACE'] = str(rd / 'native_sta_frontier.jsonl')
    if args.native_cases:
        env['VPR_JOINT_NATIVE_OBJECTIVE'] = args.objective
        env['VPR_JOINT_NATIVE_REQUEST'] = str(args.native_cases.resolve())
        env['VPR_CURRENT_STA_NATIVE_PRESSURE_START'] = str(args.pressure_start)
        env['VPR_JOINT_NATIVE_OUTPUT'] = str(rd / 'joint_native.log')
    preparation_seconds = time.monotonic() - started
    result = io.run(rd.name, cmd, environment=env, timeout=1800,
                    frozen=[cmd[0], cmd[1], cmd[2], graph, b / 'registration.json'],
                    private_inputs=[rd / n for n in before], tags=dict(phase='native_endpoint_vector', route_search_calls=0))
    checks = dict(completed=result['status'] == 'completed', native_FULL=result['metrics'].get('native_full_check_passed', False),
                  inputs_unchanged=all(sha(rd/n) == h for n, h in before.items()),
                  route_loaded='Finished loading route file' in (rd/'stdout.log').read_text())
    audit_start = time.monotonic()
    if observation:
        shutil.copy2(source / 'independent_audit.json', rd / 'independent_audit.json')
        write(b / 'physical_audit_reuse.json', dict(passed=checks['inputs_unchanged'], original=str(source/'independent_audit.json'),
              original_sha256=sha(source/'independent_audit.json'), exact_route_sha256=sha(route), graph_sha256=sha(graph),
              qualification='Audit content is copied with explicit original provenance, not presented as a newly executed physical audit.'))
        checks['physical_audit'] = checks['inputs_unchanged']
        if args.native_cases:
            query_lines=(rd/'joint_native.log').read_text().splitlines() if (rd/'joint_native.log').exists() else []
            checks['native_control_complete'] = bool(query_lines) and 'occupancy_restored' in query_lines[-1]
        if args.reserve_targets:
            reserve_lines=(rd/'pending_reservations.log').read_text().splitlines()
            checks['reservations_cleared']=bool(reserve_lines) and reserve_lines[-1].endswith('reservations_cleared')
        else:
            checks['reservations_disabled']=not (rd/'pending_reservations.log').exists()
        checks['CPD_matches_original'] = result['metrics'].get('critical_path_ns') == manifest['metrics']['critical_path_ns']
    else:
        study.BASE = b
        audit = study.audit_batch({'fixture': {'original_graph': str(graph)}}, [result], b/'independent_native_analysis_audit.json')
        checks['physical_audit'] = audit['passed']
    audit_seconds = time.monotonic() - audit_start
    vector = None
    if all(checks.values()) and not args.trace_off:
        vector = load(rd / 'native_sta_frontier.jsonl')
        checks['full_precision_CPD_matches_report'] = float(format(vector['cpd_s']*1e9, '.6g')) == result['metrics']['critical_path_ns']
        write(b / 'endpoint_vector.json', vector)
    io.seal_inputs(b / 'input_seal.json')
    checks['inputs_sealed'] = read(b/'input_seal.json')['passed']
    write(rd / 'analysis_gate.json', dict(passed=all(checks.values()), checks=checks))
    write(b / 'completion.json', dict(status='native_analysis_terminal', passed=all(checks.values()), accepted=None,
          run=str(rd), observation_only=observation, native_analysis_calls=1, route_search_calls=0,
          cpd_ns=result['metrics'].get('critical_path_ns'), full_precision_cpd_s=None if vector is None else vector['cpd_s'],
          endpoints=None if vector is None else len(vector['endpoint_ids']),
          process_status=result['status'], route_body_sha256=route_body(rd/'routed.route'),
          timing=dict(preparation_seconds=preparation_seconds, native_process_seconds=result['wall_seconds'],
                      independent_audit_seconds=audit_seconds, complete_evaluation_seconds=time.monotonic()-started),
          checks=checks, acceptance='Deferred to full-precision branch policy; never inferred from process success.'))
    print(dict(passed=all(checks.values()), cpd_ns=result['metrics'].get('critical_path_ns'),
               cpd_s=None if vector is None else vector['cpd_s'], endpoints=None if vector is None else len(vector['endpoint_ids'])), flush=True)
    assert all(checks.values()), 'Preserve terminal evaluation; diagnose without repeating a completed native process'


if __name__ == '__main__':
    main()
