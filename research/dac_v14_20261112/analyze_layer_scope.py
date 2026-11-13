#!/usr/bin/env python3
"""Saved-trace detours and paired quality for identical layer-scope controls."""
from pathlib import Path
import collections, hashlib, json, sys
D=Path(__file__).resolve().parent;ROOT=D.parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(D)]
from check_route import read_trace
from routing_log_metrics import last_iteration
B=Path(sys.argv[1]);reg=json.loads((B/'registration.json').read_text());sealed=(B/'input_seal.json').exists() and json.loads((B/'input_seal.json').read_text())['passed']
result=dict(scope='Same-input all-layer search-scope diagnostic. Detours are complete saved-route net records with same-layer terminals and at least one actual inter-layer edge, deduplicated within net. Failed traces are descriptive only. Native FULL and independent audit plus input seal required for legal CPD comparison. Cross-resource accounting comes from independent audit, not raw edge counts.',sealed=sealed,circuits={})
for circuit in reg['circuits']:
 arms={};refs=json.loads((B/f'{circuit}_references.json').read_text()) if (B/f'{circuit}_references.json').exists() else {}
 locations={a:Path(v['path']) for a,v in refs.items()};locations.update({a:B/'runs'/f'{circuit}_{a}' for a in reg['arms']})
 for arm,rd in locations.items():
  if not (rd/'manifest.json').exists():arms[arm]=dict(status='missing');continue
  m=json.loads((rd/'manifest.json').read_text());status=m['status']
  if status not in ['completed','failed','timeout'] or not (rd/'routed.route').exists():arms[arm]=dict(status=status);continue
  audit=json.loads((rd/'independent_audit.json').read_text()) if (rd/'independent_audit.json').exists() else None
  if status=='completed':status='legal' if m['metrics']['native_full_check_passed'] and audit and audit['audit']['passed'] and (sealed or arm in refs) else 'completed_pending_audit_or_seal'
  traces=read_trace(rd/'routed.route');classes=collections.Counter();detours=[];cross_edges={}
  for net,info in traces.items():
   trace=info['trace']
   if not trace:continue
   same=all(n.low[2]==trace[0].low[2] for n in trace if n.kind=='SINK')
   edges={(a.inode,b.inode) for a,b in zip(trace,trace[1:]) if a.switch!=-1 and a.low[2]!=b.low[2]}
   classes['same_layer_terminal_nets' if same else 'remote_terminal_nets']+=1
   if edges:
    classes['same_layer_nets_with_detour' if same else 'remote_nets_with_crossing']+=1
    if same:detours.append(net)
   cross_edges[net]=len(edges)
  native=last_iteration((rd/'stdout.log').read_text().splitlines())
  arms[arm]=dict(status=status,metrics=m['metrics'],physical_metrics=audit['physical_metrics'] if audit else None,
     native_last_iteration=native,net_classes=dict(classes),same_layer_detour_nets=sorted(detours),
     per_net_unique_cross_edge_count=sum(cross_edges.values()),route_sha256=hashlib.sha256((rd/'routed.route').read_bytes()).hexdigest(),path=str(rd))
 result['circuits'][circuit]=arms
result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(B/'layer_scope_mechanisms.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({c:{a:{k:v for k,v in r.items() if k in ['status','net_classes','native_last_iteration']} for a,r in arms.items()} for c,arms in result['circuits'].items()},indent=2))
