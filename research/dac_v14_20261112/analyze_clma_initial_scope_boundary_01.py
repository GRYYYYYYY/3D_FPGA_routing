"""Explain the three observed redundant nets with the unchanged selector primitives."""
from pathlib import Path
import collections,fcntl,hashlib,json,sys,time
D=Path(__file__).resolve().parent;B=D/'CLMA_initial_scope_boundary_01';C=D/'cp1r6_clma_pair_01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
 assert read(D/'CLMA_complete_admission_01/queue/completion.json')['status']=='all_registered_readonly_stages_accounted'
 assert read(D/'CLMA_complete_admission_01/pair/completion.json')['matched_complete_quality_pair']
 plan=read(C/'plan.json');runtime=Path(plan['release'])/'runtime';sys.path.insert(0,str(runtime))
 from full_route_graph_cache import FullRouteGraphCache
 from resource_opportunity_census import stream_trace,tree_data,release_scope,pin_screen
 from immutable_rr_audit_cache import KINDS
 case=Path(plan['inputs'][0]['workspace'])/'native';flow=case/'flow/resource_flow';state=flow/'initial';rd=Path(read(state/'completion.json')['run'])
 selection=flow/'repair/round_000/selection';owner=flow/'repair/round_000/owner_selection'
 base=read(selection/'completion.json');classes=read(owner/'classifications.json');assert base['multi_crossing_nets']==3 and base['candidate_scopes']==0
 targets={r['net'] for r in classes};assert len(targets)==3
 B.mkdir(exist_ok=False);sources=[Path(__file__).resolve(),selection/'completion.json',selection/'candidates.json',owner/'classifications.json',state/'completion.json',state/'endpoint_vector.json',rd/'manifest.json',runtime/'resource_opportunity_census.py',runtime/'current_crossing_share_selector_v2.py']
 write(B/'registration.json',dict(source_sha256={str(p):sha(p) for p in sources},targets=sorted(targets),reason='Explain all three existing positive-excess nets behind zero eligible initial scopes; exact frozen helper logic, no rule/threshold changes or new queries.'))
 lock=(D/'critical_scope_runner.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);start=time.monotonic()
 manifest=read(rd/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);cache=FullRouteGraphCache(graph,flow/'full_graph_cache');g=cache.g
 v=read(state/'endpoint_vector.json');pins=collections.defaultdict(dict)
 for line in (rd/'native_sta_frontier.jsonl').open():
  r=json.loads(line)
  if r.get('type')=='pin' and r['net'] in targets and not r['driver'] and r['route_tree_present']:pins[r['net']][r['pin']]=dict(slack_s=r['setup_slack_s'],criticality=r['setup_criticality_raw'],ignored=r['ignored'],**{'global':r['global']})
 rows=[]
 for rec in stream_trace(rd/'routed.route'):
  if rec['net'] not in targets:continue
  local={}
  def metadata(n):
   if n not in local:
    r=g.nodes[n];direction,_=map(int,cache.extra[n]);local[n]=dict(kind=KINDS[int(r[1])],low=tuple(map(int,r[2:5])),high=tuple(map(int,r[5:8])),direction=cache.meta['directions'][direction])
   return local[n]
  tree=tree_data(rec['trace'],metadata);groups=collections.defaultdict(set)
  for node,e in tree['crossing'].items():groups[e['resource_kind'],e['resource']].update(tree['descendants'][node])
  seen=set();scopes=[]
  for _,sinkset in sorted(groups.items()):
   key=tuple(sorted(sinkset))
   if key in seen:continue
   seen.add(key);screen=pin_screen(sinkset,pins[rec['net']],v['metrics']['least_slack_s'],base['minimum_margin_s']);released=release_scope(tree,sinkset,metadata);freed=len(released['released_SB'])+len(released['released_CB']);kept=sorted((tree['SB']-set(released['released_SB']))|(tree['CB']-set(released['released_CB'])))
   eligible=bool(screen['eligible'] and freed and kept);assert not eligible
   scopes.append(dict(pins=list(key),screen=screen,released_SB=released['released_SB'],released_CB=released['released_CB'],retained_crossing_sources=kept,freed_crossings=freed,eligible=eligible,rejection='STA_or_pin_screen' if not screen['eligible'] else 'no_freed_crossing' if not freed else 'no_retained_crossing_alternative'))
  rows.append(dict(net=rec['net'],name=rec['name'],SB=sorted(tree['SB']),CB=sorted(tree['CB']),terminal_cut_reference=tree['layer_cut_reference'],scopes=scopes,owner=next(r for r in classes if r['net']==rec['net'])))
 assert {r['net'] for r in rows}==targets
 write(B/'rows.json',rows)
 write(B/'completion.json',dict(passed=True,actual_redundant_nets=3,eligible_shared_domain_scopes=0,scope_rejection_counts=dict(collections.Counter(s['rejection'] for r in rows for s in r['scopes'])),new_native_or_STA_calls=0,complete_readonly_seconds=time.monotonic()-start,source_sha256={str(p):sha(p) for p in sources},artifact_sha256={'rows.json':sha(B/'rows.json')},qualification='Retrospective diagnosis on the actual admitted native initial root; original screening and domain requirements unchanged. Not a new confirmation or proof of global infeasibility; no excluded branch was executed.'))
 print(read(B/'completion.json'))
if __name__=='__main__':main()
