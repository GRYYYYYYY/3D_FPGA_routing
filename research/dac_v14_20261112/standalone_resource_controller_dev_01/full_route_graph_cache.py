#!/usr/bin/env python3
"""Exact raw-XML metadata adapter for the unchanged complete-route auditor."""
import argparse,array,collections,json,resource,shutil,time
from pathlib import Path
import numpy as np
from immutable_rr_audit_cache import GraphAuditCache,KINDS
from retained_prefix_workflow import read,write,sha
from verify_path_witnesses_v2 import graph_records

def build(parent,output):
    start=time.monotonic();parent=Path(parent).resolve();output=Path(output).resolve()
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));assert shutil.disk_usage(output.parent).free>=80*1024**3
    output.mkdir(exist_ok=False);original=read(parent/'completion.json');graph=Path(original['graph']);g=GraphAuditCache(graph,parent)
    write(output/'registration.json',dict(status='registered_before_build',parent_cache=str(parent),question='Can the complete-route auditor receive exactly the same raw XML metadata through a digest-bound cache?',source_sha256={str(Path(__file__).resolve()):sha(__file__),str(parent/'completion.json'):sha(parent/'completion.json')},native_calls=0))
    directions=[];timings=[];direction_ids={};timing_ids={};extra=array.array('I');switch_timing={};switch_types=collections.Counter();node_types=collections.Counter();count=0
    for section,e in graph_records(graph):
        a=e.attrib;t=e.find('timing');timing={} if t is None else dict(t.attrib)
        if section=='rr_edges':break # All edge evidence already bound to the same actual XML.
        if section=='switches':
            switch_types[a.get('type','unknown')]+=1;switch_timing[int(a['id'])]=timing
        else:
            node=int(a['id']);assert node==count;count+=1
            kind=a['type'];assert kind in KINDS and kind!='CHANZ'
            node_types[kind]+=1;loc=e.find('loc').attrib
            low=tuple(int(loc[k]) for k in ['xlow','ylow'])+(int(loc.get('layer_low',loc.get('layer','0'))),)
            high=tuple(int(loc[k]) for k in ['xhigh','yhigh'])+(int(loc.get('layer_high',loc.get('layer','0'))),)
            c=g.nodes[node];assert kind==KINDS[int(c[1])] and tuple(c[2:5])==low and tuple(c[5:8])==high and int(c[0])==int(a['capacity'])
            direction=a.get('direction','NONE');token=json.dumps(timing,sort_keys=True)
            if direction not in direction_ids:direction_ids[direction]=len(directions);directions.append(direction)
            if token not in timing_ids:timing_ids[token]=len(timings);timings.append(timing)
            extra.extend([direction_ids[direction],timing_ids[token]])
    assert count==g.n and len(switch_timing)==len(g.switches)
    assert sha(graph)==original['graph_sha256']
    np.save(output/'extra.npy',np.frombuffer(extra,dtype=np.uint32).reshape(count,2),allow_pickle=False)
    write(output/'metadata.json',dict(directions=directions,node_timings=timings,switch_timing=switch_timing,switch_types=dict(switch_types),node_types=dict(node_types)))
    r=dict(passed=True,format_version=1,parent_cache=str(parent),parent_completion_sha256=sha(parent/'completion.json'),graph_sha256=original['graph_sha256'],node_count=count,edge_count=original['edge_count'],payload_sha256={n:sha(output/n) for n in ['extra.npy','metadata.json']},source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),output/'registration.json',parent/'completion.json']},complete_build_seconds=time.monotonic()-start,native_calls=0,qualification='Exact strings and directions preserved for the reference auditor. This adapter explicitly supports the cached graph kinds without CHANZ; no silent approximation for other architectures.')
    write(output/'completion.json',r);return r

class FullRouteGraphCache:
    def __init__(self,graph,directory):
        start=time.monotonic();self.directory=Path(directory).resolve();c=read(self.directory/'completion.json')
        assert c['passed'] and c['format_version']==1
        parent=Path(c['parent_cache']);assert sha(parent/'completion.json')==c['parent_completion_sha256']
        self.g=GraphAuditCache(graph,parent);assert self.g.receipt['graph_sha256']==c['graph_sha256']
        for n,h in c['payload_sha256'].items():assert sha(self.directory/n)==h,n
        self.extra=np.load(self.directory/'extra.npy',mmap_mode='r',allow_pickle=False);assert self.extra.shape==(self.g.n,2) and self.extra.dtype==np.dtype('uint32')
        self.meta=read(self.directory/'metadata.json');assert not self.meta['node_types'].get('CHANZ',0)
        self.receipt=dict(cache_completion=str(self.directory/'completion.json'),cache_completion_sha256=sha(self.directory/'completion.json'),actual_XML_and_all_payloads_verified=True,load_and_digest_seconds=time.monotonic()-start,parent=self.g.receipt)

    def evidence(self,rr_graph,wanted_nodes,wanted_edges):
        assert Path(rr_graph).resolve()==self.g.graph,'Graph path differs from loaded immutable graph'
        wanted_nodes=set(wanted_nodes);wanted_edges=set(wanted_edges);nodes={}
        for node in wanted_nodes:
            if not 0<=node<self.g.n:continue
            a=self.g.nodes[node];direction,timing=map(int,self.extra[node])
            nodes[node]=dict(kind=KINDS[int(a[1])],low=tuple(map(int,a[2:5])),high=tuple(map(int,a[5:8])),capacity=int(a[0]),direction=self.meta['directions'][direction],timing=self.meta['node_timings'][timing].copy())
        valid=sorted(e for e in wanted_edges if 0<=e[0]<self.g.n and 0<=e[1]<self.g.n and e[2] in self.g.switches)
        keys=np.array([(u*self.g.n+v)*self.g.stride+s for u,v,s in valid],dtype=np.uint64);positions=np.searchsorted(self.g.edges,keys)
        available={edge for edge,key,pos in zip(valid,keys,positions) if pos<len(self.g.edges) and self.g.edges[pos]==key}
        return dict(path=str(self.g.graph),sha256=self.g.receipt['graph_sha256'],nodes=nodes,available_edges=available,node_types=collections.Counter(self.meta['node_types']),switch_types=collections.Counter(self.meta['switch_types']),z_fanin=collections.Counter(),z_fanout=collections.Counter(),total_edges=len(self.g.edges),switch_timing={int(k):v.copy() for k,v in self.meta['switch_timing'].items()},wanted_nodes=wanted_nodes,wanted_edges=wanted_edges)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=build(a.parent,a.output);print(dict(passed=True,seconds=r['complete_build_seconds'],nodes=r['node_count']),flush=True)
