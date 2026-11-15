#!/usr/bin/env python3
"""Independent cached variant of frozen audit_native_objective.py; same scope checks."""
import argparse,array,collections,math,re,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,nodes,prune_sinks,prefixes,serialize
from immutable_rr_audit_cache import GraphAuditCache
from check_route import read_trace
p=argparse.ArgumentParser();p.add_argument('--batch',type=Path,required=True);p.add_argument('--role',required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
start=time.monotonic();b=a.batch.resolve();role=a.role;reg=read(b/'registration.json')['roles'][role]
assert all(sha(p)==h for p,h in reg['source_sha256'].items())
state=b/role;assert read(state/'completion.json')['passed'];source=Path(reg['source']);rd=Path(read(state/'completion.json')['run'])
assert all(sha(source/n)==sha(rd/n) for n in ['routed.route','packed.net','placed.place'])
out=a.output.resolve();out.mkdir(exist_ok=False);lines=(rd/'joint_native.log').read_text().splitlines();last=lines[-1].split();assert last[0]=='COMPLETE' and last[-1]=='occupancy_restored'
kept=collections.defaultdict(set);raw=collections.defaultdict(list);queries=[];attempts=[]
for line in lines[:-1]:
 v=line.split()
 if v[0]=='KEEP':kept[int(v[1])].add(int(v[2]))
 elif v[0]=='NODE':raw[int(v[1])].append((int(v[2]),int(v[3]),int(v[4]),int(v[5]),float(v[6])))
 elif v[0]=='QUERY':queries.append(dict(net=int(v[1]),pin=int(v[2]),feasible=bool(int(v[3])),criticality=float(v[4]),pushes=int(v[5]),pops=int(v[6]),seconds=float(v[7])))
 elif v[0]=='ATTEMPT':attempts.append(dict(net=int(v[1]),pin=int(v[2]),pressure=float(v[3]),found=bool(int(v[4])),feasible=bool(int(v[5]))))
 elif v[0] in ['FAIL_TARGET','FAIL_EDGE','OCC','MODE']:pass # Diagnostic-only rows; never a complete candidate.
 else:raise AssertionError(v[0])
if not int(last[1]):
 write(out/'analysis.json',dict(passed=True,status='native_transaction_failed_no_candidate',candidate_route=None,queries=queries,attempts=attempts,rollback='Native occupancy restored; accepted input immutable.'))
 print('Transaction failed; original preserved');sys.exit(0)
assert int(last[2])==int(last[3])==len(reg['queries'])
assert [(r['net'],r['pin']) for r in queries]==[(r['net'],r['pin']) for r in reg['queries']]
m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);assert sha(graph)==m['shared_inputs'][str(graph)]['sha256']
wanted={(parent,node,sw) for rows in raw.values() for node,parent,sw,pin,d in rows if parent>=0}
needed={node for rows in raw.values() for node,*rest in rows}
cache=GraphAuditCache(graph,a.cache);cache.require_edges(wanted)
metadata=cache.metadata(needed);switches=cache.switches;caps=cache.capacities

traces=read_trace(source/'routed.route');text=(source/'routed.route').read_text();trees={};changes=[];scope=[]
for net,rows in raw.items():
 original=from_trace(traces[net]['trace'],switches);pruned=prune_sinks(original,reg['removed_pins'][str(net)])
 assert kept[net]==nodes(pruned),'Native pruning differs from matched external scope'
 roots=[node for node,parent,sw,pin,d in rows if parent<0];assert roots==[original['root']]
 tree=dict(root=roots[0],edges={node:(parent,sw,switches[sw]) for node,parent,sw,pin,d in rows if parent>=0},sinks={pin:node for node,parent,sw,pin,d in rows if pin>0})
 assert tree['sinks']==original['sinks']
 assert all(tree['edges'].get(v)==edge for v,edge in pruned['edges'].items())
 if reg['fixed_target_paths']:
  tx=Path(reg['transaction']);first=read(tx/'initial_transaction.json');reference=read(tx/'final_transaction_trees.json')
  if str(net) in first['target_reserved_nodes']:
   path=first['target_reserved_nodes'][str(net)]
   for u,v in zip(path,path[1:]):assert tree['edges'][v]==tuple(reference[str(net)]['edges'][str(v)])
 before,after=prefixes(original),prefixes(tree)
 for pin,sink in tree['sinks'].items():
  if before[sink]!=after[sink]:changes.append(dict(net=net,pin=pin,before_s=before[sink],after_s=after[sink]))
 scope.append(dict(net=net,retained_nodes=len(kept[net]),other_branch_edges_unchanged=True,terminal_set_unchanged=True))
 match=re.search(r'^Net '+str(net)+r' \(.*?\)\n.*?(?=^Net |\Z)',text,re.M|re.S);assert match
 text=text[:match.start()]+match.group(0).splitlines()[0]+'\n\n'+serialize(tree,metadata)+'\n'+text[match.end():];trees[net]=tree
assert set(raw)==set(map(int,reg['removed_pins']))
candidate=out/'candidate.route';candidate.write_text(text);parsed=read_trace(candidate)
assert parsed.keys()==traces.keys() and all(parsed[n]==traces[n] for n in traces if n not in trees)
assert all(from_trace(parsed[n]['trace'],switches)==tree for n,tree in trees.items())
occupancy=collections.Counter(node for t in parsed.values() for node in {x.inode for x in t['trace']});cache.require_occupancy(occupancy)
write(out/'analysis.json',dict(passed=True,status='complete_candidate_pending_FULL_STA',candidate_route=str(candidate),candidate_sha256=sha(candidate),scope=scope,queries=queries,attempts=attempts,changed_delays=changes,
 graph_cache=cache.receipt, native_transaction_seconds=float(last[4]),audit_and_serialization_seconds=time.monotonic()-start,
 source_sha256={str(p):sha(p) for p in [Path(__file__),b/'registration.json',state/'completion.json',rd/'joint_native.log',source/'routed.route',graph,a.cache/'completion.json',D/'immutable_rr_audit_cache.py',D/'audit_native_objective.py']},
 qualification='Same retained edges/terminals and fixed target paths when requested; all actual edges/capacities checked. Native FULL/STA still mandatory.'))
print(dict(role=role,changed_connections=len(changes),queries=len(queries),attempts=len(attempts)),flush=True)
