#!/usr/bin/env python3
"""Compare exact physical node/edge identities, with explicit legacy Z mapping.

The large graph summaries retain DSP pin edges and vertical channel boundaries.
The optional exact planar comparison uses full sets only for the small fixtures.
No heuristic node matching or rounded delay comparison is used for topology.
"""
import argparse
from array import array
from collections import Counter, defaultdict
import json
from pathlib import Path
import time

from lxml import etree
from lazagna_common import sha256, write_json


def records(path):
    sections={'rr_nodes','rr_edges','switches','segments','block_types','grid','channels'}
    with open(path,'rb') as stream:
        for _,e in etree.iterparse(stream,events=('end',),huge_tree=True):
            parent=e.getparent()
            if parent is not None and parent.tag in sections:
                yield parent.tag,e
                e.clear()
                while e.getprevious() is not None:
                    del parent[0]


def load(path, exact=False):
    start=time.monotonic()
    segments={};switches={};blocks={};grid={};dsp_locations=set();pin_names={}
    kinds=[];keys=[];caps=array('I');layer=array('h');z_nodes=set();dsp_opins={}
    counts=Counter();seg_counts=Counter();z_in=defaultdict(list);z_out=defaultdict(list)
    z_links=[];direct_z_pins=[];dsp_edges=defaultdict(list);source_opins=defaultdict(list)
    planar_edges=[];edge_types=Counter();sw_names={};channel_samples=[]
    for section,e in records(path):
        a=e.attrib
        if section=='segments':segments[int(a['id'])]=a['name']
        elif section=='switches':
            idx=int(a['id']);switches[idx]=dict(name=a.get('name',''),type=a.get('type',''),
                timing=dict(e.find('timing').attrib) if e.find('timing') is not None else {})
        elif section=='block_types':
            idx=int(a['id']);blocks[idx]=a['name']
            pin_names[idx]={int(p.get('ptc')):p.text for p in e.findall('pin_class/pin')}
        elif section=='grid':
            if e.tag=='grid_loc':
                loc=(int(a['x']),int(a['y']),int(a.get('layer','0')))
                grid[loc]=int(a['block_type_id'])
                if blocks.get(int(a['block_type_id']))=='complex_dsp':dsp_locations.add(loc)
        elif section=='channels':
            if len(channel_samples)<10:channel_samples.append(dict(a))
        elif section=='rr_nodes':
            inode=int(a['id'])
            if inode!=len(kinds):raise ValueError('Noncontiguous node IDs')
            l=e.find('loc').attrib
            lo=(int(l['xlow']),int(l['ylow']),int(l.get('layer_low',l.get('layer','0'))))
            hi=(int(l['xhigh']),int(l['yhigh']),int(l.get('layer_high',l.get('layer','0'))))
            seg=e.find('segment');sn=segments.get(int(seg.get('segment_id')),'') if seg is not None else ''
            kind=a['type'];is_z=kind=='CHANZ' or sn=='3D_SB_connection'
            kinds.append('Z' if is_z else kind);caps.append(int(a.get('capacity','1')));layer.append(lo[2])
            key=(kind,lo,hi,int(l['ptc']),l.get('side',''),a.get('direction','NONE'),sn)
            keys.append(key if (exact or is_z or lo in dsp_locations) else None)
            counts[kind]+=1
            if sn:seg_counts[sn]+=1
            if is_z:z_nodes.add(inode)
            if kind=='OPIN' and lo in dsp_locations:dsp_opins[inode]=(lo,int(l['ptc']))
        elif section=='rr_edges':
            u=int(a['src_node']);v=int(a['sink_node']);sw=int(a['switch_id'])
            edge_types[kinds[u]+'->'+kinds[v]]+=1
            if u in dsp_opins:dsp_edges[u].append((v,sw))
            if kinds[u]=='SOURCE' and v in dsp_opins:source_opins[u].append(v)
            if u in z_nodes and v in z_nodes:z_links.append((u,v,sw))
            elif v in z_nodes:
                z_in[v].append((u,sw))
                if kinds[u] in ('IPIN','OPIN'):direct_z_pins.append((u,v,sw))
            elif u in z_nodes:
                z_out[u].append((v,sw))
                if kinds[v] in ('IPIN','OPIN'):direct_z_pins.append((u,v,sw))
            elif exact:
                planar_edges.append((u,v,sw))
    by_site=defaultdict(list)
    for u,(loc,ptc) in dsp_opins.items():by_site[loc].append(u)
    dsp_profiles=[]
    for loc,opins in sorted(by_site.items()):
        boundary=set(v for u in opins for v,_ in dsp_edges[u])
        sides={}
        for side in sorted(set(keys[u][4] for u in opins)):
            us=[u for u in opins if keys[u][4]==side]
            vs=set(v for u in us for v,_ in dsp_edges[u])
            sides[side]=dict(opins=len(us),distinct_exit_nodes=len(vs),capacity=sum(caps[v] for v in vs))
        dsp_profiles.append(dict(coordinate=loc,opin_count=len(opins),
            distinct_exit_nodes=len(boundary),exit_capacity=sum(caps[v] for v in boundary),
            output_edges=sum(len(dsp_edges[u]) for u in opins),sides=sides,
            per_pin=[dict(ptc=dsp_opins[u][1],name=pin_names[grid[loc]].get(dsp_opins[u][1]),
                          degree=len(dsp_edges[u]),destinations=[v for v,_ in dsp_edges[u]]) for u in opins]))
    # Paired CHANX Z nodes each have capacity one; one inter-layer edge is one
    # physical vertical channel. Native CHANZ already spans the layer range.
    physical=[]
    paired=set()
    for u,v,sw in z_links:
        if layer[u]==layer[v]:raise ValueError('Legacy Z pair stays within one layer')
        if u in paired or v in paired:raise ValueError('Ambiguous legacy Z resource pairing')
        if caps[u]!=1 or caps[v]!=1:raise ValueError('Unexpected legacy Z capacity')
        if z_out[u] or z_in[v]:raise ValueError('Legacy pair has a bypass around its crossing edge')
        paired.update((u,v))
        physical.append(dict(nodes=[u,v],source_layer=layer[u],sink_layer=layer[v],
                             fanin=len(z_in[u]),fanout=len(z_out[v]),capacity=1,
                             coordinate=list(keys[u][1][:2]),cross_switch=switches[sw]))
    for u in sorted(z_nodes-paired):
        if keys[u][0]!='CHANZ':raise ValueError('Unpaired legacy Z node')
        physical.append(dict(nodes=[u],layer_range=[keys[u][1][2],keys[u][2][2]],
                             fanin=len(z_in[u]),fanout=len(z_out[u]),capacity=caps[u],
                             coordinate=list(keys[u][1][:2])))
    histogram=Counter((x['fanin'],x['fanout']) for x in physical)
    summary=dict(path=str(Path(path).resolve()),sha256=sha256(path),
        node_counts=dict(counts),segment_node_counts=dict(seg_counts),edge_counts=dict(edge_types),
        total_nodes=len(kinds),total_edges=sum(edge_types.values()),channel_header=channel_samples,
        dsp_site_count=len(dsp_profiles),dsp_exit_capacity_histogram=dict(Counter(x['exit_capacity'] for x in dsp_profiles)),
        dsp_profiles=dsp_profiles,vertical_rr_nodes=len(z_nodes),physical_vertical_channels=len(physical),
        vertical_fanin_fanout_histogram=[dict(fanin=a,fanout=b,count=n) for (a,b),n in sorted(histogram.items())],
        direct_vertical_pin_edges=direct_z_pins,physical_vertical_mapping=physical,
        switches=switches,elapsed_seconds=time.monotonic()-start)
    return summary,dict(keys=keys,kinds=kinds,edges=planar_edges,switches=switches,caps=caps,
                        source_opins=source_opins,dsp_edges=dsp_edges)


def compare(a,b):
    ka={k:i for i,k in enumerate(a['keys']) if a['kinds'][i]!='Z'}
    kb={k:i for i,k in enumerate(b['keys']) if b['kinds'][i]!='Z'}
    if len(ka)!=sum(x!='Z' for x in a['kinds']) or len(kb)!=sum(x!='Z' for x in b['kinds']):
        raise ValueError('Physical node key is not unique')
    common=set(ka)&set(kb)
    # Use exact tuple equality throughout; no digest approximation for topology.
    combined={k:i for i,k in enumerate(sorted(set(ka)|set(kb)))}
    switch_names=sorted(set(x['name'] for x in a['switches'].values())|set(x['name'] for x in b['switches'].values()))
    swi={n:i for i,n in enumerate(switch_names)}
    def edges(g):
        ids=[combined.get(k,-1) for k in g['keys']]
        return {(ids[u],ids[v],swi[g['switches'][s]['name']]) for u,v,s in g['edges']}
    ea=edges(a);eb=edges(b);onlya=ea-eb;onlyb=eb-ea
    inverse={v:k for k,v in combined.items()}
    def classes(es):
        return dict(sorted(Counter(inverse[u][0]+'->'+inverse[v][0] for u,v,_ in es).items()))
    def examples(es):return [dict(source=inverse[u],sink=inverse[v],switch=switch_names[s]) for u,v,s in sorted(es)[:12]]
    return dict(common_planar_nodes=len(common),only_left_nodes=len(set(ka)-common),only_right_nodes=len(set(kb)-common),
                left_planar_edges=len(ea),right_planar_edges=len(eb),common_edges=len(ea&eb),
                only_left_edges=len(onlya),only_right_edges=len(onlyb),
                edge_classes={'left':classes(ea),'right':classes(eb),'common':classes(ea&eb),
                              'only_left':classes(onlya),'only_right':classes(onlyb)},
                left_only_examples=examples(onlya),right_only_examples=examples(onlyb),
                identical_planar_topology=set(ka)==set(kb) and ea==eb,
                capacity_mismatches=sum(a['caps'][ka[k]]!=b['caps'][kb[k]] for k in common))


def main():
    p=argparse.ArgumentParser();p.add_argument('--left',type=Path,required=True)
    p.add_argument('--right',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise RuntimeError('Refusing to overwrite evidence')
    sa,a=load(args.left,exact=bool(args.right))
    result={'left':sa}
    if args.right:
        sb,b=load(args.right,exact=True);result.update(right=sb,comparison=compare(a,b))
    write_json(args.output,result)
    print(json.dumps({k:v for k,v in result.items() if k=='comparison'}))


if __name__=='__main__':main()
