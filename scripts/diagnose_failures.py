#!/usr/bin/env python3
"""Frozen-input, finite VPR failure diagnosis. Original results are never overwritten.

Stages: predictor off/50; off/200; off/500 for unresolved cases and their A0
controls; independent width 120/140/160 scan at off/200. All algorithms retain
their original binaries/environment. The revised --native-primary protocol
retains default normal congestion scheduling and skips 500-iteration reruns
only for independently certified infeasible instances. The earlier protocol's
fixed high-effort transition after iteration 50 remains an auxiliary arm.
"""
import argparse
import concurrent.futures
import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from check_route import sha256
from collect_results import native_counters
from run_vpr import parse_metrics

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/failure_diagnosis'
PLAN = ROOT / 'configs/failure_diagnosis.json'


def capacity_policy_file():
    refined=BASE/'certified_infeasibility_policy_source_classes.json'
    return refined if refined.exists() else BASE/'certified_infeasibility_policy.json'


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


def initialize():
    if PLAN.exists():
        raise RuntimeError('Protocol already exists; use its frozen plan')
    analysis = ROOT / 'results/analysis.json'
    rows = json.loads(analysis.read_text())['rows']
    selected = [r for r in rows if not r['valid_solution']]
    assert len(selected) == 132
    selected += [r for r in rows if (r['circuit'], r['variant']) in {
        ('clstm_like.small', 'a0'), ('clstm_like.small', 'a0_prune'), ('robot_rl', 'a0')}]
    assert len(selected) == 135
    cache = {}
    def checked_hash(path, expected):
        if path not in cache:
            cache[path] = sha256(path)
        if cache[path] != expected:
            raise RuntimeError('Frozen source changed: ' + path)
    sources = []
    for row in selected:
        path = Path(row['output']) / 'manifest.json'
        manifest = json.loads(path.read_text())
        for inp in manifest['inputs'].values():
            checked_hash(inp['path'], inp['sha256'])
        sources.append(dict(circuit=row['circuit'], variant=row['variant'],
                            original_matrix=row['matrix'], original_output=row['output'],
                            original_valid=row['valid_solution'],
                            manifest_sha256=sha256(path), manifest=manifest))
    # Prioritize the two specific regressions, then interleave circuit families.
    sources.sort(key=lambda s: (s['circuit'] not in ['clstm_like.small', 'robot_rl'],
                               s['variant'] != 'a0', s['variant'], s['circuit']))
    plan = dict(schema=1, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                original_analysis_sha256=sha256(analysis), original_failures=132,
                source_runs=len(sources), frozen_files_verified=len(cache), sources=sources,
                predictor='off', budgets=[50, 200, 500],
                congestion_mode_after_iteration=50,
                extension_rule='500 for every unresolved 200 run, plus its A0; clstm also A0_prune',
                widths=[120, 140, 160], width_budget=200,
                width_variants=['a0', 'a3', 'a4_subtree'],
                width_exceptions={'clstm_like.small': ['a0', 'a0_prune', 'a4_subtree'],
                                  'robot_rl': ['a0', 'flute_soft']},
                width_scope='All 13 affected circuit/placement cases; unchanged architecture, packing and placement. New RRG per width, shared by all methods.',
                workers=16, estimated_memory_limit_gib=180, timeout_seconds=3600,
                timing_scope='Concurrent diagnostic runs, not performance timing',
                inference_limits='Finite search failures do not prove graph infeasibility; widths need not be monotonic or represent exact Wmin')
    write_json(PLAN, plan)
    print(json.dumps({k:v for k,v in plan.items() if k!='sources'}, ensure_ascii=False))


def set_option(command, flag, value):
    if flag in command:
        command[command.index(flag)+1] = str(value)
    else:
        command.extend([flag, str(value)])


def source_key(source):
    return source['circuit'] + '__' + source['variant']


def make_job(source, stage, budget, width=100, graph_preparation=None):
    name = stage + '__' + source_key(source)
    return dict(id=name, circuit=source['circuit'], variant=source['variant'], stage=stage,
                budget=budget, width=width, source_key=source_key(source),
                original_output=source['original_output'], graph_preparation=graph_preparation,
                output=str(BASE / 'runs' / name), state='queued')


def run_one(job, source, plan):
    output = Path(job['output'])
    manifest_path = output / 'manifest.json'
    if job.get('external_receipt'):
        while True:
            receipt=json.loads(Path(job['external_receipt']).read_text())
            external=next(j for j in receipt['jobs'] if j['output']==job['output'])
            if external['state'] not in ['running','queued']:
                if external['state']=='supervisor_error':raise RuntimeError('External control failed')
                prior=json.loads(manifest_path.read_text())
                if prior['status']=='running':raise RuntimeError('Inconsistent external terminal receipt')
                for role in ['binary','architecture','circuit','packed_netlist','placement','rr_graph']:
                    if prior['inputs'][role]!=source['manifest']['inputs'][role]:
                        raise RuntimeError('External control changed fixed input '+role)
                for flag,value in [('--max_router_iterations','200'),('--routing_failure_predictor','off'),
                                   ('--congested_routing_iteration_threshold','1.0')]:
                    if prior['command'][prior['command'].index(flag)+1]!=value:
                        raise RuntimeError('External control parameter mismatch '+flag)
                if prior['experimental_environment']!=source['manifest']['experimental_environment']:
                    raise RuntimeError('External control algorithm mismatch')
                return prior
            owner=Path('/proc')/str(receipt['owner_pid'])/'cmdline'
            if not owner.exists() or b'check_failure_schedule.py' not in owner.read_bytes():
                raise RuntimeError('External control owner exited before terminal receipt')
            time.sleep(10)
    if manifest_path.exists():
        prior = json.loads(manifest_path.read_text())
        if prior['status'] == 'running':
            raise RuntimeError('Existing live/interrupted run requires inspection: ' + str(output))
        return prior
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise RuntimeError('Refusing nonempty output without manifest: ' + str(output))
    original = source['manifest']
    command = list(original['command'])
    inputs = json.loads(json.dumps(original['inputs']))
    set_option(command, '--route_file', output / 'routed.route')
    set_option(command, '--routing_failure_predictor', 'off')
    set_option(command, '--max_router_iterations', job['budget'])
    switch_after=job.get('congestion_mode_after_iteration',50)
    set_option(command, '--congested_routing_iteration_threshold', min(1, switch_after / job['budget']))
    if job['stage'].startswith('prepare_w'):
        command.remove('--read_rr_graph')
        command.remove(inputs['rr_graph']['path'])
        del inputs['rr_graph']
        set_option(command, '--route_chan_width', job['width'])
        set_option(command, '--write_rr_graph', output / 'rr_graph.xml')
        for name, role in [('packed.net', 'packed_netlist'), ('fixed.place', 'placement')]:
            (output / name).symlink_to(inputs[role]['path'])
    elif job['graph_preparation']:
        preparation = Path(job['graph_preparation'])
        prepared = json.loads((preparation / 'manifest.json').read_text())
        if 'rr_graph.xml' not in prepared.get('outputs', {}):
            raise RuntimeError('Width graph was not generated: ' + str(preparation))
        inputs['rr_graph'] = dict(path=str(preparation / 'rr_graph.xml'),
                                  sha256=prepared['outputs']['rr_graph.xml']['sha256'])
        for role in ['architecture','packed_netlist','placement','circuit']:
            if prepared['inputs'][role]['sha256'] != inputs[role]['sha256']:
                raise RuntimeError('Width scan changed fixed input: ' + role)
        set_option(command, '--read_rr_graph', inputs['rr_graph']['path'])
        set_option(command, '--route_chan_width', job['width'])
    # Inputs were fully verified at protocol initialization. Each newly generated
    # graph is hashed on preparation completion; retain all bindings in every run.
    env = {k:v for k,v in os.environ.items() if not k.startswith('VPR_H3D_')}
    env.update(original['experimental_environment'])
    manifest = dict(schema=1, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    command=command, cwd=str(output), inputs=inputs,
                    experimental_environment=original['experimental_environment'],
                    original_output=source['original_output'], protocol_sha256=sha256(plan.get('protocol_path',PLAN)),
                    status='running', route_chan_width=job['width'],
                    timeout_seconds=plan['timeout_seconds'], budget=job['budget'],
                    stage=job['stage'], congestion_mode_after_iteration=switch_after)
    write_json(manifest_path, manifest)
    start = time.monotonic()
    with (output / 'vpr.log').open('w') as stream:
        process = subprocess.Popen(['/usr/bin/time','-v','-o',str(output/'resource_usage.txt'),*command],
                                   cwd=output, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        manifest.update(supervisor_pid=os.getpid(), process_group_id=process.pid)
        write_json(manifest_path, manifest)
        try:
            code = process.wait(timeout=plan['timeout_seconds'])
            manifest.update(status='completed' if code==0 else 'failed', returncode=code)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            manifest.update(status='timeout', returncode=process.returncode)
    manifest['process_wall_seconds'] = time.monotonic()-start
    log = (output/'vpr.log').read_text(errors='replace')
    counters, history = native_counters(log)
    manifest['metrics'] = {**parse_metrics(log), **counters}
    write_json(output/'iterations.json', history)
    usage = (output/'resource_usage.txt').read_text()
    peak = re.search(r'Maximum resident set size \(kbytes\):\s+(\d+)',usage)
    manifest['peak_rss_kib'] = int(peak[1]) if peak else None
    manifest['outputs'] = {p.name:dict(bytes=p.stat().st_size,sha256=sha256(p))
                           for p in output.iterdir() if p.is_file() and p!=manifest_path}
    write_json(manifest_path, manifest)
    return manifest


def execute(native_primary=False,parallel_widths=False):
    BASE.mkdir(parents=True, exist_ok=True)
    prefix='native_' if native_primary else ''
    protocol=ROOT/'configs/failure_diagnosis_native.json' if native_primary else PLAN
    lock = (BASE/(prefix+'owner.lock')).open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lock.write(str(os.getpid()));lock.flush()
    plan=json.loads(protocol.read_text())
    plan['protocol_path']=str(protocol)
    sources={source_key(s):s for s in plan['sources']}
    path=BASE/(prefix+'state.json')
    if path.exists():
        state=json.loads(path.read_text())
        if state['protocol_sha256']!=sha256(protocol):
            raise RuntimeError('Protocol changed')
        if any(j['state']=='running' for j in state['jobs']):
            raise RuntimeError('Live/interrupted queue requires inspection')
    else:
        state=dict(owner_pid=os.getpid(), started_epoch=time.time(), protocol_sha256=sha256(protocol),
                   workers=plan['workers'], jobs=[], stages_done=[])
    state['owner_pid']=os.getpid()
    def save():write_json(path,state)
    def stage(name,jobs):
        if name in state['stages_done']:return
        admitted_ids={j['id'] for j in jobs}
        existing={j['id']:j for j in state['jobs']}
        for job in jobs:
            if job['id'] not in existing:state['jobs'].append(job)
        work=[j for j in state['jobs'] if j['id'] in admitted_ids and j['state']=='queued']
        if native_primary:
            work.sort(key=lambda j:sources[j['source_key']]['manifest']['process_wall_seconds'],reverse=True)
        state['active_stage']=name;save()
        with concurrent.futures.ThreadPoolExecutor(max_workers=plan['workers']) as pool:
            pending={}
            while work or pending:
                used=sum(v[1] for v in pending.values())
                while work and len(pending)<plan['workers']:
                    index=None
                    for k,j in enumerate(work):
                        m=sources[j['source_key']]['manifest']
                        need=max(1.0,(m.get('peak_rss_kib') or 1048576)/1024**2*1.35*j['width']/100)
                        if used+need<=plan['estimated_memory_limit_gib']:
                            index=k;break
                    if index is None:break
                    job=work.pop(index);job['state']='running';job['started_epoch']=time.time()
                    pending[pool.submit(run_one,job,sources[job['source_key']],plan)]=(job,need)
                    used+=need;save()
                if not pending and work:raise RuntimeError('No job fits resource limit')
                done,_=concurrent.futures.wait(pending,timeout=10,return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    job,_=pending.pop(future)
                    try:
                        result=future.result()
                        job.update(state=result['status'],metrics=result['metrics'],
                                   process_wall_seconds=result['process_wall_seconds'],
                                   returncode=result['returncode'])
                    except Exception as error:
                        job.update(state='supervisor_error',error=str(error))
                    job['finished_epoch']=time.time();save()
                    print(json.dumps({k:job[k] for k in ['id','state']},ensure_ascii=False),flush=True)
        bad=[j for j in state['jobs'] if j['id'] in admitted_ids and
             (j['state']=='supervisor_error' or (j['state']!='timeout' and j.get('returncode') not in [0,2]))]
        if bad:raise RuntimeError('Non-routing failure requires inspection: '+str([j['id'] for j in bad]))
        state['stages_done'].append(name);save()
    external={}
    if native_primary:
        for receipt in BASE.glob('schedule_controls*.json'):
            for job in json.loads(receipt.read_text())['jobs']:
                external[job['source_key']]=(job['output'],str(receipt))
        original=json.loads((BASE/'state.json').read_text())
        fixed50=[j for j in original['jobs'] if j['stage']=='off50']
        assert len(fixed50)==135 and all(j['state'] in ['completed','failed'] for j in fixed50)
        state['reused_off50_state']=str(BASE/'state.json');save()
    for budget in ([200] if native_primary else [50,200]):
        name=f'normal{budget}' if native_primary else f'off{budget}'
        jobs=[make_job(s,name,budget) for s in sources.values()]
        if native_primary:
            for job in jobs:
                job['congestion_mode_after_iteration']=budget
                if job['source_key'] in external:
                    job['output'],job['external_receipt']=external[job['source_key']]
        stage(name,jobs)
    base_stage='normal200' if native_primary else 'off200'
    unresolved=[j for j in state['jobs'] if j['stage']==base_stage and j['state']!='completed']
    extended={j['source_key'] for j in unresolved}
    for job in unresolved:
        extended.add(job['circuit']+'__a0')
        if job['circuit']=='clstm_like.small':extended.add(job['circuit']+'__a0_prune')
    capacity_policy=capacity_policy_file()
    if native_primary and capacity_policy.exists():
        policy=json.loads(capacity_policy.read_text())
        for case,proof in policy['cases'].items():
            if sha256(proof['evidence'])!=proof['evidence_sha256'] or sha256(proof['verification'])!=proof['verification_sha256']:
                raise RuntimeError('Capacity proof changed')
            verified=json.loads(Path(proof['verification']).read_text())
            evidence=json.loads(Path(proof['evidence']).read_text())
            certificate=evidence['certificates'][proof['certificate_index']]
            if not verified['passed'] or verified['evidence_sha256']!=proof['evidence_sha256'] or certificate['circuit']!=case or certificate['demand']<=certificate['capacity']:
                raise RuntimeError('Invalid capacity certificate')
            for source in sources.values():
                if source['circuit']!=case:continue
                inputs=source['manifest']['inputs']
                for role in ['rr_graph','packed_netlist','placement']:
                    if inputs[role]['sha256']!=proof[role+'_sha256']:
                        raise RuntimeError('Capacity proof does not apply to frozen inputs')
        skipped=sorted(key for key in extended if sources[key]['circuit'] in policy['cases'])
        if any(j['state']=='completed' and j['circuit'] in policy['cases'] for j in state['jobs'] if j['width']==100):
            raise RuntimeError('A legal route contradicts the capacity proof')
        extended.difference_update(skipped)
        state.update(skipped_500_certified=skipped,capacity_policy_sha256=sha256(capacity_policy))
        save()
    stage500='normal500' if native_primary else 'off500'
    if native_primary and capacity_policy.exists():stage500='normal500_after_capacity_check'
    jobs=[make_job(s,stage500,500) for key,s in sources.items() if key in extended]
    if native_primary:
        for job in jobs:job['congestion_mode_after_iteration']=500
    stage(stage500,jobs)
    # Width changes form a separate arm; all cases are scanned, including ones
    # rescued by iteration budget. This avoids selecting only difficult survivors.
    if parallel_widths:
        if not native_primary:raise ValueError('Parallel widths require the revised native protocol')
        state['width_execution_schedule']='All width graphs prepared, then independent width trials admitted together under unchanged worker/memory limits'
        save()
        a0s=[s for s in sources.values() if s['variant']=='a0']
        prep=[make_job(s,f'prepare_w{width}_native_parallel',1,width)
              for width in plan['widths'] for s in a0s]
        stage('prepare_widths_native_parallel',prep)
        by_case={(j['circuit'],j['width']):j['output'] for j in prep}
        chosen=[s for s in sources.values() if s['variant'] in
                plan['width_exceptions'].get(s['circuit'],plan['width_variants'])]
        jobs=[make_job(s,f'w{width}_normal200',200,width,by_case[s['circuit'],width])
              for width in plan['widths'] for s in chosen]
        for job in jobs:job['congestion_mode_after_iteration']=200
        stage('width_scan_normal200_parallel',jobs)
        state.update(finished_epoch=time.time(),active_stage='routing_finished');save()
        return
    for width in plan['widths']:
        a0s=[s for s in sources.values() if s['variant']=='a0']
        prep_stage=f'prepare_w{width}'+('_native' if native_primary else '')
        prep=[make_job(s,prep_stage,1,width) for s in a0s]
        stage(prep_stage,prep)
        by_case={j['circuit']:j['output'] for j in prep}
        chosen=[s for s in sources.values() if s['variant'] in
                plan['width_exceptions'].get(s['circuit'],plan['width_variants'])]
        width_stage=f'w{width}_normal200' if native_primary else f'w{width}_off200'
        jobs=[make_job(s,width_stage,200,width,by_case[s['circuit']]) for s in chosen]
        if native_primary:
            for job in jobs:job['congestion_mode_after_iteration']=200
        stage(width_stage,jobs)
    state.update(finished_epoch=time.time(),active_stage='routing_finished');save()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--initialize',action='store_true')
    parser.add_argument('--native-primary',action='store_true')
    parser.add_argument('--parallel-widths',action='store_true')
    args=parser.parse_args()
    if args.initialize:initialize()
    else:execute(args.native_primary,args.parallel_widths)
