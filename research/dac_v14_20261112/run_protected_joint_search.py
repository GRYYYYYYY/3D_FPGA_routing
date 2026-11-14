#!/usr/bin/env python3
"""Generate joint target paths while reserving current near-critical victim prefixes."""
import argparse
import array
import collections
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import time
from retained_prefix_workflow import D, read, write, sha
from joint_capacity_search import solve
from verify_path_witnesses_v2 import graph_records, f32


def main():
    resource.setrlimit(resource.RLIMIT_AS, (24 * 1024**3, 24 * 1024**3))
    signal.alarm(1800)
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    parser=argparse.ArgumentParser()
    parser.add_argument('--queries',type=Path,required=True)
    parser.add_argument('--batch',type=Path,required=True)
    parser.add_argument('--protected-reference',type=Path,required=True)
    args=parser.parse_args()
    batch=args.batch.resolve()
    batch.mkdir(exist_ok=False)
    references = args.queries.resolve()
    protected_dir=args.protected_reference.resolve();protected=read(protected_dir/'completion.json')
    assert protected['passed'] and all(sha(p)==h for p,h in protected['source_sha256'].items())
    reserved=read(protected_dir/'protected_nodes.json')['by_net']
    protected_results={(r['net'],r['pin']):r for r in protected['results']}
    assert protected['source_sha256'][str(references/'cases.json')]==sha(references/'cases.json')
    driver = D / 'current_sta_queries_01/critical_capacity_driver'
    binary = D / 'residual_query_offline_01/graph.bin'
    assert sha(driver) == read(D / 'current_sta_queries_01/execution.json')['output_sha256']['critical_capacity_driver']
    assert sha(binary) == read(binary.with_name('graph_binding.json'))['binary_graph_sha256']
    files = [protected_dir/'completion.json',protected_dir/'protected_nodes.json',Path(__file__), D / 'joint_capacity_search.py', D / 'test_joint_capacity_search.py', driver, binary,
             D / 'native_frontier_joint_policy_experiment_01.json']
    for role in ['current']:
        q = references
        assert read(q / 'analysis.json')['passed']
        files += [q / n for n in ['analysis.json', 'execution.json', 'cases.json', 'selection.json', 'capacities.bin', 'occupancy_owners.json']]
    bindings = {str(p): sha(p) for p in files}
    write(batch / 'registration.json', dict(status='registered_before_search', source_sha256=bindings,
          pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19], native_calls=0,
          question='Do compatible improving target paths survive protection of the currently near-critical victim prefixes, and lead to a smaller legal native repair scope?',
          selection='Current numerical worst targets with audited positive gain; protect released non-target prefixes whose slack headroom is within the maximum relaxed target gain. Diagnostic supplies exact rule and current-state binding.',
          objective='Lexicographic maximum individual source-to-sink delay then sum; local zeroRC proxy only, not circuit CPD.',
          branching='First sorted over-capacity RR node across full selected trees; forbid it on each owner where not fixed-retained, exact requery under accumulated constraints.',
          limits=dict(per_group_states=128, per_group_seconds=900, per_query_seconds=120, memory_bytes=24*1024**3, disk_reserve_bytes=80*1024**3),
          qualification='Background nets are relaxed; complete blocker restoration and native FULL/STA required. A bounded-search limit is unknown, not infeasibility. No global research limit.'))
    previous_unit=D/'native_frontier_joint_search_01/unit_validation.json'
    unit=read(previous_unit);assert unit['passed'] and all(sha(p)==h for p,h in unit['source_sha256'].items())
    write(batch/'unit_validation.json',dict(passed=True,reused=True,source_sha256={str(previous_unit):sha(previous_unit)}))
    all_results = {}
    for role in ['current']:
        q = references
        directory = batch / role
        directory.mkdir()
        analysis = read(q / 'analysis.json')
        assert all(sha(p) == h for p, h in analysis['source_sha256'].items())
        cases = {(c['net'], c['pin']): c for c in read(q / 'cases.json')}
        selected = [r for r in analysis['results'] if r['mode'] == 0 and r['improvement_ns'] > 1e-6]
        if not selected:
            write(batch/'completion.json',dict(status='no_relaxed_gain',native_calls=0))
            return
        if len({r['net'] for r in selected}) != len(selected):
            write(batch/'completion.json',dict(status='multiple_selected_pins_per_net_requires_joint_tree_model',native_calls=0))
            return
        caps = array.array('I')
        caps.frombytes((q / 'capacities.bin').read_bytes())
        actual_caps=array.array('I',caps)
        protected_count=collections.Counter(node for nodes in reserved.values() for node in nodes)
        assert not set(map(int,reserved)) & {r['net'] for r in selected}
        for node,count in protected_count.items():
            assert count<=caps[node];caps[node]-=count
        zero_nodes = {n for n, cap in enumerate(caps) if cap == 0}
        source = Path(read(q / 'execution_registration.json')['input_run'])
        manifest = read(source / 'manifest.json')
        graph = Path(manifest['command'][manifest['command'].index('--read_rr_graph') + 1])
        assert sha(graph) == manifest['shared_inputs'][str(graph)]['sha256']
        switches = {}
        for section, e in graph_records(graph):
            if section != 'switches':
                break
            t = e.find('timing')
            switches[int(e.attrib['id'])] = 0. if t is None else f32(t.attrib.get('Tdel', 0))
        fixed, initial, by_net = {}, {}, {}
        for row in selected:
            net = row['net']
            c = cases[net, row['pin']]
            fixed[net] = set(c['retained'])
            pr=protected_results[net,row['pin']];assert pr['stop']==0
            edges=pr['edges'];forward=[edges[-1][0]]+[e[0] for e in reversed(edges[:-1])]
            weights=[e[2] for e in reversed(edges[:-1])]
            used=fixed[net]|set(forward);assert not used & zero_nodes
            initial[net]=dict(nodes=used,cost=pr['cost_s'],forward=forward,weights=weights,origin='audited_protected_prefix_query')
            by_net[net] = c
        queries = []
        cache = {}
        def query(net, forbidden):
            key = net, tuple(sorted(forbidden))
            if key in cache:
                return cache[key]
            c = by_net[net]
            blocked = zero_nodes | forbidden
            assert not fixed[net] & blocked
            d = directory / f'query_{len(queries):03d}_net{net}'
            d.mkdir()
            write(d / 'case.json', dict(net=net, pin=c['pin'], sink=c['sink'], retained=sorted(fixed[net]),
                                       anchors=c['anchors'], blocked=sorted(blocked), forbidden=sorted(forbidden)))
            with (d / 'cases.txt').open('w') as stream:
                stream.write('1\n' + ' '.join(map(str, [net, c['pin'], c['sink'], len(fixed[net]), len(c['anchors']), len(blocked)])) + '\n')
                stream.write(' '.join(map(str, sorted(fixed[net]))) + '\n')
                for node, value in sorted(c['anchors'].items(), key=lambda item: int(item[0])):
                    stream.write(f'{node} {value:.17g}\n')
                stream.write(' '.join(map(str, sorted(blocked))) + '\n')
            started = time.monotonic()
            with (d / 'stdout.log').open('w') as out, (d / 'stderr.log').open('w') as err:
                proc = subprocess.run([str(driver), str(binary), str(d / 'cases.txt'), 'capacity'], stdout=out, stderr=err, timeout=120)
            receipt = dict(net=net, pin=c['pin'], forbidden=sorted(forbidden), process_seconds=time.monotonic()-started,
                           returncode=proc.returncode, case_sha256=sha(d / 'cases.txt'))
            assert proc.returncode == 0
            edges = []
            result = None
            for line in (d / 'stdout.log').read_text().splitlines():
                values = line.split()
                assert tuple(map(int, values[1:4])) == (net, c['pin'], 1)
                if values[0] == 'RESULT':
                    receipt.update(stop=int(values[4]), cost=float(values[8]), lower=float(values[9]), core_seconds=float(values[10]))
                else:
                    assert values[0] == 'EDGE' and int(values[4]) == len(edges)
                    edges.append((int(values[5]), int(values[6]), float(values[7])))
            assert receipt['stop'] in [0, 2], 'Work/storage limit is not exact infeasibility'
            if receipt['stop'] == 0:
                assert edges[-1][1] == len(caps) and edges[0][0] == c['sink']
                assert receipt['cost'] == receipt['lower']
                assert all(a[1] == b[0] for a, b in zip(edges, edges[1:]))
                forward = [edges[-1][0]] + [e[0] for e in reversed(edges[:-1])]
                weights = [e[2] for e in reversed(edges[:-1])]
                assert set(forward) & fixed[net] == {forward[0]}
                assert not (set(forward) | fixed[net]) & blocked
                result = dict(nodes=set(forward) | fixed[net], cost=receipt['cost'], forward=forward, weights=weights,
                              origin=str(d), prefix_seconds=edges[-1][2])
            queries.append(receipt)
            write(d / 'result.json', receipt)
            write(directory / 'query_progress.json', queries)
            cache[key] = result
            return result
        started = time.monotonic()
        result = solve(initial, fixed, caps, query)
        paths = result.pop('paths', {})
        targets, conflicts = [], {}
        owners = {int(k): v for k, v in read(q / 'occupancy_owners.json').items()}
        for net, path in paths.items():
            c = by_net[net]
            if not path['cost'] < c['current_physical_seconds'] - 1e-15:
                write(batch/'completion.json',dict(status='no_compatible_joint_positive_gain',native_calls=0,source_sha256=bindings,search=result));return
            targets.append(dict(net=net, pin=c['pin'], sink=c['sink'], suffix_nodes=path['forward'], suffix_weights=path['weights'],
                                physical_seconds=path['cost'], before_physical_seconds=c['current_physical_seconds'], origin=path['origin']))
        target_nets = set(paths)
        selected_owners = collections.defaultdict(set)
        for net, path in paths.items():
            for node in path['nodes']:
                selected_owners[node].add(net)
        for node, selected_nets in selected_owners.items():
            others = set(owners.get(node, [])) - target_nets
            if len(others) + len(selected_nets) > actual_caps[node]:
                conflicts[str(node)] = dict(capacity=actual_caps[node], other_nets=sorted(others), selected_nets=sorted(selected_nets))
                assert others
        result.update(protected_prefix_nets=sorted(map(int,reserved)),protected_pins=protected['protected_pins'],protected_nodes_file=str(protected_dir/'protected_nodes.json'),role=role, input_run=str(source), targets=targets, current_other_net_conflicts=conflicts,
                      query_count=len(queries), query_process_seconds=sum(r['process_seconds'] for r in queries),
                      search_seconds=time.monotonic()-started, original_selected_connections=[(r['net'], r['pin']) for r in selected],
                      source_sha256={str(q / 'analysis.json'):sha(q / 'analysis.json'), str(source / 'routed.route'):sha(source / 'routed.route'),
                                     str(batch / 'registration.json'):sha(batch / 'registration.json')},
                      qualification='RR-node compatibility among selected trees after reserving the protected existing victim prefixes; remaining background blockers still need restoration. Proxy optimum is not a CPD optimum. New query edges require independent RRG audit by transaction builder before native testing.')
        write(directory / 'opportunity.json', result)
        all_results[role] = dict(status=result['status'], selected=len(selected), queries=len(queries),
                                 expanded=result['expanded'], objective=result.get('objective'),
                                 blocker_nets=sorted({n for c in conflicts.values() for n in c['other_nets']}))
        write(batch / 'progress.json', all_results)
        print(role, all_results[role], flush=True)
    assert all(sha(p) == h for p, h in bindings.items())
    write(batch / 'completion.json', dict(status='joint_candidate_search_terminal', roles=all_results, native_calls=0,
          source_sha256=bindings, qualification='Candidate stage, not legal routing/CPD results.'))

    directory=batch/'current'
    files=[directory/'opportunity.json',batch/'registration.json',batch/'completion.json',batch/'unit_validation.json']
    files+=list(directory.glob('query_*/*'))
    write(directory/'candidate_binding.json',dict(passed=True,source_sha256={str(p):sha(p) for p in files if p.is_file()}))


if __name__ == '__main__':
    main()
