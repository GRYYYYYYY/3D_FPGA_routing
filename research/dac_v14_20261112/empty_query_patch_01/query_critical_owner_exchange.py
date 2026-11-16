from timing_runtime import query_driver,query_validation,runtime_files
from controller_runtime import package_files
#!/usr/bin/env python3
"""Diagnose a current critical-owner exchange under a fixed target witness.

No native route is replaced. Actual owner branches are pruned in private model
copies, a previously audited target witness is installed, and critical owners
are queried independently under current-capacity and protected-only occupancy.
Their bounds ignore future owner competition; only full native transactions can
establish legal final quality. The zero-RC adapter is required explicitly.
"""
import argparse,collections,copy,json,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from immutable_rr_audit_cache import GraphAuditCache,KINDS
from coordinated_repair_tree import from_trace,nodes,prune_sinks,prefixes,attach,downstream_pins
from run_native_frontier_queries import write_cases
from critical_action_patterns import patterns
from check_route import read_trace
p=argparse.ArgumentParser()
for n in ['feedback','output','audit-cache','query-graph']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
f=a.feedback.resolve();b=a.output.resolve();b.mkdir(exist_ok=False);assert shutil.disk_usage(D).free>=80*1024**3
op=read(f/'owners/completion.json');cone=read(f/'cone.json');capacity=read(f/'capacity/analysis.json');relaxed=read(f/'relaxed/analysis.json')
for x in [op,cone,capacity,relaxed]:assert x['passed'] and all(sha(p)==h for p,h in x['source_sha256'].items())
state=Path(op['input_state']);assert Path(cone['source_state'])==state
source=Path(read(state/'completion.json')['run']);assert Path(read(f/'capacity/execution_registration.json')['input_run'])==source
# The exact original exchange predicate can be evaluated before graph loading.
protected={r['net'] for r in cone['routed_connections']}
selected=[r for r in op['rows'] if r['capacity_gap_ns']>0 and any(o['net'] in protected for o in r['owner_release_scope'])]
if not selected:
 binding_path=a.query_graph/'graph_binding.json';cache_path=a.audit_cache/'completion.json'
 binding=read(binding_path);cache_proof=read(cache_path);source_manifest=read(source/'manifest.json')
 source_graph=source_manifest['command'][source_manifest['command'].index('--read_rr_graph')+1]
 assert binding['passed'] and cache_proof['passed'] and binding['source_rrg_sha256']==cache_proof['graph_sha256']==source_manifest['shared_inputs'][source_graph]['sha256'],'Empty-menu graph argument identity mismatch'
 driver=query_driver('capacity');assert driver.is_file()
 files=[Path(__file__).resolve(),f/'owners/completion.json',f/'cone.json',f/'capacity/analysis.json',f/'relaxed/analysis.json',source/'manifest.json',state/'completion.json',*package_files(),*runtime_files()]
 files += [binding_path,cache_path,driver]
 bound={str(p):sha(p) for p in files}
 write(b/'registration.json',dict(status='registered_empty_exchange_target_set',input_state=str(state),input_run=str(source),targets=[],protected_current_cone_nets=sorted(protected),source_sha256=bound,native_calls=0,empty_menu_certificate='No positive capacity-gap target has a current critical owner, under the original predicate.'))
 write(b/'completion.json',dict(passed=True,rows=[],native_calls=0,source_sha256=bound,query_subprocess_executed=False,graph_mapping_executed=False,complete_process_seconds=time.monotonic()-started,qualification='No current target with a critical-owner conflict; original source/proof/state checks passed. Empty menu omitted graph mapping, not a global search or final candidate. No imputed query cost or quality.'))
 raise SystemExit(0)
m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);g=GraphAuditCache(graph,a.audit_cache)
binary=a.query_graph.resolve()/'graph.bin';binding=read(binary.with_name('graph_binding.json'));assert sha(binary)==binding['binary_graph_sha256'] and g.receipt['graph_sha256']==binding['source_rrg_sha256']
driver=query_driver('capacity');assert driver.is_file() # query_driver verified explicit binary hash
protected={r['net'] for r in cone['routed_connections']};routed={(r['net'],r['pin']):r for r in cone['routed_connections']}
selected=[r for r in op['rows'] if r['capacity_gap_ns']>0 and any(o['net'] in protected for o in r['owner_release_scope'])]
files=[Path(__file__).resolve(),D/'critical_action_patterns.py',D/'coordinated_repair_tree.py',D/'run_native_frontier_queries.py',f/'owners/completion.json',f/'cone.json',f/'capacity/analysis.json',f/'relaxed/analysis.json',f/'capacity/cases.json',f/'capacity/occupancy_owners.json',source/'routed.route',state/'endpoint_vector.json',source/'manifest.json',a.audit_cache.resolve()/'completion.json',binary,binary.with_name('graph_binding.json'),driver]
files += [*package_files(),*runtime_files()]
bound={str(p):sha(p) for p in files}
write(b/'registration.json',dict(status='registered_before_diagnostic_query',input_state=str(state),input_run=str(source),targets=[r['target'] for r in selected],protected_current_cone_nets=sorted(protected),source_sha256=bound,native_calls=0,
 question='Does a locally shorter target path leave a sufficiently short replacement for its current critical owners, or does the owner detour cancel the gain even with noncritical occupancy relaxed?',
 limits=dict(child_query_seconds=900,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3),
 qualification='Fixed-target conditional zero-RC model only. Actual closure pins are derived from descendant owner branches, never a net-ID whitelist. Partial pruned trees are not legal final states. No final acceptance or CPD claim.'))
if not selected:
 write(b/'completion.json',dict(passed=True,rows=[],native_calls=0,source_sha256=bound,qualification='No current target with a critical-owner conflict; operator-local outcome, not research completion.'));raise SystemExit(0)
traces=read_trace(source/'routed.route');owners={int(n):set(ns) for n,ns in read(f/'capacity/occupancy_owners.json').items()};base_cases={(c['net'],c['pin']):c for c in read(f/'capacity/cases.json')};zero=set(map(int,np.flatnonzero(g.capacities==0)));rows=[];costs=[]

def query_case(net,pin,tree,original,counts):
 retained=nodes(tree);prefix=prefixes(tree);sink=original['sinks'][pin]
 blocked=zero|{n for n,count in counts.items() if count-int(n in retained)>=g.capacities[n]}
 # Counts always include this net's retained tree exactly once.
 assert not retained&blocked and sink not in retained
 return dict(net=net,pin=pin,sink=sink,retained=sorted(retained),anchors={str(n):prefix[n] for n in sorted(retained) if KINDS[int(g.nodes[n,1])] not in ['IPIN','SINK']},blocked=sorted(blocked))

def solve(cases,directory):
 directory.mkdir();write(directory/'cases.json',cases);write_cases(directory/'cases.txt',cases);t=time.monotonic()
 with (directory/'stdout.log').open('w') as out,(directory/'stderr.log').open('w') as err:
  result=subprocess.run([str(driver),str(binary),str(directory/'cases.txt'),'capacity'],stdout=out,stderr=err,timeout=900)
 elapsed=time.monotonic()-t;assert result.returncode==0;costs.append(dict(directory=str(directory),queries=len(cases),complete_query_process_seconds=elapsed))
 answers={};paths=collections.defaultdict(list)
 for line in (directory/'stdout.log').open():
  v=line.split();key=int(v[1]),int(v[2]);assert int(v[3])==1
  if v[0]=='RESULT':answers[key]=dict(stop=int(v[4]),distance_s=float(v[8]),lower_s=float(v[9]),expansions=int(v[5]),query_seconds=float(v[10]))
  else:assert v[0]=='EDGE' and int(v[4])==len(paths[key]);paths[key].append((int(v[5]),int(v[6]),float(v[7])))
 audited=[]
 for c in cases:
  key=c['net'],c['pin'];r=answers[key];edges=paths[key]
  if r['stop']==2:
   assert r['distance_s']==-1 and not edges;audited.append(dict(net=key[0],pin=key[1],status='unreachable_in_this_conditional_model',**r));continue
  assert r['stop']==0 and r['distance_s']==r['lower_s']
  assert edges[0][0]==c['sink'] and edges[-1][1]==g.n and all(x[1]==z[0] for x,z in zip(edges,edges[1:])) and len({x[0] for x in edges})==len(edges)
  assert not {x[0] for x in edges[:-1]}&set(c['retained']) and not {x[0] for x in edges}&set(c['blocked'])
  assert str(edges[-1][0]) in c['anchors'] and edges[-1][2]==c['anchors'][str(edges[-1][0])]
  assert abs(sum(x[2] for x in edges)-r['distance_s'])<1e-23
  switches=[]
  for dest,src,w in reversed(edges[:-1]):
   lo=np.uint64((src*g.n+dest)*g.stride);i,j=np.searchsorted(g.edges,[lo,lo+np.uint64(g.stride)]);choices=[int(x)%g.stride for x in g.edges[i:j] if g.switches[int(x)%g.stride]==w];assert choices;switches.append(min(choices))
  audited.append(dict(net=key[0],pin=key[1],status='exact_conditional_distance',suffix_nodes=[edges[-1][0]]+[x[0] for x in reversed(edges[:-1])],suffix_switches=switches,**r))
 write(directory/'analysis.json',dict(passed=True,rows=audited,query_process_seconds=elapsed,source_sha256={str(directory/n):sha(directory/n) for n in ['cases.json','cases.txt','stdout.log','stderr.log']},qualification='Actual directed edges/switch weights, retained anchors, blocked sets and completed exact/unreachable solver results checked. No jointly feasible owner restoration claimed.'))
 return audited

for index,r in enumerate(selected):
 target=tuple(r['target']);directory=b/f'target_{index:03d}';directory.mkdir();removed=collections.defaultdict(set);removed[target[0]].add(target[1]);critical_owners=[]
 for owner in r['owner_release_scope']:
  n=owner['net'];original=from_trace(traces[n]['trace'],g.switches)
  actual=set().union(*(downstream_pins(original,res) for res in owner['scarce_nodes']))
  assert actual=={p['pin'] for p in owner['affected_sink_pins']};removed[n].update(actual)
  if n in protected:critical_owners.append(n)
 originals={n:from_trace(traces[n]['trace'],g.switches) for n in removed};pruned={n:prune_sinks(originals[n],pins) for n,pins in removed.items()}
 assert nodes(pruned[target[0]])==set(base_cases[target]['retained'])
 forward=r['relaxed_suffix_nodes'];switches=r['relaxed_suffix_switches'];weights=[g.switches[s] for s in switches];g.require_edges(zip(forward,forward[1:],switches))
 target_tree=attach(pruned[target[0]],target[1],originals[target[0]]['sinks'][target[1]],forward,switches,weights)
 target_distance=prefixes(target_tree)[target_tree['sinks'][target[1]]];assert abs(target_distance-r['relaxed_delay_s'])<1e-23
 # Snapshot actual partial occupancy, and a relaxation protecting every other
 # current-cone net. The selected critical owners retain their unmodified trees.
 actual=collections.Counter({n:len(ns) for n,ns in owners.items()});fixed=collections.Counter({n:len(ns&protected) for n,ns in owners.items()})
 for net in removed:
  for node in nodes(originals[net]):
   actual[node]-=1
   if net in protected:fixed[node]-=1
  for node in nodes(pruned[net]):
   actual[node]+=1
   if net in protected:fixed[node]+=1
 for node in nodes(pruned[target[0]]):
  actual[node]-=1
  if target[0] in protected:fixed[node]-=1
 for node in nodes(target_tree):actual[node]+=1;fixed[node]+=1
 g.require_occupancy(actual);g.require_occupancy(fixed)
 query_pins=[(n,pin) for n in sorted(critical_owners) for pin in sorted(removed[n])]
 assert query_pins and target[0] not in critical_owners,'Self-owned conflicts cannot require another-net release'
 actions=[]
 for key in [target,*query_pins]:actions.append(dict(target=list(key),atom_nodes=[a['tnode_external'] for a in routed.get(key,{}).get('atoms',[])]))
 pattern=patterns(cone,actions)
 entry=dict(target=list(target),removed_pins={str(n):sorted(ps) for n,ps in removed.items()},critical_owners=critical_owners,target_current_s=r['current_delay_s'],target_preset_s=target_distance,winning_path_patterns=pattern,modes={})
 write(directory/'closure.json',entry)
 for mode,counts in [('current_other_occupancy',actual),('noncritical_background_relaxed',fixed)]:
  cases=[query_case(n,pin,pruned[n],originals[n],counts) for n,pin in query_pins];answers=solve(cases,directory/mode);deltas=[target_distance-r['current_delay_s']]
  for answer in answers:
   key=answer['net'],answer['pin'];old=prefixes(originals[key[0]])[originals[key[0]]['sinks'][key[1]]];answer['current_physical_s']=old;answer['delta_s']=None if answer['stop']!=0 else answer['distance_s']-old;deltas.append(answer['delta_s'])
  distributions=[]
  for mask,count in pattern['pattern_counts'].items():
   affected=[i for i in range(len(actions)) if int(mask)&(1<<i)];delta=None if any(deltas[i] is None for i in affected) else sum(deltas[i] for i in affected)
   distributions.append(dict(mask=int(mask),edge_paths=count,optimistic_current_path_delta_ps=None if delta is None else delta*1e12))
  entry['modes'][mode]=dict(answers=answers,path_model=distributions,qualification='Each owner queried independently with other missing owner paths absent. This is optimistic for the fixed target witness; additional future competition, noncritical detours, native float32 STA and new critical paths are not included. No acceptance decision.')
 rows.append(entry)
assert all(sha(p)==h for p,h in bound.items());write(b/'process_costs.json',costs)
write(b/'completion.json',dict(passed=True,rows=rows,input_state=str(state),native_calls=0,route_commits=0,complete_process_seconds=time.monotonic()-started,query_process_seconds=sum(c['complete_query_process_seconds'] for c in costs),source_sha256=bound,
 qualification='Conditional optimistic zero-RC delay models only, not strict mathematical global CPD bounds or final jointly legal routes. Critical owner and noncritical release pins are discovered from current occupancy/STA; no manually injected repairs. Whole native legality/STA and matched free-path control are still required before acceptance. No fixed research limit is implied by this operator.'))
print([dict(target=r['target'],closure=sum(map(len,r['removed_pins'].values())),modes={k:v['path_model'] for k,v in r['modes'].items()}) for r in rows],flush=True)
