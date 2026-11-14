"""Rank reusable-crossing branches from this exact state and current native STA."""
import collections,json,time
from fractions import Fraction
from pathlib import Path
from retained_prefix_workflow import read,write,sha
from resource_opportunity_census import stream_trace,tree_data,release_scope,pin_screen,wire_units
from immutable_rr_audit_cache import KINDS
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import resource_assurance

def select(state,cache,output,minimum_margin_s=.2e-9):
 state=Path(state).resolve();out=Path(output).resolve();out.mkdir(exist_ok=False);started=time.monotonic();rd=run_dir(state);v=read(state/'endpoint_vector.json');assert read(state/'completion.json')['passed'];g=cache.g;view=resource_assurance(state);expected=dict(physical_metrics=view['physical_metrics']);assert view['passed'];pins=collections.defaultdict(dict)
 for line in (rd/'native_sta_frontier.jsonl').open():
  r=json.loads(line)
  if r.get('type')=='pin' and not r['driver'] and r['route_tree_present']:pins[r['net']][r['pin']]=dict(slack_s=r['setup_slack_s'],criticality=r['setup_criticality_raw'],ignored=r['ignored'],**{'global':r['global']})
 candidates=[];sb=collections.Counter();cb=collections.Counter();wire=0;multiple=0
 for rec in stream_trace(rd/'routed.route'):
  if not rec['trace']:continue
  local={}
  def metadata(n):
   if n not in local:
    r=g.nodes[n];direction,_=map(int,cache.extra[n]);local[n]=dict(kind=KINDS[int(r[1])],low=tuple(map(int,r[2:5])),high=tuple(map(int,r[5:8])),direction=cache.meta['directions'][direction])
   return local[n]
  tree=tree_data(rec['trace'],metadata);sb.update(tree['SB']);cb.update(tree['CB']);wire+=sum(wire_units(metadata(n)) for n in tree['used'])
  if len(tree['SB'])+len(tree['CB'])<=tree['layer_cut_reference']:continue
  multiple+=1;groups=collections.defaultdict(set)
  for node,e in tree['crossing'].items():groups[e['resource_kind'],e['resource']].update(tree['descendants'][node])
  seen=set()
  for _,targets in sorted(groups.items()):
   identity=tuple(sorted(targets))
   if identity in seen:continue
   seen.add(identity);screen=pin_screen(targets,pins[rec['net']],v['metrics']['least_slack_s'],minimum_margin_s)
   if not screen['eligible']:continue
   released=release_scope(tree,targets,metadata);freed=len(released['released_SB'])+len(released['released_CB']);kept=sorted((tree['SB']-set(released['released_SB']))|(tree['CB']-set(released['released_CB'])))
   if not freed or not kept:continue
   by_pin={r['pin']:r for r in screen['pins']};candidates.append(dict(net=rec['net'],name=rec['name'],removed_crossing_resources=freed,minimum_margin_s=screen['minimum_margin_s'],resource_per_sink=str(Fraction(freed,len(targets))),retained_crossing_sources=kept,**released,ordered_queries=[dict(net=rec['net'],pin=p,raw_criticality=by_pin[p]['raw_criticality']) for p in sorted(targets)]))
 candidates.sort(key=lambda r:(-Fraction(r['removed_crossing_resources'],len(r['pins'])),len(r['pins']),-r['minimum_margin_s'],r['net'],r['pins']))
 actual=dict(planar_wirelength_excluding_sb_half_nodes=wire,sb_pairs_used=len(sb),sb_pair_net_occupancy=sum(sb.values()),cb_crossing_output_sources_used=len(cb),cb_crossing_output_source_net_occupancy=sum(cb.values()));assert all(expected['physical_metrics'][k]==n for k,n in actual.items()),'Current resource census mismatch'
 write(out/'candidates.json',candidates);result=dict(passed=True,source_state=str(state),route_sha256=sha(rd/'routed.route'),CPD_s=v['cpd_s'],constraints_sha256=v['constraints_sha256'],minimum_margin_s=minimum_margin_s,multi_crossing_nets=multiple,candidate_scopes=len(candidates),actual_resources=actual,ranking='released crossings per sink, fewer sinks, larger current worst slack margin, net/pin ID',resource_assurance=dict(kind=view['assurance_kind'],independent_physical_audit=view['independent_physical_audit'],evidence=view['evidence']),source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),Path(__file__).with_name('state_resource_assurance.py'),Path(view['evidence']),state/'completion.json',state/'endpoint_vector.json',rd/'routed.route',rd/'native_sta_frontier.jsonl',out/'candidates.json']},complete_selector_seconds=time.monotonic()-started,qualification='Current-state structural/slack screening only; each candidate requires native feasibility, complete replacement, full physical/STA gates. Candidate release quantities overlap and are not additive savings. No persistent initial target list.')
 write(out/'completion.json',result);return candidates
