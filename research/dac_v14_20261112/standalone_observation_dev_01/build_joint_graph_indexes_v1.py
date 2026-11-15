"""Build existing audit/full/query payload formats in one actual XML traversal.

Source XML and all zero-RC/directed/geometry checks remain mandatory. Sorted
edge keys feed physical audits; query graph preserves original XML edge order.
Component elapsed time is shared, not three independently addable build costs.
"""
import argparse,array,collections,json,os,resource,shutil,signal,struct,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import read,write,sha
from verify_path_witnesses_v2 import graph_records,f32
from immutable_rr_audit_cache import KINDS
from seed_census_analysis_pool_v2 import process_identity


def build(graph, output):
    started=time.monotonic();graph=Path(graph).resolve();output=Path(output).resolve()
    resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
    assert not output.exists() and shutil.disk_usage(output.parent).free>=80*1024**3
    output.mkdir();audit=output/'audit_cache';full=output/'full_cache';query=output/'query_graph'
    for path in [audit,full,query]:path.mkdir()
    digest=sha(graph)
    write(output/'registration.json',dict(status='registered_before_joint_generation',pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
        graph=str(graph),graph_sha256=digest,native_calls_new=0,source_sha256={str(Path(__file__).resolve()):sha(__file__)},
        limits=dict(timeout_seconds=1800,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3)))
    nodes=array.array('q');edges=array.array('Q');extra=array.array('I');assert nodes.itemsize==edges.itemsize==8 and extra.itemsize==4
    switches={};switch_timing={};switch_types=collections.Counter();node_types=collections.Counter()
    directions=[];timings=[];direction_ids={};timing_ids={};n=0;edge_count=0;stride=None;span_sum=span_count=0
    with (query/'graph.bin').open('wb') as binary:
        binary.write(b'H3DRQ001'+struct.pack('<IQdd',0,0,0.,0.))
        for section,e in graph_records(graph):
            a=e.attrib;t=e.find('timing');timing={} if t is None else dict(t.attrib)
            if section=='switches':
                assert all(f32(timing.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal'])
                sid=int(a['id']);assert sid not in switches
                switches[sid]=f32(timing.get('Tdel',0));assert switches[sid]>=0
                switch_timing[sid]=timing;switch_types[a.get('type','unknown')]+=1
            elif section=='rr_nodes':
                assert stride is None and int(a['id'])==n and all(f32(timing.get(k,0))==0 for k in ['R','C'])
                kind=a['type'];assert kind in KINDS and kind!='CHANZ'
                loc=e.find('loc').attrib
                x,y,xh,yh=[int(loc[k]) for k in ['xlow','ylow','xhigh','yhigh']]
                z=int(loc.get('layer_low',loc.get('layer','0')));zh=int(loc.get('layer_high',loc.get('layer','0')))
                assert z==zh,'Frozen query format requires single-layer nodes'
                nodes.extend([int(a['capacity']),KINDS.index(kind),x,y,z,xh,yh,zh,int(loc['ptc'])])
                direction=a.get('direction','NONE');token=json.dumps(timing,sort_keys=True)
                if direction not in direction_ids:direction_ids[direction]=len(directions);directions.append(direction)
                if token not in timing_ids:timing_ids[token]=len(timings);timings.append(timing)
                extra.extend([direction_ids[direction],timing_ids[token]]);node_types[kind]+=1
                dec=direction=='DEC_DIR';binary.write(struct.pack('<iiiii',x,y,xh if dec else x,yh if dec else y,z));n+=1
                if kind in ['CHANX','CHANY'] and direction!='NONE':span_sum+=xh-x+yh-y+1;span_count+=1
                if n%1000000==0:write(output/'progress.json',dict(phase='rr_nodes',nodes=n,edges=edge_count))
            else:
                assert section=='rr_edges'
                if stride is None:
                    assert n>0 and switches;stride=max(switches)+1;assert n*n*stride<2**64
                u,v,s=int(a['src_node']),int(a['sink_node']),int(a['switch_id'])
                assert 0<=u<n and 0<=v<n and s in switches
                edges.append((u*n+v)*stride+s)
                binary.write(struct.pack('<IId',u,v,switches[s]));edge_count+=1
                if edge_count%5000000==0:write(output/'progress.json',dict(phase='rr_edges',nodes=n,edges=edge_count))
        assert stride and n and edge_count and span_count
        positives=[v for v in switches.values() if v>0];assert positives
        unit=sum(positives)/len(positives);span=span_sum/span_count
        binary.seek(8);binary.write(struct.pack('<IQdd',n,edge_count,unit,span))
    assert sha(graph)==digest,'Actual XML changed while generating indexes'
    node_array=np.frombuffer(nodes,dtype=np.int64).reshape(n,9)
    edge_array=np.frombuffer(edges,dtype=np.uint64);edge_array.sort()
    switch_array=np.full(stride,np.nan,dtype=np.float64)
    for switch,delay in switches.items():switch_array[switch]=delay
    np.save(audit/'nodes.npy',node_array,allow_pickle=False)
    np.save(audit/'edges.npy',edge_array,allow_pickle=False)
    np.save(audit/'switches.npy',switch_array,allow_pickle=False)
    np.save(full/'extra.npy',np.frombuffer(extra,dtype=np.uint32).reshape(n,2),allow_pickle=False)
    write(full/'metadata.json',dict(directions=directions,node_timings=timings,switch_timing=switch_timing,
        switch_types=dict(switch_types),node_types=dict(node_types)))
    files=[Path(__file__).resolve(),Path(__file__).resolve().with_name('verify_path_witnesses_v2.py'),
           Path(__file__).resolve().with_name('immutable_rr_audit_cache.py'),output/'registration.json']
    hashes={str(path):sha(path) for path in files}
    common=dict(passed=True,format_version=1,native_calls=0,shared_build_receipt=str(output/'completion.json'),
        complete_build_seconds=None,build_cost_scope='one_shared_XML_generation_not_additive')
    ac=dict(common,graph=str(graph),graph_sha256=digest,node_count=n,edge_count=edge_count,switch_stride=stride,kinds=list(KINDS),
        node_columns=['capacity','kind','xlow','ylow','zlow','xhigh','yhigh','zhigh','ptc'],zero_RC=True,
        physical_delay='XML switch Tdel rounded to native float32 then represented as float64; no alternative timing model',
        payload_sha256={name:sha(audit/name) for name in ['nodes.npy','edges.npy','switches.npy']},source_sha256=hashes)
    write(audit/'completion.json',ac)
    fc=dict(common,parent_cache=str(audit),parent_completion_sha256=sha(audit/'completion.json'),graph_sha256=digest,node_count=n,edge_count=edge_count,
        payload_sha256={name:sha(full/name) for name in ['extra.npy','metadata.json']},
        source_sha256=dict(hashes,**{str(audit/'completion.json'):sha(audit/'completion.json')}),
        qualification='Exact raw timing strings/direction catalogs and kinds preserved in original encounter order. Actual XML scanned jointly with audit/query outputs, not supplied reusable state.')
    write(full/'completion.json',fc)
    qc=dict(common,source_rrg_sha256=digest,binary_graph_sha256=sha(query/'graph.bin'),nodes=n,edges=edge_count,unit=unit,mean_span=span,
        export_seconds=None,format='H3DRQ001, little endian; exact original node drive coordinates/native float32 switch delays; original XML edge order; zero node/switch RC.',source_sha256=hashes)
    write(query/'graph_binding.json',qc);write(query/'completion.json',qc)
    artifact_names=['audit_cache/nodes.npy','audit_cache/edges.npy','audit_cache/switches.npy','audit_cache/completion.json',
        'full_cache/extra.npy','full_cache/metadata.json','full_cache/completion.json','query_graph/graph.bin','query_graph/graph_binding.json','query_graph/completion.json']
    receipt=dict(passed=True,native_calls_new=0,graph=str(graph),graph_sha256=digest,nodes=n,edges=edge_count,
        XML_traversals=1,shared_complete_build_seconds=time.monotonic()-started,
        process_CPU_seconds=time.process_time(),process_RSS_high_water_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        source_sha256=hashes,artifact_sha256={name:sha(output/name) for name in artifact_names},
        qualification='Three existing payload formats produced in one actual XML traversal; original query edge order preserved separately from sorted audit keys. All graph loads/hash checks/generation/write work belongs to this shared elapsed time, not separate component costs. Data contains only immutable graph topology/geometry/timing, no route/candidate/query history. Byte equality and actual full-flow equivalence require independent validation. Existing frozen builds/inputs/experiments unchanged; no native call, new route quality, whole algorithm speedup or statistical timing claim.')
    # Include final payload hashing in the measured shared component interval.
    receipt['shared_complete_build_seconds']=time.monotonic()-started
    write(output/'completion.json',receipt);signal.alarm(0)
    print({key:receipt[key] for key in ['passed','nodes','edges','XML_traversals','shared_complete_build_seconds','process_RSS_high_water_kib']},flush=True)
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--graph',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build(a.graph,a.output)
