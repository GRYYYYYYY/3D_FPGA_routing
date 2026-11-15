"""Find and screen the residual crossing above the certified fixed-terminal bound."""
import collections,json
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS
from resource_opportunity_census import stream_trace,tree_data,release_scope,pin_screen
proof=read(D/'BNN_vertical_cut_bound_01/completion.json');assert proof['passed'] and proof['SB_plus_CB_lower_bound']==5103
points=read(D/'multiobjective_budget47_composition_01/points.json');p=next(p for p in points if p.get('actor_final_selected') and p['batch']=='stable_seed_transfer_recovery_01')
state=Path(p['state']);rd=run_dir(state);manifest=read(rd/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);cache=FullRouteGraphCache(graph,D/'full_route_graph_cache_bnn_01');g=cache.g
assert read(state/'completion.json')['passed'] and read(rd/'independent_audit.json')['audit']['passed']
reference={}
for line in (D/'BNN_vertical_cut_bound_01/fixed_terminals_and_crossings.jsonl').open():
 r=json.loads(line);reference[r['net']]=(int(g.nodes[r['source'],4]),tuple((pin,int(g.nodes[n,4])) for pin,n in r['sinks']))
extra=[];totals=collections.Counter();observed_nets=set()
for rec in stream_trace(rd/'routed.route'):
 trace=rec['trace']
 if not trace:continue
 sinks=sorted({(n.pin,n.inode) for n in trace if n.kind=='SINK'});signature=(trace[0].low[2],tuple((pin,int(g.nodes[n,4])) for pin,n in sinks));assert signature==reference[rec['net']];observed_nets.add(rec['net'])
 layers={signature[0]}|{z for _,z in signature[1]};need=int(len(layers)>1);sb=set();cb=set()
 for a,b in zip(trace,trace[1:]):
  if a.switch==-1 or a.low[2]==b.low[2]:continue
  if a.kind=='OPIN':cb.add(a.inode)
  else:sb.add(tuple(sorted([a.inode,b.inode])))
 count=len(sb)+len(cb);assert count>=need;totals.update(dict(SB=len(sb),CB=len(cb),mandatory=need,excess=count-need))
 if count>need:extra.append(dict(net=rec['net'],name=rec['name'],pins=[pin for pin,_ in sinks],required=need,actual_SB=sorted(sb),actual_CB=sorted(cb),excess=count-need,trace=trace))
assert observed_nets==reference.keys() and totals==dict(SB=33,CB=5071,mandatory=5103,excess=1)
assert len(extra)==1 and extra[0]['excess']==1
net=extra[0]['net'];pins={}
for line in (rd/'native_sta_frontier.jsonl').open():
 r=json.loads(line)
 if r.get('type')=='pin' and r.get('net')==net and not r['driver'] and r['route_tree_present']:pins[r['pin']]=dict(slack_s=r['setup_slack_s'],criticality=r['setup_criticality_raw'],ignored=r['ignored'],**{'global':r['global']})
def metadata(n):
 r=g.nodes[n];direction=int(cache.extra[n,0]);return dict(kind=KINDS[int(r[1])],low=tuple(map(int,r[2:5])),high=tuple(map(int,r[5:8])),direction=cache.meta['directions'][direction])
vector=read(state/'endpoint_vector.json');row=extra[0];tree=tree_data(row.pop('trace'),metadata);groups=collections.defaultdict(set)
for node,r in tree['crossing'].items():groups[r['resource_kind'],r['resource']].update(tree['descendants'][node])
scopes=[]
for (kind,resource),targets in groups.items():
 released=release_scope(tree,targets,metadata);kept=(tree['SB']-set(released['released_SB']))|(tree['CB']-set(released['released_CB']))
 scopes.append(dict(kind=kind,resource=resource,pins=sorted(targets),released=released,retained_crossing_sources=sorted(kept),screen_0p2ns=pin_screen(targets,pins,vector['metrics']['least_slack_s'],.2e-9),screen_zero_margin=pin_screen(targets,pins,vector['metrics']['least_slack_s'],0.)))
out=D/'R1_last_vertical_excess_diagnostic_01';out.mkdir(exist_ok=False);write(out/'scopes.json',scopes)
write(out/'completion.json',dict(passed=True,native_calls_new=0,state=str(state),CPD_ns=vector['cpd_s']*1e9,total_resources=dict(totals),terminal_layer_mapping_matches_certificate_for_every_net=True,unique_excess_net=row,scopes=scopes,whole_net_pin_count=len(row['pins']),full_native_candidate_or_future_QoR_claim=False,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),D/'BNN_vertical_cut_bound_01/completion.json',D/'BNN_vertical_cut_bound_01/fixed_terminals_and_crossings.jsonl',state/'completion.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'routed.route',rd/'independent_audit.json',rd/'native_sta_frontier.jsonl',out/'scopes.json']},qualification='Actual fixed-seed R1 final has exactly one extra occupied crossing above the same fixed-terminal5103cut bound; terminal layer signature compared for every counted net. Each crossing-descendant scope is screened against the actual current complete native STA. Screens/release quantities are not a feasible replacement or future QoR prediction. No native worker, candidate, acceptance or old rule changed; use the actual diagnosis to choose a separate intervention with full native/physical/STA checks.'))
print(dict(passed=True,unique_excess_net=row['net'],actual_SB_CB=[33,5071],scopes=[dict(pins=s['pins'],retained=len(s['retained_crossing_sources']),eligible_0p2=s['screen_0p2ns']['eligible'],minimum_margin_s=s['screen_0p2ns']['minimum_margin_s']) for s in scopes]),flush=True)
