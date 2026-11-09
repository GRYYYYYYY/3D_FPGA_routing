#!/usr/bin/env python3
"""Bounded pilot: new graph flow and separate identical-input version controls."""
import argparse
from collections import Counter, defaultdict
import concurrent.futures
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from lazagna_vtr9_common import BASE, ROOT, PYTHON, LAZAGNA, run, sha256, utc, write_json
from run_vpr import parse_metrics

OLD = ROOT / 'results/lazagna_reproduction'
BINARY = ROOT / 'artifacts/bin/lazagna-vtr9-port-buildfix/vpr'
GUARDFIX = ROOT / 'artifacts/bin/lazagna-guardfix/vpr'


def register():
    path = BASE / 'pilot_protocol.json'
    if path.exists():
        raise RuntimeError('Protocol already registered')
    assert (BINARY.parent / 'manifest.json').exists()
    a = LAZAGNA / 'arch_files/templates/dsp_bram/vtr_arch_dsp_bram.xml'
    b = ROOT / 'vendor/LaZagna-paper/arch_files/templates/dsp_bram/vtr_arch_dsp_bram.xml'
    assert sha256(a) == sha256(b)
    write_json(path, dict(utc=utc(), binary=str(BINARY), binary_sha256=sha256(BINARY),
        architecture_template=dict(modern=str(a), paper=str(b), byte_identical=True, sha256=sha256(a)),
        small_graph=dict(grid=[40,40,2], width=100, graph_clock='route', delay_ratio=.739,
                         sb_fraction=.5, sb_pattern='subset', sb_location='repeated_interval',
                         generator_control='Apply modern and paper-era generators to the identical new base graph.'),
        fixed_controls=dict(cases={'bnn':'route', 'conv_layer':'ideal', 'dla_like.small':'ideal'},
            grid=[100,100,2], width=300, seed=1, router_iterations=200, process_timeout_seconds=1800,
            arms=['paper_guardfix', 'vtr9_port_buildfix'],
            inputs='Exact archived paper graph and successful guardfix packed/place files; every attempt has private byte-identical copies.',
            graph_clock='route', ideal_clock_scope='Explicit diagnostic for BRAM Fc=0; shared graph kept byte-identical.',
            interpretation='Tool-version control conditional on legacy graph/input compatibility. Not native A0, not H3D, and not a modern end-to-end benchmark.'),
        smoke=dict(case='ex5p', clock='route', graph='modern 40x40x2 W100', full_pnr=True),
        limits=['Pilot selection of three previously successful cases; no circuit-population inference.',
                'No runtime speedup claim from concurrent runs.',
                'Modern 100x100x2 end-to-end PnR, full OpenFPGA and bitstream flow remain outside this pilot.']))


def graph_stage():
    from check_lazagna_clock_graph_mode import scan_clocks
    from audit_lazagna_vertical import scan as scan_vertical
    arch = BASE / 'architectures/modern_40.xml'
    arch.parent.mkdir(parents=True, exist_ok=True)
    if arch.exists():
        raise RuntimeError('Small graph architecture already exists')
    shutil.copyfile(OLD / 'architectures/paper_40.xml', arch)
    blif = LAZAGNA / 'benchmarks/and2/and2.blif'
    base = BASE / 'runs/modern_graph_40_w100/rr_graph.xml'
    r = run('modern_graph_40_w100', [BINARY, arch, blif, '--pack', '--route_chan_width', 100,
            '--num_workers', 1, '--clock_modeling', 'route', '--write_rr_graph', base], inputs=[BINARY, arch, blif])
    if r['status'] != 'completed':
        return
    graphs = {}
    for label, source in [('modern', LAZAGNA), ('paper_generator', ROOT / 'vendor/LaZagna-paper')]:
        name = label + '_sb_40_w100'
        graph = BASE / 'runs' / name / 'rr_graph.xml'
        creator = source / 'scripts/3d_sb_creator.py'
        r = run(name, [PYTHON, creator, '-f', base, '-o', graph, '-p', .5, '-c', 'subset',
                     '-a', arch, '-vp', 1, '--sb_location_pattern', 'repeated_interval'],
                inputs=[creator, base, arch])
        if r['status'] != 'completed':
            return
        graphs[label] = graph
    modern = graphs['modern']
    scan_vertical(modern, BASE / 'vertical_modern_40_w100.json')
    write_json(BASE / 'clock_modern_40_w100.json', scan_clocks(modern))
    for label, left, right in [
        ('paper_vs_modern_base', OLD / 'runs/paper_graph_40_w100/rr_graph.xml', base),
        ('paper_vs_modern_sb', OLD / 'runs/paper_sb_40_w100_p50/rr_graph.xml', modern),
    ]:
        r = run('compare_' + label, [PYTHON, ROOT / 'scripts/compare_lazagna_graphs.py',
                '--left', left, '--right', right, '--output', BASE / (label + '.json')],
                inputs=[left, right], timeout=1200)
        assert r['status'] == 'completed'
    from compare_lazagna_graphs import records
    def fingerprint(path):
        digests = defaultdict(hashlib.sha256)
        counts = Counter()
        def canonical(element):
            return [element.tag, sorted(element.attrib.items()), (element.text or '').strip(),
                    [canonical(c) for c in element]]
        for section, element in records(path):
            digests[section].update(json.dumps(canonical(element), separators=(',', ':')).encode() + b'\n')
            counts[section] += 1
        return dict(sha256=sha256(path), counts=dict(counts),
                    ordered_section_fingerprints={s:h.hexdigest() for s,h in digests.items()})
    fingerprints = {label:fingerprint(path) for label,path in graphs.items()}
    same = (fingerprints['modern']['counts'] == fingerprints['paper_generator']['counts'] and
            fingerprints['modern']['ordered_section_fingerprints'] == fingerprints['paper_generator']['ordered_section_fingerprints'])
    write_json(BASE / 'generator_control.json', dict(utc=utc(), graphs=fingerprints,
        all_graph_records_identical_in_order=same,
        scope='SHA256 of canonicalized records in each section, including every node, edge, switch, capacity, timing, segment and grid record. Equality implies identical serialized graph semantics for this fixture only; inequality alone does not prove topology differs.'))
    write_json(BASE / 'graphs_complete.json', dict(utc=utc(), passed=True,
        graph=str(modern), sha256=sha256(modern), generator_control_equal=same))


def route_one(name, binary, arch, blif, graph, clock, width, *, fixed=None):
    directory = BASE / 'runs' / name
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise RuntimeError(f'Existing attempt: {directory}')
    packed, place = directory / 'packed.net', directory / 'fixed.place'
    inputs = [binary, arch, blif, graph]
    cmd = [binary, arch, blif, '--route_chan_width', width, '--num_workers', 1,
           '--router_algorithm', 'timing_driven', '--flat_routing', 'off', '--check_route', 'full',
           '--clock_modeling', clock, '--seed', 1, '--read_rr_graph', graph,
           '--route_file', directory / 'routed.route', '--timing_report_npaths', 10,
           '--net_file', packed, '--place_file', place,
           '--max_router_iterations', 200, '--routing_failure_predictor', 'off',
           '--congested_routing_iteration_threshold', '1.0']
    source_hashes = {}
    if fixed:
        for source, target in [(fixed / 'packed.net', packed), (fixed / 'fixed.place', place)]:
            shutil.copyfile(source, target)
            source_hashes[str(source)] = sha256(source)
            assert sha256(target) == source_hashes[str(source)]
            inputs += [source, target]
        cmd += ['--route', '--analysis']
    else:
        cmd += ['--pack', '--place', '--route', '--analysis', '--place_bounding_box_mode', 'cube_bb', '--inner_num', .5]
    r = run(name, cmd, inputs=inputs, timeout=1800)
    log = (directory / 'stdout.log').read_text(errors='replace')
    metrics = parse_metrics(log)
    legal = r['status'] == 'completed' and metrics['native_full_check_passed'] and metrics['routing_success_reported']
    assert all(sha256(Path(p)) == h for p,h in source_hashes.items())
    result = dict(name=name, status=r['status'], native_legal=legal, metrics=metrics,
                  fixed_source=str(fixed) if fixed else None, protected_source_hashes=source_hashes,
                  graph=str(graph), directory=str(directory), clock=clock, binary=str(binary),
                  outputs={p.name:dict(path=str(p), sha256=sha256(p))
                           for p in [packed, place, directory / 'routed.route'] if p.exists()})
    write_json(directory / 'result.json', result)
    return result


def fixed_stage():
    jobs = []
    for case, clock in [('bnn','route'), ('conv_layer','ideal'), ('dla_like.small','ideal')]:
        fixed = OLD / 'runs' / f'paper_guardfix_{clock}_pnr_{case}_w300'
        for label, binary in [('paper_guardfix', GUARDFIX), ('vtr9_port_buildfix', BINARY)]:
            jobs.append(dict(name=f'{label}_fixed_{case}', binary=binary, case=case, clock=clock, fixed=fixed))
    state = dict(utc=utc(), stage='running', jobs=[dict(name=j['name'], state='queued') for j in jobs])
    path = BASE / 'fixed_state.json'
    if path.exists():
        raise RuntimeError('Fixed-input state already exists')
    write_json(path, state)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        pending = {}
        for j in jobs:
            future = pool.submit(route_one, j['name'], j['binary'], OLD / 'architectures/paper_100.xml',
                ROOT / 'benchmarks/downloads/beyond_flatland' / (j['case'] + '.blif'),
                OLD / 'runs/paper_sb_100_w300_p50/rr_graph.xml', j['clock'], 300, fixed=j['fixed'])
            pending[future] = j
        for future in concurrent.futures.as_completed(pending):
            j = pending[future]
            try:
                result = future.result()
            except Exception as error:
                result = dict(name=j['name'], status='supervisor_error', error=repr(error), native_legal=False)
            entry = next(x for x in state['jobs'] if x['name'] == j['name'])
            entry.update(state='finished', **result)
            write_json(path, state)
    state.update(stage='finished', finished_utc=utc())
    write_json(path, state)


def smoke_stage():
    assert (BASE / 'graphs_complete.json').exists()
    return route_one('modern_smoke_ex5p', BINARY, BASE / 'architectures/modern_40.xml',
        ROOT / 'vendor/vtr/vtr_flow/benchmarks/blif/ex5p.blif',
        BASE / 'runs/modern_sb_40_w100/rr_graph.xml', 'route', 100)


def ptc_stage():
    from compare_lazagna_graphs import records
    from audit_lazagna_vertical import scan as scan_vertical
    proof = json.loads((BASE / 'generator_node_differences.json').read_text())
    assert proof['equal_except_identified_vertical_ptc']
    source = BASE / 'runs/modern_smoke_ex5p'
    assert json.loads((source / 'result.json').read_text())['native_legal']
    fixture = BASE / 'fixtures/ex5p_balanced_clb'
    fixture.mkdir(parents=True, exist_ok=False)
    graphs = {name:BASE / 'runs' / (name + '_sb_40_w100') / 'rr_graph.xml'
              for name in ['modern', 'paper_generator']}
    grid = {}
    for section,e in records(graphs['modern']):
        if section == 'rr_nodes':
            break
        if section == 'grid':
            a = e.attrib
            grid[(int(a['x']),int(a['y']),int(a['layer']))] = (a['block_type_id'],a['width_offset'],a['height_offset'])
    clbs = {e.get('name') for e in ET.parse(source / 'packed.net').getroot().findall('block')
            if e.get('instance','').startswith('clb[')}
    lines = (source / 'fixed.place').read_text().splitlines()
    entries = []
    occupied = set()
    for index,line in enumerate(lines):
        if not line.strip() or line.startswith(('#','Netlist','Array')):
            continue
        fields = line.split()
        x,y,subtile,layer = map(int,fields[1:5])
        entries.append((index,fields,x,y,subtile,layer))
        occupied.add((x,y,subtile,layer))
    assert len({e[5] for e in entries if e[1][0] in clbs}) == 1
    candidates = []
    for e in entries:
        index,fields,x,y,subtile,layer = e
        if fields[0] in clbs and (x,y,subtile,1-layer) not in occupied:
            if grid[(x,y,layer)] == grid[(x,y,1-layer)]:
                candidates.append((hashlib.sha256(('1:' + fields[0]).encode()).digest(),e))
    candidates.sort()
    moved = []
    for _,(index,fields,x,y,subtile,layer) in candidates[:len(clbs)//2]:
        fields[4] = str(1-layer)
        lines[index] = '\t'.join(fields)
        moved.append(fields[0])
    assert len(moved) == len(clbs)//2 and moved
    shutil.copyfile(source / 'packed.net',fixture / 'packed.net')
    (fixture / 'fixed.place').write_text('\n'.join(lines) + '\n')
    write_json(BASE / 'ptc_control_protocol.json', dict(utc=utc(),
        purpose='Resolve observed generator PTC-only differences with actual cross-layer routing.',
        fixture='Synthetic balanced CLB layer partition, seed1; exact XY/subtile and matched tile types/offsets. Not optimized placement.',
        source=str(source), source_place_sha256=sha256(source / 'fixed.place'),
        clb_count=len(clbs), moved_clusters=moved, fixture_directory=str(fixture),
        fixture_hashes={p.name:sha256(p) for p in fixture.iterdir()},
        control='Same binary, architecture, BLIF, packed netlist, placement, seed, budget and every graph edge; only observed vertical PTC numbering differs.',
        scope='One synthetic functionality/control case; not benchmark QoR evidence.'))
    scan_vertical(graphs['paper_generator'], BASE / 'vertical_paper_generator_40_w100.json')
    for label,graph in graphs.items():
        route_one('ptc_control_' + label, BINARY, BASE / 'architectures/modern_40.xml',
            ROOT / 'vendor/vtr/vtr_flow/benchmarks/blif/ex5p.blif', graph, 'route', 100, fixed=fixture)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['register', 'graphs', 'fixed', 'smoke', 'ptc'])
    args = parser.parse_args()
    BASE.mkdir(parents=True, exist_ok=True)
    lock = (BASE / (args.stage + '_owner.lock')).open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.stage != 'register':
        assert (BASE / 'pilot_protocol.json').exists()
        data = json.loads((BASE / 'pilot_protocol.json').read_text())
        assert sha256(BINARY) == data['binary_sha256']
    {'register':register, 'graphs':graph_stage, 'fixed':fixed_stage, 'smoke':smoke_stage, 'ptc':ptc_stage}[args.stage]()


if __name__ == '__main__':
    main()
