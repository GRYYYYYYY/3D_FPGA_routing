#!/usr/bin/env python3
"""Build a current-state repair proposal directly from certified query feedback."""
import argparse,collections,json,resource,sys,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,downstream_pins
from critical_action_patterns import patterns
from select_critical_action_group import select
from check_route import read_trace
p=argparse.ArgumentParser()
for n in ['cone','capacity-batch','protected','audit-cache','output']:p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--fraction',type=float,default=.9);p.add_argument('--planning-seconds',type=float,default=300.);a=p.parse_args()
start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));b=a.output.resolve();b.mkdir(exist_ok=False)
cone=read(a.cone);assert cone['passed'];state=Path(cone['source_state']);source=Path(read(state/'completion.json')['run']);cap=read(a.capacity_batch/'analysis.json');protected=read(a.protected)
assert cap['passed'] and protected['passed']
assert Path(read(a.capacity_batch/'execution_registration.json')['input_run']).resolve()==source.resolve()
assert Path(read(a.protected.parent/'registration.json')['input_run']).resolve()==source.resolve()
m=read(source/'manifest.json');assert m['metrics']['native_full_check_passed'] and read(source/'independent_audit.json')['audit']['passed']
graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);cache=read(a.audit_cache/'completion.json');assert cache['zero_RC'] and sha(graph)==cache['graph_sha256']
assert sha(source/'routed.route')==m['outputs']['routed.route']['sha256']
files=[Path(__file__).resolve(),D/'critical_action_patterns.py',D/'select_critical_action_group.py',a.cone,a.capacity_batch/'analysis.json',a.capacity_batch/'execution_registration.json',a.protected,a.protected.parent/'registration.json',state/'completion.json',source/'manifest.json',source/'routed.route',source/'native_sta_frontier.jsonl',graph,a.audit_cache/'completion.json',a.audit_cache/'switches.npy']
bindings={str(p.resolve()):sha(p) for p in files}
write(b/'registration.json',dict(status='registered_before_planning',source_state=str(state),fraction=a.fraction,source_sha256=bindings,native_calls=0,
 question='Select an automatically current-path-covering group directly from this state/query feedback, with a uniform proxy-retention fraction and minimum distinct repair connections.',
 qualification='Proposal only. Positive protected-relaxed witnesses do not prove complete legal owner replacement. Resource/endpoint-vector opportunities remain outside this strict-CPD selector.'))
assert sha(a.audit_cache/'switches.npy')==cache['payload_sha256']['switches.npy'];sw=np.load(a.audit_cache/'switches.npy');switches={i:float(v) for i,v in enumerate(sw) if np.isfinite(v)}
direct={(r['net'],r['pin']):r for r in cap['results'] if r['improvement_ns']>1e-6};relaxed={tuple(r['target']):r for r in protected['rows'] if r['gain_ns']>1e-6}
connections={(r['net'],r['pin']):r for r in cone['routed_connections']};targets=sorted(set(direct)|set(relaxed));assert set(targets)<=connections.keys()
traces=read_trace(source/'routed.route') if targets else {};sta={}
for line in (source/'native_sta_frontier.jsonl').open():
 r=json.loads(line)
 if r.get('type')=='pin' and not r['driver']:sta[r['net'],r['pin']]=r
actions=[]
for target in targets:
 gain=direct.get(target,{}).get('improvement_ns',0.);donors=set();witness=relaxed.get(target)
 if witness and witness['gain_ns']>gain:
  gain=witness['gain_ns'];conflicts=collections.defaultdict(set)
  for c in witness['conflicts']:
   assert not c['protected_owners']
   for net in c['releasable_noncritical_owners']:conflicts[net].add(c['node'])
  for net,nodes in conflicts.items():
   tree=from_trace(traces[net]['trace'],switches)
   for node in nodes:donors.update((net,pin) for pin in downstream_pins(tree,node))
  assert all(float(sta[x]['setup_slack_s'])>float(cone['worst_slack_s']) for x in donors)
 actions.append(dict(target=target,optimistic_gain_ns=gain,donors=sorted(donors),atom_nodes=sorted({a['tnode_external'] for a in connections[target]['atoms']})))
pattern_data=patterns(cone,actions);selection=select(pattern_data,actions,a.fraction,a.planning_seconds);selected=[actions[i] for i in selection['selected']]
chosen={tuple(x['target']) for x in selected};pins=set(chosen)
for x in selected:pins.update(map(tuple,x['donors']))
ordered=sorted(chosen,key=lambda x:(float(sta[x]['setup_slack_s']),x))+[x for x in sorted(pins) if x not in chosen]
write(b/'plan.json',dict(passed=True,source_state=str(state),actions=actions,selection=selection,ordered_queries=[dict(net=n,pin=pin,raw_criticality=sta[n,pin]['setup_criticality_raw']) for n,pin in ordered],
 repair_pins=sorted(pins),compressed_winning_paths=dict(edge_paths=pattern_data['edge_paths'],patterns=pattern_data['distinct_patterns']),
 complete_planning_workflow_seconds=time.monotonic()-start,source_sha256=bindings,native_calls=0,accepted=False,
 qualification='Current-state strict-CPD proposal, not a new route/commit or guarantee of final CPD. No-positive cover means this proposal class is empty, not overall research completion. Budgeted incumbent may have uncertified proxy optimality.'))
print(dict(status=selection['status'],targets=selection.get('targets',[]),repair_connections=len(pins),seconds=time.monotonic()-start),flush=True)
