#!/usr/bin/env python3
"""Compare exact ordinary nodes/edges while excluding all vertical resources."""
from collections import Counter
import json
from pathlib import Path
import sys

from compare_lazagna_graphs import records
from lazagna_common import ROOT,sha256,utc,write_json

BASE=ROOT/'results/architecture_flow_20261027'


def load(path,reference=None):
    segments={};switches={};keys=[];locations=[];edges=set();cross=Counter()
    if reference is None: identities={}
    else: identities=reference
    mapping=[];unknown=set();normal_keys=set()
    for section,e in records(path):
        a=e.attrib
        if section=='segments':segments[int(a['id'])]=a['name']
        elif section=='switches':
            timing=tuple(sorted((k,float(v)) for k,v in e.find('timing').attrib.items()))
            switches[int(a['id'])]=(a.get('name'),a.get('type'),timing)
        elif section=='rr_nodes':
            assert int(a['id'])==len(keys)
            loc=e.find('loc').attrib;seg=e.find('segment');t=e.find('timing')
            layer=int(loc.get('layer',loc.get('layer_low','0')));locations.append(layer)
            is_half=a['type']=='CHANX' and a.get('direction')=='NONE'
            key=None if is_half else (a['type'],int(a['capacity']),
                tuple(int(loc[k]) for k in ['xlow','ylow','xhigh','yhigh','ptc']),layer,
                loc.get('side'),a.get('direction'),segments[int(seg.get('segment_id'))] if seg is not None else None,
                tuple(sorted((k,float(v)) for k,v in t.attrib.items())) if t is not None else ())
            keys.append(key)
            if key is not None:
                assert key not in normal_keys,'Physical node identity is not unique'
                normal_keys.add(key)
                if reference is None:identities[key]=len(identities)
                elif key not in identities:unknown.add(key)
            mapping.append(identities.get(key,-1))
        elif section=='rr_edges':
            u,v,s=(int(a[k]) for k in ['src_node','sink_node','switch_id'])
            if locations[u]!=locations[v]:
                cross[('SB' if keys[u] is None else keys[u][0])+'->'+('SB' if keys[v] is None else keys[v][0])]+=1
            elif mapping[u]>=0 and mapping[v]>=0:
                edge=(mapping[u],mapping[v],switches[s])
                assert edge not in edges,'Duplicate planar edge'
                edges.add(edge)
    return dict(identities=identities,keys=normal_keys,unknown=unknown,edges=edges,cross=dict(cross))


def main():
    size,width=(map(int,sys.argv[1:]) if len(sys.argv)>1 else (25,100))
    paths={f:BASE/'runs'/f'controlled_graph_{f}_n{size}_w{width}_ideal'/'rr_graph.xml' for f in ['sb','cb_o','hybrid_o']}
    output=BASE/f'controlled_plane_comparison_n{size}_w{width}.json'
    if output.exists():raise FileExistsError(output)
    reference=load(paths['sb']);rows={}
    for family in ['cb_o','hybrid_o']:
        other=load(paths[family],reference['identities'])
        missing=reference['edges']-other['edges'];added=other['edges']-reference['edges']
        rows[family]=dict(same_ordinary_nodes=reference['keys']==other['keys'],
            ordinary_nodes=len(other['keys']),unknown_nodes=len(other['unknown']),
            same_planar_edges=not missing and not added,planar_edges=len(other['edges']),
            missing_vs_sb=len(missing),added_vs_sb=len(added),crossing_edges=other['cross'])
        print(family,rows[family],flush=True)
    write_json(output,dict(utc=utc(),paths={f:dict(path=str(p),sha256=sha256(p)) for f,p in paths.items()},
        comparison='Exact physical ordinary-node identities and directed same-layer edges including switch name/type/all timing fields; CHANX/NONE SB half-nodes and all inter-layer edges excluded',
        reference=dict(ordinary_nodes=len(reference['keys']),planar_edges=len(reference['edges']),crossing_edges=reference['cross']),
        results=rows,passed=all(r['same_ordinary_nodes'] and r['same_planar_edges'] for r in rows.values())))


if __name__=='__main__':main()
