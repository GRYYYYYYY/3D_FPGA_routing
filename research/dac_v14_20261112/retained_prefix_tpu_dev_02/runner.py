#!/usr/bin/env python3
"""One registered seed-specific default-off/trace-on diagnostic pair."""
from pathlib import Path
import argparse
import fcntl
import os
import shutil
import socket
import sys
from retained_prefix_workflow import D, read, write, sha, require_formal_terminal, normalized_command, route_body, original_records

ROOT = D.parents[1]
OLD = ROOT / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0] = [str(OLD / 'execution_scripts'), str(ROOT / 'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from audit_final_guides import audit as audit_guides

CASES = {
    'eltwise_layer': (11, 'target_feedback_dev_01'),
    'tpu_like.small.os': (21, 'target_feedback_transfer_expansion_dev_01'),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--circuit', choices=CASES, required=True)
    ap.add_argument('--stage', default='retained_prefix_candidate_01')
    args = ap.parse_args()
    require_formal_terminal()
    lock = (D / 'retained_prefix_runner.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    stage = D / args.stage
    binding = read(stage / 'binding.json')
    assert sha(stage / 'bin/vpr') == binding['binary_sha256']
    for relative, digest in binding['source_sha256'].items():
        assert sha(stage / 'src' / relative) == digest
    seed, previous_batch = CASES[args.circuit]
    previous = D / previous_batch / 'runs' / f'{args.circuit}_Tf'
    prior = read(previous / 'manifest.json')
    assert read(previous.parent.parent / 'input_seal.json')['passed']
    assert prior['status'] == 'completed' and prior['metrics']['native_full_check_passed']
    assert read(previous / 'independent_audit.json')['audit']['passed']
    assert read(previous / 'final_guide_audit.json')['passed']
    assert prior['command'][prior['command'].index('--seed') + 1] == str(seed)
    assert prior['environment']['VPR_H3D_TARGET_FEEDBACK'] == '1'
    assert prior['environment']['VPR_H3D_ALL_LAYER_BB'] == '0'
    out = D / args.out
    out.mkdir(exist_ok=False)
    (out / 'bin').mkdir()
    shutil.copy2(stage / 'bin/vpr', out / 'bin/vpr')
    shutil.copytree(stage / 'src', out / 'source')
    shutil.copy2(stage / 'binding.json', out / 'candidate_binding.json')
    shutil.copy2(stage / 'CMakeCache.txt', out / 'CMakeCache.txt')
    shutil.copy2(__file__, out / 'runner.py')
    shutil.copy2(D / 'retained_prefix_workflow.py', out / 'retained_prefix_workflow.py')
    shutil.copy2(OLD / 'runtime_dependency_binding.json', out / 'runtime_dependency_binding.json')
    binary = out / 'bin/vpr'
    env = dict(prior['environment'])
    env.update(VPR_H3D_TRACE_RETAINED_PREFIX='0', VPR_H3D_TRACE_GUIDE_MARGIN='0',
               VPR_H3D_TRACE_DP_SENSITIVITY='0', VPR_H3D_DP_TIE_PRESSURE='0',
               VPR_H3D_DP_MARGIN_PRESSURE='0', VPR_H3D_REFRESH_ASSIGNMENT='inherit')
    reg = dict(hypothesis='Decision-neutral retained crossing prefix observations on original-scope target feedback. '
        'C must reproduce frozen Tf; T changes only tracing and must reproduce C including original records. '
        'Rejected plans and uncovered calls remain visible. No new queries or objective/guidance changes.',
        circuits=[args.circuit], seed=seed, family='hybrid_o', flow='p0', width=100,
        arms=['C', 'T'], reference_arms=['A0', 'R1', 'Tf'], environment=env,
        source_sha256=binding['source_sha256'], binary=str(binary), binary_sha256=sha(binary),
        runner_sha256=sha(__file__), helper_sha256=sha(D / 'retained_prefix_workflow.py'),
        support_scripts_sha256={m.__file__: sha(m.__file__) for m in list(sys.modules.values())
            if getattr(m, '__file__', None) and m.__file__.endswith('.py') and str(ROOT) in m.__file__},
        timeout=1800, memory_bytes=64 * 1024**3, disk_reserve_bytes=80 * 1024**3, workers=1,
        pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
        host=socket.gethostname(), boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        timing_use='Diagnostic overhead only, not formal performance or independent QoR observations.')
    write(out / 'registration.json', reg)
    io.BASE = out
    io.ADDRESS_SPACE_BYTES = reg['memory_bytes']
    io.frozen_hash(stage / 'binding.json', sha(stage / 'binding.json'))
    for relative, digest in binding['source_sha256'].items():
        io.frozen_hash(stage / 'src' / relative, digest)
    io.frozen_hash(D / 'retained_prefix_workflow.py', reg['helper_sha256'])
    for path, digest in reg['support_scripts_sha256'].items():
        io.frozen_hash(path, digest)
    for path in [previous.parent.parent / 'input_seal.json', previous / 'final_guide_audit.json',
                 previous / 'h3d_final_guides.csv', D / previous_batch / f'{args.circuit}_references.json']:
        io.frozen_hash(path, sha(path))
    oldrefs = read(D / previous_batch / f'{args.circuit}_references.json')
    refs, rows = {}, []
    for role in ['A0', 'R1', 'Tf']:
        rd = previous if role == 'Tf' else Path(oldrefs[role]['path'])
        m = read(rd / 'manifest.json')
        assert normalized_command(m['command']) == normalized_command(prior['command'])
        for filename in ['packed.net', 'placed.place']:
            assert sha(rd / filename) == sha(previous / filename)
        for p, expected in m['shared_inputs'].items():
            io.frozen_hash(p, expected['sha256'])
        for filename, expected in m['outputs'].items():
            io.frozen_hash(rd / filename, expected['sha256'])
        io.frozen_hash(rd / 'manifest.json', sha(rd / 'manifest.json'))
        audit = read(rd / 'independent_audit.json') if (rd / 'independent_audit.json').exists() else None
        legal = m['status'] == 'completed' and m['metrics']['native_full_check_passed'] and audit and audit['audit']['passed']
        if audit:
            io.frozen_hash(rd / 'independent_audit.json', sha(rd / 'independent_audit.json'))
        refs[role] = dict(path=str(rd), status='legal' if legal else m['status'],
                          manifest_sha256=sha(rd / 'manifest.json'), metrics=m['metrics'],
                          physical_metrics=audit['physical_metrics'] if audit else None)
        rows.append(dict(circuit=args.circuit, arm=role, **refs[role]))
    write(out / f'{args.circuit}_references.json', refs)
    receipts, gated = [], False
    for arm in ['C', 'T']:
        require_formal_terminal()
        assert shutil.disk_usage(out).free >= reg['disk_reserve_bytes']
        name = f'{args.circuit}_{arm}'
        rd = out / 'runs' / name
        rd.mkdir(parents=True)
        for filename in ['packed.net', 'placed.place']:
            shutil.copy2(previous / filename, rd / filename)
        cmd = list(prior['command']); cmd[0] = str(binary)
        for option, filename in [('--net_file', 'packed.net'), ('--place_file', 'placed.place'), ('--route_file', 'routed.route')]:
            cmd[cmd.index(option) + 1] = str(rd / filename)
        settings = dict(env, VPR_H3D_TRACE_RETAINED_PREFIX='0' if arm == 'C' else '1')
        receipt = io.run(name, cmd, environment=settings, timeout=reg['timeout'],
            frozen=[binary, cmd[1], cmd[2], cmd[cmd.index('--read_rr_graph') + 1],
                    previous / 'packed.net', previous / 'placed.place', out / 'registration.json'],
            private_inputs=[rd / 'packed.net', rd / 'placed.place'],
            tags=dict(circuit=args.circuit, arm=arm, phase='development', diagnostic_only=True,
                      hypothesis='decision_neutral_retained_prefix'))
        checks = {f: sha(rd / f) == sha(previous / f) for f in ['packed.net', 'placed.place']}
        write(rd / 'pair_check.json', dict(passed=all(checks.values()), checks=checks, source=str(previous)))
        assert all(checks.values())
        receipts.append(receipt)
        reference = previous if arm == 'C' else out / 'runs' / f'{args.circuit}_C'
        checks = dict(native_full=receipt['status'] == 'completed' and receipt['metrics'].get('native_full_check_passed', False))
        if checks['native_full']:
            rm = read(reference / 'manifest.json')
            old_lines = (reference / 'stdout.log').read_text().splitlines()
            new_lines = (rd / 'stdout.log').read_text().splitlines()
            allowed = {line.split()[0] for line in old_lines if line.startswith('H3D_')}
            checks.update(route_body=route_body(rd / 'routed.route') == route_body(reference / 'routed.route'),
                metrics=all(receipt['metrics'].get(k) == rm['metrics'].get(k) for k in ['critical_path_ns', 'wirelength', 'iterations']),
                guides=sha(rd / 'h3d_final_guides.csv') == sha(reference / 'h3d_final_guides.csv'),
                original_records=original_records(new_lines, allowed if arm == 'C' else None) == original_records(old_lines))
        write(rd / 'prefix_trace_equivalence.json', dict(passed=all(checks.values()), checks=checks, reference=str(reference),
             qualification='C compares all prefixes present in historical Tf; T compares every original current-binary H3D record. Time fields excluded.'))
        if not all(checks.values()):
            gated = True
            write(out / 'gate_failure.json', dict(arm=arm, native_status=receipt['status'], checks=checks,
                missing_dependent_arms=['T'] if arm == 'C' else [], research_status='active_diagnose_this_branch'))
            break
    study.BASE = OLD
    audit_context = study.context(args.circuit, 'hybrid_o', seed, 100)
    study.BASE = out
    study.audit_batch(audit_context, receipts, out / f'{args.circuit}_audit.json')
    for receipt in receipts:
        rd = out / 'runs' / receipt['name']
        audit = read(rd / 'independent_audit.json') if (rd / 'independent_audit.json').exists() else None
        if audit and audit['audit']['passed']:
            audit_guides(rd)
        rows.append(dict(circuit=args.circuit, arm=receipt['tags']['arm'], path=str(rd),
            status='legal' if audit and audit['audit']['passed'] else receipt['status'], metrics=receipt['metrics'],
            physical_metrics=audit['physical_metrics'] if audit else None, process_seconds=receipt['wall_seconds']))
    io.seal_inputs(out / 'input_seal.json')
    write(out / 'observations.json', rows)
    write(out / 'completion.json', dict(status='diagnostic_gate_failed_preserved' if gated else 'diagnostic_pair_complete_not_research_complete',
        gate_passed=not gated, observations=len(rows)))


if __name__ == '__main__':
    main()
