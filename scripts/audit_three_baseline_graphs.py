#!/usr/bin/env python3
"""Audit exact full-size graphs; compare DSP endpoints by physical identities."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path

from three_baseline_common import BASE, read, sha256, utc, write_json


def vertical(graph, family):
    from audit_lazagna_vertical import scan
    path = BASE / f'vertical_{family}.json'
    assert not path.exists()
    scan(graph, path)
    assert read(path)['passed']
    return str(path)


def clocks(graph, family):
    from check_lazagna_clock_graph_mode import scan_clocks
    path = BASE / f'clock_{family}.json'
    assert not path.exists()
    write_json(path, scan_clocks(graph))
    return str(path)


def dsp(graph, family):
    from audit_lazagna_dsp_correspondence import scan
    path = BASE / f'dsp_{family}.json'
    assert not path.exists()
    pins, summary = scan(graph)
    digest = hashlib.sha256()
    for key in sorted(pins):
        digest.update(json.dumps([key, pins[key]], separators=(',', ':')).encode())
        digest.update(b'\n')
    summary['canonical_pin_endpoint_multisets_sha256'] = digest.hexdigest()
    summary['digest_definition'] = 'Sorted physical OPIN keys with sorted physical destination multisets, compact JSON one record per line; includes capacities, excludes version-local node IDs and switch delays.'
    write_json(path, summary)
    return str(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('family', choices=['modern', 'native'])
    family = parser.parse_args().family
    output = BASE / f'graph_audit_{family}.json'
    assert not output.exists()
    record = read(BASE / f'{family}_graph.json')
    graph = Path(record['graph'])
    assert sha256(graph) == record['sha256']
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(fn, graph, family) for fn in (vertical, clocks, dsp)]
        paths = [f.result() for f in futures]
    assert all(read(p)['graph_sha256'] == record['sha256'] for p in paths)
    write_json(output, dict(utc=utc(), family=family, graph_sha256=record['sha256'],
                           evidence={p: sha256(p) for p in paths}, passed=True))


if __name__ == '__main__':
    main()
