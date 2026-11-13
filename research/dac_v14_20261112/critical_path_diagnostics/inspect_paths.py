#!/usr/bin/env python3
"""Bind existing worst-setup reports to packed atoms and placed cluster layers."""
from pathlib import Path
import xml.etree.ElementTree as ET
import re,json,sys,hashlib
D=Path(__file__).resolve().parents[1];ROOT=D.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_route import read_trace

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def report_points(text):
 points=[];started=False
 for line in text.splitlines():
  if line.startswith('Point '):started=True;continue
  if started and line.startswith('data arrival time'):break
  m=re.match(r'^(.+?)\s+\(([^)]+)\)(?:\s+\[[^]]+\])?\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$',line)
  if started and m and m[2] not in ['rise edge','fall edge']:points.append(dict(pin=m[1],model=m[2],increment_ns=float(m[3]),arrival_ns=float(m[4])))
 return points

def inspect(rd):
 rd=Path(rd);report=rd/'report_timing.setup.rpt';text=report.read_text();points=report_points(text)
 assert points and '# Unit scale: 1e-09 seconds' in text
 placed={}
 for line in (rd/'placed.place').read_text().splitlines():
  fields=line.split()
  if len(fields)==6 and fields[-1].startswith('#'):
   placed[fields[0]]=tuple(map(int,fields[1:5]))
 root=ET.parse(rd/'packed.net').getroot();pins={}
 for cluster in root.findall('block'):
  name=cluster.get('name')
  for atom in cluster.iter('block'):
   if atom.findall('block') or atom.get('name')=='open':continue
   for kind in ['inputs','outputs','clocks']:
    for port in atom.findall(kind+'/port'):
     for i,token in enumerate((port.text or '').split()):
      key=f"{atom.get('name')}.{port.get('name')}[{i}]"
      assert key not in pins,key
      pins[key]=dict(cluster=name,location=placed[name],kind=kind,token=token)
 for point in points:
  assert point['pin'] in pins,point
  point.update(pins[point['pin']])
 nets=read_trace(rd/'routed.route');by_name={v['name']:(k,v) for k,v in nets.items()}
 edges=[]
 for prev,now in zip(points,points[1:]):
  if prev['kind']!='outputs' or now['kind']!='inputs':continue
  inter=prev['cluster']!=now['cluster'];name=prev['token']
  edge=dict(source_pin=prev['pin'],sink_pin=now['pin'],net=name,delay_ns_rounded=now['increment_ns'],inter_cluster=inter,source_location=prev['location'],sink_location=now['location'],cross_layer_endpoints=prev['location'][3]!=now['location'][3])
  if inter:
   assert name in by_name,(name,edge)
   net,info=by_name[name];trace=info['trace'];nodes={n.inode:n for n in trace};parents={}
   for a,b in zip(trace,trace[1:]):
    if a.switch!=-1:
     assert b.inode not in parents or parents[b.inode]==a.inode
     parents[b.inode]=a.inode
   x,y,_,z=now['location'];matches={n.inode for n in trace if n.kind=='SINK' and n.low[0]<=x<=n.high[0] and n.low[1]<=y<=n.high[1] and n.low[2]<=z<=n.high[2]}
   paths=[]
   for sink in sorted(matches):
    child=sink;crossings=[];path=[];visited=set()
    while child in parents:
     assert child not in visited;visited.add(child);path.append(child);parent=parents[child]
     if nodes[parent].low[2]!=nodes[child].low[2]:crossings.append(parent)
     child=parent
    path.append(child)
    paths.append(dict(sink=sink,route_pins=sorted({n.pin for n in trace if n.inode==sink and n.pin is not None}),crossing_entries=crossings,path_nodes=len(path),rr_path=list(reversed(path))))
   edge.update(cluster_net=net,sink_location_matches=len(matches),sink_paths=paths,match_scope='Atom driver net name + placed sink cluster location, not an exact atom-pin-to-cluster-pin mapping')
  edges.append(edge)
 return dict(path=str(rd),status='existing_legal_route_diagnostic',source_sha256={f:sha(rd/f) for f in ['report_timing.setup.rpt','packed.net','placed.place','routed.route','manifest.json','independent_audit.json']},startpoint=re.search(r'^Startpoint:\s*(.+)$',text,re.M)[1],endpoint=re.search(r'^Endpoint\s*:\s*(.+)$',text,re.M)[1],cpd_ns=json.loads((rd/'manifest.json').read_text())['metrics']['critical_path_ns'],points=points,connections=edges,scope='Worst reported path only; increments rounded to 0.001 ns, include connection timing model overhead; endpoint changes prevent same-path causal attribution. Placement layers fixed; exact pin mapping not inferred from location alone.')

if __name__=='__main__':
 out=D/'critical_path_diagnostics';results=[]
 for rel in ['h1_dev_02/runs/spmv_F','h1_dev_02/runs/spmv_M','h2_dp_dev_01/runs/spmv_H','h2_expansion_01/runs/eltwise_layer_F','h2_expansion_01/runs/eltwise_layer_H']:
  rd=D/rel;manifest=json.loads((rd/'manifest.json').read_text());audit=json.loads((rd/'independent_audit.json').read_text());assert manifest['status']=='completed' and manifest['metrics']['native_full_check_passed'] and audit['audit']['passed']
  result=inspect(rd);results.append(result)
  (out/(rd.name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
 (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
 for r in results:
  print(r['path'],r['cpd_ns'])
  for c in r['connections']:
   if c['inter_cluster']:print(' ',c['net'],c['delay_ns_rounded'],'cross_layer_endpoints',c['cross_layer_endpoints'],'matches',c['sink_location_matches'],'crossings',[p['crossing_entries'] for p in c['sink_paths']])
