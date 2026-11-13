#!/usr/bin/env python3
"""Compare saved worst-path connections across matched, audited legal routes."""
from pathlib import Path
import argparse
import csv
import json
from inspect_paths import inspect, sha
from check_route import read_trace
from compare_connections import extract

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--run', action='append', required=True, help='Unique label=run directory')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists(), 'Preserve existing diagnostic attempts'
    runs = {}
    reports = []
    bindings = {}
    identities = []
    for spec in args.run:
        arm, path = spec.split('=', 1)
        assert arm not in runs
        rd = Path(path).resolve()
        m = json.loads((rd/'manifest.json').read_text())
        audit = json.loads((rd/'independent_audit.json').read_text())
        assert m['status'] == 'completed' and m['metrics']['native_full_check_passed']
        assert audit['audit']['passed']
        graph = m['command'][m['command'].index('--read_rr_graph')+1]
        identities.append([sha(rd/f) for f in ['packed.net', 'placed.place']] +
                          [m['shared_inputs'][k]['sha256'] for k in [m['command'][1], m['command'][2], graph]])
        required = ['manifest.json', 'routed.route', 'independent_audit.json',
                    'report_timing.setup.rpt', 'packed.net', 'placed.place']
        guides = {}
        if (rd/'h3d_final_guides.csv').exists():
            required += ['h3d_final_guides.csv', 'final_guide_audit.json']
            assert json.loads((rd/'final_guide_audit.json').read_text())['passed']
            with (rd/'h3d_final_guides.csv').open() as f:
                guides = {(int(r['net']), int(r['pin'])): r for r in csv.DictReader(f)}
        seal = rd.parent.parent/'input_seal.json'
        sealed = seal.exists() and json.loads(seal.read_text())['passed']
        if seal.exists(): bindings[str(seal)] = sha(seal)
        bindings.update({str(rd/f): sha(rd/f) for f in required})
        report = inspect(rd)
        report.update(arm=arm, batch_sealed=sealed,
                      status='legal_saved_route_diagnostic' if sealed else 'pending_batch_seal_diagnostic_only')
        reports.append(report)
        runs[arm] = (rd, audit, guides)
    assert len(runs) >= 2 and all(v == identities[0] for v in identities)
    connections = {(c['net'], tuple(c['sink_location'])) for report in reports
                   for c in report['connections'] if c['inter_cluster']}
    rows = []
    for arm, (rd, audit, guides) in runs.items():
        traces = read_trace(rd/'routed.route')
        by_name = {v['name']: (k, v) for k, v in traces.items()}
        for name, location in sorted(connections):
            net, info = by_name[name]
            paths = extract(info, location)
            assert len(paths) == 1, 'Ambiguous sink-cluster mapping; do not infer an atom-pin identity'
            p = paths[0]
            pins = {n.pin for n in info['trace'] if n.inode == p['sink'] and n.pin is not None}
            assert len(pins) == 1
            pin = next(iter(pins))
            g = guides.get((net, pin))
            rows.append(dict(arm=arm, net=name, cluster_net=net, pin=pin, sink_location=location,
                             source_rr=info['trace'][0].inode, sink_rr=p['sink'],
                             physical_connection_ns=audit['audit']['nets'][str(net)]['routed_sink_delay_ns'][str(pin)],
                             crossings=p['crossings'], direct_guide=g,
                             any_guide_on_net=any(n == net for n, _ in guides)))
    for name, location in connections:
        group = [r for r in rows if r['net'] == name and tuple(r['sink_location']) == location]
        assert len(group) == len(runs) and len({(r['source_rr'], r['sink_rr']) for r in group}) == 1
    out = dict(scope='Union of saved worst-setup-path connections, matched packed/place/architecture/netlist/RRG. '
               'Unique sink-cluster location plus identical source/sink RR; not a certified atom-pin mapping. '
               'Physical audited RR delay is not full STA delay. Direct and any-net final guides distinguish '
               'possible indirect effects, not single-event causality or earlier guide history. '
               'Unsealed batches are exploratory diagnostics, excluded from quality aggregates.',
               reports=reports, rows=rows, bindings=bindings,
               script_sha256=sha(Path(__file__)),
               helper_sha256={n: sha(Path(__file__).parent/n) for n in ['inspect_paths.py', 'compare_connections.py']})
    args.out.mkdir(parents=True)
    (args.out/'comparison.json').write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps(dict(connections=len(connections), runs={r['arm']:dict(cpd_ns=r['cpd_ns'], status=r['status']) for r in reports}, rows=rows), indent=2))

if __name__ == '__main__':
    main()
