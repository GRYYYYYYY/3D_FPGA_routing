#!/usr/bin/env python3
"""Actual-XML-bound zero-RC graph cache for physical audits, never STA reuse."""
import argparse, array, resource, shutil, time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import read, write, sha
from verify_path_witnesses_v2 import graph_records, f32

KINDS = ('SOURCE','SINK','IPIN','OPIN','CHANX','CHANY')

def build(graph, output):
    start=time.monotonic();graph=Path(graph).resolve();output=Path(output).resolve()
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
    assert shutil.disk_usage(output.parent).free >= 80*1024**3
    output.mkdir(exist_ok=False)
    digest=sha(graph)
    write(output/'registration.json',dict(status='registered_before_build',graph=str(graph),graph_sha256=digest,source_sha256={str(Path(__file__).resolve()):sha(__file__)},question='Can immutable graph metadata replace repeated XML scans without changing edge, switch, capacity or physical-delay checks?',native_calls=0))
    nodes=array.array('q');edges=array.array('Q');switches={};n=0;stride=None
    assert nodes.itemsize==8 and edges.itemsize==8
    for section,e in graph_records(graph):
        a=e.attrib;t=e.find('timing');v={} if t is None else t.attrib
        if section=='switches':
            assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal'])
            sid=int(a['id']);assert sid not in switches
            switches[sid]=f32(v.get('Tdel',0));assert switches[sid]>=0
        elif section=='rr_nodes':
            assert stride is None and int(a['id'])==n
            assert all(f32(v.get(k,0))==0 for k in ['R','C'])
            loc=e.find('loc').attrib;z=int(loc.get('layer_low',loc.get('layer',0)))
            nodes.extend([int(a['capacity']),KINDS.index(a['type']),int(loc['xlow']),int(loc['ylow']),z,int(loc['xhigh']),int(loc['yhigh']),int(loc.get('layer_high',z)),int(loc['ptc'])]);n+=1
        else:
            if stride is None:
                assert n>0 and switches
                stride=max(switches)+1;assert n*n*stride < 2**64
            u,v,s=int(a['src_node']),int(a['sink_node']),int(a['switch_id'])
            assert 0<=u<n and 0<=v<n and s in switches
            edges.append((u*n+v)*stride+s)
    assert stride is not None
    node_array=np.frombuffer(nodes,dtype=np.int64).reshape(n,9)
    edge_array=np.frombuffer(edges,dtype=np.uint64);edge_array.sort()
    sw_array=np.full(stride,np.nan,dtype=np.float64)
    for s,v in switches.items():sw_array[s]=v
    np.save(output/'nodes.npy',node_array,allow_pickle=False)
    np.save(output/'edges.npy',edge_array,allow_pickle=False)
    np.save(output/'switches.npy',sw_array,allow_pickle=False)
    assert sha(graph)==digest,'Graph changed during cache construction'
    result=dict(passed=True,format_version=1,graph=str(graph),graph_sha256=digest,node_count=n,edge_count=len(edges),switch_stride=stride,kinds=list(KINDS),node_columns=['capacity','kind','xlow','ylow','zlow','xhigh','yhigh','zhigh','ptc'],zero_RC=True,physical_delay='XML switch Tdel rounded to native float32 then represented as float64; no alternative timing model',payload_sha256={name:sha(output/name) for name in ['nodes.npy','edges.npy','switches.npy']},source_sha256={str(Path(__file__).resolve()):sha(__file__),str(output/'registration.json'):sha(output/'registration.json')},complete_build_seconds=time.monotonic()-start,native_calls=0)
    write(output/'completion.json',result);return result

class GraphAuditCache:
    def __init__(self, graph, directory):
        start=time.monotonic();self.directory=Path(directory).resolve();self.graph=Path(graph).resolve()
        c=read(self.directory/'completion.json')
        assert c['passed'] and c['format_version']==1 and c['zero_RC'] and c['kinds']==list(KINDS)
        assert sha(self.graph)==c['graph_sha256'],'Actual XML graph differs from cached graph'
        for name,digest in c['payload_sha256'].items():assert sha(self.directory/name)==digest,name
        self.nodes=np.load(self.directory/'nodes.npy',mmap_mode='r',allow_pickle=False)
        self.edges=np.load(self.directory/'edges.npy',mmap_mode='r',allow_pickle=False)
        self.delays=np.load(self.directory/'switches.npy',mmap_mode='r',allow_pickle=False)
        self.n=c['node_count'];self.stride=c['switch_stride']
        assert self.nodes.shape==(self.n,9) and self.nodes.dtype==np.dtype('int64')
        assert self.edges.shape==(c['edge_count'],) and self.edges.dtype==np.dtype('uint64')
        assert self.delays.shape==(self.stride,) and self.delays.dtype==np.dtype('float64')
        self.capacities=self.nodes[:,0]
        self.switches={i:float(v) for i,v in enumerate(self.delays) if np.isfinite(v)}
        self.receipt=dict(graph_sha256=c['graph_sha256'],cache_completion=str(self.directory/'completion.json'),cache_completion_sha256=sha(self.directory/'completion.json'),payloads_verified=True,actual_XML_digest_verified=True,load_and_digest_seconds=time.monotonic()-start,qualification='Only immutable physical graph data reused. Current candidate trees, occupancy, scope and native FULL/STA still checked separately.')

    def require_edges(self, wanted):
        wanted=sorted(set(wanted))
        assert all(0<=u<self.n and 0<=v<self.n and s in self.switches for u,v,s in wanted),'Invalid edge endpoint or switch'
        keys=np.array([(u*self.n+v)*self.stride+s for u,v,s in wanted],dtype=np.uint64)
        where=np.searchsorted(self.edges,keys)
        assert np.all(where<len(self.edges)),'Missing actual RR edge'
        assert np.array_equal(self.edges[where],keys),'Missing actual RR edge/switch triple'

    def metadata(self, needed):
        assert all(0<=v<self.n for v in needed),'Invalid node'
        result={}
        for v in needed:
            a=self.nodes[v]
            result[v]=dict(kind=KINDS[int(a[1])],low=tuple(map(int,a[2:5])),high=tuple(map(int,a[5:8])),ptc=int(a[8]))
        return result

    def require_occupancy(self, occupancy):
        assert all(0<=node<self.n and 0<=count<=self.capacities[node] for node,count in occupancy.items()),'RR capacity exceeded'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--graph',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=build(a.graph,a.output);print({k:r[k] for k in ['node_count','edge_count','complete_build_seconds']},flush=True)
