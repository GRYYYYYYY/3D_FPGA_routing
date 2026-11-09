#!/usr/bin/env python3
"""Paper-condition PnR followed by fixed packed-netlist/placement comparisons."""
import argparse
import concurrent.futures
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import time

from lazagna_common import BASE, ROOT, run, sha256, utc, write_json
from run_vpr import parse_metrics


def graph_job(family,width):
    path=BASE/f'{family}_graph_state.json'
    if not path.exists():return None
    state=json.loads(path.read_text())
    for x in state['jobs']:
        if x['size']==100 and x['width']==width:
            return x if x['state']=='complete' else None


def run_one(job,primary,clock_model='route',legacy_netlist_compat=False,binary_override=None):
    family=job['family'];name=job['name'];width=job['width'];case=job['case']
    graph=Path(graph_job(family,width)['graph']);arch=BASE/'architectures'/f'{family}_100.xml'
    binary=ROOT/'artifacts/bin'/('lazagna-paper' if family=='paper' else 'baseline')/'vpr'
    if binary_override is not None:binary=Path(binary_override)
    circuit=ROOT/'benchmarks/downloads/beyond_flatland'/f'{case}.blif'
    directory=BASE/'runs'/name
    packed=directory/'packed.net';place=directory/'fixed.place'
    cmd=[binary,arch,circuit,'--route_chan_width',width,'--num_workers',1,
         '--router_algorithm','timing_driven','--flat_routing','off','--check_route','full',
         '--clock_modeling',clock_model,'--seed',1,'--read_rr_graph',graph,
         '--route_file',directory/'routed.route','--timing_report_npaths',10]
    inputs=[binary,arch,circuit,graph]
    if job['arm']=='primary':
        cmd+=['--pack','--place','--route','--analysis','--place_bounding_box_mode','cube_bb','--inner_num','0.5']
    else:
        source_packed=Path(primary['directory'])/'packed.net';source_place=Path(primary['directory'])/'fixed.place'
        if not source_packed.exists() or not source_place.exists():
            return dict(state='not_run_no_fixed_placement',reason='Primary paper-condition PnR did not produce packed netlist and placement.')
        # The historical vpr_flow rewrites PlaceFile after STAGE_LOAD as well.
        # Isolate future runs so that parallel readers never share that output.
        directory.mkdir(parents=True,exist_ok=True)
        if (directory/'manifest.json').exists() or packed.exists() or place.exists():
            raise RuntimeError('Refusing to replace an existing fixed-input run')
        shutil.copyfile(source_packed,packed);shutil.copyfile(source_place,place)
        assert sha256(source_packed)==sha256(packed) and sha256(source_place)==sha256(place)
        inputs += [source_packed,source_place,packed,place]
        cmd += ['--route','--analysis','--max_router_iterations',200,'--routing_failure_predictor','off',
                '--congested_routing_iteration_threshold','1.0']
        if family=='native':
            proof=json.loads((BASE/'architecture_specification_comparison.json').read_text())['equalities']
            assert proof['models']['paper_equals_native'] and proof['complexblocklist']['paper_equals_native']
            assert proof['tiles_ignoring_explicit_zero_direct_Z_Fc']
            # Only the architecture digest differs; the shared packed netlist
            # and placement are hashed and preserved, and all block interfaces
            # and intra-cluster models are exactly equal after normalization.
            cmd += ['--verify_file_digests','off']
    cmd += ['--net_file',packed,'--place_file',place]
    if legacy_netlist_compat:
        assert family=='native'
        cmd += ['--merge_constant_generators','off']
    r=run(name,cmd,timeout=3600,inputs=inputs)
    text=(directory/'stdout.log').read_text(errors='replace');m=parse_metrics(text)
    outputs={p.name:dict(path=str(p),sha256=sha256(p)) for p in [packed,place,directory/'routed.route'] if p.exists()}
    success=r['status']=='completed' and m['native_full_check_passed'] and m['routing_success_reported']
    if success:classification='native_legal_pending_independent_audit'
    elif r['status']=='timeout':classification='timeout'
    elif 'Circuit cannot be implemented' in text or 'does not fit' in text or 'required resources' in text.lower():classification='packing_or_device_capacity_failure'
    elif 'Routing failed' in text or 'Routing aborted' in text or 'Circuit is unrouteable' in text:classification='routing_failure'
    else:classification='tool_or_input_failure'
    result=dict(state=r['status'],classification=classification,native_legal=success,
                metrics=m,outputs=outputs,directory=str(directory),run_manifest=str(directory/'manifest.json'))
    write_json(directory/'result.json',result)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=6);args=p.parse_args()
    lock=(BASE/'route_owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    statepath=BASE/'route_state.json'
    if statepath.exists():raise RuntimeError('An owner/state already exists')
    protocol=json.loads((BASE/'protocol.json').read_text())
    cases=protocol['diagnostics']['focus_cases']
    jobs=[]
    for case in cases:
        jobs.append(dict(name=f'paper_primary_{case}_w300',case=case,family='paper',width=300,arm='primary',state='queued'))
    for case in cases:
        for family in ['paper','native']:
            for width in [100,300]:
                jobs.append(dict(name=f'{family}_fixed_{case}_w{width}_i200',case=case,family=family,width=width,arm='fixed',state='queued'))
    state=dict(owner_pid=os.getpid(),started_utc=utc(),stage='routing',workers=args.workers,jobs=jobs,
               note='Primary uses the paper-era toolchain and paper architecture conditions on existing exact BLIF inputs. Fixed arms share primary packed/place bytes. This is not a reconstruction of unpublished synthesis scripts or exact historical author seeds.')
    write_json(statepath,state)
    primaries={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending={}
        while any(j['state']=='queued' for j in jobs) or pending:
            for j in jobs:
                if len(pending)>=args.workers:break
                if j['state']!='queued' or not graph_job(j['family'],j['width']):continue
                if j['arm']=='fixed' and j['case'] not in primaries:continue
                j['state']='running'
                pending[pool.submit(run_one,j,primaries.get(j['case']))]=j
                write_json(statepath,state)
            if not pending:
                graph_states=[json.loads((BASE/f'{f}_graph_state.json').read_text()) for f in ['paper','native']]
                if all(s['stage'] in ('complete','completed_with_failures','build_failed') for s in graph_states):
                    for j in jobs:
                        if j['state']=='queued':j.update(state='not_run_graph_unavailable')
                    break
                time.sleep(5);continue
            done,_=concurrent.futures.wait(pending,timeout=5,return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                j=pending.pop(future)
                try:r=future.result()
                except Exception as e:r=dict(state='supervisor_error',error=repr(e),directory=str(BASE/'runs'/j['name']))
                j.update(r)
                if j['arm']=='primary':primaries[j['case']]=r
                write_json(statepath,state)
                print(json.dumps({k:j.get(k) for k in ['name','state','classification','native_legal','metrics','error']}),flush=True)
    state.update(stage='finished',finished_utc=utc());write_json(statepath,state)


if __name__=='__main__':main()
