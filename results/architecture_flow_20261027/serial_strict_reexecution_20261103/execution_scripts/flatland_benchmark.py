#!/usr/bin/env python3
"""Shared frozen-input placement/routing operations for registered benchmarks."""
from collections import Counter
import json
from pathlib import Path
import shutil

import check_route as cr
from compare_lazagna_graphs import records
import flatland_experiment_io as io
from lazagna_common import ROOT, sha256, utc, write_json
from prepare_flatland_benchmark_models import choose_size
from run_flatland_pack_census import packed_summary
from validate_lazagna_vtr9_pilot import placements

BASE = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/results/architecture_flow_20261027/serial_strict_reexecution_20261103')


def read(path): return json.loads(Path(path).read_text())


def context(circuit, family, seed, width=100):
    protocol = read(BASE/'benchmark_protocol.json')
    selection = read(BASE/'capacity_selection.json')
    assert selection['status'] == 'frozen'
    binding = selection['circuits'][circuit]
    census_path = Path(binding['census'])
    io.frozen_hash(census_path, binding['census_sha256'])
    census = read(census_path)
    assert census['status'] == 'completed'
    size = choose_size(census['block_counts'], protocol)
    assert size == binding['size']
    io.frozen_hash(census_path.parent/'packed.net', binding['packed_sha256'])
    model_path = BASE/'benchmark_models'/f'n{size}_w{width}'/'manifest.json'
    model = read(model_path); assert model['status'] == 'ready'
    fixture = model['fixtures'][family]
    return dict(circuit=circuit, family=family, seed=seed, size=size, width=width,
        protocol=protocol, fixture=fixture, model_path=model_path, census=census,
        packed=census_path.parent/'packed.net', blif=Path(protocol['benchmarks'][circuit]['path']))


def prefix(ctx, stage, flow):
    return f"{stage}_{ctx['circuit']}_s{ctx['seed']}_{ctx['family']}_n{ctx['size']}_w{ctx['width']}_{flow}"


def tags(ctx, stage, flow, **extra):
    return {k:ctx[k] for k in ['circuit','family','seed','size','width']} | dict(stage=stage, placement=flow, **extra)


def existing(name):
    path = BASE/'runs'/name/'manifest.json'
    if not path.exists(): return None
    result = read(path)
    if result['status'] in ('running','starting'):
        raise RuntimeError(f'Unresolved existing attempt requires owner/liveness audit: {path}')
    for p, info in result.get('shared_inputs', {}).items(): io.frozen_hash(p, info['sha256'])
    for filename, info in result.get('outputs', {}).items():
        assert sha256(path.parent/filename) == info['sha256'], path.parent/filename
    return result


def placement(ctx, stage, flow):
    assert flow in ('p0','p1')
    assert flow != 'p1' or ctx['family'] != 'matched_2d'
    name = prefix(ctx, stage, flow)+'_place'
    if (previous := existing(name)) is not None: return previous
    d = BASE/'runs'/name; d.mkdir(parents=True, exist_ok=False)
    packed, placed = d/'packed.net', d/'placed.place'
    fixture = ctx['fixture']; paper = flow == 'p1'
    label = 'P1' if paper else 'A0'
    info = ctx['protocol']['binaries'][label]; binary = info['path']; io.frozen_hash(binary, info['sha256'])
    arch = fixture['architecture'] if paper else fixture['conversion']['architecture']
    graph = fixture['original_graph'] if paper else fixture['conversion']['graph']
    command = [binary, arch, ctx['blif']]
    private = []
    frozen = [binary, arch, graph, ctx['blif'], ctx['packed'], ctx['model_path'], BASE/'benchmark_protocol.json',BASE/'capacity_selection.json']
    if paper: command.extend(['--pack','--place'])
    else:
        shutil.copy2(ctx['packed'], packed); private.append(packed); command.append('--place')
    command.extend(['--device', f"controlled_{ctx['size']}" if paper else 'fixture',
        '--route_chan_width', ctx['width'], '--num_workers', 1, '--seed', ctx['seed'], '--clock_modeling', 'ideal',
        '--verify_file_digests', 'off', '--read_rr_graph', graph, '--timing_report_npaths', 0,
        '--net_file', packed, '--place_file', placed])
    if paper:
        key = dict(sb='SB', cb_o='CB-O', hybrid_o='Hybrid-O')[ctx['family']]+'_paper'
        configs = read(BASE/'published_reference_analysis.json')['datasets'][key]['configs']
        options = {json.dumps(v,sort_keys=True) for v in configs.values()}; assert len(options)==1
        for key,value in json.loads(options.pop()).items(): command.extend([key,str(value)])
        command.extend(['--partition_post_pack','--soft_partitioning','init_place'])
        frozen.extend([Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/results/architecture_flow_20261027/single_thread_candidate_20261103/run_serial_triton_bridge.py'), Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/results/architecture_flow_20261027/single_thread_candidate_20261103/openroad_build_boost183/src/openroad')])
    else: command.extend(['--merge_constant_generators','off'])
    result = io.run(name, command, frozen=frozen, private_inputs=private, timeout=3600, tags=tags(ctx,stage,flow,operation='placement'))
    check = dict(utc=utc(), passed=False, status=result['status'])
    if result['status']=='completed' and packed.exists() and placed.exists():
        semantic = packed_summary(packed)
        check.update(packed_semantic=semantic, expected_semantic_sha256=ctx['census']['semantic_sha256'],
            placed_blocks=len(placements(placed)),
            passed=semantic['semantic_sha256']==ctx['census']['semantic_sha256'] and len(placements(placed))==ctx['census']['blocks'])
    write_json(d/'placement_check.json', check)
    if result['status']=='completed' and not check['passed']:
        raise RuntimeError(f'Placement/packing control mismatch; stop dependent routes: {d}')
    return result


def route(ctx, stage, flow, router, variant=None, config=None):
    p_name = prefix(ctx,stage,flow)+'_place'; source = BASE/'runs'/p_name
    assert read(source/'placement_check.json')['passed']
    arm = router.lower() if router != 'R1' else f'{variant}_c{config}'
    name = prefix(ctx,stage,flow)+'_'+arm
    if (previous := existing(name)) is not None: return previous
    d = BASE/'runs'/name; d.mkdir(parents=True, exist_ok=False)
    for filename in ['packed.net','placed.place']: shutil.copy2(source/filename,d/filename)
    info = ctx['protocol']['binaries'][router]; binary=info['path']; io.frozen_hash(binary,info['sha256'])
    f=ctx['fixture']; legacy=router=='B2'
    arch=f['architecture'] if legacy else f['conversion']['architecture']
    graph=f['original_graph'] if legacy else f['conversion']['graph']
    command=[binary,arch,ctx['blif'],'--route','--analysis','--device',f"controlled_{ctx['size']}" if legacy else 'fixture',
        '--route_chan_width',ctx['width'],'--num_workers',1,'--seed',ctx['seed'],'--clock_modeling','ideal',
        '--check_route','full','--verify_file_digests','off','--read_rr_graph',graph,
        '--max_router_iterations',200,'--routing_failure_predictor','off','--timing_report_npaths',0,
        '--net_file',d/'packed.net','--place_file',d/'placed.place','--route_file',d/'routed.route']
    if not legacy: command.extend(['--merge_constant_generators','off'])
    env=ctx['protocol']['tuning']['variants'][variant][config]['environment'] if router=='R1' else {}
    result=io.run(name,command,frozen=[binary,arch,graph,ctx['blif'],source/'packed.net',source/'placed.place',
        ctx['model_path'],BASE/'benchmark_protocol.json',BASE/'capacity_selection.json'],private_inputs=[d/'packed.net',d/'placed.place'],
        environment=env,timeout=1800,tags=tags(ctx,stage,flow,operation='route',router=router,variant=variant,config=config))
    checks=dict(packed_identical=sha256(d/'packed.net')==sha256(source/'packed.net'),
                placement_identical=placements(d/'placed.place')==placements(source/'placed.place'))
    write_json(d/'pair_check.json',dict(utc=utc(),passed=all(checks.values()),checks=checks,source=str(source)))
    if not all(checks.values()): raise RuntimeError(f'Paired input changed: {d}')
    return result


def physical_route_metrics(route_path,evidence):
    sb,cb=Counter(),Counter();wirelength=0;crossing_edges=Counter()
    for net in cr.read_trace(route_path).values():
        trace=net['trace'];used={n.inode for n in trace};sb_net=set();cb_net=set()
        for n in used:
            meta=evidence['nodes'][n]
            if meta['kind'] in ('CHANX','CHANY') and meta['direction']!='NONE':
                wirelength += 1+abs(meta['high'][0]-meta['low'][0])+abs(meta['high'][1]-meta['low'][1])
        for a,b in zip(trace,trace[1:]):
            if a.switch==-1 or a.low[2]==b.low[2]:continue
            crossing_edges[a.kind+'->'+b.kind]+=1
            if a.kind=='OPIN':cb_net.add(a.inode)
            else:
                assert a.kind=='CHANX' and evidence['nodes'][a.inode]['direction']=='NONE'
                sb_net.add(a.inode)
        sb.update(sb_net);cb.update(cb_net)
    return dict(planar_wirelength_excluding_sb_half_nodes=wirelength,
        sb_pairs_used=len(sb),sb_pair_net_occupancy=sum(sb.values()),
        cb_crossing_output_sources_used=len(cb),cb_crossing_output_source_net_occupancy=sum(cb.values()),
        actual_crossing_edge_traversals=dict(crossing_edges),
        qualification='CB edges share source OPIN and destination channel capacity; no independent per-edge via count')


def audit_batch(ctx, receipts, output):
    cr.graph_records=records
    if Path(output).exists(): raise FileExistsError(output)
    legal=[];failed=[]
    for result in receipts:
        m=result.get('metrics',{})
        if result['status']=='completed' and m.get('native_full_check_passed') and m.get('routing_success_reported'):
            legal.append(BASE/'runs'/result['name'])
        else:failed.append(dict(name=result['name'],status=result['status'],metrics=m))
    graph=ctx['fixture']['original_graph'];rows=[]
    if legal:
        evidence=cr.batch_graph_evidence(graph,[d/'routed.route' for d in legal])
        for d in legal:
            result=cr.audit(graph,d/'routed.route',graph_evidence=evidence)
            pair=read(d/'pair_check.json');assert pair['passed']
            physical=physical_route_metrics(d/'routed.route',evidence) if result['passed'] else None
            write_json(d/'independent_audit.json',dict(utc=utc(),audit=result,physical_metrics=physical))
            assert result['passed'],(d,result['errors'])
            rows.append(dict(name=d.name,passed=True,metrics=read(d/'manifest.json')['metrics'],physical_metrics=physical))
    summary=dict(utc=utc(),passed=True,registered_route_count=len(receipts),legal_count=len(rows),
        failed_count=len(failed),legal=rows,failed=failed,graph_sha256=sha256(graph))
    write_json(output,summary)
    return summary
