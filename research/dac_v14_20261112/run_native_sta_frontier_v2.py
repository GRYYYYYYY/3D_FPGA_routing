#!/usr/bin/env python3
"""Observe frozen routes with native all-pin STA export; never run route search."""
import fcntl
import os
from pathlib import Path
import re
import shutil
import sys

from retained_prefix_workflow import D, read, write, sha, require_formal_terminal

ROOT = D.parents[1]
OLD = ROOT / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0] = [str(OLD / 'execution_scripts'), str(ROOT / 'scripts')]
import flatland_timing_io_candidate as io


def sta(path):
    text = path.read_text()
    result = {}
    for label in ['sWNS', 'sTNS', 'hWNS', 'hTNS']:
        match = re.search(r'\(' + label + r'\):\s*([-+0-9.eE]+) ns', text)
        result[label] = float(match[1]) if match else None
    return result


def main():
    require_formal_terminal()
    lock = (D / 'critical_scope_runner.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    stage = D / 'native_sta_frontier_stage_02'
    binding = read(stage / 'binding.json')
    assert sha(stage / 'bin/vpr') == binding['binary_sha256']
    assert all(sha(stage / 'src' / p) == h for p, h in binding['source_sha256'].items())
    b = D / 'native_sta_frontier_dev_02'
    b.mkdir(exist_ok=False)
    (b / 'bin').mkdir()
    shutil.copy2(stage / 'bin/vpr', b / 'bin/vpr')
    shutil.copy2(OLD / 'runtime_dependency_binding.json', b / 'runtime_dependency_binding.json')
    inputs = {role: D / 'native_reconvergence_eltwise_dev_01/runs' / ('eltwise_layer_' + role)
              for role in ['A0', 'R1', 'Tf']}
    inputs['jointR1'] = D / 'joint_coordinated_native_01/runs/eltwise_layer_R'
    files = [Path(__file__), D / 'native_sta_frontier_experiment_01.json', stage / 'binding.json', b / 'bin/vpr']
    for source in inputs.values():
        files += [source / name for name in ['manifest.json', 'independent_audit.json', 'packed.net', 'placed.place', 'routed.route', 'stdout.log']]
    sources = {str(p): sha(p) for p in files}
    write(b / 'registration.json', dict(status='registered_before_analysis', input_runs={k: str(v) for k, v in inputs.items()},
          source_sha256=sources, pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
          native_analysis_calls_planned=8, route_search_calls=0,
          question='Off/on paired native FULL/STA on four frozen states, exact endpoint mapping and native delay validation. No QoR intervention.',
          limits=dict(timeout_seconds=1800, memory_bytes=64 * 1024**3, disk_reserve_bytes=80 * 1024**3)))
    io.BASE = b
    io.ADDRESS_SPACE_BYTES = 64 * 1024**3
    for p, h in sources.items():
        io.frozen_hash(p, h)
    receipts = []
    pairs = []
    for role, source in inputs.items():
        pm = read(source / 'manifest.json')
        assert pm['status'] == 'completed' and pm['metrics']['native_full_check_passed']
        assert read(source / 'independent_audit.json')['audit']['passed']
        graph = Path(pm['command'][pm['command'].index('--read_rr_graph') + 1])
        assert sha(graph) == pm['shared_inputs'][str(graph)]['sha256']
        pair = []
        for mode in ['off', 'on']:
            assert shutil.disk_usage(D).free >= 80 * 1024**3
            rd = b / 'runs' / (role + '_' + mode)
            rd.mkdir(parents=True)
            for name in ['packed.net', 'placed.place', 'routed.route']:
                shutil.copy2(source / name, rd / name)
            before = {name: sha(rd / name) for name in ['packed.net', 'placed.place', 'routed.route']}
            cmd = list(pm['command'])
            cmd[0] = str(b / 'bin/vpr')
            if '--route' in cmd:
                cmd.remove('--route')
            assert '--analysis' in cmd and '--route' not in cmd
            cmd[cmd.index('--timing_report_npaths') + 1] = '10'
            if '--verify_route_file_switch_id' not in cmd:
                cmd.extend(['--verify_route_file_switch_id', 'on'])
            else:
                cmd[cmd.index('--verify_route_file_switch_id') + 1] = 'on'
            for opt, name in [('--net_file', 'packed.net'), ('--place_file', 'placed.place'), ('--route_file', 'routed.route')]:
                cmd[cmd.index(opt) + 1] = str(rd / name)
            env = {'VPR_H3D_MODE': 'off'}
            if mode == 'on':
                env['VPR_H3D_FINAL_STA_TRACE'] = str(rd / 'native_sta_frontier.jsonl')
            result = io.run(rd.name, cmd, environment=env, timeout=1800,
                            frozen=[cmd[0], cmd[1], cmd[2], graph, b / 'registration.json'],
                            private_inputs=[rd / name for name in before],
                            tags=dict(circuit='eltwise_layer', arm=role, phase='native_STA_frontier_observer', mode=mode, route_search_calls=0))
            checks = dict(completed=result['status'] == 'completed', native_FULL=result['metrics'].get('native_full_check_passed', False),
                          unchanged_inputs=all(sha(rd / name) == h for name, h in before.items()),
                          CPD_matches_original=result['metrics'].get('critical_path_ns') == pm['metrics']['critical_path_ns'],
                          STA_matches_original=sta(rd / 'stdout.log') == sta(source / 'stdout.log'),
                          trace_presence=(rd / 'native_sta_frontier.jsonl').exists() == (mode == 'on'),
                          route_loaded='Finished loading route file' in (rd / 'stdout.log').read_text())
            write(rd / 'observer_gate.json', dict(passed=all(checks.values()), checks=checks,
                  original_run=str(source), original_route_sha256=sha(source / 'routed.route'),
                  physical_audit_reuse='Input route/net/place/RRG identity preserved; reuse original independent directed-tree/capacity audit. Native FULL newly rerun.'))
            receipts.append(dict(role=role, mode=mode, run=str(rd), passed=all(checks.values()),
                                 status=result['status'], cpd_ns=result['metrics'].get('critical_path_ns'),
                                 STA=sta(rd / 'stdout.log'), process_seconds=result['wall_seconds']))
            write(b / 'progress.json', dict(receipts=receipts))
            print(receipts[-1], flush=True)
            assert all(checks.values()), 'Preserve failed observer evidence; diagnose without repeating a completed native process'
            pair.append(receipts[-1])
        pairs.append(dict(role=role, exact_CPD=pair[0]['cpd_ns'] == pair[1]['cpd_ns'], exact_STA=pair[0]['STA'] == pair[1]['STA']))
    seal = io.seal_inputs(b / 'input_seal.json')
    assert read(b / 'input_seal.json')['passed']
    write(b / 'completion.json', dict(passed=all(r['passed'] for r in receipts), status='native_observer_terminal',
          native_analysis_calls=len(receipts), route_search_calls=0, pairs=pairs, receipts=receipts,
          physical_trace_validation='pending separate all-pin native float/route mapping audit',
          qualification='Read-only analysis-only pairs, not new routing quality or formal full-process timing.'))


if __name__ == '__main__':
    main()
