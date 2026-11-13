from pathlib import Path
import sys,json,struct,math
D=Path(__file__).resolve().parent;ROOT=D.parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from compare_lazagna_graphs import records
from check_route import read_trace,sha256
ref=json.loads((D.parent/'h1_dev_02/spmv_references.json').read_text())['R1'];rd=Path(ref['path']);m=json.loads((rd/'manifest.json').read_text());graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
assert sha256(graph)==m['shared_inputs'][str(graph)]['sha256']
out=D/'rrg_spmv';out.mkdir(exist_ok=False)
switches={};nodes=edges=0
with (out/'layers.bin').open('wb') as nf,(out/'edges.bin').open('wb') as ef:
 for section,e in records(graph):
  a=e.attrib
  if section=='switches':
   t=e.find('timing').attrib
   assert all(float(t.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal'])
   delay=float(t.get('Tdel',0));assert math.isfinite(delay) and delay>=0;switches[int(a['id'])]=delay
  elif section=='rr_nodes':
   assert int(a['id'])==nodes
   t=e.find('timing').attrib;assert float(t.get('R',0))==float(t.get('C',0))==0
   loc=e.find('loc').attrib;layer=int(loc.get('layer_low',loc.get('layer','0')));assert int(loc.get('layer_high',layer))==layer
   nf.write(struct.pack('<i',layer));nodes+=1
  elif section=='rr_edges':
   ef.write(struct.pack('<IIf',int(a['src_node']),int(a['sink_node']),switches[int(a['switch_id'])]));edges+=1
queries=[]
for net,info in sorted(read_trace(rd/'routed.route').items()):
 trace=info['trace'];parent={};meta={n.inode:n for n in trace}
 for a,b in zip(trace,trace[1:]):
  if a.switch!=-1:parent[b.inode]=a.inode
 for end in trace:
  if end.kind!='SINK' or end.pin is None:continue
  child=end.inode;cross=[]
  while child in parent:
   src=parent[child]
   if meta[src].low[2]!=meta[child].low[2]:cross.append(src)
   child=src
  if cross:
   queries.extend([(child,0,cross[0]),(end.inode,1,cross[0])])
   if len(queries)>=16:break
 if len(queries)>=16:break
(out/'queries.txt').write_text(''.join(f'{a} {b} {c}\n' for a,b,c in queries))
(out/'binding.json').write_text(json.dumps({'graph':str(graph),'graph_sha256':sha256(graph),'route':str(rd/'routed.route'),'route_sha256':sha256(rd/'routed.route'),'nodes':nodes,'edges':edges,'queries':queries,'selection':'First eight cross-layer pin records in ascending net order, both directions. No outcome-based selection.','format':'little-endian int32 layers; uint32 source,uint32 sink,float32 switch delay edges; no physical graph modification','export_sha256':{p.name:sha256(p) for p in out.iterdir() if p.is_file()}},indent=2)+'\n')
print(nodes,edges,len(queries),flush=True)
