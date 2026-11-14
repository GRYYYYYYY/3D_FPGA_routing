#!/usr/bin/env python3
"""Stream an independently bound actual RRG into the frozen query format."""
import argparse,resource,shutil,signal,struct,time
from pathlib import Path
from retained_prefix_workflow import read,write,sha
from verify_path_witnesses_v2 import graph_records,f32

p=argparse.ArgumentParser();p.add_argument('--graph',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
graph=a.graph.resolve();out=a.output.resolve();assert shutil.disk_usage(out.parent).free>=80*1024**3;out.mkdir(exist_ok=False);start=time.monotonic();digest=sha(graph)
write(out/'registration.json',dict(status='registered_before_export',graph=str(graph),graph_sha256=digest,source_sha256={str(Path(__file__).resolve()):sha(__file__)},question='Bind the current circuit actual zeroRC RRG to the frozen exact-query representation; never reuse another architecture by filename.',native_calls=0,limits=dict(timeout_seconds=1800,memory_bytes=24*1024**3)))
switches={};nodes=0;edges=0;span_sum=0;span_count=0
with (out/'graph.bin').open('wb') as f:
 f.write(b'H3DRQ001'+struct.pack('<IQdd',0,0,0.,0.))
 for section,e in graph_records(graph):
  at=e.attrib;t=e.find('timing');timing={} if t is None else t.attrib
  if section=='switches':
   assert all(f32(timing.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal']);switches[int(at['id'])]=f32(timing.get('Tdel',0));assert switches[int(at['id'])]>=0
  elif section=='rr_nodes':
   assert int(at['id'])==nodes and all(f32(timing.get(k,0))==0 for k in ['R','C'])
   loc=e.find('loc').attrib;z=int(loc.get('layer_low',loc.get('layer',0)));assert z==int(loc.get('layer_high',loc.get('layer',0)))
   x,y,xh,yh=[int(loc[k]) for k in ['xlow','ylow','xhigh','yhigh']];dec=at.get('direction')=='DEC_DIR';f.write(struct.pack('<iiiii',x,y,xh if dec else x,yh if dec else y,z));nodes+=1
   if at['type'] in ['CHANX','CHANY'] and at.get('direction')!='NONE':span_sum+=xh-x+yh-y+1;span_count+=1
  else:
   u,v,sw=int(at['src_node']),int(at['sink_node']),int(at['switch_id']);assert 0<=u<nodes and 0<=v<nodes
   f.write(struct.pack('<IId',u,v,switches[sw]));edges+=1
 unit=sum(v for v in switches.values() if v>0)/sum(v>0 for v in switches.values());span=span_sum/span_count
 f.seek(8);f.write(struct.pack('<IQdd',nodes,edges,unit,span))
assert sha(graph)==digest
r=dict(passed=True,source_rrg_sha256=digest,binary_graph_sha256=sha(out/'graph.bin'),nodes=nodes,edges=edges,unit=unit,mean_span=span,
 export_seconds=time.monotonic()-start,format='H3DRQ001, little endian; same exact node drive coordinates and native float32 switch delays as frozen exporter; all node/switch RC zero checked.',
 source_sha256={str(Path(__file__).resolve()):sha(__file__),str(out/'registration.json'):sha(out/'registration.json')},native_calls=0)
write(out/'graph_binding.json',r);write(out/'completion.json',r);print(dict(nodes=nodes,edges=edges,seconds=r['export_seconds']),flush=True)
