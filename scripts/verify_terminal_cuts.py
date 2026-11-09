#!/usr/bin/env python3
"""Verify proposed cuts by enumerating all crossing RRG edges independently.

This verifier knows nothing about SOURCE/OPIN or IPIN/SINK region construction.
It checks the literal vertex set, full directed boundary, native capacities,
distinct fixed net demands, and the strict demand > capacity inequality.
"""
import argparse
from collections import defaultdict
import concurrent.futures
import json
from pathlib import Path
import time

from check_route import graph_records, read_trace, sha256
from diagnose_failures import BASE, write_json


def verify_one(evidence):
    path=Path(evidence);data=json.loads(path.read_text());output=path.with_suffix('.verified.json')
    if output.exists():
        prior=json.loads(output.read_text())
        if prior['evidence_sha256']==sha256(path) and prior['verifier_sha256']==sha256(__file__):return prior
    start=time.monotonic();certs=data['certificates']
    memberships=defaultdict(list);regions=[];frontiers=[set() for _ in certs];wanted=set();caps={};types={}
    for i,c in enumerate(certs):
        inside=set(c['region']);regions.append(inside)
        for inode in inside:memberships[inode].append(i)
        wanted.update(n['node'] for n in c['boundary'])
        for w in c['witnesses']:wanted.update([w['source'],w['sink']])
    for section,e in graph_records(data['rr_graph']):
        a=e.attrib
        if section=='rr_nodes':
            inode=int(a['id'])
            if inode in wanted:caps[inode]=int(a['capacity']);types[inode]=a['type']
        elif section=='rr_edges':
            u=int(a['src_node']);v=int(a['sink_node'])
            for i in memberships.get(u,()):
                if certs[i]['direction'] in ['output','both'] and v not in regions[i]:frontiers[i].add(v)
            for i in memberships.get(v,()):
                if certs[i]['direction'] in ['input','both'] and u not in regions[i]:frontiers[i].add(u)
    if sha256(data['rr_graph'])!=data['rr_graph_sha256']:raise RuntimeError('Graph hash mismatch')
    endpoints={}
    for source in data['route_sources']:
        if not any(c['circuit']==source['circuit'] for c in certs):continue
        if sha256(source['route'])!=source['route_sha256']:raise RuntimeError('Route hash mismatch')
        trace=read_trace(source['route'])
        endpoints[source['circuit']]={nid:(n['trace'][0].inode,{v.inode for v in n['trace'] if v.kind=='SINK'})
                                       for nid,n in trace.items() if n['trace']}
        del trace
    summaries=[]
    for i,c in enumerate(certs):
        expected={n['node'] for n in c['boundary']}
        if frontiers[i]!=expected:raise RuntimeError('Incomplete or excessive claimed boundary')
        if any(caps[n['node']]!=n['capacity'] for n in c['boundary']):raise RuntimeError('Wrong capacity')
        capacity=sum(caps[n] for n in frontiers[i])
        ids={w['net'] for w in c['witnesses']}
        if len(ids)!=len(c['witnesses']) or len(ids)!=c['demand']:raise RuntimeError('Non-distinct net demand')
        for w in c['witnesses']:
            source,sinks=endpoints[c['circuit']][w['net']]
            if source!=w['source'] or w['sink'] not in sinks:raise RuntimeError('Wrong fixed terminal witness')
            if types[w['source']]!='SOURCE' or types[w['sink']]!='SINK':raise RuntimeError('Wrong terminal type')
            if c['direction']=='both':
                if (w['source'] in regions[i])==(w['sink'] in regions[i]):raise RuntimeError('Demand does not cross proposed cut')
            else:
                expected_in=c['direction']=='output'
                if (w['source'] in regions[i])!=expected_in or (w['sink'] in regions[i])==expected_in:
                    raise RuntimeError('Demand does not cross proposed cut')
        if not (capacity==c['capacity'] and len(ids)>capacity):raise RuntimeError('No capacity violation')
        summaries.append({k:c[k] for k in ['circuit','direction','coordinate','demand','capacity','deficit']})
    result=dict(passed=True,evidence=str(path),evidence_sha256=sha256(path),
                verifier_sha256=sha256(__file__),rr_graph_sha256=data['rr_graph_sha256'],
                verified_certificates=len(certs),certificates=summaries,seconds=time.monotonic()-start,
                scope='Verified impossibility of satisfying the recorded distinct fixed net terminal demands on the given capacitated directed RRG; not a statement about other layouts, architectures, widths, packing, or silicon.')
    write_json(output,result);return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hall',action='store_true')
    parser.add_argument('--combined',action='store_true')
    parser.add_argument('--source-classes',action='store_true')
    args=parser.parse_args()
    suffix='_source_classes' if args.source_classes else '_combined' if args.combined else '_hall' if args.hall else ''
    state=json.loads((BASE/('terminal_cuts'+suffix+'.json')).read_text())
    evidence=[r['evidence'] for r in state['results'] if r['certificates']]
    results=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        for result in pool.map(verify_one,evidence):
            results.append(result)
            write_json(BASE/('verified_terminal_cuts'+suffix+'.json'),dict(complete_graph_scan='finished_epoch' in state,results=results))
            print(json.dumps({k:result[k] for k in ['passed','evidence','verified_certificates','seconds']}),flush=True)


if __name__=='__main__':main()
