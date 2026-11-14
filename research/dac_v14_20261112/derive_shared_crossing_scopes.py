#!/usr/bin/env python3
"""Derive every slack-bearing crossing-sharing scope; do not choose history best."""
import collections,json,resource,shutil,signal,time
from fractions import Fraction
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS
from resource_opportunity_census import stream_trace,tree_data,release_scope
from run_native_scope_policy_v4 import run_dir
b=D/'shared_crossing_scopes_01';b.mkdir(exist_ok=False);started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800);assert shutil.disk_usage(b).free>=80*1024**3
census=D/'resource_opportunity_census_01';c=read(census/'completion.json');assert c['passed'];assert read(D/'resource_census_validation_01.json')['passed']
states=read(census/'registration.json')['states'];first=run_dir(Path(states['A0']));m=read(first/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);cache=FullRouteGraphCache(graph,D/'full_route_graph_cache_bnn_01');g=cache.g
files=[Path(__file__).resolve(),D/'resource_opportunity_census.py',census/'completion.json',D/'resource_census_validation_01.json']
write(b/'registration.json',dict(status='before_derivation',pid=__import__('os').getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],question='Can current noncritical branch groups remove one or more crossing resources while another crossing remains in their own retained tree?',states=states,ranking='Decreasing released crossing resources per pruned sink; then fewer sinks; then larger minimum margin to current worst; then net and pin IDs. Same rule for every state; no historical result selection.',source_sha256={str(p):sha(p) for p in files},native_calls=0,query_calls=0,limits=dict(memory_bytes=24*1024**3,seconds=1800,disk_reserve_bytes=80*1024**3)))
results={}
for name,raw_state in states.items():
 state=Path(raw_state);rd=run_dir(state);out=b/name;out.mkdir();selected={}
 with (census/name/'nets.jsonl').open() as stream:
  for line in stream:
   r=json.loads(line)
   if r['resource_excess_over_reference']>0:selected[r['net']]=r
 candidates=[]
 for rec in stream_trace(rd/'routed.route'):
  net=rec['net']
  if net not in selected:continue
  row=selected[net];local={}
  def metadata(n):
   if n not in local:
    a=g.nodes[n];direction,_=map(int,cache.extra[n]);local[n]=dict(kind=KINDS[int(a[1])],low=tuple(map(int,a[2:5])),high=tuple(map(int,a[5:8])),direction=cache.meta['directions'][direction])
   return local[n]
  tree=tree_data(rec['trace'],metadata);by_source=collections.defaultdict(set)
  for node,e in tree['crossing'].items():by_source[e['resource_kind'],e['resource']].update(tree['descendants'][node])
  pinrows={r['pin']:r for r in row['whole_net_screen']['pins']};seen=set()
  for key,pins in sorted(by_source.items()):
   identity=tuple(sorted(pins))
   if identity in seen:continue
   seen.add(identity)
   if not all(pinrows[p]['eligible'] for p in pins):continue
   release=release_scope(tree,pins,metadata);freed=len(release['released_SB'])+len(release['released_CB']);kept=sorted((tree['SB']-set(release['released_SB']))|(tree['CB']-set(release['released_CB'])))
   if not freed or not kept:continue
   minimum=min(pinrows[p]['margin_s'] for p in pins);candidates.append(dict(net=net,name=rec['name'],pins=sorted(pins),released_SB=release['released_SB'],released_CB=release['released_CB'],released_wire=release['released_wire'],released_nodes=release['released_nodes'],retained_crossing_sources=kept,removed_crossing_resources=freed,minimum_margin_s=minimum,resource_per_sink=str(Fraction(freed,len(pins))),ordered_queries=[dict(net=net,pin=p,raw_criticality=pinrows[p]['raw_criticality']) for p in sorted(pins)],actual_original_SB=len(tree['SB']),actual_original_CB=len(tree['CB'])))
 def ranking(r):return (-Fraction(r['removed_crossing_resources'],len(r['pins'])),len(r['pins']),-r['minimum_margin_s'],r['net'],r['pins'])
 candidates.sort(key=ranking);write(out/'candidates.json',candidates)
 if candidates:
  r=candidates[0];bindings={str(p):sha(p) for p in [out/'candidates.json',census/'completion.json',census/name/'nets.jsonl',state/'completion.json',state/'endpoint_vector.json',rd/'routed.route',rd/'native_sta_frontier.jsonl',Path(__file__).resolve(),D/'resource_opportunity_census.py']}
  plan=dict(passed=True,source_state=str(state),actions=[],repair_pins=[[r['net'],p] for p in r['pins']],ordered_queries=r['ordered_queries'],selection=dict(status='resource_crossing_share_scope',targets=[[r['net'],p] for p in r['pins']],resource_objective=['SB_pairs','CB_sources'],crossing_reuse_net=r['net'],ranking='resource_per_sink_then_fewer_sinks_then_margin_then_ID'),scope_reference=r,source_sha256=bindings,native_calls=0,qualification='Automatic first ranked current-state scope. Retained crossing sources are available for sharing but capacity-constrained alternatives and final native FULLSTA are unproven. No forced suffix or new search primitive.')
  write(out/'plan.json',plan);(out/'domain_nets.txt').write_text('1\n'+str(r['net'])+'\n')
 result=dict(passed=True,state=str(state),multi_crossing_nets=len(selected),candidate_scopes=len(candidates),selected=candidates[0] if candidates else None,source_sha256={str(p):sha(p) for p in [census/name/'nets.jsonl',rd/'routed.route',out/'candidates.json']});write(out/'completion.json',result);results[name]=result;print(dict(state=name,multi_crossing_nets=len(selected),scopes=len(candidates),selected=None if not candidates else {k:candidates[0][k] for k in ['net','pins','removed_crossing_resources','minimum_margin_s']}),flush=True)
assert all(sha(p)==h for p,h in read(b/'registration.json')['source_sha256'].items());write(b/'completion.json',dict(passed=True,rows=results,source_sha256={str(p):sha(p) for p in [b/'registration.json',Path(__file__).resolve(),*[b/n/'completion.json' for n in states]]},native_calls=0,query_calls=0,complete_process_seconds=time.monotonic()-started,qualification='Automatic ranked scopes from actual routes. No candidate replaced or savings proven. Source=current specified sealed state; original routing/delay data are reused exactly.'))
