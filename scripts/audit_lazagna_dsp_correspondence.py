#!/usr/bin/env python3
"""Compare every DSP OPIN endpoint on the full paper-sized graphs.

Node IDs are version-local. Equality uses physical keys and capacities instead.
The second pass stops at rr_edges, keeping memory bounded to DSP endpoints.
"""
from collections import Counter, defaultdict
import gc
import json
from compare_lazagna_graphs import records
from lazagna_common import BASE, sha256, utc, write_json


def node_key(e, segments):
    a=e.attrib;l=e.find('loc').attrib;segment=e.find('segment')
    return (a['type'],int(l['xlow']),int(l['ylow']),int(l.get('layer_low',l.get('layer',0))),
            int(l['xhigh']),int(l['yhigh']),int(l.get('layer_high',l.get('layer',0))),
            int(l['ptc']),l.get('side',''),a.get('direction','NONE'),
            segments[int(segment.get('segment_id'))] if segment is not None else '',int(a['capacity']))


def scan(graph):
    blocks={};grid={};segments={};opins={};edges=defaultdict(list);edge_count=0
    for sec,e in records(graph):
        a=e.attrib
        if sec=='segments':segments[int(a['id'])]=a['name']
        elif sec=='block_types':blocks[int(a['id'])]=a['name']
        elif sec=='grid' and blocks[int(a['block_type_id'])]=='complex_dsp':
            grid[(int(a['x']),int(a['y']),int(a.get('layer',0)))]=True
        elif sec=='rr_nodes' and a['type']=='OPIN':
            l=e.find('loc').attrib
            location=(int(l['xlow']),int(l['ylow']),int(l.get('layer_low',l.get('layer',0))))
            if location in grid:opins[int(a['id'])]=node_key(e,segments)
        elif sec=='rr_edges':
            edge_count+=1;u=int(a['src_node'])
            if u in opins:edges[u].append(int(a['sink_node']))
    wanted={v for vs in edges.values() for v in vs};destinations={}
    for sec,e in records(graph):
        if sec=='rr_edges':break
        if sec=='rr_nodes' and int(e.get('id')) in wanted:
            destinations[int(e.get('id'))]=node_key(e,segments)
    assert len(destinations)==len(wanted)
    assert all(k[0] in ('CHANX','CHANY') and k[10]!='3D_SB_connection' for k in destinations.values())
    per_pin={opins[u]:tuple(sorted(destinations[v] for v in edges[u])) for u in opins}
    assert len(per_pin)==len(opins)
    sites=defaultdict(set);sides=defaultdict(set)
    for pin,vs in per_pin.items():
        sites[pin[1:4]].update(vs);sides[(pin[1:4],pin[8])].update(vs)
    summary={'graph':str(graph),'graph_sha256':sha256(graph),'complete_graph_edge_scan':True,
             'edges_scanned':edge_count,'dsp_sites':len(sites),'dsp_opins':len(opins),
             'dsp_output_edges':sum(map(len,edges.values())),
             'site_capacity_histogram':dict(Counter(sum(v[-1] for v in vs) for vs in sites.values())),
             'side_capacity_histogram':dict(Counter(sum(v[-1] for v in vs) for vs in sides.values())),
             'direct_vertical_pin_edges':0}
    return per_pin,summary


def main():
    for width in (100,300):
        output=BASE/f'dsp_correspondence_100_w{width}.json'
        if output.exists():raise RuntimeError('Existing full DSP comparison')
        left,ls=scan(BASE/'runs'/f'paper_sb_100_w{width}_p50'/'rr_graph.xml')
        print('paper scan',width,ls['dsp_opins'],flush=True)
        right,rs=scan(BASE/'runs'/f'native_graph_100_w{width}'/'rr_graph.xml')
        common=set(left)&set(right);mismatch=[p for p in common if left[p]!=right[p]]
        result={'utc':utc(),'width':width,'left':ls,'right':rs,'common_opins':len(common),
                'only_left_opins':len(left.keys()-right.keys()),'only_right_opins':len(right.keys()-left.keys()),
                'mismatched_pin_endpoint_multisets':len(mismatch),'examples':mismatch[:12],
                'passed':left==right,
                'scope':'All full-grid DSP OPINs and outgoing endpoint multisets, matched by physical type/coordinates/layers/ptc/side/direction/segment/capacity, not raw node IDs. Switch delays are audited separately; this is not a planar-fabric equivalence claim.'}
        write_json(output,result);print('DSP comparison',width,result['passed'],flush=True)
        del left,right;gc.collect()


if __name__=='__main__':main()
