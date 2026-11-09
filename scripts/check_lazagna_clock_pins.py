#!/usr/bin/env python3
"""Prove whether BRAM clock IPINs have any incoming graph edge."""
import argparse
from collections import Counter
from pathlib import Path
from compare_lazagna_graphs import records
from lazagna_common import sha256,write_json


def scan(graph):
    types={};clockptc={};sites={};wanted={};incoming=Counter();edges=0
    for sec,e in records(graph):
        a=e.attrib
        if sec=='block_types':
            i=int(a['id']);types[i]=a['name']
            if a['name']=='spram':clockptc[i]={int(p.get('ptc')) for p in e.findall('pin_class/pin') if p.text=='spram.clk[0]'}
        elif sec=='grid':
            t=int(a['block_type_id'])
            if t in clockptc:sites[(int(a['x']),int(a['y']),int(a.get('layer',0)))]=t
        elif sec=='rr_nodes' and a['type']=='IPIN':
            l=e.find('loc').attrib;loc=(int(l['xlow']),int(l['ylow']),int(l.get('layer_low',l.get('layer',0))))
            if loc in sites and int(l['ptc']) in clockptc[sites[loc]]:wanted[int(a['id'])]=loc
        elif sec=='rr_edges':
            edges+=1;v=int(a['sink_node'])
            if v in wanted:incoming[v]+=1
    assert wanted
    return {'graph':str(graph),'sha256':sha256(graph),'complete_graph_scan':True,'edges_scanned':edges,
            'bram_clock_ipins':len(wanted),'zero_fanin_clock_ipins':sum(incoming[i]==0 for i in wanted),
            'incoming_edges':sum(incoming.values()),'examples':[{'node':i,'coordinate':loc,'fanin':incoming[i]} for i,loc in list(wanted.items())[:12]],
            'scope':'No incoming edge means no route to this physical BRAM clock pin at any iteration or congestion setting. This is independent of DSP output cuts.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--graph',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise RuntimeError('Existing evidence')
    d=scan(a.graph);write_json(a.output,d);print({k:v for k,v in d.items() if k!='examples'})
