#!/usr/bin/env python3
"""Look for independently verifiable vertex-capacity cuts at fixed terminals.

For output regions, include active SOURCE classes and all their OPIN children.
For input regions, include active SINK classes and all their IPIN predecessors.
Every distinct net must cross the region's appropriate boundary. A required-net
count exceeding the sum of boundary vertex capacities is an infeasibility
certificate for the recorded fixed SOURCE/SINK terminal demands on this RRG.
Absence of such a cut does NOT establish routability.
"""
import argparse
from array import array
from collections import defaultdict
import concurrent.futures
import json
from pathlib import Path
import time

from check_route import graph_records, read_trace, sha256
from diagnose_failures import BASE, ROOT, write_json

KINDS={'SOURCE':1,'OPIN':2,'IPIN':3,'SINK':4,'CHANX':5,'CHANY':6,'CHANZ':7}


def hall_subset(groups,capacities):
    """Find a deficient union in the output-to-boundary capacity relaxation."""
    import numpy as np
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import maximum_flow,breadth_first_order
    resources=sorted(set().union(*(g['boundary'] for g in groups)))
    count=len(groups);index={n:count+1+i for i,n in enumerate(resources)}
    sink=count+len(resources)+1;total=sum(len(g['demands']) for g in groups)
    rows=[];cols=[];values=[]
    for i,g in enumerate(groups,1):
        rows.append(0);cols.append(i);values.append(len(g['demands']))
        for n in g['boundary']:rows.append(i);cols.append(index[n]);values.append(total+1)
    for n in resources:rows.append(index[n]);cols.append(sink);values.append(int(capacities[n]))
    graph=csr_matrix((np.asarray(values,dtype=np.int64),(rows,cols)),shape=(sink+1,sink+1))
    result=maximum_flow(graph,0,sink,method='dinic')
    if result.flow_value==total:return [],total,int(result.flow_value)
    residual=graph-result.flow;residual.data[residual.data<=0]=0;residual.eliminate_zeros()
    reachable=set(map(int,breadth_first_order(residual,0,directed=True,return_predecessors=False)))
    return [i for i in range(count) if i+1 in reachable],total,int(result.flow_value)


def scan_group(item):
    graph_hash,sources,with_hall,with_combined,with_source_classes=item
    start=time.monotonic();groups=[];expected={};out_endpoint=defaultdict(list);in_endpoint=defaultdict(list)
    provenance=[]
    for source in sources:
        route=Path(source['original_output'])/'routed.route'
        manifest=source['manifest']
        route_hash=sha256(route)
        if route_hash!=manifest['outputs']['routed.route']['sha256']:raise RuntimeError('Route changed')
        nets=read_trace(route);out=defaultdict(dict);inp=defaultdict(dict)
        for net_id,net in nets.items():
            trace=net['trace']
            if not trace:continue
            src=trace[0];assert src.kind=='SOURCE'
            sinks=[n for n in trace if n.kind=='SINK']
            assert sinks
            expected[src.inode]=('SOURCE',src.low)
            record=dict(net=net_id,source=src.inode,sinks=sorted(set(n.inode for n in sinks)))
            out[src.low][net_id]=record
            for sink in sinks:
                expected[sink.inode]=('SINK',sink.low)
                inp[sink.low][net_id]=record
        for direction,table in [('output',out),('input',inp)]:
            for coord,demands in table.items():
                # Candidate selection is a search heuristic, not part of a
                # certificate. Every reported positive cut is fully verified.
                if len(demands)<16:continue
                endpoints=set(r['source'] for r in demands.values()) if direction=='output' else {
                    sink for r in demands.values() for sink in r['sinks'] if expected[sink][1]==coord}
                gid=len(groups)
                groups.append(dict(circuit=source['circuit'],direction=direction,coordinate=coord,
                                   region=set(endpoints),endpoints=endpoints,demands=list(demands.values()),boundary=set()))
                mapping=out_endpoint if direction=='output' else in_endpoint
                for inode in endpoints:mapping[inode].append(gid)
                if direction=='output' and with_source_classes:
                    by_source=defaultdict(list)
                    for r in demands.values():by_source[r['source']].append(r)
                    for inode,records in by_source.items():
                        gid=len(groups)
                        groups.append(dict(circuit=source['circuit'],direction='output',coordinate=coord,
                            method='source_class',region={inode},endpoints={inode},demands=records,boundary=set()))
                        out_endpoint[inode].append(gid)
        provenance.append(dict(circuit=source['circuit'],route=str(route),route_sha256=route_hash,
                               packed_netlist_sha256=manifest['inputs']['packed_netlist']['sha256'],
                               placement_sha256=manifest['inputs']['placement']['sha256']))
        del nets
    graph=Path(sources[0]['manifest']['inputs']['rr_graph']['path'])
    kinds=array('B');capacities=array('I');opin_edges=array('I');ipin_edges=array('I')
    active_opin=defaultdict(set);active_ipin=defaultdict(set);edge_count=0
    for section,element in graph_records(graph):
        a=element.attrib
        if section=='rr_nodes':
            inode=int(a['id'])
            if inode!=len(kinds):raise RuntimeError('Expected contiguous node ids')
            kind=a['type'];kinds.append(KINDS[kind]);capacities.append(int(a['capacity']))
            if inode in expected:
                loc=element.find('loc').attrib
                xyz=(int(loc['xlow']),int(loc['ylow']),int(loc.get('layer_low',loc.get('layer','0'))))
                if expected[inode]!=(kind,xyz):raise RuntimeError('Terminal differs from RRG')
        elif section=='rr_edges':
            u=int(a['src_node']);v=int(a['sink_node']);edge_count+=1
            if kinds[u]==2:opin_edges.extend((u,v))
            if kinds[v]==3:ipin_edges.extend((u,v))
            if u in out_endpoint:
                for gid in out_endpoint[u]:
                    if kinds[v]==2:
                        groups[gid]['region'].add(v);active_opin[v].add(gid)
                    else:groups[gid]['boundary'].add(v)
            if v in in_endpoint:
                for gid in in_endpoint[v]:
                    if kinds[u]==3:
                        groups[gid]['region'].add(u);active_ipin[u].add(gid)
                    else:groups[gid]['boundary'].add(u)
    for i in range(0,len(opin_edges),2):
        u,v=opin_edges[i],opin_edges[i+1]
        for gid in active_opin.get(u,()):
            if v not in groups[gid]['region']:groups[gid]['boundary'].add(v)
    for i in range(0,len(ipin_edges),2):
        u,v=ipin_edges[i],ipin_edges[i+1]
        for gid in active_ipin.get(v,()):
            if u not in groups[gid]['region']:groups[gid]['boundary'].add(u)
    certificates=[];summaries=defaultdict(lambda:dict(tested_regions=0,violations=0,largest_deficit=0))
    for g in groups:
        g['boundary'].difference_update(g['region'])
        capacity=sum(capacities[n] for n in g['boundary']);demand=len(g['demands'])
        summary=summaries[g['circuit']];summary['tested_regions']+=1
        if demand<=capacity:continue
        summary['violations']+=1;summary['largest_deficit']=max(summary['largest_deficit'],demand-capacity)
        witnesses=[]
        for r in g['demands']:
            sink=next(s for s in r['sinks'] if (s in g['region'])==(g['direction']=='input'))
            witnesses.append(dict(net=r['net'],source=r['source'],sink=sink))
        certificates.append(dict(circuit=g['circuit'],direction=g['direction'],coordinate=g['coordinate'],
                                 demand=demand,capacity=capacity,deficit=demand-capacity,
                                 region=sorted(g['region']),boundary=[dict(node=n,capacity=capacities[n],kind=kinds[n]) for n in sorted(g['boundary'])],
                                 witnesses=witnesses))
    hall_results=[]
    if with_hall:
        for source in sources:
            case=source['circuit'];subset=[g for g in groups if g['circuit']==case and g['direction']=='output'
                and (not with_source_classes or g.get('method')=='source_class')]
            if not subset:continue
            selected,total,flow=hall_subset(subset,capacities)
            info=dict(circuit=case,candidate_regions=len(subset),demand=total,relaxation_flow=flow,
                      selected_regions=len(selected),granularity='source_class' if with_source_classes else 'block');hall_results.append(info)
            if not selected:continue
            chosen=[subset[i] for i in selected]
            region=set().union(*(g['region'] for g in chosen))
            boundary=set().union(*(g['boundary'] for g in chosen))-region
            demands={r['net']:r for g in chosen for r in g['demands']}
            capacity=sum(capacities[n] for n in boundary)
            if len(demands)<=capacity:raise RuntimeError('Hall candidate failed literal boundary check')
            witnesses=[dict(net=r['net'],source=r['source'],sink=next(s for s in r['sinks'] if s not in region))
                       for r in demands.values()]
            certificates.append(dict(circuit=case,direction='output',coordinate=None,method='hall_source_class_union' if with_source_classes else 'hall_output_union',
                member_regions=sorted(set(g['coordinate'] for g in chosen)),demand=len(demands),capacity=capacity,
                deficit=len(demands)-capacity,region=sorted(region),
                boundary=[dict(node=n,capacity=capacities[n],kind=kinds[n]) for n in sorted(boundary)],witnesses=witnesses))
            info.update(certified_demand=len(demands),certified_capacity=capacity,deficit=len(demands)-capacity)
            if with_source_classes:
                sites=defaultdict(list)
                for g in chosen:sites[g['coordinate']].append(g)
                for coord,parts in sites.items():
                    local_region=set().union(*(g['region'] for g in parts))
                    local_boundary=set().union(*(g['boundary'] for g in parts))-local_region
                    local_demands={r['net']:r for g in parts for r in g['demands']}
                    local_capacity=sum(capacities[n] for n in local_boundary)
                    if len(local_demands)<=local_capacity:continue
                    witnesses=[dict(net=r['net'],source=r['source'],sink=next(s for s in r['sinks'] if s not in local_region)) for r in local_demands.values()]
                    certificates.append(dict(circuit=case,direction='output',coordinate=coord,method='source_classes_at_one_site',
                        demand=len(local_demands),capacity=local_capacity,deficit=len(local_demands)-local_capacity,
                        region=sorted(local_region),boundary=[dict(node=n,capacity=capacities[n],kind=kinds[n]) for n in sorted(local_boundary)],witnesses=witnesses))
    if with_combined:
        physical_groups=defaultdict(list)
        for g in groups:physical_groups[(g['circuit'],g['coordinate'])].append(g)
        for (case,coordinate),children in physical_groups.items():
            if len(children)<2:continue
            region=set().union(*(g['region'] for g in children))
            boundary=set().union(*(g['boundary'] for g in children))-region
            demands={r['net']:r for g in children for r in g['demands']}
            witnesses=[]
            for r in demands.values():
                sink=next((s for s in r['sinks'] if (s in region)!=(r['source'] in region)),None)
                if sink is not None:witnesses.append(dict(net=r['net'],source=r['source'],sink=sink))
            capacity=sum(capacities[n] for n in boundary)
            summaries[case]['tested_regions']+=1
            if len(witnesses)<=capacity:continue
            summaries[case]['violations']+=1
            summaries[case]['largest_deficit']=max(summaries[case]['largest_deficit'],len(witnesses)-capacity)
            certificates.append(dict(circuit=case,direction='both',coordinate=coordinate,
                method='combined_terminal_region',demand=len(witnesses),capacity=capacity,deficit=len(witnesses)-capacity,
                region=sorted(region),boundary=[dict(node=n,capacity=capacities[n],kind=kinds[n]) for n in sorted(boundary)],
                witnesses=witnesses))
    actual_hash=sha256(graph)
    if actual_hash!=graph_hash:raise RuntimeError('RRG changed')
    result=dict(rr_graph=str(graph),rr_graph_sha256=graph_hash,node_count=len(kinds),edge_count=edge_count,
                route_sources=provenance,candidate_minimum_distinct_nets=16,summaries=dict(summaries),
                certificates=certificates,hall_results=hall_results,scan_seconds=time.monotonic()-start,
                scope='Necessary vertex-capacity condition for recorded fixed SOURCE/SINK demands. No negative certificate implies routability; terminal-to-netlist mapping remains the native VPR input contract.')
    folder='cuts_source_classes' if with_source_classes else 'cuts_combined' if with_combined else 'cuts_hall' if with_hall else 'cuts'
    path=BASE/folder/f'{graph_hash[:16]}.json';write_json(path,result)
    return dict(evidence=str(path),rr_graph_sha256=graph_hash,summaries=dict(summaries),
                certificates=len(certificates),hall_results=hall_results,scan_seconds=result['scan_seconds'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hall',action='store_true')
    parser.add_argument('--combined',action='store_true')
    parser.add_argument('--source-classes',action='store_true')
    args=parser.parse_args()
    plan=json.loads((ROOT/'configs/failure_diagnosis_native.json').read_text())
    by_graph=defaultdict(list)
    for source in plan['sources']:
        if source['variant']=='a0':by_graph[source['manifest']['inputs']['rr_graph']['sha256']].append(source)
    state=dict(started_epoch=time.time(),workers=2,graphs=len(by_graph),results=[])
    suffix='_source_classes' if args.source_classes else '_combined' if args.combined else '_hall' if args.hall else ''
    path=BASE/('terminal_cuts'+suffix+'.json');write_json(path,state)
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(scan_group,(*item,args.hall or args.combined or args.source_classes,args.combined,args.source_classes)) for item in sorted(by_graph.items(),key=lambda x:Path(x[1][0]['manifest']['inputs']['rr_graph']['path']).stat().st_size)]
        for future in concurrent.futures.as_completed(futures):
            result=future.result();state['results'].append(result);write_json(path,state)
            print(json.dumps(result),flush=True)
    state['finished_epoch']=time.time();write_json(path,state)


if __name__=='__main__':main()
