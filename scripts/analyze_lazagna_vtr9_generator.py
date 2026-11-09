#!/usr/bin/env python3
"""Resolve the observed generator fingerprint difference without ignoring it."""
from collections import Counter
import itertools
import json

from compare_lazagna_graphs import records
from lazagna_vtr9_common import BASE, sha256, utc, write_json


def nodes(path):
    for section, element in records(path):
        if section == 'rr_edges':
            break
        if section == 'rr_nodes':
            yield dict(element.attrib), [(e.tag, dict(e.attrib), (e.text or '').strip()) for e in element]


def main():
    output = BASE / 'generator_node_differences.json'
    assert not output.exists()
    modern = BASE / 'runs/modern_sb_40_w100/rr_graph.xml'
    old = BASE / 'runs/paper_generator_sb_40_w100/rr_graph.xml'
    counts = Counter()
    shifts = Counter()
    exceptions = []
    examples = []
    for a,b in itertools.zip_longest(nodes(modern), nodes(old)):
        assert a is not None and b is not None
        counts['all_nodes'] += 1
        if a == b:
            counts['identical_nodes'] += 1
            continue
        counts['different_nodes'] += 1
        # Compare every other field verbatim before classifying a PTC-only change.
        aa = (dict(a[0]), [(tag,dict(attrs),text) for tag,attrs,text in a[1]])
        bb = (dict(b[0]), [(tag,dict(attrs),text) for tag,attrs,text in b[1]])
        aloc = next(attrs for tag,attrs,_ in aa[1] if tag == 'loc')
        bloc = next(attrs for tag,attrs,_ in bb[1] if tag == 'loc')
        ap, bp = aloc.pop('ptc'), bloc.pop('ptc')
        if aa != bb:
            exceptions.append(dict(modern=a, old=b))
            continue
        segment = next(attrs['segment_id'] for tag,attrs,_ in aa[1] if tag == 'segment')
        if a[0]['type'] != 'CHANX' or a[0]['direction'] != 'NONE' or segment != '2':
            exceptions.append(dict(reason='PTC changed outside expected vertical channels', modern=a, old=b))
            continue
        counts['vertical_ptc_only'] += 1
        shifts[int(ap)-int(bp)] += 1
        if len(examples) < 12:
            examples.append(dict(node=a[0]['id'], modern_ptc=ap, paper_generator_ptc=bp, location=aloc))
    fingerprints = json.loads((BASE / 'generator_control.json').read_text())['graphs']
    a,b = fingerprints['modern'], fingerprints['paper_generator']
    other_sections_equal = (a['counts'] == b['counts'] and all(
        value == b['ordered_section_fingerprints'][section]
        for section,value in a['ordered_section_fingerprints'].items() if section != 'rr_nodes'))
    write_json(output, dict(utc=utc(), modern_sha256=sha256(modern), paper_generator_sha256=sha256(old),
        counts=dict(counts), ptc_shifts=dict(shifts), exceptions=exceptions, examples=examples,
        all_non_node_records_identical=other_sections_equal,
        equal_except_identified_vertical_ptc=not exceptions and other_sections_equal,
        scope='Exhaustive equality of node IDs, type, direction, capacity, geometry, layers, timing and segment, excluding only the listed PTC changes; every edge including switch ID is unchanged. This is a graph-semantic check, not proof of identical tool behavior for every PTC numbering.'))
    print(dict(counts), dict(shifts), 'exceptions', len(exceptions), flush=True)


if __name__ == '__main__':
    main()
