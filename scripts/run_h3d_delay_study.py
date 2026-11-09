#!/usr/bin/env python3
"""Registered, isolated factorial experiment for delay scores and critical selection."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import fcntl
import hashlib
from pathlib import Path
import re
import shutil

import three_baseline_common as receipts
from three_baseline_common import ROOT, read, sha256, utc, write_json
from run_vpr import parse_metrics
from validate_lazagna_vtr9_pilot import placements

BASE = ROOT / 'results/h3d_delay_20261027'
BINARY = ROOT / 'artifacts/bin/delay-20261027/vpr'
OLD_BINARY = ROOT / 'artifacts/bin/a4scc/vpr'
COMMON = dict(VPR_H3D_MODE='static', VPR_H3D_REACHABILITY='scc', VPR_H3D_STATS='1')
ARMS = {
    'legacy': COMMON,
    'delay': {**COMMON, 'VPR_H3D_CANDIDATE_COST':'delay', 'VPR_H3D_DELAY_BUDGET':'4096'},
    'critical': {**COMMON, 'VPR_H3D_MIN_CRITICALITY':'0.9'},
    'delay_critical': {**COMMON, 'VPR_H3D_CANDIDATE_COST':'delay',
                       'VPR_H3D_DELAY_BUDGET':'4096', 'VPR_H3D_MIN_CRITICALITY':'0.9'},
    'off': {},
    'budget1': {**COMMON, 'VPR_H3D_CANDIDATE_COST':'delay', 'VPR_H3D_DELAY_BUDGET':'1'},
    'archived_a3': COMMON,
}


def option(command, flag):
    return command[command.index(flag)+1]


def route_body_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        stream.readline()  # The first line embeds the private placement pathname/digest.
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def register():
    assert not (BASE/'protocol.json').exists()
    fixtures = {}
    newbase = ROOT/'results/three_baselines_20261027'
    for case in read(newbase/'protocol.json')['cases']:
        if case == 'dla_like.medium':
            continue  # prior proven upstream capacity failure, no placement available
        fixtures['w300_'+case] = str(newbase/'runs'/('a0_'+case)/'manifest.json')
    for case in ['clstm_like.small', 'robot_rl', 'conv_layer_hls', 'reduction_layer']:
        fixtures['w100_'+case] = str(ROOT/'results/runs'/f'koios_a0a4_seed1_{case}_a0/manifest.json')
    fixtures['smoke_ex5p'] = str(ROOT/'results/runs/paired_seeds_all_ex5p_seed1_a0/manifest.json')
    bindings = {}
    for path in fixtures.values():
        command = read(path)['command']
        for p in [path,command[1],command[2],*[option(command,f) for f in
                    ['--read_rr_graph','--net_file','--place_file']]]:
            if p not in bindings:
                bindings[p] = sha256(p)
    for binary in [BINARY, OLD_BINARY]:
        assert sha256(binary) == read(binary.parent/'manifest.json')['binary_sha256']
        bindings[str(binary)] = sha256(binary)
        bindings[str(binary.parent/'manifest.json')] = sha256(binary.parent/'manifest.json')
    bindings[str(Path(__file__).resolve())] = sha256(__file__)
    jobs = []
    def add(phase, fixture, arm, repeat=0):
        jobs.append(dict(name=f'{phase}_{fixture}_{arm}_r{repeat}', phase=phase,
                         fixture=fixture, arm=arm, repeat=repeat))
    for arm in ['off','legacy','delay','critical','delay_critical','budget1']:
        add('pilot','smoke_ex5p',arm)
    for fixture in fixtures:
        if fixture != 'smoke_ex5p':
            for arm in ['legacy','delay','critical','delay_critical']:
                add('main',fixture,arm)
    for fixture in ['w100_clstm_like.small','w300_conv_layer_hls']:
        add('main',fixture,'off')
    # Balanced rotating order; no other study jobs run during this phase.
    timing_arms = ['archived_a3','legacy','delay','critical','delay_critical']
    for repeat in range(3):
        for fixture in ['w100_clstm_like.small','w100_robot_rl']:
            for arm in timing_arms[repeat:]+timing_arms[:repeat]:
                add('serial',fixture,arm,repeat+1)
    write_json(BASE/'protocol.json',dict(utc=utc(),fixtures=fixtures,bindings=bindings,
        binary=str(BINARY),binary_sha256=sha256(BINARY),environments=ARMS,jobs=jobs,
        timeout_seconds=1200,parallel_workers=6,serial_workers=1,
        treatment='2x2 delay proxy / criticality>=0.9; original soft congestion guide, K8, miss2, opening8',
        selection='All 10 legal W300 diagnostic fixtures; 4 W100 historical gain/neutral/regression cases selected before new measurements. Not an unbiased full benchmark.',
        command_policy='Clone archived A0 options, replace executable and private paths, timing_report_npaths=0. Preserve each fixture routing budget/clock/seed.',
        smoke_gate='All six pilots must pass native FULL; off trace must match A0; budget1 must match legacy trace with no delay-scored pins.',
        metrics='CPD primary; independent planar length and vertical occupancy, failures, delay coverage, serial wall/router/planning time and peak memory secondary.',
        comparison='Within each fixture use the same binary, architecture, graph, packing, placement, seed and options. W100 and W300 reported separately.',
        limitations='No threshold tuning, no new placement seeds, no claim of LaZagna speedup. Unknown bounded distances fall back; graph is never pruned. No general RC timing model.',
        status='registered'))
    print('Registered', len(jobs), 'jobs',flush=True)


def run_one(job, protocol):
    name, fixture, arm = job['name'], job['fixture'], job['arm']
    directory = BASE/'runs'/name
    assert not directory.exists(), name
    directory.mkdir(parents=True)
    source = read(protocol['fixtures'][fixture])
    command = source['command'].copy()
    binary = OLD_BINARY if arm == 'archived_a3' else BINARY
    command[0] = str(binary)
    source_hashes = {}
    for flag, filename in [('--net_file','packed.net'),('--place_file','fixed.place')]:
        original = Path(option(command, flag)); private = directory/filename
        expected = protocol['bindings'][str(original)]
        assert sha256(original) == expected
        shutil.copyfile(original, private)
        assert sha256(private) == expected
        source_hashes[str(original)] = expected
        command[command.index(flag)+1] = str(private)
    command[command.index('--route_file')+1] = str(directory/'routed.route')
    command[command.index('--timing_report_npaths')+1] = '0'
    inputs = [binary, command[1], command[2],option(command,'--read_rr_graph'),
              directory/'packed.net',directory/'fixed.place',*source_hashes]
    receipt = receipts.run(name,command,inputs=inputs,environment=protocol['environments'][arm],
                           timeout=protocol['timeout_seconds'])
    log = (directory/'stdout.log').read_text(errors='replace')
    metrics = parse_metrics(log)
    full = receipt['status']=='completed' and metrics['native_full_check_passed'] and metrics['routing_success_reported']
    assert all(sha256(p)==h for p,h in source_hashes.items())
    assert placements(directory/'fixed.place') == placements(option(source['command'],'--place_file'))
    stats = {}
    for tag in ['H3D_INIT','H3D_SCORE','H3D_DELAY_INIT','H3D_DELAY','H3D_SUMMARY']:
        lines = re.findall(r'^'+tag+r' (.*)$', log, re.M)
        if lines:
            stats[tag] = dict(re.findall(r'(\w+)=([^\s]+)',lines[-1]))
    outputs = {p.name:dict(path=str(p),sha256=sha256(p)) for p in
               [directory/'packed.net',directory/'fixed.place',directory/'routed.route',
                directory/'stdout.log',directory/'time.txt',directory/'report_timing.setup.rpt'] if p.exists()}
    result = dict(**job,directory=str(directory),source_manifest=protocol['fixtures'][fixture],
        graph=option(command,'--read_rr_graph'),source_hashes=source_hashes,metrics=metrics,
        native_legal=full,status=receipt['status'],wall_seconds=receipt['wall_seconds'],stats=stats,outputs=outputs)
    if full:
        result['route_body_sha256'] = route_body_hash(directory/'routed.route')
        oldroute = Path(option(source['command'],'--route_file'))
        result['matches_archived_a0_route'] = result['route_body_sha256']==route_body_hash(oldroute)
    write_json(directory/'result.json',result)
    return result


def phase_run(phase):
    lock = (BASE/'runner.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    protocol = read(BASE/'protocol.json')
    assert sha256(BINARY)==protocol['binary_sha256']
    assert sha256(__file__)==protocol['bindings'][str(Path(__file__).resolve())]
    state_path = BASE/(phase+'_state.json')
    assert not state_path.exists()
    if phase != 'pilot':
        assert read(BASE/'pilot_state.json')['gate_passed']
    if phase == 'serial':
        assert read(BASE/'main_state.json')['stage']=='finished'
    jobs = [j for j in protocol['jobs'] if j['phase']==phase]
    state = dict(utc=utc(),stage='running',jobs=jobs,finished=[])
    write_json(state_path,state)
    receipts.BASE=BASE
    with ThreadPoolExecutor(max_workers=1 if phase=='serial' else protocol['parallel_workers']) as pool:
        futures = [pool.submit(run_one,job,protocol) for job in jobs]
        results = [f.result() for f in as_completed(futures)]
    state.update(stage='finished',finish_utc=utc(),finished=[r['name'] for r in results])
    if phase=='pilot':
        byarm = {r['arm']:r for r in results}
        state['gate_passed'] = (all(r['native_legal'] for r in results)
            and byarm['off']['matches_archived_a0_route']
            and byarm['budget1']['route_body_sha256']==byarm['legacy']['route_body_sha256']
            and int(byarm['budget1']['stats']['H3D_SCORE']['delay_scored'])==0)
    write_json(state_path,state)
    print(phase,'finished',len(results),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['register','pilot','main','serial'])
    action=parser.parse_args().action
    register() if action=='register' else phase_run(action)
