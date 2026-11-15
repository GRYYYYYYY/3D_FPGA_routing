"""Certify total SB+CB and conditional SB bounds for the fixed BNN terminal cut."""
import hashlib,json
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS
from resource_opportunity_census import stream_trace

archive=D/'multiobjective_budget47_composition_01';pc=read(archive/'completion.json');assert pc['passed'];points=read(archive/'points.json')
point=next(p for p in points if p['arm']=='complete_resource_paired_then_current_STA_native');state=Path(point['state']);rd=run_dir(state)
assert read(state/'completion.json')['passed'] and read(state/'input_seal.json')['passed']
m=read(rd/'manifest.json');assert m['metrics']['native_full_check_passed'];audit=read(rd/'independent_audit.json');assert audit['audit']['passed']
for f in ['packed.net','placed.place','routed.route']:assert sha(rd/f)==m['outputs'][f]['sha256']
graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);cache=FullRouteGraphCache(graph,D/'full_route_graph_cache_bnn_01');g=cache.g
assert np.array_equal(g.nodes[:,4],g.nodes[:,7]) and set(map(int,np.unique(g.nodes[:,4])))=={0,1}
opin=KINDS.index('OPIN');chanx=KINDS.index('CHANX');chany=KINDS.index('CHANY');cb_sources=set();sb_partner={};cross_count=0
for start in range(0,len(g.edges),500000):
 encoded=g.edges[start:start+500000]//g.stride;u=(encoded//g.n).astype(np.int64);v=(encoded%g.n).astype(np.int64)
 mask=g.nodes[u,4]!=g.nodes[v,4];u=u[mask];v=v[mask];cross_count+=len(u)
 assert np.all(g.nodes[u,0]==1) and np.all(g.nodes[v,0]==1),'A crossing resource can be shared across nets'
 is_cb=g.nodes[u,1]==opin
 assert np.all(np.isin(g.nodes[v[is_cb],1],[chanx,chany]));cb_sources.update(map(int,u[is_cb]))
 su,sv=u[~is_cb],v[~is_cb];assert np.all(g.nodes[su,1]==chanx) and np.all(g.nodes[sv,1]==chanx)
 assert all(cache.meta['directions'][int(cache.extra[n,0])]=='NONE' for n in set(map(int,np.concatenate([su,sv]))))
 assert np.array_equal(g.nodes[su,2:4],g.nodes[sv,2:4]) and np.array_equal(g.nodes[su,5:7],g.nodes[sv,5:7])
 for aa,bb in zip(su,sv):
  a,b=int(aa),int(bb)
  for first,second in [(a,b),(b,a)]:
   assert first not in sb_partner or sb_partner[first]==second,'SB half-node belongs to multiple physical pairs'
   sb_partner[first]=second
assert cross_count and cb_sources and sb_partner
out=D/'BNN_vertical_cut_bound_01';out.mkdir(exist_ok=False);witness=out/'fixed_terminals_and_crossings.jsonl';count=mandatory=0;global_resources=set();used_sb=set();used_cb=set()
with witness.open('w') as f:
 for rec in stream_trace(rd/'routed.route'):
  trace=rec['trace']
  if not trace:continue
  assert trace[0].kind=='SOURCE';source=trace[0].inode;sinks=sorted({(n.pin,n.inode) for n in trace if n.kind=='SINK'});assert sinks
  assert all(pin is not None and pin>0 for pin,_ in sinks)
  layers={int(g.nodes[source,4])}|{int(g.nodes[n,4]) for _,n in sinks};need=int(len(layers)>1);actual=set()
  for a,b in zip(trace,trace[1:]):
   if a.switch==-1 or g.nodes[a.inode,4]==g.nodes[b.inode,4]:continue
   if a.kind=='OPIN':
    assert a.inode in cb_sources;resource=('CB',a.inode);used_cb.add(a.inode)
   else:
    assert sb_partner[a.inode]==b.inode;pair=tuple(sorted([a.inode,b.inode]));resource=('SB',*pair);used_sb.add(pair)
   actual.add(resource)
  assert len(actual)>=need and not global_resources.intersection(actual)
  global_resources.update(actual);mandatory+=need;count+=1
  f.write(json.dumps(dict(net=rec['net'],source=source,sinks=sinks,terminal_layers=sorted(layers),required_crossings=need,actual_crossing_resources=sorted(actual)),separators=(',',':'))+'\n')
physical=audit['physical_metrics'];assert len(used_sb)==physical['sb_pairs_used']==43 and len(used_cb)==physical['cb_crossing_output_sources_used']==5060
assert mandatory==len(global_resources)==len(used_sb)+len(used_cb)==5103
population=[p for p in points if p['quality_cohort']==point['quality_cohort'] and p['circuit']=='bnn']
assert all(p['SB_pairs']+p['CB_sources']>=mandatory for p in population)
files=[Path(__file__).resolve(),archive/'completion.json',archive/'points.json',state/'completion.json',state/'input_seal.json',rd/'manifest.json',rd/'routed.route',rd/'independent_audit.json',D/'full_route_graph_cache_bnn_01/completion.json',Path(cache.g.directory)/'completion.json',witness]
write(out/'completion.json',dict(passed=True,native_calls_new=0,fixed_terminal_nets=count,nets_requiring_layer_crossing=mandatory,graph_crossing_edges=cross_count,graph_CB_sources=len(cb_sources),graph_SB_pairs=len(sb_partner)//2,all_nodes_single_layer=True,all_crossings_are_unit_capacity_CB_or_unique_SB_pairs=True,SB_plus_CB_lower_bound=mandatory,actual_SB=43,actual_CB=5060,bound_attained=True,conditional_SB_lower_bound_given_CB_at_most_5060=mandatory-5060,conditional_SB_bound_attained=True,matched_archive_observations=len(population),all_matched_observations_respect_total_bound=True,source_sha256={str(f):sha(f) for f in files},proof='Each counted nonglobal net with fixed terminals on both layers must use at least one crossing. Every graph crossing consumes either a unit-capacity OPIN source (one CB resource) or both unit-capacity halves of one unique SB pair. Different nets cannot share either counted resource, and the classes are disjoint. Thus S+C>=5103. A legal43SB/5060CB route attains equality. Under C<=5060, S>=43, also attained.',qualification='Exact vertical-occupancy and conditional SB bounds for this supplied two-layer Hybrid-O graph, counted nonglobal net set and fixed terminal RR mapping. Unit capacities/unique SB pairing checked over all cross-layer graph edges; witness covers every routed net. This proves neither wire/CPD/global-route optimum nor routability after changed mapping/architecture/packing/placement/clock accounting. It does not prohibit lower SB by allowing higher CB. Read-only one-time certificate cost is separate research validation, not measured algorithm work; existing trajectories and stops unchanged.'))
print(dict(passed=True,total_vertical_lower_bound=5103,actual=[43,5060],conditional_SB_minimum_at_CB_cap5060=43),flush=True)
