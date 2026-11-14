#!/usr/bin/env python3
"""Census sealed BNN starts and a current accepted state without rerouting."""
import collections,json,math,resource,signal,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS
from resource_opportunity_census import stream_trace,tree_data,release_scope,wire_units,pin_screen
from run_native_scope_policy_v4 import run_dir
b=D/'resource_opportunity_census_01';b.mkdir(exist_ok=False);started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
states={'A0':D/'timing_cone_bnn_dev_02/A0','R1':D/'timing_cone_bnn_dev_02/R1','Tf':D/'timing_cone_bnn_dev_01/Tf','A0_endpoint_bridge':D/'portfolio_execution_dev_01/A0_endpoint/round_001/proposal_03/transaction/current_group_evaluation'}
owner_files={'A0':D/'bnn_baseline_release_screens_01/A0_owners/completion.json','R1':D/'bnn_baseline_release_screens_01/R1_owners/completion.json','Tf':D/'bnn_slack_release_screen_01/owner_slack/completion.json','A0_endpoint_bridge':D/'portfolio_execution_dev_01/A0_endpoint/round_002/feedback/owners/completion.json'}
files=[Path(__file__).resolve(),D/'resource_opportunity_census.py',D.parents[1]/'scripts/check_route.py',D.parents[1]/'scripts/flatland_benchmark.py',D/'full_route_graph_cache.py',D/'immutable_rr_audit_cache.py',D/'resource_opportunity_hypothesis_01.json']
for name,state in states.items():
 assert read(state/'completion.json')['passed'];rd=run_dir(state);files += [state/'completion.json',state/'endpoint_vector.json',rd/'routed.route',rd/'native_sta_frontier.jsonl',rd/'manifest.json',rd/'independent_audit.json',owner_files[name]]
source_hashes={str(p):sha(p) for p in files};margin=.2e-9;minimum_wire=8
write(b/'registration.json',dict(status='before_census',pid=__import__('os').getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],states={k:str(v) for k,v in states.items()},source_sha256=source_hashes,question='How much actual crossing occupation is structurally mandatory versus excursion/reference excess, and which slack-bearing scopes could release resources independently of positive-delay current-path filtering?',screen=dict(margin_to_current_worst_s=margin,minimum_wire_only_scope=minimum_wire),limits=dict(seconds=1800,memory_bytes=24*1024**3),native_calls=0,route_calls=0,qualification='Read-only four-state development census, not new final routes, mathematical global optimum, confirmed candidate choices or performance. Terminal-only cut reference ignores topology/capacity and SB/CB substitution. Release is an optimistic terminal-path scope pending native pruning and feasible replacement.'))
first=run_dir(states['A0']);manifest=read(first/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);cache=FullRouteGraphCache(graph,D/'full_route_graph_cache_bnn_01');g=cache.g;assert sorted(set(g.nodes[:,4].tolist()))==[0,1]
results={}
for name,state in states.items():
 t=time.monotonic();out=b/name;out.mkdir();rd=run_dir(state);m=read(rd/'manifest.json');assert Path(m['command'][m['command'].index('--read_rr_graph')+1])==graph;assert sha(rd/'routed.route')==m['outputs']['routed.route']['sha256'];expected=read(rd/'independent_audit.json');assert expected['audit']['passed'];expected=expected['physical_metrics'];vector=read(state/'endpoint_vector.json');worst=vector['metrics']['least_slack_s'];pins=collections.defaultdict(dict)
 for line in (rd/'native_sta_frontier.jsonl').open():
  r=json.loads(line)
  if r.get('type')=='pin' and not r['driver'] and r['route_tree_present']:
   pins[r['net']][r['pin']]=dict(slack_s=r['setup_slack_s'],criticality=r['setup_criticality_raw'],ignored=r['ignored'],global_net=r['global'],**{'global':r['global']})
 owners=read(owner_files[name]);assert owners['passed'] and Path(owners['input_state'])==state;scarce=collections.defaultdict(set)
 for row in owners['rows']:
  for node,conflict in row['blocked_resources'].items():
   for net in conflict['other_nets']:scarce[net].add(int(node))
 totals=collections.Counter();cross_edge_kinds=collections.Counter();sb=collections.Counter();cb=collections.Counter();hist=collections.Counter();candidates=[]
 with (out/'nets.jsonl').open('w') as netfile:
  for rec in stream_trace(rd/'routed.route'):
   trace=rec['trace'];net=rec['net'];totals['nets']+=1
   if not trace:totals['empty_nets']+=1;continue
   local={}
   def metadata(n):
    if n not in local:
     row=g.nodes[n];direction,timing=map(int,cache.extra[n]);local[n]=dict(kind=KINDS[int(row[1])],low=tuple(map(int,row[2:5])),high=tuple(map(int,row[5:8])),direction=cache.meta['directions'][direction])
    return local[n]
   tree=tree_data(trace,metadata);wire=sum(wire_units(metadata(n)) for n in tree['used']);sb.update(tree['SB']);cb.update(tree['CB']);totals['wire']+=wire;totals['layer_cut_reference_sum']+=tree['layer_cut_reference'];totals['crossing_nets']+=bool(tree['SB'] or tree['CB']);totals['excursion_edges']+=len(tree['excursions']);totals['nets_with_excursion']+=bool(tree['excursions']);excess=len(tree['SB'])+len(tree['CB'])-tree['layer_cut_reference'];hist[excess]+=1;totals['sum_resource_excess_over_reference']+=excess
   for node,edge in tree['crossing'].items():cross_edge_kinds[metadata(edge['up'])['kind']+'->'+metadata(node)['kind']]+=1
   whole=pin_screen(tree['sinks'],pins[net],worst,margin)
   row=dict(net=net,name=rec['name'],sink_pins=len(tree['sinks']),wirelength=wire,SB_pairs=len(tree['SB']),CB_sources=len(tree['CB']),terminal_layer_cut_reference=tree['layer_cut_reference'],resource_excess_over_reference=excess,pure_return_excursions=tree['excursions'],whole_net_screen=whole,scarce_nodes=sorted(scarce[net]))
   netfile.write(json.dumps(row,separators=(',',':'))+'\n')
   groups={}
   if whole['eligible'] and (tree['SB'] or tree['CB']):groups[tuple(sorted(tree['sinks']))]={'whole_noncritical_crossing_net'}
   for e in tree['excursions']:
    key=tuple(e['pins']);screen=pin_screen(key,pins[net],worst,margin)
    if screen['eligible']:groups.setdefault(key,set()).add('pure_return_excursion')
   for pin in tree['sinks']:
    screen=pin_screen([pin],pins[net],worst,margin)
    if not screen['eligible']:continue
    scope=release_scope(tree,[pin],metadata)
    if scope['released_SB'] or scope['released_CB'] or scope['released_wire']>=minimum_wire:groups.setdefault((pin,),set()).add('slack_bearing_sink')
   for group,kinds in groups.items():
    scope=release_scope(tree,group,metadata);screen=pin_screen(group,pins[net],worst,margin);overlap=sorted(set(scope['released_nodes'])&scarce[net]);candidates.append(dict(net=net,net_name=rec['name'],kinds=sorted(kinds),**scope,screen=screen,released_scarce_nodes=overlap,terminal_layer_cut_reference=tree['layer_cut_reference'],net_reference_excess=excess))
 potential_sb=set();potential_cb=set();overlap_count=0
 for r in candidates:
  r['exclusive_SB']=[n for n in r['released_SB'] if sb[n]==1];r['exclusive_CB']=[n for n in r['released_CB'] if cb[n]==1];potential_sb.update(r['exclusive_SB']);potential_cb.update(r['exclusive_CB']);overlap_count+=bool(r['released_scarce_nodes'])
 with (out/'candidates.jsonl').open('w') as stream:
  for r in candidates:stream.write(json.dumps(r,separators=(',',':'))+'\n')
 actual=dict(planar_wirelength_excluding_sb_half_nodes=totals['wire'],sb_pairs_used=len(sb),sb_pair_net_occupancy=sum(sb.values()),cb_crossing_output_sources_used=len(cb),cb_crossing_output_source_net_occupancy=sum(cb.values()),actual_crossing_edge_traversals=dict(cross_edge_kinds))
 assert all(actual[k]==expected[k] for k in actual),(name,actual,expected)
 summary=dict(passed=True,state=str(state),CPD_ns=vector['cpd_s']*1e9,actual_resources=actual,census=dict(totals),excess_histogram=dict(hist),candidates=len(candidates),candidate_kind_counts=dict(collections.Counter(k for r in candidates for k in r['kinds'])),candidate_union_exclusive_SB=len(potential_sb),candidate_union_exclusive_CB=len(potential_cb),scopes_overlapping_measured_critical_scarcity=overlap_count,nonadditive_scopes=True,complete_census_seconds=time.monotonic()-t,qualification='Exact current resource census matches sealed physical auditor. Candidate unions and reference excess are optimistic potential, not feasible savings. Overlapping scopes cannot be summed; replacement may consume the same/more resources. Slack margin is screening, not endpoint feasibility proof.')
 write(out/'summary.json',summary);results[name]=summary;write(b/'progress.json',results);print(dict(state=name,candidates=len(candidates),SB=len(sb),CB=len(cb),excursions=totals['excursion_edges'],excess=totals['sum_resource_excess_over_reference']),flush=True)
assert all(sha(p)==h for p,h in source_hashes.items());write(b/'completion.json',dict(passed=True,rows=results,source_sha256=source_hashes,graph_cache_receipt=cache.receipt,complete_census_seconds=time.monotonic()-started,native_calls=0,route_calls=0,final_savings=None,qualification='Observed actual resources and structural/slack screening only. No new routing query or candidate replaced. Next discriminate feasible resource-oriented alternatives with exact capacity/native FULLSTA controls.'))
