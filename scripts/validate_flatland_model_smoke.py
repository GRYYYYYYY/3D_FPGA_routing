#!/usr/bin/env python3
"""Batch independent route and schema checks for the controlled model gate."""
from concurrent.futures import ProcessPoolExecutor
from itertools import zip_longest
import json
from pathlib import Path

import check_route as cr
from compare_lazagna_graphs import records
from lazagna_common import ROOT, sha256, utc, write_json
from run_flatland_pack_census import packed_summary
from run_vpr import parse_metrics
from validate_flatland_pilots import semantic_records
from validate_lazagna_vtr9_pilot import placements

BASE = ROOT/'results/architecture_flow_20261027'


def run(family):
    cr.graph_records = records
    protocol = json.loads((BASE/'model_smoke_protocol.json').read_text())
    fixture = protocol['fixtures'][family]
    original, native = fixture['graph'], fixture['conversion']['graph']
    count = 0
    for a, b in zip_longest(semantic_records(original), semantic_records(native)):
        assert a == b, (family, count)
        count += 1
    controls = ['p0_a0', 'p0_off'] if family == 'matched_2d' else ['p0_a0', 'p0_delay', 'p1_paper', 'p1_a0', 'p1_delay']
    directories = [BASE/'runs'/f'model_smoke_{family}_{arm}' for arm in controls]
    evidence = cr.batch_graph_evidence(original, [d/'routed.route' for d in directories])
    expected_pack = packed_summary(BASE/'runs/placement_smoke_ex5p_sb_paper_3d/packed.net')['semantic_sha256']
    results = []
    for arm, d in zip(controls, directories):
        receipt = json.loads((d/'manifest.json').read_text()); assert receipt['status'] == 'completed'
        metrics = parse_metrics((d/'stdout.log').read_text())
        assert metrics['native_full_check_passed'] and metrics['routing_success_reported']
        assert packed_summary(d/'packed.net')['semantic_sha256'] == expected_pack
        reference = BASE/'runs'/f"model_smoke_{family}_{'p0_a0' if arm.startswith('p0') else 'p1_paper'}"/'placed.place'
        assert placements(d/'placed.place') == placements(reference)
        result = cr.audit(original, d/'routed.route', graph_evidence=evidence)
        assert result['passed'], result['errors']
        output = BASE/'model_smoke_validation'/f'{d.name}.json'
        write_json(output, dict(utc=utc(), metrics=metrics, independent_audit=result,
            pack_semantic_sha256=expected_pack, placement_reference=str(reference),
            interpretation='Ex5p model gate only; no benchmark gains. Native FULL plus this scoped audit are both required.'))
        results.append(dict(name=d.name, passed=True, metrics=metrics, audit_path=str(output)))
    return dict(family=family, passed=True, schema_records_exactly_equal=count,
                original_sha256=sha256(original), native_sha256=sha256(native), results=results)


def main():
    output = BASE/'model_smoke_validation'; output.mkdir(exist_ok=False)
    assert json.loads((BASE/'common_plane_models/v2/n25_w100/independent_validation.json').read_text())['passed']
    negative = BASE/'runs/model_smoke_matched_2d_p0_delay'
    assert json.loads((negative/'manifest.json').read_text())['status'] == 'failed'
    assert 'currently require clustered routing, two stacked layers' in (negative/'stdout.log').read_text()
    with ProcessPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(run, ['sb', 'cb_o', 'hybrid_o', 'matched_2d']))
    write_json(output/'summary.json', dict(utc=utc(), passed=True, results=results, legal_routes=17,
        attempted_routes=18, negative_test=dict(path=str(negative), result='Single-layer graph rejected by active two-layer-only H3D guard; retained failure, not an algorithm QoR result'),
        gates=['common plane exact equality', 'vertical resources preserved', '2D logical capacities matched',
               'original/native schema semantics identical', '17 FULL + independent route checks', 'packing and paired placements controlled']))
    print('Controlled model gate:17 routes,4 graph imports,all passed')


if __name__ == '__main__': main()
