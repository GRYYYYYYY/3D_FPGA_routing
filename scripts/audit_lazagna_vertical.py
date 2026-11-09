#!/usr/bin/env python3
"""Verify complete physical Z mapping and delays without loading XML trees."""
import argparse
from array import array
from collections import Counter,defaultdict
from pathlib import Path
from compare_lazagna_graphs import records
from lazagna_common import sha256,write_json


def scan(path,output):
    segments={};switches={};z=set();kinds=[];layers=array('h');caps=array('I')
    locs={};fanin=Counter();fanout=Counter();ins=defaultdict(set);outs=defaultdict(set)
    inlayers=defaultdict(set);outlayers=defaultdict(set);pairs=[];direct=[]
    sample_in=defaultdict(list);sample_out=defaultdict(list);track=Counter();xy=array('i')
    ntypes=Counter();etypes=Counter();zero_rc=True
    for section,e in records(path):
        a=e.attrib
        if section=='segments':segments[int(a['id'])]=a['name']
        elif section=='switches':
            t=e.find('timing');switches[int(a['id'])]={'name':a.get('name'), 'timing':dict(t.attrib) if t is not None else {}}
        elif section=='rr_nodes':
            i=int(a['id']);assert i==len(kinds)
            l=e.find('loc').attrib;seg=e.find('segment');sn=segments[int(seg.get('segment_id'))] if seg is not None else ''
            isz=a['type']=='CHANZ' or sn=='3D_SB_connection'
            kind='Z' if isz else a['type'];kinds.append(kind);ntypes[kind]+=1
            layer=int(l.get('layer_low',l.get('layer','0')));layers.append(layer);caps.append(int(a['capacity']))
            x,y=int(l['xlow']),int(l['ylow']);xy.extend((x,y))
            if isz:
                z.add(i);locs[i]=(x,y,layer,int(l.get('layer_high',l.get('layer','0'))))
            if a['type']=='CHANX' and not isz and layer==0 and y==20 and x<=20<=int(l['xhigh']):track[sn]+=1
            t=e.find('timing')
            if t is not None:zero_rc &= all(float(t.get(k,0))==0 for k in ['R','C'])
        elif section=='rr_edges':
            u,v,s=int(a['src_node']),int(a['sink_node']),int(a['switch_id']);etypes[kinds[u]+'->'+kinds[v]]+=1
            if u in z and v in z:pairs.append((u,v,s))
            elif v in z:
                fanin[v]+=1;ins[v].add(s);inlayers[v].add(layers[u])
                if kinds[u] in ('OPIN','IPIN'):direct.append((u,v,s))
                if locs[v][:2]==(26,12):sample_in[v].append((u,v,s))
            elif u in z:
                fanout[u]+=1;outs[u].add(s);outlayers[u].add(layers[v])
                if kinds[v] in ('OPIN','IPIN'):direct.append((u,v,s))
                if locs[u][:2]==(26,12):sample_out[u].append((u,v,s))
    channels={};seen=set();errors=[];hist=Counter();delays=Counter();sites=set();examples=[]
    def delay(s):return float(switches[s]['timing'].get('Tdel',0))*1e12
    for u,v,s in pairs:
        if u in seen or v in seen:errors.append(['duplicate_pair',u,v])
        seen.update([u,v]);sites.add(locs[u][:2])
        if caps[u]!=1 or caps[v]!=1 or locs[u][:2]!=locs[v][:2] or layers[u]==layers[v]:errors.append(['invalid_pair',u,v])
        if fanout[u] or fanin[v]:errors.append(['pair_bypass',u,v])
        if inlayers[u]!={layers[u]} or outlayers[v]!={layers[v]}:errors.append(['wrong_endpoint_layer',u,v])
        channels[f'legacy:{u}:{v}']={'nodes':[u,v],'capacity':1}
        hist[(fanin[u],fanout[v])]+=1
        for a in ins[u]:
            for b in outs[v]:delays[round(delay(a)+delay(s)+delay(b),9)]+=1
        if len(examples)<12 and locs[u][:2]==(26,12):
            examples.append({'nodes':[u,v],'coordinate':locs[u][:2],'source_layer':layers[u],'sink_layer':layers[v],
                'input_edges':sample_in[u],'cross_edge':[u,v,s],'output_edges':sample_out[v]})
    for u in sorted(z-seen):
        if locs[u][2]==locs[u][3]:errors.append(['unpaired_legacy_node',u]);continue
        channels[f'native:{u}']={'nodes':[u],'capacity':caps[u]};sites.add(locs[u][:2]);hist[(fanin[u],fanout[u])]+=1
        for a in ins[u]:
            for b in outs[u]:delays[round(delay(a)+delay(b),9)]+=1
        if len(examples)<12 and locs[u][:2]==(26,12):
            examples.append({'nodes':[u],'coordinate':locs[u][:2],'layer_range':locs[u][2:],
                             'input_edges':sample_in[u],'output_edges':sample_out[u]})
    wanted={i for ex in examples for key in ['input_edges','output_edges'] for edge in ex[key] for i in edge[:2]}
    metadata={}
    for section,e in records(path):
        if section=='rr_edges':break
        if section=='rr_nodes' and int(e.get('id')) in wanted:
            seg=e.find('segment');metadata[e.get('id')]={'type':e.get('type'),'direction':e.get('direction'),
                'location':dict(e.find('loc').attrib),'segment':segments[int(seg.get('segment_id'))] if seg is not None else None}
    mapfile=output.with_suffix('.resource_map.json')
    write_json(mapfile,{'schema':1,'graph_sha256':sha256(path),'channels':channels,
                       'verification':'Every legacy pair has exactly one cross-layer edge, no bypass, capacity-one halves, and local plane endpoints.'})
    result={'graph':str(path),'graph_sha256':sha256(path),'passed':not errors,'errors':errors,
            'nodes_by_type':dict(ntypes),'edges_by_type':dict(etypes),'physical_vertical_channels':len(channels),
            'vertical_locations':len(sites),'direct_vertical_pin_edges':direct,'zero_node_rc':zero_rc,
            'sample_channel_at_20_20_layer0':dict(track),'fanin_fanout_histogram':[{'fanin':a,'fanout':b,'count':n} for (a,b),n in sorted(hist.items())],
            'plane_to_plane_switch_delay_ps_values':sorted(delays),'switches':switches,'examples':examples,'example_node_metadata':metadata,
            'resource_map':str(mapfile),'resource_map_sha256':sha256(mapfile),
            'interpretation':'Native bidirectional CHANZ is one shared capacity resource; legacy opposite directions are distinct physical groups. Delay list sums actual crossing-path switches; same-layer paths through native CHANZ are also possible.'}
    write_json(output,result);print(str(output),result['passed'],len(channels),dict(track),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--graph',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise RuntimeError('Output already exists')
    scan(a.graph,a.output)
