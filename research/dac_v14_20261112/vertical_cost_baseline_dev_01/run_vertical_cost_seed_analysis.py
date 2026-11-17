#!/usr/bin/env python3
"""Evaluate an immutable current/candidate route once with native endpoint STA.

An identical-route observation reuses the source physical audit. A replacement
receives its own independent physical/capacity audit after native FULL/STA.
Acceptance is deliberately a separate policy decision.
"""
import argparse
import collections

import fcntl
import os
from pathlib import Path
import shutil
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coordinated_repair_tree import from_trace
from retained_prefix_workflow import D, read, write, sha, require_formal_terminal, route_body
from endpoint_timing_policy import load

ROOT = D.parents[1]
OLD = ROOT / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0] = [str(OLD / 'execution_scripts'), str(ROOT / 'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed-order',choices=['native','rr_id','delay_rr_id'],required=True)
    parser.add_argument('--vertical-cost-weight',type=float,choices=[0.,.5,1.,2.],required=True)
    parser.add_argument('--domain-feedback',action='store_true')
    parser.add_argument('--candidate-full-sta',action='store_true')
    parser.add_argument('--expected-loaded-source-route',type=Path)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--candidate-route', type=Path)
    parser.add_argument('--trace-off', action='store_true')
    parser.add_argument('--native-cases', type=Path)
    parser.add_argument('--crossing-domain', type=Path)
    parser.add_argument('--explicit-crossings',type=Path)
    parser.add_argument('--objective',choices=['weighted_soft','weighted_capacity','physical_soft','physical_capacity'],default='weighted_soft')
    parser.add_argument('--pressure-start',type=float,default=1.)
    args = parser.parse_args()
    assert not args.crossing_domain and not args.domain_feedback and not args.explicit_crossings
    assert args.objective == 'weighted_soft' and args.candidate_full_sta and not args.trace_off
    assert args.candidate_route is None and args.pressure_start == 1.
    started = time.monotonic()
    require_formal_terminal()
    lock = (args.batch.resolve().parent / (args.batch.name + '.independent_native.lock')).open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    source, b = args.source.resolve(), args.batch.resolve()
    stage = D / 'vertical_cost_baseline_dev_01/build'
    binding = read(stage / 'binding.json')
    assert sha(stage / 'bin/vpr') == binding['binary_sha256']
    manifest = read(source / 'manifest.json')
    assert manifest['status'] == 'completed' and manifest['metrics']['native_full_check_passed']
    assert read(source / 'independent_audit.json')['audit']['passed']
    route = args.candidate_route.resolve() if args.candidate_route else source / 'routed.route'
    observation = sha(route) == sha(source / 'routed.route')
    graph = Path(manifest['command'][manifest['command'].index('--read_rr_graph') + 1])
    assert sha(graph) == manifest['shared_inputs'][str(graph)]['sha256']
    b.mkdir(exist_ok=False)
    (b / 'bin').mkdir()
    shutil.copy2(stage / 'bin/vpr', b / 'bin/vpr')
    shutil.copy2(OLD / 'runtime_dependency_binding.json', b / 'runtime_dependency_binding.json')
    files = [Path(__file__), D / 'endpoint_timing_policy.py', D / 'native_endpoint_vector_experiment_01.json',
             stage / 'binding.json', source / 'manifest.json', source / 'routed.route', source / 'packed.net',
             source / 'placed.place', source / 'independent_audit.json', route, graph, b / 'bin/vpr']
    if args.expected_loaded_source_route:
        files.append(args.expected_loaded_source_route.resolve())
    if args.native_cases:
        files.append(args.native_cases.resolve())
    if args.crossing_domain:
        assert args.native_cases is not None
        files.append(args.crossing_domain.resolve())
    if args.explicit_crossings:
        assert args.crossing_domain and not args.domain_feedback
        files.append(args.explicit_crossings.resolve())
    hashes = {str(p): sha(p) for p in files}
    write(b / 'registration.json', dict(status='registered_before_native', source=str(source), candidate_route=str(route),
          observation_only=observation, trace_off=args.trace_off, source_sha256=hashes, vertical_cost_weight=args.vertical_cost_weight,
          pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
          native_analysis_calls_planned=1, route_search_calls=0,seed_order=args.seed_order,domain_failure_release=args.domain_feedback,candidate_full_STA=args.candidate_full_sta,explicit_crossings=None if args.explicit_crossings is None else str(args.explicit_crossings.resolve()),expected_loaded_source_route=None if args.expected_loaded_source_route is None else str(args.expected_loaded_source_route.resolve()),
          limits=dict(timeout_seconds=1800, memory_bytes=64*1024**3, disk_reserve_bytes=80*1024**3)))
    io.BASE = b
    io.ADDRESS_SPACE_BYTES = 64 * 1024**3
    for p, h in hashes.items():
        io.frozen_hash(p, h)
    rd = b / 'runs/state'
    rd.mkdir(parents=True)
    for name in ['packed.net', 'placed.place']:
        shutil.copy2(source / name, rd / name)
    shutil.copy2(route, rd / 'routed.route')
    before = {n: sha(rd / n) for n in ['packed.net', 'placed.place', 'routed.route']}
    write(rd / 'pair_check.json', dict(passed=True, checks={n: sha(rd/n) == sha(source/n) for n in ['packed.net', 'placed.place']},
          scope='Exact packing and placement; input route frozen within this evaluation.'))
    cmd = list(manifest['command'])
    cmd[0] = str(b / 'bin/vpr')
    if '--route' in cmd:
        cmd.remove('--route')
    assert '--analysis' in cmd and '--route' not in cmd
    cmd[cmd.index('--timing_report_npaths') + 1] = '10'
    if '--verify_route_file_switch_id' not in cmd:
        cmd += ['--verify_route_file_switch_id', 'on']
    else:
        cmd[cmd.index('--verify_route_file_switch_id') + 1] = 'on'
    for option, name in [('--net_file', 'packed.net'), ('--place_file', 'placed.place'), ('--route_file', 'routed.route')]:
        cmd[cmd.index(option) + 1] = str(rd / name)
    env = {'VPR_JOINT_NATIVE_EXPLICIT_CROSSINGS': '', 'VPR_H3D_MODE': 'off', 'VPR_JOINT_NATIVE_REUSE_CROSSINGS': '', 'VPR_JOINT_NATIVE_VERTICAL_DOMAIN_TRACE': ''}
    env['VPR_JOINT_NATIVE_VERTICAL_COST_WEIGHT']=format(args.vertical_cost_weight,'.17g')
    env['VPR_JOINT_NATIVE_SEARCH_TRACE']=str(rd/'search_cost_trace.log')
    assert not args.domain_feedback or args.crossing_domain is not None
    env.update(VPR_JOINT_NATIVE_SEED_ORDER=args.seed_order,VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE='1' if args.domain_feedback else '0')
    if args.crossing_domain:
        env['VPR_JOINT_NATIVE_REUSE_CROSSINGS'] = str(args.crossing_domain.resolve())
        env['VPR_JOINT_NATIVE_VERTICAL_DOMAIN_TRACE'] = str(rd/'vertical_domain.log')
    if args.explicit_crossings:
        env['VPR_JOINT_NATIVE_EXPLICIT_CROSSINGS']=str(args.explicit_crossings.resolve())
    if not args.trace_off:
        env['VPR_H3D_FINAL_STA_TRACE'] = str(rd / 'native_sta_frontier.jsonl')
    if args.native_cases:
        env['VPR_JOINT_NATIVE_OBJECTIVE'] = args.objective
        env['VPR_JOINT_NATIVE_REQUEST'] = str(args.native_cases.resolve())
        env['VPR_CURRENT_STA_NATIVE_PRESSURE_START'] = str(args.pressure_start)
        env['VPR_JOINT_NATIVE_OUTPUT'] = str(rd / 'joint_native.log')
    if args.candidate_full_sta:
        assert args.native_cases is not None
        (rd/'candidate').mkdir();(rd/'candidate_restored').mkdir()
        env['VPR_JOINT_NATIVE_CANDIDATE_DIRECTORY']=str(rd/'candidate')
    preparation_seconds = time.monotonic() - started
    result = io.run(rd.name, cmd, environment=env, timeout=1800,
                    frozen=[cmd[0], cmd[1], cmd[2], graph, b / 'registration.json'],
                    private_inputs=[rd / n for n in before], tags=dict(phase='native_endpoint_vector', route_search_calls=0))
    checks = dict(completed=result['status'] == 'completed', native_FULL=result['metrics'].get('native_full_check_passed', False),
                  inputs_unchanged=all(sha(rd/n) == h for n, h in before.items()),
                  route_loaded='Finished loading route file' in (rd/'stdout.log').read_text())
    if args.crossing_domain:
        checks['domain_trace_created'] = (rd/'vertical_domain.log').is_file() and 'occupancy_restored' in (rd/'vertical_domain.log').read_text()
    audit_start = time.monotonic()
    if observation:
        shutil.copy2(source / 'independent_audit.json', rd / 'independent_audit.json')
        write(b / 'physical_audit_reuse.json', dict(passed=checks['inputs_unchanged'], original=str(source/'independent_audit.json'),
              original_sha256=sha(source/'independent_audit.json'), exact_route_sha256=sha(route), graph_sha256=sha(graph),
              qualification='Audit content is copied with explicit original provenance, not presented as a newly executed physical audit.'))
        checks['physical_audit'] = checks['inputs_unchanged']
        if args.native_cases:
            query_lines=(rd/'joint_native.log').read_text().splitlines() if (rd/'joint_native.log').exists() else []
            checks['native_control_complete'] = bool(query_lines) and 'occupancy_restored' in query_lines[-1]
        checks['reported_CPD_matches_source_at_report_precision'] = result['metrics'].get('critical_path_ns') == float(format(manifest['metrics']['critical_path_ns'], '.6g'))
    else:
        study.BASE = b
        audit = study.audit_batch({'fixture': {'original_graph': str(graph)}}, [result], b/'independent_native_analysis_audit.json')
        checks['physical_audit'] = audit['passed']
    audit_seconds = time.monotonic() - audit_start
    vector = None
    if checks['completed'] and checks['native_FULL'] and not args.trace_off:
        vector = load(rd / 'native_sta_frontier.jsonl')
        checks['full_precision_CPD_matches_report'] = float(format(vector['cpd_s']*1e9, '.6g')) == result['metrics']['critical_path_ns']
        write(b / 'endpoint_vector.json', vector)
    if args.candidate_full_sta:
        restored=rd/'candidate_restored'
        checks['actual_restored_gate']=(restored/'native_state_gate.txt').read_text()=='restored_source FULL fresh_STA actual_installed_trees\n'
        def structure(path):
            return {n:from_trace(row['trace'],collections.defaultdict(float)) if row['trace'] else None for n,row in study.cr.read_trace(path).items()}
        checks['restored_physical_tree_exact']=structure(restored/'routed.route')==structure(rd/'routed.route')
        if args.expected_loaded_source_route:
            checks['restored_ordered_native_route_exact']=route_body(restored/'routed.route')==route_body(args.expected_loaded_source_route)
        else:
            assert args.native_cases.read_text().split()==['0','0','0'],'A real repair requires an independently executed native serialization source control'
            checks['empty_control_candidate_and_restored_exact']=route_body(rd/'candidate/routed.route')==route_body(restored/'routed.route')
        restored_vector=load(restored/'native_sta_frontier.jsonl')
        checks['restored_full_vector_exact']=vector is not None and all(restored_vector[k]==vector[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
        candidate=rd/'candidate';gate=candidate/'native_state_gate.txt'
        if gate.exists():
            checks['actual_candidate_gate']=gate.read_text()=='candidate FULL fresh_STA actual_installed_trees\n'
            checks['dedicated_candidate_vector']=(candidate/'native_sta_frontier.jsonl').is_file()
        write(b/'candidate_exports.json',dict(passed=all(checks.values()),candidate_gate_present=gate.exists(),candidate=str(candidate),restored=str(restored),
            qualification='Actual same-process candidate FULL/new STA callback, exact source restoration and dedicated exports. Candidate identity differs from the outer source manifest; no separate candidate LOAD is claimed.'))
    io.seal_inputs(b / 'input_seal.json')
    checks['inputs_sealed'] = read(b/'input_seal.json')['passed']
    write(rd / 'analysis_gate.json', dict(passed=all(checks.values()), checks=checks))
    write(b / 'completion.json', dict(status='native_analysis_terminal', passed=all(checks.values()), accepted=None,
          run=str(rd), observation_only=observation, native_analysis_calls=1, route_search_calls=0,
          cpd_ns=result['metrics'].get('critical_path_ns'), full_precision_cpd_s=None if vector is None else vector['cpd_s'],
          endpoints=None if vector is None else len(vector['endpoint_ids']),
          process_status=result['status'], route_body_sha256=route_body(rd/'routed.route'),
          timing=dict(preparation_seconds=preparation_seconds, native_process_seconds=result['wall_seconds'],
                      independent_audit_seconds=audit_seconds, complete_evaluation_seconds=time.monotonic()-started),
          checks=checks, acceptance='Deferred to full-precision branch policy; never inferred from process success.'))
    print(dict(passed=all(checks.values()), cpd_ns=result['metrics'].get('critical_path_ns'),
               cpd_s=None if vector is None else vector['cpd_s'], endpoints=None if vector is None else len(vector['endpoint_ids'])), flush=True)
    assert all(checks.values()), 'Preserve terminal evaluation; diagnose without repeating a completed native process'


if __name__ == '__main__':
    main()
