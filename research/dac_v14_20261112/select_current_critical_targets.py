#!/usr/bin/env python3
"""Select repair targets from the supplied current legal state's STA report.

No circuit/net/pin whitelist and no reference-router route is consumed. Location
matching can be ambiguous; retain all matched route sinks and record that scope,
rather than pretending to have an exact atom-pin-to-cluster-pin mapping.
"""
import argparse
from pathlib import Path
import sys
from retained_prefix_workflow import D, read, write, sha
sys.path.insert(0, str(D / 'critical_path_diagnostics'))
from inspect_paths import inspect


def select(run):
    run = Path(run).resolve()
    manifest = read(run / 'manifest.json')
    audit = read(run / 'independent_audit.json')
    assert manifest['status'] == 'completed'
    assert manifest['metrics']['native_full_check_passed'] and audit['audit']['passed']
    path = inspect(run)
    targets = {}
    unresolved = []
    for connection in path['connections']:
        if not connection['inter_cluster']:
            continue
        if not connection['sink_paths']:
            unresolved.append(connection)
        for sink in connection['sink_paths']:
            if not sink['route_pins']:
                unresolved.append(dict(connection=connection, sink=sink))
            for pin in sink['route_pins']:
                key = (connection['cluster_net'], pin, sink['sink'])
                target = targets.setdefault(key, dict(net=key[0], pin=key[1], sink=key[2], observations=[]))
                target['observations'].append(dict(
                    source_atom_pin=connection['source_pin'], sink_atom_pin=connection['sink_pin'],
                    sink_location_matches=connection['sink_location_matches'],
                    route_pins_at_sink=len(sink['route_pins']),
                    report_increment_ns_rounded=connection['delay_ns_rounded']))
    return dict(status='current_worst_path_targets_selected', targets=list(targets.values()), unresolved=unresolved,
                current_cpd_ns=path['cpd_ns'], startpoint=path['startpoint'], endpoint=path['endpoint'],
                input_run=str(run), source_sha256={**path['source_sha256'],
                    'selector':sha(Path(__file__)), 'inspector':sha(D/'critical_path_diagnostics/inspect_paths.py')},
                mapping_scope='Current reported atom-driver net and placed sink cluster location; include every matching routed sink/pin. Ambiguous locations are explicitly retained as a conservative target set, not exact pin identity.',
                selection_scope='Worst reported setup path only. Re-run selection on each newly accepted state; near-critical multi-path extension remains a separate factor.',
                route_search_calls=0, native_analysis_calls=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists(), 'Preserve prior evidence; choose a fresh output.'
    result = select(args.run)
    write(args.output, result)
    print(dict(targets=[(r['net'], r['pin']) for r in result['targets']],
               unresolved=len(result['unresolved']), cpd_ns=result['current_cpd_ns']))
