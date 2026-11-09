#!/usr/bin/env python3
"""Independently check pilot routes and graph round trips, retaining failures."""
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import itertools
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import check_route
from compare_lazagna_graphs import records
from lazagna_common import ROOT, sha256, utc, write_json
from run_vpr import parse_metrics
from validate_lazagna_vtr9_pilot import placements

BASE = ROOT/'results/architecture_flow_20261027'


def canonical(e):
    attrs = dict(e.attrib)
    if e.tag == 'loc' and 'layer' in attrs:
        attrs['layer_low'] = attrs['layer_high'] = attrs.pop('layer')
    if e.tag == 'loc' and attrs.get('twist') == '0': del attrs['twist']
    return (e.tag, tuple(sorted(attrs.items())), (e.text or '').strip(), tuple(canonical(c) for c in e))


def semantic_records(path):
    for section, e in records(path):
        if section == 'segments' and e.get('name') == 'unused_native_Z_schema':
            continue  # Explicitly unused parser metadata; no RR node uses it.
        yield section, canonical(e)


def roundtrip(family):
    name = f'graph_{family}_25_w100_routeclock' + ('_explicit' if family in ('cb_o','hybrid_o') else '')
    original = BASE/'runs'/name/'rr_graph.xml'
    final = BASE/'runs'/f'native_import_full_{family}'/'roundtrip.xml'
    counts = Counter()
    for a, b in itertools.zip_longest(semantic_records(original), semantic_records(final)):
        if a != b: raise ValueError(f'Graph changed: {family}: {str(a)[:300]} != {str(b)[:300]}')
        counts[a[0]] += 1
    result = dict(passed=True, original=str(original), final=str(final),
                  original_sha256=sha256(original), final_sha256=sha256(final), counts=dict(counts),
                  scope='Exact ordered equality of every graph record after scalar layer/zero-twist schema normalization, excluding unused Z segment metadata')
    write_json(BASE/'pilot_validation'/f'roundtrip_{family}.json', result)
    print('roundtrip', family, 'passed', flush=True)


def route(name):
    check_route.graph_records = records
    d = BASE/'runs'/name
    manifest = json.loads((d/'manifest.json').read_text())
    if manifest['status'] != 'completed': raise ValueError(name)
    metrics = parse_metrics((d/'stdout.log').read_text())
    if not metrics['native_full_check_passed'] or not metrics['routing_success_reported']:
        raise ValueError(f'Not native legal: {name}')
    command = manifest['command']
    graph = command[command.index('--read_rr_graph')+1] if '--read_rr_graph' in command else str(d/'rr_graph.xml')
    result = check_route.audit(graph, d/'routed.route')
    if not result['passed']: raise ValueError(result['errors'])
    write_json(BASE/'pilot_validation'/f'{name}.json', dict(metrics=metrics, audit=result,
        physical_occupancy='Not quantified here; audit checks RR capacities. SB pair structure is separately checked in graph_audits_v2; CB edges are not independent capacities.'))
    print('route',name,'passed',flush=True)


def equivalent_defaults():
    a = BASE/'runs/placement_smoke_ex5p_sb_published_default'
    b = BASE/'runs/placement_smoke_ex5p_sb_integrated_default'
    packed = [ET.parse(d/'packed.net').getroot() for d in (a,b)]
    for element, directory in zip(packed, (a,b)):
        if element.attrib.pop('name') != str(directory/'packed.net'):
            raise ValueError('Unexpected packed-netlist root filename')
    checks = {'packed_netlist_except_private_root_filename': ET.tostring(packed[0]) == ET.tostring(packed[1]),
              'placement_coordinates': placements(a/'placed.place') == placements(b/'placed.place')}
    def body(p):
        h = hashlib.sha256()
        with p.open('rb') as stream:
            stream.readline()
            for part in iter(lambda: stream.read(4*1024*1024), b''): h.update(part)
        return h.hexdigest()
    checks['route_body'] = body(a/'routed.route') == body(b/'routed.route')
    checks['graph'] = sha256(a/'rr_graph.xml') == sha256(b/'rr_graph.xml')
    write_json(BASE/'pilot_validation/default_equivalence.json', dict(utc=utc(), checks=checks,
        meaning='Triton integration with partition disabled vs build-only paper binary, one smoke input'))
    if not all(checks.values()): raise ValueError(checks)


if __name__ == '__main__':
    (BASE/'pilot_validation').mkdir(exist_ok=True)
    if sys.argv[1] == 'roundtrip':
        with ProcessPoolExecutor(max_workers=4) as pool:
            list(pool.map(roundtrip, ['2d','sb','cb_o','hybrid_o']))
    elif sys.argv[1] == 'routes':
        names = ['native_import_full_'+f for f in ['2d','sb','cb_o','hybrid_o']]
        names += ['placement_smoke_ex5p_sb_'+f for f in ['published_default','integrated_default','paper_3d']]
        with ProcessPoolExecutor(max_workers=4) as pool: list(pool.map(route,names))
        equivalent_defaults()
    elif sys.argv[1] == 'defaults':
        equivalent_defaults()
