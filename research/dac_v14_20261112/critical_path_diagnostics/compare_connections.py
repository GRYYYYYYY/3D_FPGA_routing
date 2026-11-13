#!/usr/bin/env python3
"""Compare identical critical-path net/cluster connections in already legal routes."""
from pathlib import Path
import json,sys,struct,csv
from inspect_paths import D,ROOT,sha
sys.path.insert(0,str(ROOT/'scripts'))
from check_route import read_trace
from compare_lazagna_graphs import records

def extract(info,location):
 trace=info['trace'];nodes={n.inode:n for n in trace};parents={};switches={}
 for a,b in zip(trace,trace[1:]):
  if a.switch!=-1:
   assert b.inode not in parents or parents[b.inode]==a.inode
   parents[b.inode]=a.inode;switches[a.inode,b.inode]=a.switch
 x,y,_,z=location;sinks={n.inode for n in trace if n.kind=='SINK' and n.low[0]<=x<=n.high[0] and n.low[1]<=y<=n.high[1] and n.low[2]<=z<=n.high[2]}
 paths=[]
 for sink in sorted(sinks):
  child=sink;path=[];sw=[];crossings=[]
  while child in parents:
   assert child not in path;path.append(child);parent=parents[child];sw.append(switches[parent,child])
   if nodes[parent].low[2]!=nodes[child].low[2]:crossings.append(parent)
   child=parent
  path.append(child);paths.append(dict(sink=sink,nodes=path,switches=sw,crossings=crossings))
 return paths

def main():
 out=D/'critical_path_diagnostics';reports=json.loads((out/'summary.json').read_text());groups={}
 for r in reports:
  circuit=Path(r['path']).name.rsplit('_',1)[0];groups.setdefault(circuit,[]).append(r)
 rows=[];needed=set();graphs=set();sources={}
 for circuit,runs in groups.items():
  connections={}
  for r in runs:
   for c in r['connections']:
    if c['inter_cluster']:connections[c['net'],tuple(c['sink_location'])]=c
  hashes=[{f:sha(Path(r['path'])/f) for f in ['packed.net','placed.place']} for r in runs]
  assert all(x==hashes[0] for x in hashes),hashes
  for r in runs:
   rd=Path(r['path']);m=json.loads((rd/'manifest.json').read_text());graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);graphs.add(graph)
   sources[str(rd)]=dict(report=sha(rd/'report_timing.setup.rpt'),route=sha(rd/'routed.route'),manifest=sha(rd/'manifest.json'))
   by_name={v['name']:v for v in read_trace(rd/'routed.route').values()}
   for (net,location),connection in connections.items():
    assert net in by_name
    paths=extract(by_name[net],location);assert len(paths)==1,(net,location,len(paths))
    p=paths[0];needed.update(p['nodes'])
    rows.append(dict(circuit=circuit,arm=rd.name.rsplit('_',1)[1],net=net,sink_pin_report=connection['sink_pin'],sink_location=location,sink_rr=p['sink'],rr_nodes=len(p['nodes']),crossings=p['crossings'],switches=p['switches'],route_source=str(rd)))
 assert len(graphs)==1,graphs
 graph=next(iter(graphs));switch_delays={};verified=set()
 for section,e in records(graph):
  if section=='switches':
   t=e.find('timing').attrib
   assert all(float(t.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal'])
   switch_delays[int(e.attrib['id'])]=struct.unpack('<f',struct.pack('<f',float(t.get('Tdel',0))))[0]
  elif section=='rr_nodes' and int(e.attrib['id']) in needed:
   t=e.find('timing').attrib;assert float(t.get('R',0))==float(t.get('C',0))==0;verified.add(int(e.attrib['id']))
  elif section=='rr_edges':break
 assert verified==needed
 for row in rows:row['physical_switch_delay_ns']=sum(switch_delays[s] for s in row['switches'])*1e9
 result=dict(rows=rows,graph=str(graph),graph_sha256=sha(graph),verified_zero_rc_path_nodes=len(needed),sources=sources,scope='One unique RR SINK at each named atom-net/placed-cluster location. Physical RR switch-delay sums under verified zero RC, not complete atom-to-atom STA delay; no causality inferred from changed routing. Only union of reported worst-path inter-cluster connections; not all connections.')
 (out/'connection_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
 with (out/'connection_comparison.csv').open('w') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 for row in rows:print(row['circuit'],row['arm'],row['net'],row['sink_pin_report'],round(row['physical_switch_delay_ns'],6),len(row['crossings']))
if __name__=='__main__':main()
