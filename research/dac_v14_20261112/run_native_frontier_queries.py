#!/usr/bin/env python3
"""Common native-STA tie selection and source-bound exact-query reuse.

No route search is invoked. Historical query answers are reused only for equal
solver inputs and unchanged solver/driver semantics; every merged witness is
subsequently audited against its present route/RRG/capacities.
"""
import array
import collections
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time
from retained_prefix_workflow import D, read, write, sha, require_formal_terminal

sys.path.insert(0, str(D.parents[1] / 'scripts'))
from check_route import read_trace
from verify_path_witnesses_v2 import graph_records, f32


def fingerprint(case, mode):
    """Canonical exact solver input; mode0 never reads the occupancy filter."""
    payload = [case['net'], case['pin'], case['sink'], mode,
               sorted(case['retained']), sorted((int(n), float(v)) for n, v in case['anchors'].items()),
               sorted(case['blocked']) if mode else []]
    return hashlib.sha256(json.dumps(payload, separators=(',', ':')).encode()).hexdigest()


def groups(path):
    result = collections.defaultdict(list)
    for line in path.open():
        fields = line.split()
        assert fields[0] in ['RESULT', 'EDGE']
        key = tuple(map(int, fields[1:4]))
        result[key].append(line)
    assert all(lines[0].startswith('RESULT ') for lines in result.values())
    return result


def write_cases(path, cases):
    with path.open('w') as stream:
        stream.write(str(len(cases)) + '\n')
        for c in cases:
            stream.write(' '.join(map(str, [c['net'], c['pin'], c['sink'], len(c['retained']), len(c['anchors']), len(c['blocked'])])) + '\n')
            stream.write(' '.join(map(str, c['retained'])) + '\n')
            for node, delay in sorted(c['anchors'].items(), key=lambda pair: int(pair[0])):
                stream.write(f'{node} {delay:.17g}\n')
            stream.write(' '.join(map(str, c['blocked'])) + '\n')


def make_case(connection, traces, kinds, delays, owners, capacities):
    net, pin, sink = connection['net'], connection['pin'], connection['sink']
    trace = traces[net]['trace']
    nodes = {n.inode: n for n in trace}
    parents, switches = {}, {}
    children = collections.defaultdict(set)
    for a, z in zip(trace, trace[1:]):
        if a.switch == -1:
            continue
        assert z.inode not in parents or parents[z.inode] == a.inode
        parents[z.inode] = a.inode
        switches[a.inode, z.inode] = a.switch
        children[a.inode].add(z.inode)
    removed, node = set(), sink
    assert not children[sink]
    while node in parents:
        if children[node] - removed or (node != sink and kinds[node] == 'SINK'):
            break
        removed.add(node)
        node = parents[node]
    retained, root = set(nodes) - removed, trace[0].inode
    prefixes, stack = {root: 0.}, [root]
    while stack:
        parent = stack.pop()
        for child in children[parent]:
            assert child not in prefixes
            prefixes[child] = prefixes[parent] + delays[switches[parent, child]]
            stack.append(child)
    assert prefixes.keys() == nodes.keys()
    assert any(n.inode == sink and n.pin == pin and n.kind == 'SINK' for n in trace)
    anchors = {str(n): prefixes[n] for n in sorted(retained) if kinds[n] not in ['SINK', 'IPIN']}
    blocked = {n for n, cap in enumerate(capacities) if len(owners.get(n, [])) - int(n in nodes) >= cap}
    assert not retained & blocked
    original, node = [], sink
    while node in parents:
        original.append(node)
        node = parents[node]
    original.append(node)
    original.reverse()
    at = max(i for i, n in enumerate(original) if n in retained)
    assert str(original[at]) in anchors and not set(original[at:]) & blocked
    other = {n.inode for n in trace if n.kind == 'SINK' and n.pin is not None and n.pin != pin}
    assert other <= retained and sink not in other
    return dict(net=net, pin=pin, sink=sink, root=root, original_nodes=sorted(nodes), retained=sorted(retained),
                removed=sorted(removed), anchors=anchors, blocked=sorted(blocked), current_physical_seconds=prefixes[sink],
                original_path=original, other_sinks=sorted(other), tree_edges=[[u, v, sw, delays[sw]] for (u, v), sw in switches.items()],
                anchor_eligibility='Retained SOURCE/OPIN/channel; no IPIN/SINK anchors; same semantics as original capacity reference.',
                domain='Full-device graph; no single-cross restriction.')


def main():
    require_formal_terminal()
    resource.setrlimit(resource.RLIMIT_AS, (24 * 1024**3, 24 * 1024**3))
    signal.alarm(1800)
    lock = (D / 'critical_scope_runner.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    protocol = D / 'native_frontier_joint_policy_experiment_01.json'
    reg = read(protocol)
    assert all(sha(p) == h for p, h in reg['source_sha256'].items())
    out = D / 'native_frontier_queries_01'
    out.mkdir(exist_ok=False)
    started = time.monotonic()
    graph_binary = D / 'residual_query_offline_01/graph.bin'
    graph_binding = read(graph_binary.with_name('graph_binding.json'))
    assert sha(graph_binary) == graph_binding['binary_graph_sha256']
    first = read(Path(reg['inputs']['A0']) / 'manifest.json')
    graph = Path(first['command'][first['command'].index('--read_rr_graph') + 1])
    graph_sha = sha(graph)
    assert graph_sha == 'e695cd129be100079b479a58aefa84d69e5221df4e06f189b1f632b898e30895'
    reference = D / 'critical_capacity_potential_01'
    driver_dirs = {0: D / 'current_sta_relaxed_01', 1: D / 'current_sta_queries_01'}
    accepted_driver_hashes = {sha(p / 'src/critical_capacity_driver.cpp') for p in [reference, *driver_dirs.values()]}
    core_hashes = {n: sha(reference / 'src' / n) for n in ['critical_capacity_adapter.h', 'h3d_candidate_path.h']}
    for mode, directory in driver_dirs.items():
        ex = read(directory / 'execution.json')
        assert sha(directory / 'critical_capacity_driver') == ex['output_sha256']['critical_capacity_driver']
        assert all(sha(directory / 'src' / n) == h for n, h in core_hashes.items())
    write(out / 'registration.json', dict(status='registered_before_preparation', source_sha256={str(p): sha(p) for p in [
        Path(__file__), protocol, D / 'native_sta_frontier_dev_03/frontier_mechanism_analysis.json', graph_binary, graph]},
        pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
        query_modes=[0, 1], selection='All native worst-slack connections within eight float ULPs; no net-ID whitelist.',
        limits=reg['limits'], native_route_calls=0,
        reuse='Exact graph/core/driver semantics, target, retained nodes and prefixes; capacity-mode blocked set exact. Mode0 ignores blocked by the bound adapter, so only physical reference is reused, never capacity legality or timing.'))
    capacities, kinds, delays = array.array('I'), [], {}
    for section, element in graph_records(graph):
        attributes = element.attrib
        timing = element.find('timing')
        values = {} if timing is None else timing.attrib
        if section == 'switches':
            assert all(f32(values.get(k, 0)) == 0 for k in ['R', 'Cin', 'Cout', 'Cinternal'])
            delays[int(attributes['id'])] = f32(values.get('Tdel', 0))
        elif section == 'rr_nodes':
            assert int(attributes['id']) == len(capacities)
            assert all(f32(values.get(k, 0)) == 0 for k in ['R', 'C'])
            capacities.append(int(attributes['capacity']))
            kinds.append(attributes['type'])
        elif section == 'rr_edges':
            break
    assert len(capacities) == graph_binding['nodes'] and sys.byteorder == 'little'
    with (out / 'capacities.bin').open('wb') as stream:
        capacities.tofile(stream)
    # Discover candidates from completed reference batches. Validate a batch's
    # full source/output identities before consuming a selected cache entry.
    cache = collections.defaultdict(list)
    for path in sorted(D.glob('*/cases.json')):
        parent = path.parent
        needed = ['analysis.json', 'execution.json', 'query_stdout.log', 'src/critical_capacity_driver.cpp']
        if not all((parent / n).exists() for n in needed):
            continue
        if sha(parent / 'src/critical_capacity_driver.cpp') not in accepted_driver_hashes:
            continue
        if not all((parent / 'src' / n).exists() and sha(parent / 'src' / n) == h for n, h in core_hashes.items()):
            continue
        analysis = read(parent / 'analysis.json')
        ex = read(parent / 'execution.json')
        if not analysis.get('passed') or ex.get('source_sha256', {}).get(str(graph_binary)) != graph_binding['binary_graph_sha256']:
            continue
        cases = read(path)
        if not isinstance(cases, list):
            continue
        lookup = {(r['net'], r['pin']): r for r in cases}
        for r in analysis.get('results', []):
            if r.get('mode') not in [0, 1]:
                continue
            case = lookup[r['net'], r['pin']]
            cache[fingerprint(case, r['mode'])].append((parent, r))
    validated, memo, log_cache = set(), {}, {}
    def checked_hash(path):
        path = Path(path)
        if path not in memo:
            memo[path] = sha(path)
        return memo[path]
    def validate_history(parent):
        if parent in validated:
            return
        ex, analysis = read(parent / 'execution.json'), read(parent / 'analysis.json')
        assert all(checked_hash(p) == h for p, h in ex['source_sha256'].items())
        assert all(checked_hash(parent / p) == h for p, h in ex['output_sha256'].items())
        assert all(checked_hash(p) == h for p, h in analysis['source_sha256'].items())
        validated.add(parent)
        log_cache[parent] = groups(parent / 'query_stdout.log')
    native = read(D / 'native_sta_frontier_dev_03/frontier_mechanism_analysis.json')['roles']
    all_rows = []
    for role, source_name in reg['inputs'].items():
        source = Path(source_name)
        b = out / role
        b.mkdir()
        manifest = read(source / 'manifest.json')
        assert manifest['metrics']['native_full_check_passed'] and read(source / 'independent_audit.json')['audit']['passed']
        assert manifest['shared_inputs'][str(graph)]['sha256'] == graph_sha
        observed = D / 'native_sta_frontier_dev_03/runs' / (role + '_on')
        assert all(sha(source / n) == sha(observed / n) for n in ['routed.route', 'packed.net', 'placed.place'])
        rows = {(r['net'], r['pin']): r for r in read(D / 'native_sta_frontier_dev_03/ranked_frontiers.json')[role]}
        selected = [dict(net=r['net'], pin=r['pin'], sink=rows[r['net'], r['pin']]['tree_rr'],
                         slack_s=r['slack_s'], raw_criticality=r['criticality_raw']) for r in native[role]['tie_group']]
        write(b / 'selection.json', dict(targets=selected, input_run=str(source), selection_scope='native full-connection numerical worst-slack ties'))
        traces = read_trace(source / 'routed.route')
        owners = collections.defaultdict(list)
        for net, info in traces.items():
            for node in {n.inode for n in info['trace']}:
                owners[node].append(net)
        write(b / 'occupancy_owners.json', {str(n): v for n, v in owners.items()})
        shutil.copy2(out / 'capacities.bin', b / 'capacities.bin')
        cases = [make_case(r, traces, kinds, delays, owners, capacities) for r in selected]
        write(b / 'cases.json', cases)
        write_cases(b / 'cases.txt', cases)
        write(b / 'unit_validation.json', dict(passed=True, reused=True, scope='Unchanged validated query adapters and driver binaries.',
              source_sha256={str(p / 'unit_validation.json'): sha(p / 'unit_validation.json') for p in driver_dirs.values()}))
        inputs = [Path(__file__), protocol, out / 'registration.json', source / 'manifest.json', source / 'routed.route',
                  source / 'independent_audit.json', b / 'selection.json', graph, graph_binary, *[p / 'critical_capacity_driver' for p in driver_dirs.values()]]
        bindings = {str(p): sha(p) for p in inputs}
        write(b / 'execution_registration.json', dict(status='registered_before_query', input_run=str(source), query_modes=[0, 1],
              source_sha256=bindings, limits=reg['limits'], native_route_calls=0))
        results, receipts, processes = {}, [], []
        for mode in [0, 1]:
            missing = []
            for case in cases:
                key = (case['net'], case['pin'], mode)
                hits = cache.get(fingerprint(case, mode), [])
                if not hits:
                    missing.append(case)
                    continue
                parent, old_row = hits[0]
                validate_history(parent)
                results[key] = log_cache[parent][key]
                for name in ['analysis.json', 'execution.json', 'cases.json', 'query_stdout.log']:
                    bindings[str(parent / name)] = checked_hash(parent / name)
                receipts.append(dict(net=key[0], pin=key[1], mode=mode, reused=True, source=str(parent),
                                     query_fingerprint=fingerprint(case, mode), historical_core_seconds=old_row.get('query_seconds')))
            if missing:
                query_file = b / f'missing_mode{mode}.txt'
                write_cases(query_file, missing)
                cmd = [str(driver_dirs[mode] / 'critical_capacity_driver'), str(graph_binary), str(query_file)]
                if mode:
                    cmd.append('capacity')
                begin = time.monotonic()
                with (b / f'new_mode{mode}.log').open('w') as stdout, (b / f'new_mode{mode}.stderr').open('w') as stderr:
                    result = subprocess.run(cmd, stdout=stdout, stderr=stderr, timeout=900)
                elapsed = time.monotonic() - begin
                processes.append(dict(mode=mode, command=cmd, returncode=result.returncode, seconds=elapsed, queries=len(missing)))
                write(b / 'new_processes.json', processes)
                assert result.returncode == 0
                fresh = groups(b / f'new_mode{mode}.log')
                assert set(fresh) == {(c['net'], c['pin'], mode) for c in missing}
                results.update(fresh)
                for case in missing:
                    receipts.append(dict(net=case['net'], pin=case['pin'], mode=mode, reused=False, query_fingerprint=fingerprint(case, mode)))
        with (b / 'query_stdout.log').open('w') as stream:
            for key in sorted(results):
                stream.writelines(results[key])
        (b / 'query_stderr.log').write_text('')
        write(b / 'reuse_receipts.json', receipts)
        assert all(sha(p) == h for p, h in bindings.items())
        outputs = ['capacities.bin', 'occupancy_owners.json', 'cases.json', 'cases.txt', 'query_stdout.log',
                   'query_stderr.log', 'unit_validation.json', 'reuse_receipts.json']
        write(b / 'execution.json', dict(status='offline_terminal_pending_physical_audit', source_sha256=bindings,
              output_sha256={n: sha(b / n) for n in outputs}, native_route_calls=0,
              query_process_seconds=sum(p['seconds'] for p in processes), new_queries=sum(not r['reused'] for r in receipts),
              reused_queries=sum(r['reused'] for r in receipts), query_times_in_merged_log='Historical times for reused entries; never interpreted as current execution timing.'))
        record = dict(role=role, targets=len(cases), new_queries=sum(not r['reused'] for r in receipts),
                      reused_queries=sum(r['reused'] for r in receipts), query_process_seconds=sum(p['seconds'] for p in processes))
        all_rows.append(record)
        write(out / 'progress.json', all_rows)
        print(record, flush=True)
    write(out / 'completion.json', dict(status='query_terminal_pending_physical_audits', roles=all_rows, native_route_calls=0,
          wall_seconds=time.monotonic() - started, historic_batches_validated=[str(p) for p in sorted(validated)]))


if __name__ == '__main__':
    main()
