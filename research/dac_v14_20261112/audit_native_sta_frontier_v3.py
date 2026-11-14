#!/usr/bin/env python3
"""Validate all-pin native observer against immutable route/switch evidence."""
import collections
import json
import math
from pathlib import Path
import resource
import signal
import sys
from retained_prefix_workflow import D, read, write, sha

sys.path.insert(0, str(D.parents[1] / 'scripts'))
from check_route import read_trace
from verify_path_witnesses_v2 import graph_records, f32
sys.path.insert(0, str(D / 'critical_path_diagnostics'))
from inspect_paths import report_points


def load(path):
    records = [json.loads(line) for line in path.open()]
    assert records[0]['type'] == 'metadata' and records[-1]['type'] == 'complete'
    rows = [r for r in records if r['type'] == 'pin']
    assert len(rows) == records[-1]['pin_rows']
    assert len({(r['net'], r['pin']) for r in rows}) == len(rows)
    return rows, [r for r in records if r['type'] == 'domain']


def physical_delays(route, switches):
    result = {}
    for net, info in route.items():
        trace = info['trace']
        edges = collections.defaultdict(dict)
        for a, b in zip(trace, trace[1:]):
            if a.switch != -1:
                edges[a.inode][b.inode] = a.switch
        # This graph's R/C are independently verified zero. Native RouteTree
        # accumulates float Tdel; the offline double model is recorded separately.
        values = {trace[0].inode: (0., 0.)}
        stack = [trace[0].inode]
        while stack:
            u = stack.pop()
            for v, switch in edges[u].items():
                assert v not in values
                values[v] = (f32(values[u][0] + switches[switch]), values[u][1] + switches[switch])
                stack.append(v)
        for node in trace:
            if node.kind == 'SINK':
                key = (net, node.pin)
                assert key not in result
                result[key] = dict(sink=node.inode, native_float_s=values[node.inode][0], double_s=values[node.inode][1])
    return result


def main():
    resource.setrlimit(resource.RLIMIT_AS, (24 * 1024**3, 24 * 1024**3))
    signal.alarm(1800)
    b = D / 'native_sta_frontier_dev_03'
    assert read(b / 'completion.json')['passed'] and read(b / 'input_seal.json')['passed']
    reg = read(b / 'registration.json')
    assert all(sha(p) == h for p, h in reg['source_sha256'].items())
    m = read(b / 'runs/R1_on/manifest.json')
    graph = Path(m['command'][m['command'].index('--read_rr_graph') + 1])
    assert sha(graph) == 'e695cd129be100079b479a58aefa84d69e5221df4e06f189b1f632b898e30895'
    switches = {}
    for section, element in graph_records(graph):
        if section != 'switches':
            break
        timing = element.find('timing')
        attributes = {} if timing is None else timing.attrib
        assert all(f32(attributes.get(k, 0)) == 0 for k in ['R', 'Cin', 'Cout', 'Cinternal'])
        switches[int(element.attrib['id'])] = f32(attributes.get('Tdel', 0))
    assert switches
    summaries = {}
    binding = {str(Path(__file__)): sha(__file__), str(b / 'completion.json'): sha(b / 'completion.json'),
               str(b / 'registration.json'): sha(b / 'registration.json'), str(graph): sha(graph)}
    all_frontiers = {}
    for role in ['A0', 'R1', 'Tf', 'jointR1']:
        rd = b / 'runs' / (role + '_on')
        rows, domains = load(rd / 'native_sta_frontier.jsonl')
        route = read_trace(rd / 'routed.route')
        physical = physical_delays(route, switches)
        routable = {(r['net'], r['pin']): r for r in rows if not r['driver'] and not r['ignored']}
        assert routable.keys() == physical.keys()
        mismatches = []
        double_errors = []
        atom_ids = set()
        atom_names = set()
        for key, row in routable.items():
            p = physical[key]
            assert row['tree_rr'] == p['sink'] and row['terminal_rr'] == p['sink']
            assert row['route_tree_present'] and row['atoms']
            assert row['net_name'] == route[key[0]]['name']
            if row['native_net_delay_s'] != p['native_float_s']:
                mismatches.append(dict(net=key[0], pin=key[1], exported=row['native_net_delay_s'], replay=p['native_float_s']))
            double_errors.append(abs(row['native_net_delay_s'] - p['double_s']))
            for atom in row['atoms']:
                assert atom['id'] not in atom_ids and atom['name'] not in atom_names
                atom_ids.add(atom['id'])
                atom_names.add(atom['name'])
                assert atom['tnode_external'] is not None
                assert all(t['launch'] in ({d['id'] for d in domains} | {None}) and t['capture'] in ({d['id'] for d in domains} | {None})
                           for t in atom['setup_tags'] + atom['hold_tags'])
            finite = [a['setup_slack_s'] for a in row['atoms'] if isinstance(a['setup_slack_s'], (int, float))]
            if finite:
                assert row['setup_slack_s'] == min(finite)
        numeric = [r for r in routable.values() if isinstance(r['setup_slack_s'], (float, int))]
        numeric.sort(key=lambda r: (r['setup_slack_s'], -r['native_net_delay_s'], r['net'], r['pin']))
        worst = numeric[0]['setup_slack_s']
        exact_ties = [r for r in numeric if r['setup_slack_s'] == worst]
        # This is descriptive, not a claimed final group-selection rule.
        near = [r for r in numeric if r['setup_slack_s'] <= worst + .2e-9]
        all_frontiers[role] = numeric
        by_atom = collections.defaultdict(list)
        for row in rows:
            for atom in row['atoms']:
                by_atom[atom['name']].append(row)
        report_matches = []
        for path_index, block in enumerate((rd / 'report_timing.setup.rpt').read_text().split('#Path ')[1:], 1):
            points = report_points(block)
            for source_point, sink_point in zip(points, points[1:]):
                drivers = {r['net'] for r in by_atom[source_point['pin']] if r['driver']}
                matches = [r for r in by_atom[sink_point['pin']] if not r['driver'] and r['net'] in drivers]
                if not matches:
                    continue
                assert len(matches) == 1
                row = matches[0]
                report_matches.append(dict(path=path_index, source_atom=source_point['pin'], sink_atom=sink_point['pin'],
                                           net=row['net'], pin=row['pin'], ignored=row['ignored'],
                                           exact_pin_mapping=True, location_matching_used=False))
        summary = dict(pins=len(rows), routed_connections=len(routable), unique_routed_atom_pins=len(atom_ids),
                       drivers=sum(r['driver'] for r in rows), ignored_pin_rows=sum(r['ignored'] for r in rows),
                       global_pin_rows=sum(r['global'] for r in rows), unmapped_pin_rows=sum(not r['atoms'] for r in rows),
                       exact_rr_mapping=True, native_float_mismatches=len(mismatches), native_float_mismatch_examples=mismatches[:5],
                       max_float_vs_double_error_s=max(double_errors), domains=domains,
                       worst_setup_slack_s=worst, exact_worst_slack_connections=len(exact_ties),
                       near_worst_within_0p2ns_connections=len(near),
                       top10_report_exact_connections=report_matches,
                       exact_ties=[dict(net=r['net'], pin=r['pin'], delay_ns=r['native_net_delay_s'] * 1e9,
                                       criticality=r['setup_criticality_raw'], atoms=[a['name'] for a in r['atoms']]) for r in exact_ties],
                       known_connections=[r for r in numeric if (r['net'], r['pin']) in {(6587,4),(6590,4),(1429,1),(2926,2),(6563,1),(7963,2),(5479,36)}])
        summaries[role] = summary
        for name in ['native_sta_frontier.jsonl', 'routed.route', 'manifest.json', 'observer_gate.json']:
            binding[str(rd / name)] = sha(rd / name)
    passed = all(r['native_float_mismatches'] == 0 for r in summaries.values())
    write(b / 'frontier_validation.json', dict(passed=passed, roles=summaries, source_sha256=binding,
          native_analysis_calls_added=0, route_search_calls=0,
          scope='All four already-completed observer exports; exact native float delay recurrence on the bound zero-RC graph, direct route pin/RR mapping and atom uniqueness. 0.2ns near-slack window is descriptive, not a frozen policy.',
          limitations='Atom mapping is authoritative native lookup; no independent reimplementation of intra-cluster traversal. Nonzero-RC/flat circuits not validated by this fixture. Pin slack measures worst paths through a pin, not causal CPD derivative.'))
    write(b / 'ranked_frontiers.json', all_frontiers)
    print({role: {k: v for k, v in r.items() if k not in ['known_connections', 'exact_ties']} for role, r in summaries.items()})
    assert passed, 'Preserve completed exports; diagnose recurrence/model differences without rerunning native analysis'


if __name__ == '__main__':
    main()
