#!/usr/bin/env python3
"""Register the complete experiment before observing new benchmark QoR."""
import json

from lazagna_common import ROOT, sha256, utc, write_json

BASE = ROOT/'results/architecture_flow_20261027'


def main():
    output = BASE/'benchmark_protocol.json'
    if output.exists():
        raise FileExistsError(output)
    lock = ROOT/'benchmarks/beyond_flatland.lock.json'
    benchmarks = {}
    for archive in json.loads(lock.read_text())['files']:
        for entry in archive['files']:
            path = ROOT/entry['path']
            assert sha256(path) == entry['sha256']
            benchmarks[path.stem] = dict(path=str(path), sha256=entry['sha256'])
    assert len(benchmarks) == 20
    train = ['attention_layer', 'bnn', 'eltwise_layer', 'gemm_layer', 'softmax', 'spmv']
    heldout = sorted(set(benchmarks)-set(train))
    points = [
        (8, 2, 8, 4096, .9), (4, 1, 4, 1024, .7),
        (4, 4, 16, 16384, .95), (8, 1, 16, 8192, .8),
        (8, 4, 4, 1024, .95), (16, 1, 8, 16384, .9),
        (16, 2, 16, 4096, .7), (16, 4, 4, 8192, .8)]
    variants = {}
    for variant in ['geometry', 'delay', 'critical', 'delay_critical']:
        configs = []
        for index, (k, miss, opening, budget, criticality) in enumerate(points):
            configs.append(dict(id=index, environment=dict(
                VPR_H3D_MODE='static', VPR_H3D_REACHABILITY='scc', VPR_H3D_GRAPH_ENCODING='edge',
                VPR_H3D_STATS='1', VPR_H3D_CANDIDATES=str(k), VPR_H3D_MISS_WEIGHT=str(miss),
                VPR_H3D_OPENING_WEIGHT=str(opening), VPR_H3D_DELAY_BUDGET=str(budget),
                VPR_H3D_CANDIDATE_COST='delay' if 'delay' in variant else 'geometry',
                VPR_H3D_MIN_CRITICALITY=str(criticality if 'critical' in variant else 0))))
        variants[variant] = configs
    binaries = {label: ROOT/'artifacts/bin'/name/'vpr' for label, name in [
        ('A0', 'baseline'), ('R1', 'flatland-edge-v2'), ('B2', 'lazagna-vtr9-port-buildfix'),
        ('paper_buildfix', 'flatland-buildfix'), ('P1', 'flatland-triton-integrated')]}
    write_json(output, dict(utc=utc(), status='registered_before_formal_benchmark_QoR',
        benchmarks=benchmarks, training=train, heldout=heldout, tuning_seeds=[11], evaluation_seeds=[21, 23, 25],
        disclosure='All 20 circuits have prior-study observations. This is a fresh circuit/seed split for this selection exercise, not a claim of previously unseen benchmark families.',
        architectures=['sb', 'cb_o', 'hybrid_o'],
        architecture_model='Explicit common-plane counterfactuals: common 260/40 segments, SB planar graph, original generated vertical resources. Keep as-released author architectures as historical/reference data. No equal-area or equal-via-budget claim.',
        model_gate=['exact ordinary-node and same-layer-edge equality', 'unchanged full cross-layer resources and switch timing',
                    'original/native import semantic equality', 'FULL and independent route audit on small control'],
        sizing=dict(census_seed=11, census_grid=[150, 150, 2], candidate_sides=[25, 40, 60, 80, 100, 125, 150, 200],
            rule='Smallest registered side with every logical block class occupancy <=0.80 using actual paper-packed counts and actual/deterministically derived grid capacities. Common size across all architectures/placements for each circuit. No CPD-based resizing.',
            failures='Keep census failure or capacity overflow registered; any extension requires a dated amendment before dependent routing.'),
        channel_width=100, clock_modeling='ideal',
        width_sensitivity=dict(width=300, circuits=['spmv', 'bnn', 'robot_rl', 'conv_layer_hls'],
            seed_by_split=dict(training=11, heldout=21), flows=['P0', 'P1'], routers=['A0', 'R1', 'B2'],
            tuning='Transfer W100 selections unchanged; not another tuning budget'),
        placement=dict(P0='Official native VTR9 placement on the same paper-packed netlist and imported physical graph',
            P1='Complete paper placement including weighted TritonPart, fixed author CSV settings for each architecture; no local placement hyperparameter retuning',
            partition_seed=1, imbalance=0.03, packing_control='P1 must execute packing for critical weights. Assert packed semantics match the census across seed/architecture; stop affected pairs and diagnose if they differ.',
            pair_control='Private copies of exactly the same packed netlist, placement coordinates, graph and timing for A0/R1/B2'),
        tuning=dict(variants=variants, configurations_per_variant=8, circuit_count=6, architectures=3,
            placement='P0', route_budget=576, fixed_ablation_id=0,
            selection='Per architecture and variant: maximize number of legal results out of six, then minimize geometric mean CPD over common successful training cases among tied candidates, then geometric mean router time, then configuration ID. No CPD tie-break if common set empty.',
            overall_R1='Choose among four selected variants by the same rule; deterministic variant order geometry,delay,critical,delay_critical breaks final ties. Freeze selection before held-out routing.',
            interpretation='Finite shared design, not exhaustive optimization. Ignored feature-specific parameters do not create extra runs/budget; no causal parameter effect inferred from confounded search points.'),
        evaluation=dict(main='All 14 held-out circuits x3 seeds x3 architectures x2 placements x A0/R1/B2',
            matched_2d='Official A0 P0 on exact logical-capacity matched near-square 2D, all evaluation circuits/seeds; common denominator for all three 3D architectures',
            fixed_ablation='All14 held-out circuits, seed21, P1, all3 architectures, each of four variants at config0',
            tuned_ablation='Same fixed-ablation cases, independently selected config per variant at equal 8-config training budget',
            deduplication='Identical immutable input/environment runs may be reused with explicit reference, never counted as independent repeats'),
        statistics=dict(primary='Circuit-balanced geometric mean paired CPD ratio; average the three seed CPDs within circuit first',
            display='Improvement against same-architecture A0 (common 2D in parentheses), plus absolute CPD, geomean, maximum with circuit/seed, regressions and failures',
            rankings='Absolute final CPD and common-2D normalization; per-seed rankings, complete-common intersection, coverage and failures. Rank reversal is not required.',
            failures='Every registered case retained. Report legal/attempted, timeout/resource/route failure separately; no ratio using zero/missing CPD and no unqualified all-suite claim from successful subset.',
            costs=['router and end-to-end time', 'packing/partition/graph conversion setup separately', 'planar wirelength excluding SB half-nodes',
                   'actual crossing source occupancy, SB pair occupancy, CB output-pin sharing', 'delay known/unknown and query budget coverage']),
        external_baselines=dict(B1='Published LaZagna VTR8.1 normalized literature values only; absent shared denominator, no direct absolute ratio or blanket victory claim',
            B2='Frozen modern LaZagna VTR9-code port on identical graph/pack/place; toolchain/router comparison',
            B3='Official VTR9 A0 on identical graph/pack/place; isolates our routing changes'),
        runtime=dict(serial=True, repeats=3, circuits=['spmv', 'robot_rl'], seeds=dict(spmv=11, robot_rl=21),
            architectures=['sb', 'cb_o', 'hybrid_o'], flows=['P0', 'P1'], routers=['A0', 'R1', 'B2'],
            ordering='Rotate router order by repetition; no concurrent VPR/partition processes owned by this study during serial timing',
            scope='Runtime inference limited to this preregistered subset; parallel sweep wall time is not speedup evidence'),
        execution=dict(max_workers=6, threads_per_process=1, route_timeout_seconds=1800,
            placement_timeout_seconds=3600, max_router_iterations=200, failure_predictor='off', check_route='full',
            independent_audit='Every reported legal route: directed edge, switch, tree and RR node capacity checks; native FULL remains required'),
        binaries={k: dict(path=str(p), sha256=sha256(p)) for k,p in binaries.items()},
        registration_source_sha256=sha256(__file__), benchmark_lock_sha256=sha256(lock),
        amendments='Append dated evidence without changing this protocol. Do not erase failed attempts or tune on held-out QoR.'))
    print('Registered20 circuits; train6 / evaluation14; 576 tuning routes; held-out seeds21/23/25')


if __name__ == '__main__': main()
