#!/usr/bin/env python3
"""Classify descendants of audited failed-route overuse; no native route or legality promotion."""
from pathlib import Path
import collections,csv,hashlib,json,sys
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'scripts'));import check_route as cr
B=D/'failed_attention_diagnostic_01';assert json.loads((B/'input_seal.json').read_text())['passed'];reg=json.loads((B/'registration.json').read_text());rd=Path(reg['source']);raw=json.loads((B/'analysis.json').read_text());assert raw['native_status']=='failed'
paths=[rd/'routed.route',rd/'h3d_final_guides.csv',B/'analysis.json',Path(__file__)];bindings={str(p):cr.sha256(p) for p in paths}
traces=cr.read_trace(rd/'routed.route');guides={(int(r['net']),int(r['pin'])):r for r in csv.DictReader((rd/'h3d_final_guides.csv').open())};guided_nets={n for n,p in guides};affected=collections.defaultdict(list)
for r in raw['overused']:
 for net in r['nets']:affected[net].append(r['node'])
rows=[];connections=set();guided_connections=set();remote_connections=set();root_layers=collections.Counter()
for net,resources in affected.items():
 trace=traces[net]['trace'];source=trace[0];root_layers[source.low[2]]+=1;children=collections.defaultdict(set);sinks={}
 for n in trace:
  if n.kind=='SINK':sinks[n.inode]=(n.pin,n.low[2])
 for a,b in zip(trace,trace[1:]):
  if a.switch!=-1:children[a.inode].add(b.inode)
 for resource in resources:
  todo=[resource];seen=set();desc=[]
  while todo:
   u=todo.pop()
   if u in seen:continue
   seen.add(u)
   if u in sinks:
    pin,layer=sinks[u];key=(net,pin);remote=layer!=source.low[2];guided=key in guides;connections.add(key)
    if guided:guided_connections.add(key)
    if remote:remote_connections.add(key)
    desc.append(dict(pin=pin,sink=u,remote=remote,guided=guided))
   todo.extend(children[u])
  rows.append(dict(net=net,overused_node=resource,source_layer=source.low[2],net_has_any_final_guide=net in guided_nets,descendant_connections=len(desc),remote_descendants=sum(r['remote'] for r in desc),guided_descendants=sum(r['guided'] for r in desc),connections=desc))
summary=dict(affected_nets=len(affected),affected_nets_with_any_final_guide=len(set(affected)&guided_nets),net_resource_events=len(rows),distinct_affected_connections=len(connections),distinct_remote_connections=len(remote_connections),distinct_same_layer_connections=len(connections-remote_connections),distinct_guided_connections=len(guided_connections),source_layers=dict(root_layers),events_with_guided_descendants=sum(r['guided_descendants']>0 for r in rows),events_with_remote_descendants=sum(r['remote_descendants']>0 for r in rows))
checks={p:cr.sha256(p)==h for p,h in bindings.items()};assert all(checks.values());out=dict(passed=True,scope='Descendants in the saved failed route tree, using its terminal pin labels and finalguide CSV. Sets deduplicate connections; net/resource rows are repeated events. No statement of timing criticality for unguided connections, causal failure attribution, or netlist endpoint certification.',summary=summary,rows=rows,input_sha256=bindings,input_seal=checks)
(B/'path_classification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(summary,indent=2))
