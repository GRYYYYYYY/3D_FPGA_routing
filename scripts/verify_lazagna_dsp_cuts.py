#!/usr/bin/env python3
"""Independently rescan every reported SOURCE/OPIN cut and its boundary."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from compare_lazagna_graphs import records
from lazagna_common import sha256,write_json


def verify(path):
    data=json.loads(path.read_text());graph=Path(data['graph']);assert sha256(graph)==data['graph_sha256']
    certs=data['certificates'];membership=defaultdict(list);regions=[];observed=[set() for _ in certs];caps={};metadata={}
    for i,c in enumerate(certs):
        region=set(c['source_nodes'])|set(c['opin_nodes']);regions.append(region)
        for n in region:membership[n].append(i)
        for p,h in [('packed_netlist','packed_sha256'),('placement','placement_sha256')]:
            # Verify each file once below, not once per certificate.
            metadata[c[p]]=c[h]
    for p,h in metadata.items():assert sha256(p)==h
    targets=set(membership)|{n for c in certs for n in c['boundary_nodes']};kinds={};cross_edges=0
    for sec,e in records(graph):
        if sec=='rr_nodes':
            i=int(e.get('id'))
            if i in targets:caps[i]=int(e.get('capacity'));kinds[i]=e.get('type')
        elif sec=='rr_edges':
            u,v=int(e.get('src_node')),int(e.get('sink_node'))
            for i in membership.get(u,()):
                if v not in regions[i]:observed[i].add(v);cross_edges+=1
    checked=[]
    for i,c in enumerate(certs):
        assert observed[i]==set(c['boundary_nodes'])
        assert all(kinds[n]=='SOURCE' for n in c['source_nodes'])
        assert all(kinds[n]=='OPIN' for n in c['opin_nodes'])
        capacity=sum(caps[n] for n in observed[i]);demand=len({x['net'] for x in c['nets']})
        assert capacity==c['capacity'] and demand==c['demand'] and demand>capacity
        assert all(x['external_sink_example']!=c['block'] for x in c['nets'])
        checked.append({k:c[k] for k in ['case','coordinate','subset','demand','capacity','deficit']})
    return {'passed':True,'complete_graph_scan':True,'input':str(path),'input_sha256':sha256(path),
            'graph_sha256':data['graph_sha256'],'certificates':checked,
            'scope':'Independent exact region-boundary and capacity verification; packed endpoint resolution is covered by the separately tested resolver and retained per-net witnesses.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise RuntimeError('Existing verification')
    d=verify(a.input);write_json(a.output,d);print(d['passed'],len(d['certificates']))
