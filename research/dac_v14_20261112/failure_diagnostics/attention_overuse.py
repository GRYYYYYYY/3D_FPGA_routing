#!/usr/bin/env python3
"""Describe residual occupancy in failed final traces; never certify legality or STA."""
from pathlib import Path
import sys,json,csv,collections,hashlib
D=Path(__file__).resolve().parents[1];ROOT=D.parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(D)]
from check_route import read_trace
from compare_lazagna_graphs import records
from routing_log_metrics import last_iteration
B=D/'feedback_expansion_01';data={};needed=set();graph=None
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for arm in ['F','U']:
 rd=B/'runs'/f'attention_layer_{arm}';m=json.loads((rd/'manifest.json').read_text());assert m['status']=='failed'
 g=Path(m['command'][m['command'].index('--read_rr_graph')+1]);assert graph is None or graph==g;graph=g
 traces=read_trace(rd/'routed.route');counts=collections.Counter();nodes={};groups={};guided={};cross=set();recommended_cross=set()
 for row in csv.DictReader((rd/'h3d_final_guides.csv').open()):guided.setdefault(int(row['net']),set()).update(int(x) for x in row['preferred'].split(';') if x)
 for net,info in traces.items():
  trace=info['trace']
  if not trace:continue
  counts.update({n.inode for n in trace});nodes.update({n.inode:n for n in trace})
  groups[net]='remote_endpoint_net' if any(n.kind=='SINK' and n.low[2]!=trace[0].low[2] for n in trace) else 'entirely_same_layer_endpoints'
  for a,b in zip(trace,trace[1:]):
   if a.switch!=-1 and a.low[2]!=b.low[2]:
    cross.update([a.inode,b.inode])
    if a.inode in guided.get(net,set()):recommended_cross.update([a.inode,b.inode])
 needed.update(n for n,count in counts.items() if count>1)
 data[arm]=dict(rd=rd,manifest=m,traces=traces,counts=counts,nodes=nodes,groups=groups,guided=guided,cross=cross,recommended_cross=recommended_cross)
capacity={};seen_nodes=False
for section,e in records(graph):
 if section=='rr_nodes':
  seen_nodes=True;n=int(e.get('id'))
  assert int(e.get('capacity','1'))>=1, 'Single-occupancy nodes require explicit capacity handling if zero exists'
  if n in needed:capacity[n]=int(e.get('capacity','1'))
 elif seen_nodes:break
assert set(capacity)==needed
result=dict(scope='Post-hoc descriptive occupancy of saved FAILED route traces, not a FULL legality certificate, CPD result or proof of causation. Compare to last native iteration separately; local reservations/best-route serialization may differ.',graph=str(graph),graph_expected_sha256=data['F']['manifest']['shared_inputs'][str(graph)]['sha256'],arms={})
for arm,a in data.items():
 over={n:c for n,c in a['counts'].items() if c>capacity.get(n,1)};owners={n:[] for n in over}
 for net,info in a['traces'].items():
  for n in {x.inode for x in info['trace']} & over.keys():owners[n].append(net)
 rows=[]
 for n,count in over.items():
  node=a['nodes'][n];own=owners[n]
  rows.append(dict(rr=n,kind=node.kind,low=node.low,high=node.high,occupancy=count,capacity=capacity[n],owners=own,owner_groups=dict(collections.Counter(a['groups'][net] for net in own)),guided_owners=sum(net in a['guided'] for net in own),actual_crossing_endpoint=n in a['cross'],recommended_actual_crossing_endpoint=n in a['recommended_cross']))
 native=last_iteration((a['rd']/'stdout.log').read_text().splitlines())
 result['arms'][arm]=dict(native_last_iteration=native,trace_overused_nodes=len(over),trace_excess=sum(c-capacity[n] for n,c in over.items()),same_count_as_native=len(over)==native['overused_rr_nodes'],node_kinds=dict(collections.Counter(x['kind'] for x in rows)),layer_counts=dict(collections.Counter(x['low'][2] for x in rows)),overused_actual_crossing_endpoints=sum(x['actual_crossing_endpoint'] for x in rows),overused_recommended_actual_crossing_endpoints=sum(x['recommended_actual_crossing_endpoint'] for x in rows),nodes_with_guided_owner=sum(x['guided_owners']>0 for x in rows),nodes_all_owners_same_layer_endpoints=sum(set(x['owner_groups'])=={'entirely_same_layer_endpoints'} for x in rows),rows=rows,input_sha256={str(a['rd']/f):sha(a['rd']/f) for f in ['manifest.json','routed.route','h3d_final_guides.csv','stdout.log']})
result['capacity_minimum_one_checked']=True
result['script_sha256']=sha(Path(__file__))
result['shared_overused_rr']=len({x['rr'] for x in result['arms']['F']['rows']} & {x['rr'] for x in result['arms']['U']['rows']})
(D/'failure_diagnostics/attention_overuse.json').write_text(json.dumps(result,indent=2)+'\n')
for arm,x in result['arms'].items():print(arm,{k:v for k,v in x.items() if k not in ['rows','input_sha256']})
print('shared_overused_rr',result['shared_overused_rr'])
