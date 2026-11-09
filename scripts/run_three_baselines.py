#!/usr/bin/env python3
"""Published reference plus full-size modern LaZagna and paired native A0/A3."""
import argparse
import concurrent.futures
import fcntl
import json
import os
from pathlib import Path
import shutil
import urllib.request
import xml.etree.ElementTree as ET

from three_baseline_common import BASE,ROOT,OLD,PYTHON,MODERN,A0,A3,A3_ENV,read,run,sha256,utc,write_json
from run_vpr import parse_metrics
from prepare_lazagna_study import canonical


def register():
    if (BASE/'protocol.json').exists():
        raise RuntimeError('Protocol exists')
    frozen = read(ROOT/'docs/handoff_source_evidence_2026-10-25.json')['frozen_evidence_sha256']
    for p in ['results/lazagna_vtr9_port/validation.json','results/lazagna_vtr9_port/finalization.json',
              'docs/LaZagna后续分支验证_2026-10-25.md']:
        frozen[p] = sha256(ROOT/p)
    assert all(sha256(ROOT/p)==h for p,h in frozen.items())
    binaries = {}
    for name,path in [('modern',MODERN),('a0',A0),('a3',A3)]:
        manifest=read(path.parent/'manifest.json')
        assert sha256(path)==manifest['binary_sha256']
        binaries[name]=dict(path=str(path),sha256=sha256(path),manifest=str(path.parent/'manifest.json'))
    sources=BASE/'sources';sources.mkdir(parents=True,exist_ok=True)
    url='https://arxiv.org/html/2505.05579v1'
    content=urllib.request.urlopen(url,timeout=90).read()
    htmlpath=sources/'lazagna_2505.05579v1.html';htmlpath.write_bytes(content)
    from lxml import html
    tree=html.fromstring(content)
    tables=tree.xpath('//*[@id="S4.T4"]//table')
    assert len(tables)==1
    rows=[]
    for row in tables[0].xpath('.//tr'):
        cells=[' '.join(c.text_content().split()) for c in row.xpath('./td|./th')]
        if len(cells)==5 and cells[0].startswith('3D'):
            rows.append(dict(architecture=cells[0],vertical_connections=int(cells[1].replace(',','')),
                vertical_per_grid=float(cells[2]),wirelength_ratio_to_author_2d=float(cells[3].split()[0]),
                cpd_ratio_to_author_2d=float(cells[4].split()[0])))
    assert len(rows)==11
    write_json(BASE/'published_reference.json',dict(utc=utc(),url=url+'#S4.T4',html_sha256=sha256(htmlpath),
        reported_vtr='8.1',table='IV',rows=rows,normalization='Authors own 2D FPGA baseline, not native A0',
        exact_author_experiment_commit=None,absolute_per_circuit_cpd_available_in_table=False,
        warning='Table IV uses 100/66/33% SB variants; our published-XML 50% SB runs are a different condition. Never calculate improvement by subtracting their percent reduction from A3/A0.'))
    arches={}
    for family,source in [('modern',OLD/'architectures/paper_100.xml'),('native',OLD/'architectures/native_100.xml')]:
        target=BASE/'architectures'/f'{family}_100.xml';target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source,target)
        arches[family]=dict(path=str(target),sha256=sha256(target),source=str(source))
    roots={f:ET.parse(a['path']).getroot() for f,a in arches.items()}
    for tag in ['models','complexblocklist']:
        assert canonical(roots['modern'].find(tag))==canonical(roots['native'].find(tag))
    native_tiles=roots['native'].find('tiles')
    for fc in native_tiles.findall('tile/sub_tile/fc'):
        for child in list(fc):
            if child.attrib==dict(fc_type='abs',fc_val='0',segment_name='z_segment'):
                fc.remove(child)
    assert canonical(native_tiles)==canonical(roots['modern'].find('tiles'))
    cases=read(OLD/'protocol.json')['diagnostics']['focus_cases']
    write_json(BASE/'protocol.json',dict(utc=utc(),requested_baselines=[
        {'id':'B1_published','meaning':'LaZagna paper Table IV reported results, VTR 8.1; literature reference only'},
        {'id':'B2_modern','meaning':'2026 LaZagna VTR9-code port, pinned 5abd3aca plus documented build-only patch'},
        {'id':'B3_native','meaning':'Pristine official VTR 9.0.0-dev+0b91233, the exact parent of our algorithm'}],
        treatment='A3 static H3D-inspired planning with SCC reachability, archived a4scc binary',
        binaries=binaries,architectures=arches,cases=cases,grid=[100,100,2],width=300,
        graph_generation_clock='route for both families',route_clock='ideal for all measured arms',
        clock_reason='Separate disclosed diagnostic: released spram.clk Fc=0 is incompatible with routed BRAM clocks. Strict historical failures remain in the original study.',
        routing=dict(seed=1,workers_per_vpr=1,max_iterations=200,predictor='off',timeout_seconds=3600),
        reporting='timing_report_npaths=0 in every arm, to avoid the known CHANZ detailed-report defect without changing routing/STA',
        modern_stage='pack, place, route, analysis on its own newly generated full-size graph; cube_bb and inner_num0.5',
        native_stages='route-only on modern packed netlist and placement with private copies, native graph; merge_constant_generators=off and verify_file_digests=off with exact models/tiles compatibility proof',
        comparisons={'A3_vs_A0':'algorithm comparison: same packed netlist, placement, graph, settings',
                     'A3_vs_modern':'system comparison conditional on the same placement and netlist; graph model and toolchain differ',
                     'A3_vs_published':'reference comparison; ratio unavailable without a common 2D denominator and identical author inputs'},
        selection='All 11 pre-existing LaZagna diagnostic cases, not a claim that these are the exact author synthesized inputs. Include failures and missing placements.',
        preserved_sources=frozen,hardware_timing='Concurrent wall/router times are diagnostic, not speedup comparisons',
        status='registered'))


def make_graph(family):
    binary=MODERN if family=='modern' else A0
    arch=BASE/'architectures'/f'{family}_100.xml'
    circuit=ROOT/'vendor/LaZagna/benchmarks/and2/and2.blif'
    name=f'{family}_base_graph';base=BASE/'runs'/name/'rr_graph.xml'
    r=run(name,[binary,arch,circuit,'--pack','--route_chan_width',300,'--num_workers',1,
        '--clock_modeling','route','--write_rr_graph',base],inputs=[binary,arch,circuit])
    assert r['status']=='completed'
    graph=base
    if family=='modern':
        creator=ROOT/'vendor/LaZagna/scripts/3d_sb_creator.py'
        graph=BASE/'runs/modern_sb_graph/rr_graph.xml'
        r=run('modern_sb_graph',[PYTHON,creator,'-f',base,'-o',graph,'-p',.5,'-c','subset',
            '-a',arch,'-vp',1,'--sb_location_pattern','repeated_interval'],inputs=[creator,base,arch])
        assert r['status']=='completed'
    write_json(BASE/f'{family}_graph.json',dict(utc=utc(),family=family,graph=str(graph),sha256=sha256(graph)))


def route_one(case,arm,source=None):
    name=f'{arm}_{case}';directory=BASE/'runs'/name;directory.mkdir(parents=True,exist_ok=True)
    if any(directory.iterdir()):raise RuntimeError(f'Existing route {name}')
    family='modern' if arm=='modern' else 'native'
    graph=Path(read(BASE/f'{family}_graph.json')['graph'])
    arch=BASE/'architectures'/f'{family}_100.xml'
    binary={'modern':MODERN,'a0':A0,'a3':A3}[arm]
    circuit=ROOT/'benchmarks/downloads/beyond_flatland'/f'{case}.blif'
    packed=directory/'packed.net';place=directory/'fixed.place'
    inputs=[binary,arch,graph,circuit];source_hashes={}
    command=[binary,arch,circuit,'--route_chan_width',300,'--num_workers',1,'--router_algorithm','timing_driven',
        '--flat_routing','off','--check_route','full','--clock_modeling','ideal','--seed',1,'--read_rr_graph',graph,
        '--net_file',packed,'--place_file',place,'--route_file',directory/'routed.route','--timing_report_npaths',0,
        '--max_router_iterations',200,'--routing_failure_predictor','off','--congested_routing_iteration_threshold','1.0']
    if arm=='modern':
        command+=['--pack','--place','--route','--analysis','--place_bounding_box_mode','cube_bb','--inner_num',.5]
    else:
        for src,dest in [(source/'packed.net',packed),(source/'fixed.place',place)]:
            shutil.copyfile(src,dest);source_hashes[str(src)]=sha256(src)
            assert sha256(dest)==source_hashes[str(src)]
            inputs += [src,dest]
        command+=['--route','--analysis','--verify_file_digests','off','--merge_constant_generators','off']
    r=run(name,command,inputs=inputs,environment=A3_ENV if arm=='a3' else {})
    log=(directory/'stdout.log').read_text(errors='replace');metrics=parse_metrics(log)
    legal=r['status']=='completed' and metrics['native_full_check_passed'] and metrics['routing_success_reported']
    assert all(sha256(Path(p))==h for p,h in source_hashes.items())
    if legal:classification='native_legal_pending_audit'
    elif r['status']=='timeout':classification='budget_timeout'
    elif 'Circuit cannot be implemented' in log or 'does not fit' in log:classification='device_capacity_failure'
    elif 'Routing failed' in log or 'unrouteable' in log:classification='routing_failure'
    else:classification='tool_or_input_failure'
    result=dict(name=name,case=case,arm=arm,status=r['status'],classification=classification,native_legal=legal,
        graph=str(graph),directory=str(directory),metrics=metrics,source=str(source) if source else None,
        source_hashes=source_hashes,outputs={p.name:dict(path=str(p),sha256=sha256(p))
        for p in [packed,place,directory/'routed.route'] if p.exists()})
    write_json(directory/'result.json',result)
    return result


def routes(workers):
    path=BASE/'route_state.json'
    if path.exists():raise RuntimeError('Route state already exists')
    cases=read(BASE/'protocol.json')['cases']
    jobs=[dict(name=f'{arm}_{case}',case=case,arm=arm,state='queued') for case in cases for arm in ['modern','a0','a3']]
    state=dict(owner_pid=os.getpid(),started_utc=utc(),stage='routing',jobs=jobs,workers=workers);write_json(path,state)
    modern_results={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        pending={}
        while any(j['state']=='queued' for j in jobs) or pending:
            for j in jobs:
                if len(pending)>=workers:break
                if j['state']!='queued':continue
                source=None
                if j['arm']!='modern':
                    if j['case'] not in modern_results:continue
                    source=BASE/'runs'/('modern_'+j['case'])
                    if not all((source/f).exists() for f in ['packed.net','fixed.place']):
                        j.update(state='not_run_no_placement',native_legal=False,reason='Modern primary did not produce fixed inputs')
                        write_json(path,state);continue
                j['state']='running';pending[pool.submit(route_one,j['case'],j['arm'],source)]=j
                write_json(path,state)
            if not pending:continue
            done,_=concurrent.futures.wait(pending,timeout=5,return_when=concurrent.futures.FIRST_COMPLETED)
            for f in done:
                j=pending.pop(f)
                try:j.update(f.result(),state='finished')
                except Exception as error:j.update(state='supervisor_error',error=repr(error),native_legal=False)
                if j['arm']=='modern':modern_results[j['case']]=j
                write_json(path,state)
    state.update(stage='finished',finished_utc=utc());write_json(path,state)


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['register','graphs','routes']);p.add_argument('--workers',type=int,default=6);a=p.parse_args()
    BASE.mkdir(parents=True,exist_ok=True)
    lock=(BASE/(a.stage+'_owner.lock')).open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if a.stage=='register':register()
    elif a.stage=='graphs':
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            fs=[pool.submit(make_graph,f) for f in ['modern','native']]
            for f in fs:f.result()
    else:routes(a.workers)


if __name__=='__main__':main()
