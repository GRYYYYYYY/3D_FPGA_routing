#!/usr/bin/env python3
"""Trace exact native maximum-arrival predecessors of the masking input."""
import collections,json,struct
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from native_timing_echo_v2 import read_echo

obs=read(D/'timing_cone_spmv_dev_04/completion.json');state=Path(obs['roles']['plateau_on']['state']);run=Path(read(state/'completion.json')['run']);g=read_echo(run/'timing_graph.full_precision.echo')
mechanism=read(D/'spmv_timing_cone_analysis_01.json');boundary=mechanism['masking_boundaries'];assert len(boundary)==1
dominant=[p for p in boundary[0]['incoming'] if p['before_native_max_attained']];assert dominant
domain=tuple(dominant[0]['domain']);assert all(tuple(p['domain'])==domain for p in dominant)
arrivals={node:v for (typ,entity,node,l,c),v in g['tags'].items() if typ=='SETUP_DATA_ARRIVAL' and entity=='node' and (l,c)==domain}
roots={p['source_node'] for p in dominant};seen=set();todo=list(roots);selected_edges=set();unresolved=[];sources=[]
def f32(v):return struct.unpack('f',struct.pack('f',v))[0]
while todo:
 n=todo.pop()
 if n in seen:continue
 seen.add(n)
 if g['nodes'][n]['type']=='SOURCE':sources.append(n);continue
 wins=[]
 for edge in g['nodes'][n]['in_edges']:
  e=g['edges'][edge];src=e['src_node']
  if e['disabled'] or src not in arrivals or 'max_delay' not in g['delays'][edge]:continue
  if f32(arrivals[src]+g['delays'][edge]['max_delay'])==arrivals[n]:wins.append(edge)
 if not wins:unresolved.append(n)
 for edge in wins:selected_edges.add(edge);todo.append(g['edges'][edge]['src_node'])
pins=[]
for line in (run/'native_sta_frontier.jsonl').open():
 p=json.loads(line)
 if p.get('type')!='pin' or p['driver'] or p['ignored'] or p['global']:continue
 match=[a for a in p['atoms'] if a['tnode_external'] in seen]
 if match:pins.append(dict(net=p['net'],pin=p['pin'],net_name=p['net_name'],pin_name=p['pin_name'],native_net_delay_s=p['native_net_delay_s'],setup_slack_s=p['setup_slack_s'],atoms=match))
files=[Path(__file__).resolve(),D/'native_timing_echo_v2.py',D/'timing_cone_spmv_dev_04/completion.json',D/'spmv_timing_cone_analysis_01.json',run/'timing_graph.full_precision.echo',run/'native_sta_frontier.jsonl']
write(D/'spmv_dominant_arrival_cone_01.json',dict(passed=True,roots=sorted(roots),launch_capture=domain,exact_max_predecessor_nodes=sorted(seen),exact_max_predecessor_edges=sorted(selected_edges),source_boundaries=sources,unresolved_non_source_nodes=unresolved,routed_connections=pins,source_state=str(state),source_sha256={str(p):sha(p) for p in files},qualification='Current native float32 maximum-arrival predecessor cone; includes all exact winning fanins, stops at timing SOURCE nodes. Not a physical-route capacity bound, endpoint improvement guarantee or global-optimality certificate.'))
print(dict(nodes=len(seen),edges=len(selected_edges),unresolved=unresolved,connections=[(p['net'],p['pin']) for p in pins]))
