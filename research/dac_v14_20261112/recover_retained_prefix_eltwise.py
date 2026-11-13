#!/usr/bin/env python3
"""Finish audits/sealing of two completed native runs; never invoke VPR."""
import os
import socket
import time
from pathlib import Path
import run_retained_prefix as original
from retained_prefix_workflow import D, read, write, sha, require_formal_terminal

def main():
    require_formal_terminal()
    out = D / 'retained_prefix_eltwise_dev_01'
    assert not (out / 'completion.json').exists()
    assert read(D / 'retained_prefix_pipeline_01/state.json')['status'] == 'terminal_requires_diagnosis'
    reg = read(out / 'registration.json')
    assert sha(D / 'run_retained_prefix.py') == reg['runner_sha256']
    assert sha(D / 'retained_prefix_workflow.py') == reg['helper_sha256']
    original.io.BASE = out
    original.study.BASE = original.OLD
    # Resolve immutable protocol/model inputs before pointing audit outputs at this batch.
    ctx = original.study.context('eltwise_layer', 'hybrid_o', 11, 100)
    receipts = []
    for arm in ['C', 'T']:
        rd = out / 'runs' / f'eltwise_layer_{arm}'
        m = read(rd / 'manifest.json')
        assert m['status'] == 'completed' and m['metrics']['native_full_check_passed']
        assert read(rd / 'prefix_trace_equivalence.json')['passed']
        receipts.append(m)
    for m in receipts + [read(Path(r['path']) / 'manifest.json') for r in read(out / 'eltwise_layer_references.json').values()]:
        for p, expected in m['shared_inputs'].items():
            original.io.frozen_hash(p, expected['sha256'])
        rd = Path(m['cwd'])
        for filename, expected in m['outputs'].items():
            original.io.frozen_hash(rd / filename, expected['sha256'])
    for p, digest in reg['support_scripts_sha256'].items():
        original.io.frozen_hash(p, digest)
    stage = D / 'retained_prefix_candidate_01'
    binding = read(stage / 'binding.json')
    assert sha(out / 'candidate_binding.json') == sha(stage / 'binding.json')
    for relative, digest in binding['source_sha256'].items():
        original.io.frozen_hash(stage / 'src' / relative, digest)
        assert sha(out / 'source' / relative) == digest
    write(out / 'recovery_identity.json', dict(pid=os.getpid(), host=socket.gethostname(),
        start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
        time=time.time(), script_sha256=sha(__file__), reused_native=2, new_native=0,
        cause='study.BASE changed before context() read immutable benchmark protocol; original attempt/log preserved.'))
    original.study.BASE = out
    original.study.audit_batch(ctx, receipts, out / 'eltwise_layer_audit.json')
    rows = [dict(circuit='eltwise_layer', arm=role, **ref) for role, ref in read(out / 'eltwise_layer_references.json').items()]
    for m in receipts:
        rd = out / 'runs' / m['name']; audit = read(rd / 'independent_audit.json')
        assert audit['audit']['passed']
        original.audit_guides(rd)
        rows.append(dict(circuit='eltwise_layer', arm=m['tags']['arm'], path=str(rd), status='legal',
            metrics=m['metrics'], physical_metrics=audit['physical_metrics'], process_seconds=m['wall_seconds']))
    original.io.seal_inputs(out / 'input_seal.json')
    write(out / 'observations.json', rows)
    write(out / 'completion.json', dict(status='diagnostic_pair_recovered_not_research_complete',
        gate_passed=True, observations=len(rows), reused_native=2, new_native=0,
        recovery_identity_sha256=sha(out / 'recovery_identity.json')))

if __name__ == '__main__':
    main()
