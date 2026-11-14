#!/usr/bin/env python3
"""Small exact coverage reference over existing candidate witnesses, not routing optimum."""
import collections,itertools,json,resource,sys,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,downstream_pins
sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace
start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));out=D/'critical_group_cover_reference_01';out.mkdir(exist_ok=False)
obs=read(D/'timing_cone_bnn_dev_02/completion.json');files=[Path(__file__).resolve(),D/'coordinated_repair_tree.py',D/'timing_cone_bnn_dev_02/completion.json',D/'rr_audit_cache_bnn_01/completion.json',D/'rr_audit_cache_bnn_01/switches.npy']
write(out/'registration.json',dict(pid=__import__('os').getpid(),question='Can current winning-path coverage identify smaller or higher-value coordinated groups than selecting every positive local candidate?',
 scope='All subsets of existing positive direct/protected-critical witnesses for pristineTf/A0/R1. Exact combinatorial coverage in current winning timing DAG; timing gain and connection-count cost are proxies, not final CPD/resource/runtime bounds.',native_calls=0,source_sha256={str(p):sha(p) for p in files}))
cache=read(D/'rr_audit_cache_bnn_01/completion.json');assert sha(D/'rr_audit_cache_bnn_01/switches.npy')==cache['payload_sha256']['switches.npy']
switches={i:float(v) for i,v in enumerate(np.load(D/'rr_audit_cache_bnn_01/switches.npy')) if np.isfinite(v)};results={}
for arm in ['Tf','A0','R1']:
 state=Path(obs['roles'][arm]['state']);cone_path=Path(obs['roles'][arm]['cone']);cone=read(cone_path);assert cone['passed'];source=Path(read(state/'completion.json')['run'])
 q=D/'bnn_slack_release_screen_01/Tf_capacity' if arm=='Tf' else D/'bnn_baseline_capacity_screens_01'/arm
 pp=D/'bnn_slack_release_screen_01/protected_critical/completion.json' if arm=='Tf' else D/'bnn_baseline_release_screens_01'/(arm+'_protected/completion.json')
 protected=read(pp);cap=read(q/'analysis.json');assert protected['passed'] and cap['passed']
 direct={(r['net'],r['pin']):r for r in cap['results'] if r['improvement_ns']>1e-6}
 relaxed={tuple(r['target']):r for r in protected['rows'] if r['gain_ns']>1e-6};targets=sorted(set(direct)|set(relaxed));assert len(targets)<=20
 traces=read_trace(source/'routed.route');connections={(r['net'],r['pin']):r for r in cone['routed_connections']};actions=[]
 for target in targets:
  donors=set();witness=relaxed.get(target);gain=direct.get(target,{}).get('improvement_ns',0.)
  if witness and witness['gain_ns']>gain:
   gain=witness['gain_ns'];conflicts=collections.defaultdict(set)
   for c in witness['conflicts']:
    assert not c['protected_owners']
    for net in c['releasable_noncritical_owners']:conflicts[net].add(c['node'])
   for net,nodes in conflicts.items():
    tree=from_trace(traces[net]['trace'],switches)
    for node in nodes:donors.update((net,pin) for pin in downstream_pins(tree,node))
  actions.append(dict(target=target,optimistic_gain_ns=gain,donors=sorted(donors),atom_nodes=sorted({a['tnode_external'] for a in connections[target]['atoms']})))
 paths=[]
 for launch,t in cone['cones'].items():
  parents={f['node']:[c['source'] for c in f['choices'] if c['edge'] in f['winning_edges']] for f in t['fanins']};sources=set(t['sources'])
  def back(node):
   if node in sources:return [(node,)]
   return [p+(node,) for source in parents[node] for p in back(source)]
  for endpoint in cone['selected_endpoints']:
   if str(endpoint['identity'][3])==launch:paths += back(endpoint['identity'][0])
 assert paths and len(paths)<=100000
 profiles=[]
 for flags in itertools.product([0,1],repeat=len(actions)):
  chosen=[a for a,f in zip(actions,flags) if f];repair=set()
  for a in chosen:repair.add(tuple(a['target']));repair.update(map(tuple,a['donors']))
  gains=[sum(a['optimistic_gain_ns'] for a in chosen if set(a['atom_nodes'])&set(path)) for path in paths]
  profiles.append(dict(targets=[a['target'] for a in chosen],repair_connections=len(repair),repair_pins=sorted(repair),winning_path_gains_ns=gains,min_current_winning_path_gain_ns=min(gains),all_current_paths_covered=min(gains)>0))
 frontier=[p for p in profiles if p['all_current_paths_covered'] and not any(q['repair_connections']<=p['repair_connections'] and q['min_current_winning_path_gain_ns']>=p['min_current_winning_path_gain_ns'] and (q['repair_connections']<p['repair_connections'] or q['min_current_winning_path_gain_ns']>p['min_current_winning_path_gain_ns']) for q in profiles)]
 results[arm]=dict(source_state=str(state),winning_paths=len(paths),actions=actions,enumerated_subsets=len(profiles),profiles=profiles,proxy_frontier=frontier)
 files += [cone_path,state/'completion.json',source/'routed.route',q/'analysis.json',pp]
 write(out/'progress.json',results);print(arm,'paths',len(paths),'frontier',[(p['targets'],p['repair_connections'],p['min_current_winning_path_gain_ns']) for p in frontier],flush=True)
write(out/'completion.json',dict(passed=True,results=results,source_sha256={str(p):sha(p) for p in files},complete_process_seconds=time.monotonic()-start,native_calls=0,
 qualification='Exact exhaustive minimum/coverage tradeoff only within measured candidate set and current winning DAG. Path gain ignores resource interactions and newly critical paths; search-connection count is an engineering proxy. Neither is a strict global FPGA bound or final method performance. Resource-only and endpoint-vector opportunities are outside this strict-CPD reference, not discarded.'))
