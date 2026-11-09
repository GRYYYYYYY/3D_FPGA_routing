#!/usr/bin/env python3
"""Map packed DSP output nets to exact physical SOURCE/OPIN cut boundaries."""
import argparse
from array import array
from collections import defaultdict
from pathlib import Path
import re
from lxml import etree as ET
from compare_lazagna_graphs import records
from lazagna_common import BASE,sha256,write_json


def output_net(block,port,bit,depth=0):
    if depth>10:raise ValueError('Cyclic/deep packed output reference')
    value=block.find(f"outputs/port[@name='{port}']").text.split()[bit]
    if value=='open':return None
    if '->' not in value:return value
    m=re.fullmatch(r'(.+\[\d+\])\.([^\[]+)\[(\d+)\]->.+',value)
    if not m:raise ValueError('Unknown packed reference: '+value)
    child=block.find(f"block[@instance='{m[1]}']")
    if child is None:raise ValueError('Missing packed child: '+m[1])
    return output_net(child,m[2],int(m[3]),depth+1)


def demands(case):
    p=BASE/'runs'/f'paper_primary_{case}_w300';packed=p/'packed.net';place=p/'fixed.place'
    if not packed.exists() or not place.exists():return []
    packed_hash=sha256(packed);place_hash=sha256(place)
    root=ET.parse(str(packed)).getroot();blocks=root.findall('block');sinks=defaultdict(set)
    for b in blocks:
        for port in b.findall('inputs/port')+b.findall('clocks/port'):
            for net in (port.text or '').split():
                if net!='open':sinks[net].add(b.get('name'))
    placements={}
    for line in place.read_text().splitlines():
        t=line.split()
        if len(t)==6 and t[-1].startswith('#'):
            placements[t[0]]=(int(t[1]),int(t[2]),int(t[4]))
    found=[]
    for b in blocks:
        if not b.get('instance','').startswith('complex_dsp['):continue
        name=b.get('name');nets=[]
        for bit in range(74):
            net=output_net(b,'result',bit)
            if net and sinks[net]-{name}:nets.append({'bit':bit,'net':net,'external_sink_example':sorted(sinks[net]-{name})[0]})
        if len({x['net'] for x in nets})<24:continue
        for label,subset in [('all',nets),('low37',[x for x in nets if x['bit']<37]),('high37',[x for x in nets if x['bit']>=37])]:
            if len({x['net'] for x in subset})<24:continue
            found.append({'case':case,'block':name,'coordinate':placements[name],'subset':label,'nets':subset,
                          'packed_netlist':str(packed),'packed_sha256':packed_hash,'placement':str(place),'placement_sha256':place_hash})
    return found


def prove(graph,groups):
    blocks={};pinclass={};classes={};sites={};sources={};opin={};caps=array('I');kind=[];source_edges=defaultdict(set);opin_edges=defaultdict(set)
    locations={tuple(g['coordinate']) for g in groups}
    for sec,e in records(graph):
        a=e.attrib
        if sec=='block_types' and a['name']=='complex_dsp':
            dspid=int(a['id'])
            for cls,c in enumerate(e.findall('pin_class')):
                if c.get('type')!='OUTPUT':continue
                for p in c.findall('pin'):
                    m=re.fullmatch(r'complex_dsp.result\[(\d+)\]',p.text)
                    assert m;pinclass[int(m[1])]=cls
        elif sec=='grid':
            loc=(int(a['x']),int(a['y']),int(a.get('layer',0)))
            if loc in locations:assert int(a['block_type_id'])==dspid
        elif sec=='rr_nodes':
            i=int(a['id']);assert i==len(caps);caps.append(int(a['capacity']));kind.append(a['type'])
            if a['type'] not in ['SOURCE','OPIN']:continue
            l=e.find('loc').attrib;loc=(int(l['xlow']),int(l['ylow']),int(l.get('layer_low',l.get('layer',0))))
            if loc not in locations:continue
            if a['type']=='SOURCE':sources[(loc,int(l['ptc']))]=i
            else:opin[i]=loc
        elif sec=='rr_edges':
            u,v=int(a['src_node']),int(a['sink_node'])
            if kind[u]=='SOURCE' and v in opin:source_edges[u].add(v)
            if u in opin:opin_edges[u].add(v)
    certificates=[]
    for g in groups:
        loc=tuple(g['coordinate']);roots={sources[(loc,pinclass[n['bit']])] for n in g['nets']}
        pins=set().union(*(source_edges[s] for s in roots));boundary=set().union(*(opin_edges[u] for u in pins))
        n=len({x['net'] for x in g['nets']});capacity=sum(caps[v] for v in boundary)
        if n>capacity:
            certificates.append({**g,'demand':n,'capacity':capacity,'deficit':n-capacity,'source_nodes':sorted(roots),
                                 'opin_nodes':sorted(pins),'boundary_nodes':sorted(boundary)})
    return {'graph':str(graph),'graph_sha256':sha256(graph),'complete_graph_scan':True,'certificates':certificates,
            'scope':'Necessary vertex-capacity condition for distinct packed DSP outputs with explicit external-cluster sinks. SOURCE pin classes expanded to all candidate OPINs; exact outgoing boundary and RR capacities used. Independent of congestion settings.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--graph',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise RuntimeError('Existing cut evidence')
    groups=[g for c in ['attention_layer','conv_layer','dla_like.small'] for g in demands(c)]
    d=prove(a.graph,groups);write_json(a.output,d)
    print({c:sum(x['case']==c for x in d['certificates']) for c in ['attention_layer','conv_layer','dla_like.small']},flush=True)
