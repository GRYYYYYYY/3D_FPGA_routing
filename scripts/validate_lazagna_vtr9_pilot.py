#!/usr/bin/env python3
"""Independently audit successful pilot routes and validate frozen evidence."""
from collections import defaultdict
import argparse
import json
from pathlib import Path
import subprocess

import check_route as cr
from compare_lazagna_graphs import records
from lazagna_vtr9_common import BASE, ROOT, SOURCE, sha256, utc, write_json


def read(path):
    return json.loads(Path(path).read_text())


def placements(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        if not line.strip() or line.startswith(('#', 'Netlist', 'Array')):
            continue
        fields = line.split('#')[0].split()
        assert len(fields) == 5, fields
        assert fields[0] not in result
        result[fields[0]] = tuple(map(int, fields[1:]))
    assert result
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--small-only', action='store_true', help='Audit the completed small-graph subset while fixed controls run')
    args = parser.parse_args()
    validation_path = BASE / ('small_validation.json' if args.small_only else 'validation.json')
    if validation_path.exists():
        raise RuntimeError('Validation already exists')
    state = read(BASE / 'fixed_state.json')
    if not args.small_only:
        assert state['stage'] == 'finished'
    assert (BASE / 'graphs_complete.json').exists()
    assert (BASE / 'runs/modern_smoke_ex5p/result.json').exists()
    all_results = [read(p) for p in sorted((BASE / 'runs').glob('*/result.json'))]
    if args.small_only:
        all_results = [r for r in all_results if '_fixed_' not in r['name']]
    assert len(all_results) == (3 if args.small_only else 9)
    receipts = [read(p) for p in sorted((BASE / 'runs').glob('*/manifest.json'))]
    if args.small_only:
        receipts = [r for r in receipts if '_fixed_' not in r['name']]
    assert all(x['status'] in ('completed', 'failed', 'timeout') for x in receipts)
    digest_cache = {}
    def digest(path):
        key = str(Path(path).resolve())
        if key not in digest_cache:
            digest_cache[key] = sha256(key)
        return digest_cache[key]
    frozen = read(BASE / 'source_lock.json')['protected_files']
    assert all(digest(ROOT / path) == expected for path,expected in frozen.items())
    input_changes = []
    result_by_name = {r['name']:r for r in all_results}
    for receipt in receipts:
        for path, expected in receipt['inputs'].items():
            if digest(path) != expected:
                # A fixed-input solver may rewrite only the private placement header.
                result = result_by_name[receipt['name']]
                assert result['fixed_source']
                assert Path(path) == Path(result['directory']) / 'fixed.place'
                source = Path(result['fixed_source']) / 'fixed.place'
                assert placements(path) == placements(source)
                input_changes.append(dict(name=receipt['name'], path=path,
                    reason='Solver rewrote private placement header; every block coordinate is unchanged.'))
    groups = defaultdict(list)
    audits = []
    for result in all_results:
        for output in result['outputs'].values():
            assert digest(output['path']) == output['sha256']
        if result['fixed_source']:
            source = Path(result['fixed_source'])
            directory = Path(result['directory'])
            assert digest(source / 'packed.net') == digest(directory / 'packed.net')
            assert placements(source / 'fixed.place') == placements(directory / 'fixed.place')
            for p,h in result['protected_source_hashes'].items():
                assert digest(p) == h
        if result['native_legal']:
            route = Path(result['directory']) / 'routed.route'
            with route.open() as stream:
                assert result['outputs']['fixed.place']['sha256'] in stream.readline()
            existing = BASE / 'audits' / (result['name'] + '.json')
            if existing.exists():
                audit = read(existing)
                vertical = read(BASE / ('vertical_paper_generator_40_w100.json'
                    if result['name'] == 'ptc_control_paper_generator' else 'vertical_modern_40_w100.json'))
                assert audit['passed']
                assert audit['inputs']['route_sha256'] == digest(route)
                assert audit['inputs']['rr_graph_sha256'] == digest(result['graph'])
                assert audit['inputs']['resource_map_sha256'] == digest(vertical['resource_map'])
                audits.append(dict(name=result['name'], passed=True, path=str(existing),
                    sha256=digest(existing), route=audit['route'], errors=[]))
            else:
                groups[result['graph']].append(result)
    cr.graph_records = records
    for graph_name, results in groups.items():
        graph = Path(graph_name)
        if graph == BASE / 'runs/modern_sb_40_w100/rr_graph.xml':
            vertical = read(BASE / 'vertical_modern_40_w100.json')
        elif graph == BASE / 'runs/paper_generator_sb_40_w100/rr_graph.xml':
            vertical = read(BASE / 'vertical_paper_generator_40_w100.json')
        else:
            vertical = read(ROOT / 'results/lazagna_reproduction/vertical_paper_100_w300.json')
        assert vertical['passed'] and digest(graph) == vertical['graph_sha256']
        mapping = Path(vertical['resource_map'])
        assert digest(mapping) == vertical['resource_map_sha256']
        physical = read(mapping)
        assert physical['graph_sha256'] == digest(graph)
        wanted_nodes = {n for g in physical['channels'].values() for n in g['nodes']}
        wanted_edges = set()
        del physical
        for result in results:
            route = Path(result['directory']) / 'routed.route'
            for net in cr.read_trace(route).values():
                trace = net['trace']
                wanted_nodes.update(n.inode for n in trace)
                wanted_edges.update((a.inode,b.inode,a.switch) for a,b in zip(trace,trace[1:]) if a.switch != -1)
        evidence = cr.read_graph_evidence(graph, wanted_nodes, wanted_edges)
        assert evidence['sha256'] == digest(graph)
        for result in results:
            route = Path(result['directory']) / 'routed.route'
            out = BASE / 'audits' / (result['name'] + '.json')
            assert not out.exists()
            audit = cr.audit(graph, route, mapping, graph_evidence=evidence)
            audit['route'].pop('horizontal_track_length', None)
            audit['metric_note'] = 'Do not treat CHANX vertical halves as planar wirelength.'
            write_json(out, audit)
            audits.append(dict(name=result['name'], passed=audit['passed'], path=str(out),
                               sha256=sha256(out), route=audit['route'], errors=audit['errors'][:20]))
            print(result['name'], 'audit', audit['passed'], flush=True)
        del evidence
    assert all(x['passed'] for x in audits)
    ptc_audits = [a for a in audits if a['name'].startswith('ptc_control_')]
    assert len(ptc_audits) == 2
    assert all(a['route']['cross_layer_sink_connections'] > 0 for a in ptc_audits)
    pairs = []
    for case in ([] if args.small_only else ['bnn', 'conv_layer', 'dla_like.small']):
        left = result_by_name['paper_guardfix_fixed_' + case]
        right = result_by_name['vtr9_port_buildfix_fixed_' + case]
        lm = read(Path(left['directory']) / 'manifest.json')
        rm = read(Path(right['directory']) / 'manifest.json')
        def normalized(command):
            out = []
            for i, arg in enumerate(command):
                if i == 0:
                    out.append('<binary>')
                elif i > 0 and command[i-1] in ('--net_file', '--place_file', '--route_file'):
                    out.append('<private_output>')
                else:
                    out.append(arg)
            return out
        assert normalized(lm['command']) == normalized(rm['command'])
        assert left['fixed_source'] == right['fixed_source'] and left['graph'] == right['graph']
        row = dict(case=case, old_status=left['status'], modern_status=right['status'],
                   old_legal=left['native_legal'], modern_legal=right['native_legal'],
                   identical_command_except_binary_and_private_paths=True)
        if left['native_legal'] and right['native_legal']:
            row.update(old_cpd_ns=left['metrics']['critical_path_ns'], modern_cpd_ns=right['metrics']['critical_path_ns'],
                       cpd_change_percent=(right['metrics']['critical_path_ns']/left['metrics']['critical_path_ns']-1)*100,
                       old_iterations=left['metrics']['iterations'], modern_iterations=right['metrics']['iterations'])
        pairs.append(row)
    assert subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'], text=True) == ''
    summary = dict(utc=utc(), passed=True, pilot_only=True, attempted_routes=len(all_results),
        full_and_independently_audited_routes=len(audits), audits=audits, fixed_pairs=pairs,
        frozen_files_unchanged=len(frozen), manifests_checked=len(receipts), unique_files_rehashed=len(digest_cache),
        private_placement_header_changes=input_changes,
        version=read(ROOT / 'artifacts/bin/lazagna-vtr9-port-buildfix/manifest.json')['version_output'],
        limitations=read(BASE / 'pilot_protocol.json')['limits'])
    write_json(validation_path, summary)
    print(json.dumps({k:v for k,v in summary.items() if k in ('passed','attempted_routes','full_and_independently_audited_routes','fixed_pairs')}, indent=2))


if __name__ == '__main__':
    main()
