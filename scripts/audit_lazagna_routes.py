#!/usr/bin/env python3
"""Audit every reported legal result, scanning each shared RRG once per group."""
import concurrent.futures
import argparse
import json
import time
from pathlib import Path
import check_route as cr
from compare_lazagna_graphs import records
from lazagna_common import BASE,sha256,utc,write_json


def audit_group(group):
    family,width,jobs=group
    graph=BASE/'runs'/(f'paper_sb_100_w{width}_p50' if family=='paper' else f'native_graph_100_w{width}')/'rr_graph.xml'
    verfile=BASE/f'vertical_{family}_100_w{width}.json'
    while not verfile.exists():time.sleep(5)
    vertical=json.loads(verfile.read_text());assert vertical['passed']
    mapping=Path(vertical['resource_map']) if family=='paper' else None
    # Use lxml's bounded-memory record iterator; audit semantics remain those
    # of the independently tested route checker, including exact switch IDs.
    cr.graph_records=records
    wanted_nodes=set();wanted_edges=set()
    routes=[Path(j['directory'])/'routed.route' for j in jobs]
    for p in routes:
        for net in cr.read_trace(p).values():
            trace=net['trace'];wanted_nodes.update(n.inode for n in trace)
            wanted_edges.update((a.inode,b.inode,a.switch) for a,b in zip(trace,trace[1:]) if a.switch!=-1)
    if mapping:
        m=json.loads(mapping.read_text());assert m['graph_sha256']==vertical['graph_sha256']
        wanted_nodes.update(n for g in m['channels'].values() for n in g['nodes']);del m
    evidence=cr.read_graph_evidence(graph,wanted_nodes,wanted_edges)
    assert evidence['sha256']==vertical['graph_sha256']
    results=[]
    for job,route in zip(jobs,routes):
        out=BASE/'audits'/(job['name']+'.json')
        if out.exists():raise RuntimeError('Existing audit result')
        result=cr.audit(graph,route,mapping,graph_evidence=evidence)
        # Legacy Z halves are serialized as CHANX. The generic checker's
        # horizontal length includes those halves; suppress that incomparable
        # metric in this study rather than presenting it as planar wirelength.
        if family=='paper':
            result['route'].pop('horizontal_track_length',None)
            result['metric_note']='Legacy CHANX Z halves excluded from reported horizontal-length comparisons; no cross-tool wirelength claim.'
        write_json(out,result)
        results.append({'name':job['name'],'passed':result['passed'],'errors':result['errors'][:20],
                        'audit':str(out),'sha256':sha256(out),'route':result['route']})
        print(job['name'],result['passed'],flush=True)
    return results


def main():
    p=argparse.ArgumentParser();p.add_argument('--state',default='route_state.json');p.add_argument('--prefix',default='route')
    args=p.parse_args();output=BASE/f'{args.prefix}_audit_summary.json'
    if output.exists():raise RuntimeError('Audit summary exists')
    pending={};finished=set();results=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        while True:
            state=json.loads((BASE/args.state).read_text())
            for family in ['paper','native']:
                for width in [100,300]:
                    key=(family,width)
                    if key in finished or key in pending.values():continue
                    jobs=[j for j in state['jobs'] if j['family']==family and j['width']==width]
                    if any(j['state'] in ['queued','running'] for j in jobs):continue
                    legal=[j for j in jobs if j.get('native_legal')]
                    if not legal:finished.add(key);continue
                    pending[pool.submit(audit_group,(family,width,legal))]=key
            for f in list(pending):
                if f.done():
                    key=pending.pop(f);results.extend(f.result());finished.add(key)
                    write_json(BASE/f'{args.prefix}_audit_progress.json',{'utc':utc(),'finished_groups':sorted(finished),'results':results})
            if len(finished)==4:break
            time.sleep(5)
    write_json(output,{'utc':utc(),'scope':'Native FULL checker plus independent directed tree/edge/switch/capacity and verified physical Z grouping; not independent bitstream certification.',
                       'passed':all(r['passed'] for r in results),'count':len(results),'results':results})


if __name__=='__main__':main()
