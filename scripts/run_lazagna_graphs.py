#!/usr/bin/env python3
"""Create archived native and paper-era graphs with original LaZagna SB code."""
import argparse
import concurrent.futures
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from lazagna_common import BASE, PAPER, PYTHON, ROOT, run, sha256, utc, write_json


def archive_binary():
    source=PAPER/'OpenFPGA/build/vtr-verilog-to-routing/vpr/vpr'
    dest=ROOT/'artifacts/bin/lazagna-paper'
    dest.mkdir(parents=True,exist_ok=True)
    record=dest/'manifest.json'
    if record.exists():
        d=json.loads(record.read_text())
        if sha256(dest/'vpr')!=d['binary_sha256']:raise RuntimeError('Archived binary changed')
        return dest/'vpr'
    shutil.copy2(source,dest/'vpr')
    shutil.copy2(PAPER/'OpenFPGA/build/CMakeCache.txt',dest/'CMakeCache.txt')
    commits={}
    for name,path in [('lazagna',PAPER),('openfpga',PAPER/'OpenFPGA'),('vtr',PAPER/'OpenFPGA/vtr-verilog-to-routing')]:
        commits[name]=dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip(),
                           status=subprocess.check_output(['git','status','--porcelain'],cwd=path,text=True).strip())
    write_json(record,dict(utc=utc(),binary_sha256=sha256(dest/'vpr'),sources=commits,
                           cache_sha256=sha256(dest/'CMakeCache.txt'),
                           build_manifest=str(BASE/'runs/build_paper_toolchain/manifest.json')))
    return dest/'vpr'


def main():
    p=argparse.ArgumentParser();p.add_argument('--family',choices=['native','paper'],required=True)
    p.add_argument('--wait-build',action='store_true');args=p.parse_args()
    lock=(BASE/f'{args.family}_graph_owner.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    statepath=BASE/f'{args.family}_graph_state.json'
    if statepath.exists():raise RuntimeError('Graph queue already exists')
    jobs=[dict(size=n,width=w,state='queued') for n,w in [(40,100),(40,300),(100,300),(100,100)]]
    state=dict(owner_pid=os.getpid(),started_utc=utc(),family=args.family,stage='waiting_build' if args.wait_build else 'starting',jobs=jobs)
    write_json(statepath,state)
    if args.wait_build:
        receipt=BASE/'runs/build_paper_toolchain/manifest.json'
        while True:
            if receipt.exists():
                d=json.loads(receipt.read_text())
                if d['status'] not in ('starting','running'):
                    if d['returncode']!=0:
                        state.update(stage='build_failed',finished_utc=utc());write_json(statepath,state)
                        return
                    break
            time.sleep(5)
    binary=archive_binary() if args.family=='paper' else ROOT/'artifacts/bin/baseline/vpr'
    circuit=PAPER/'benchmarks/and2/and2.blif';creator=PAPER/'scripts/3d_sb_creator.py'
    state['stage']='graphs';write_json(statepath,state)
    # The historical XML generator retains the full graph in memory. Serialize
    # graphs so its peak memory cannot overlap another historical generator.
    for job in jobs:
        n,w=job['size'],job['width'];name=f'{args.family}_graph_{n}_w{w}'
        arch=BASE/'architectures'/f'{args.family}_{n}.xml'
        directory=BASE/'runs'/name;graph=directory/'rr_graph.xml'
        job['state']='running';write_json(statepath,state)
        receipt=directory/'manifest.json'
        if receipt.exists():
            r=json.loads(receipt.read_text())
            if r['status']=='running':raise RuntimeError('Graph invocation already running')
        else:
            cmd=[binary,arch,circuit,'--route_chan_width',w,'--pack','--write_rr_graph',graph,
                 '--num_workers',1,'--clock_modeling','route' if args.family=='paper' else 'ideal']
            r=run(name,cmd,timeout=3600,inputs=[binary,arch,circuit])
        job.update(base_status=r['status'],base_graph=str(graph))
        if r['status']!='completed' or not graph.exists():
            job['state']='base_graph_failed';write_json(statepath,state);continue
        job['base_graph_sha256']=sha256(graph)
        if args.family=='paper':
            sb_name=f'paper_sb_{n}_w{w}_p50'
            sb_graph=BASE/'runs'/sb_name/'rr_graph.xml'
            cmd=[PYTHON,creator,'-f',graph,'-o',sb_graph,'-p','0.5','-c','subset','-a',arch,
                 '-vp','1','--sb_location_pattern','repeated_interval']
            r=run(sb_name,cmd,timeout=7200,inputs=[creator,arch,graph])
            job.update(sb_status=r['status'],graph=str(sb_graph))
            if r['status']!='completed' or not sb_graph.exists():
                job['state']='sb_graph_failed';write_json(statepath,state);continue
            job['graph_sha256']=sha256(sb_graph)
        else:
            job.update(graph=str(graph),graph_sha256=job['base_graph_sha256'])
        job['state']='complete';write_json(statepath,state)
        print(json.dumps({k:v for k,v in job.items() if not k.endswith('sha256')}),flush=True)
    state.update(stage='complete' if all(x['state']=='complete' for x in jobs) else 'completed_with_failures',finished_utc=utc())
    write_json(statepath,state)


if __name__=='__main__':main()
