#!/usr/bin/env python3
"""Near-square 2D reference with exact logical capacities from a generated 3D grid."""
import argparse
from collections import Counter
import copy
import hashlib
import math
import xml.etree.ElementTree as ET

from compare_lazagna_graphs import records
from lazagna_common import ROOT,sha256,utc,write_json
from prepare_flatland_controlled_architectures import common_root

BASE=ROOT/'results/architecture_flow_20261027'


def grid_counts(graph):
    types={};counts=Counter()
    for section,e in records(graph):
        if section=='block_types':types[int(e.get('id'))]=e.get('name')
        elif section=='grid' and e.tag=='grid_loc':
            if int(e.get('width_offset','0'))==0 and int(e.get('height_offset','0'))==0:
                counts[types[int(e.get('block_type_id'))]]+=1
        elif section=='rr_nodes':break
    return counts


def order_key(kind,point):
    return hashlib.sha256(f'{kind}:{point[0]}:{point[1]}'.encode()).digest()


def prepare(size,width):
    graph=BASE/'runs'/f'controlled_graph_sb_n{size}_w{width}_ideal'/'rr_graph.xml'
    target=grid_counts(graph)
    assert set(target)<={'io','clb','spram','complex_dsp','EMPTY'}
    core_types=['clb','spram','complex_dsp']
    needed=sum(target[t] for t in core_types)
    side=math.isqrt(needed)
    if side*side<needed:side+=1
    side+=2
    root=common_root('sb',size)
    for t in root.findall('tiles/tile'):
        assert int(t.get('height','1'))==int(t.get('width','1'))==1
    cells={(x,y):('complex_dsp' if (x-2)%8==0 else 'spram' if (x-4)%8==0 else 'clb')
           for x in range(1,side-1) for y in range(1,side-1)}
    edits=[]
    for kind in ['complex_dsp','spram']:
        present=[p for p,t in cells.items() if t==kind]
        excess=len(present)-target[kind]
        if excess>0:
            chosen=sorted(present,key=lambda p:(min(p[1]-1,side-2-p[1]),order_key(kind,p)))[:excess]
            for p in chosen:cells[p]='clb';edits.append(dict(x=p[0],y=p[1],old=kind,new='clb'))
    for kind,start in [('complex_dsp',2),('spram',4)]:
        missing=target[kind]-sum(t==kind for t in cells.values())
        columns=list(range(start,side-1,8))
        chosen=sorted((p for p,t in cells.items() if t=='clb'),
            key=lambda p:(min(abs(p[0]-x) for x in columns),order_key(kind,p)))[:missing]
        assert len(chosen)==missing
        for p in chosen:cells[p]=kind;edits.append(dict(x=p[0],y=p[1],old='clb',new=kind))
    excess=sum(t=='clb' for t in cells.values())-target['clb']
    assert excess>=0
    chosen=sorted((p for p,t in cells.items() if t=='clb'),
        key=lambda p:(min(p[0]-1,p[1]-1,side-2-p[0],side-2-p[1]),order_key('EMPTY',p)))[:excess]
    for p in chosen:cells[p]='EMPTY';edits.append(dict(x=p[0],y=p[1],old='clb',new='EMPTY'))
    boundary=([(x,0) for x in range(1,side-1)] + [(side-1,y) for y in range(1,side-1)]
              + [(x,side-1) for x in range(side-2,0,-1)] + [(0,y) for y in range(side-2,0,-1)])
    io=root.find("tiles/tile[@name='io']")
    io_sub=io.find('sub_tile');capacity=int(io_sub.get('capacity'))
    desired_io_slots=target['io']*capacity
    extra_slots=desired_io_slots-len(boundary)*capacity
    assert extra_slots>=0 and extra_slots%capacity==0
    doubled_count=extra_slots//capacity;assert doubled_count<=len(boundary)
    double_io=copy.deepcopy(io);double_io.set('name','io_double')
    sub=double_io.find('sub_tile');old_name=sub.get('name');sub.set('name','io_double')
    sub.set('capacity',str(2*capacity))
    for loc in sub.findall('pinlocations/loc'):loc.text=(loc.text or '').replace(old_name+'.','io_double.')
    root.find('tiles').append(double_io)
    doubled={boundary[i*len(boundary)//doubled_count] for i in range(doubled_count)} if doubled_count else set()
    for p in boundary:cells[p]='io_double' if p in doubled else 'io'
    layout=root.find('layout');layout.clear()
    fixed=ET.SubElement(layout,'fixed_layout',name=f'matched2d_{size}',width=str(side),height=str(side))
    ET.SubElement(fixed,'fill',type='EMPTY',priority='1')
    for (x,y),kind in sorted(cells.items()):
        if kind!='EMPTY':ET.SubElement(fixed,'single',type=kind,x=str(x),y=str(y),priority='10')
    switches=root.find('switchblocklist')
    switches.remove(switches.find("switchblock[@name='3d_subset']"))
    directory=BASE/'controlled_architectures'/f'n{size}'
    arch=directory/'matched_2d.xml'
    if arch.exists():raise FileExistsError(arch)
    ET.indent(root);ET.ElementTree(root).write(arch,encoding='utf-8',xml_declaration=True)
    actual=Counter(cells.values())
    assert all(actual[t]==target[t] for t in core_types)
    assert capacity*(actual['io']+2*actual['io_double'])==desired_io_slots
    write_json(directory/'matched_2d_manifest.json',dict(utc=utc(),source_graph=str(graph),source_graph_sha256=sha256(graph),
        path=str(arch),sha256=sha256(arch),source_grid=[size,size,2],grid=[side,side,1],
        target_3d_tile_counts=dict(target),derived_2d_explicit_tile_counts=dict(actual),
        logical_slot_targets={**{t:target[t] for t in core_types},'io':desired_io_slots},
        tile_capacity_edits=edits,doubled_io_coordinates=sorted(doubled),
        method='Smallest square interior accommodating all 3D core blocks; start from periodic DSP/BRAM columns; deterministic capacity adjustments, no QoR-based selection; distribute added I/O slots uniformly around perimeter',
        limitation='Exact logical capacities, same W/segment weights/planar switch rules. Physical footprint, I/O density, boundary truncation and actual planar wire capacities differ and must be measured/disclosed. This is a derived reference, not the author 2D XML.'))
    print('Matched logical-capacity 2D',side,'x',side,'target',dict(target))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--size',type=int,default=25);p.add_argument('--width',type=int,default=100)
    a=p.parse_args();prepare(a.size,a.width)
