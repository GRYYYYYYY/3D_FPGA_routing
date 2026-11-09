#!/usr/bin/env python3
"""Separate native graph-generation clock policy from BRAM zero-Fc limits."""
from collections import Counter
from pathlib import Path
from compare_lazagna_graphs import records
from lazagna_common import BASE, ROOT, PAPER, PYTHON, run, sha256, utc, write_json


def scan_clocks(graph):
    types={};pins={};sites={};wanted={};incoming=Counter();edges=0
    for sec,e in records(graph):
        a=e.attrib
        if sec=='block_types':
            i=int(a['id']);types[i]=a['name']
            pins[i]={int(p.get('ptc')) for p in e.findall('pin_class/pin') if p.text in ('clb.clk[0]','spram.clk[0]')}
        elif sec=='grid':
            t=int(a['block_type_id'])
            if pins[t]:sites[(int(a['x']),int(a['y']),int(a.get('layer',0)))]=t
        elif sec=='rr_nodes' and a['type']=='IPIN':
            l=e.find('loc').attrib;loc=(int(l['xlow']),int(l['ylow']),int(l.get('layer_low',l.get('layer',0))))
            if loc in sites and int(l['ptc']) in pins[sites[loc]]:wanted[int(a['id'])]=types[sites[loc]]
        elif sec=='rr_edges':
            edges+=1;v=int(a['sink_node'])
            if v in wanted:incoming[v]+=1
    return {'graph':str(graph),'graph_sha256':sha256(graph),'complete_graph_scan':True,'edges_scanned':edges,
            'types':{t:{'clock_ipins':sum(v==t for v in wanted.values()),
                        'zero_fanin':sum(incoming[i]==0 for i,v in wanted.items() if v==t),
                        'incoming_edges':sum(incoming[i] for i,v in wanted.items() if v==t)} for t in ('clb','spram')}}


def main():
    protocol=BASE/'clock_graph_mode_protocol.json'
    if protocol.exists():raise RuntimeError('Clock graph control already exists')
    write_json(protocol,{'utc':utc(),'finding':'Two native fixed bnn route-clock trials reported no path to clb.clk; the shared native graph was generated with ideal clock policy. This control tests whether missing CLB clock edges are a graph-generation mismatch, independently of BRAM Fc=0.',
                        'control':'Same pristine native binary, native_40.xml, W100, and2 BLIF, only graph-generation clock_modeling changes ideal->route. No benchmark or successful route is altered.',
                        'scope':'Original native-ideal diagnostic rows remain on their frozen graph. Native route-clock bnn rows are not evidence of router nonconvergence.'})
    binary=ROOT/'artifacts/bin/baseline/vpr';arch=BASE/'architectures/native_40.xml';blif=PAPER/'benchmarks/and2/and2.blif'
    name='native_routeclock_graph_40_w100';graph=BASE/'runs'/name/'rr_graph.xml'
    r=run(name,[binary,arch,blif,'--pack','--route_chan_width',100,'--num_workers',1,'--clock_modeling','route','--write_rr_graph',graph],inputs=[binary,arch,blif],timeout=600)
    assert r['status']=='completed'
    ideal=BASE/'runs/native_graph_40_w100/rr_graph.xml'
    result=run('compare_native_clock_graph_modes',[PYTHON,ROOT/'scripts/compare_lazagna_graphs.py','--left',ideal,'--right',graph,'--output',BASE/'native_clock_graph_mode_comparison.json'],inputs=[ideal,graph],timeout=1200)
    assert result['status']=='completed'
    for label,g in [('native_ideal_40_w100',ideal),('native_route_40_w100',graph),('native_ideal_100_w300',BASE/'runs/native_graph_100_w300/rr_graph.xml')]:
        write_json(BASE/f'clock_all_{label}.json',scan_clocks(g));print('clock scan',label,flush=True)
    write_json(BASE/'clock_graph_mode_complete.json',{'utc':utc(),'completed':True})


if __name__=='__main__':main()
