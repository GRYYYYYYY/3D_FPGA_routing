#!/usr/bin/env python3
"""Bind comparison inputs and independently audit every successful route."""
from collections import defaultdict
import concurrent.futures
import fcntl
from pathlib import Path

import check_route as cr
from compare_lazagna_graphs import records
from three_baseline_common import BASE, ROOT, A3_ENV, read, sha256, utc, write_json
from validate_lazagna_vtr9_pilot import placements


def normalized(command):
    return ['<binary>' if i == 0 else '<private_output>'
            if command[i-1] in ('--net_file', '--place_file', '--route_file') else arg
            for i, arg in enumerate(command)]


def audit_group(family, group, vertical_record):
    audits = []
    cr.graph_records = records
    graph = Path(group[0]['graph'])
    # Native CHANZ groups are inferred by check_route; passing a second map
    # would duplicate their capacities. Legacy paired halves need the map.
    mapping = Path(vertical_record['resource_map']) if family == 'modern' else None
    wanted_nodes, wanted_edges = set(), set()
    if mapping:
        wanted_nodes.update(n for g in read(mapping)['channels'].values() for n in g['nodes'])
    for result in group:
        for net in cr.read_trace(Path(result['directory'])/'routed.route').values():
            trace = net['trace']
            wanted_nodes.update(n.inode for n in trace)
            wanted_edges.update((a.inode, b.inode, a.switch) for a, b in zip(trace, trace[1:]) if a.switch != -1)
    print('Scanning route evidence', family, len(group), len(wanted_nodes), flush=True)
    evidence = cr.read_graph_evidence(graph, wanted_nodes, wanted_edges)
    assert evidence['sha256'] == sha256(graph)
    for result in group:
        route = Path(result['directory'])/'routed.route'
        path = BASE/'audits'/(result['name']+'.json')
        if path.exists():
            audit = read(path)
            assert audit['inputs']['route_sha256'] == sha256(route)
            assert audit['inputs']['rr_graph_sha256'] == sha256(graph)
            assert audit['inputs']['resource_map_sha256'] == (sha256(mapping) if mapping else None)
        else:
            audit = cr.audit(graph, route, mapping, graph_evidence=evidence)
            if family == 'modern':
                audit['route'].pop('horizontal_track_length', None)
                for net in audit['nets'].values():
                    net.pop('horizontal_track_length', None)
                audit['metric_note'] = 'Legacy CHANX halves encode vertical resources; omit their uncorrected horizontal length.'
            write_json(path, audit)
        audits.append(dict(name=result['name'], path=str(path), sha256=sha256(path),
                           passed=audit['passed'], route=audit['route'], errors=audit['errors'][:20]))
        print(result['name'], 'audit', audit['passed'], flush=True)
    del evidence
    return audits


def main():
    lock = (BASE/'validation_owner.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    output = BASE / 'validation.json'
    assert not output.exists()
    protocol = read(BASE / 'protocol.json')
    state = read(BASE / 'route_state.json')
    assert state['stage'] == 'finished'
    assert len(state['jobs']) == 3 * len(protocol['cases'])
    assert all(j['state'] in ('finished', 'not_run_no_placement') for j in state['jobs'])
    results = {p.parent.name: read(p) for p in sorted((BASE/'runs').glob('*/result.json'))}
    assert set(results) == {j['name'] for j in state['jobs'] if j['state'] == 'finished'}
    receipts = {p.parent.name: read(p) for p in sorted((BASE/'runs').glob('*/manifest.json'))}
    assert all(r['status'] in ('completed', 'failed', 'timeout') for r in receipts.values())
    cache = {}
    def digest(p):
        p = str(Path(p).resolve())
        if p not in cache:
            cache[p] = sha256(p)
        return cache[p]
    for p, h in protocol['preserved_sources'].items():
        assert digest(ROOT/p) == h, p
    for record in protocol['binaries'].values():
        assert digest(record['path']) == record['sha256']
    for record in protocol['architectures'].values():
        assert digest(record['path']) == record['sha256']
    vertical = {}
    for family in ('modern', 'native'):
        graph = read(BASE/f'{family}_graph.json')
        assert digest(graph['graph']) == graph['sha256']
        check = read(BASE/f'graph_audit_{family}.json')
        assert check['passed'] and check['graph_sha256'] == graph['sha256']
        for p, h in check['evidence'].items():
            assert digest(p) == h
        vertical[family] = read(BASE/f'vertical_{family}.json')
        assert vertical[family]['passed'] and vertical[family]['graph_sha256'] == graph['sha256']
        assert digest(vertical[family]['resource_map']) == vertical[family]['resource_map_sha256']
    left, right = [read(BASE/f'dsp_{family}.json') for family in ('modern', 'native')]
    dsp_equal = left['canonical_pin_endpoint_multisets_sha256'] == right['canonical_pin_endpoint_multisets_sha256']
    header_changes = []
    for name, receipt in receipts.items():
        for p, h in receipt['inputs'].items():
            if digest(p) != h:
                result = results[name]
                assert result['source'] and Path(p) == Path(result['directory'])/'fixed.place'
                assert placements(p) == placements(Path(result['source'])/'fixed.place')
                header_changes.append(dict(name=name, path=p, reason='Private header rewritten; all block coordinates unchanged'))
    pairs = []
    groups = defaultdict(list)
    for name, result in results.items():
        receipt = receipts[name]
        arm = result['arm']
        assert receipt['environment'] == (A3_ENV if arm == 'a3' else {})
        assert receipt['inputs'][receipt['command'][0]] == protocol['binaries'][arm]['sha256']
        family = 'modern' if arm == 'modern' else 'native'
        assert result['graph'] == read(BASE/f'{family}_graph.json')['graph']
        for record in result['outputs'].values():
            assert digest(record['path']) == record['sha256']
        if result['source']:
            source, directory = Path(result['source']), Path(result['directory'])
            assert digest(source/'packed.net') == digest(directory/'packed.net')
            assert placements(source/'fixed.place') == placements(directory/'fixed.place')
            assert all(digest(p) == h for p, h in result['source_hashes'].items())
            assert receipt['inputs'][str(directory/'fixed.place')] == result['source_hashes'][str(source/'fixed.place')]
        if result['native_legal']:
            assert receipt['status'] == 'completed'
            assert result['metrics']['native_full_check_passed'] and result['metrics']['routing_success_reported']
            with (Path(result['directory'])/'routed.route').open() as stream:
                assert result['outputs']['fixed.place']['sha256'] in stream.readline()
            groups[family].append(result)
    for case in protocol['cases']:
        a, b = results.get('a0_'+case), results.get('a3_'+case)
        if not (a and b):
            continue
        ar, br = receipts[a['name']], receipts[b['name']]
        assert normalized(ar['command']) == normalized(br['command'])
        assert a['graph'] == b['graph'] and a['source_hashes'] == b['source_hashes']
        pairs.append(dict(case=case, identical_input_hashes=True, identical_options_except_binary_and_paths=True))
    audits = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(audit_group, family, group, vertical[family])
                   for family, group in groups.items()]
        for future in futures:
            audits.extend(future.result())
    assert all(a['passed'] for a in audits)
    write_json(output, dict(utc=utc(), passed=True, protocol_sha256=digest(BASE/'protocol.json'),
        route_state_sha256=digest(BASE/'route_state.json'), registered_jobs=len(state['jobs']),
        attempted_routes=len(results), full_and_independently_audited_routes=len(audits), audits=audits,
        paired_native_inputs=pairs, dsp_endpoint_multisets_equal=dsp_equal,
        private_header_changes=header_changes, frozen_files_unchanged=len(protocol['preserved_sources']),
        manifests_checked=len(receipts), unique_files_rehashed=len(cache)))


if __name__ == '__main__':
    main()
