#!/usr/bin/env python3
"""Register paired native transactions from sealed current-state opportunity screens."""
import collections,copy,json,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from coordinated_repair_tree import from_trace,downstream_pins,prune_sinks,nodes
from immutable_rr_audit_cache import GraphAuditCache
import sys
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

started=time.monotonic();b=D/'bnn_release_joint_dev_01';b.mkdir(exist_ok=False)
screen=D/'bnn_slack_release_screen_01';protected=read(screen/'protected_critical/completion.json')
capacity=read(screen/'Tf_capacity/analysis.json');baselines=read(D/'bnn_baseline_capacity_screens_01/completion.json')
files=[Path(__file__).resolve(),D/'run_registered_native_transactions.py',screen/'protected_critical/completion.json',screen/'Tf_capacity/analysis.json',
       D/'bnn_baseline_capacity_screens_01/completion.json',D/'bnn_baseline_capacity_screens_01/R1/analysis.json',
       D/'current_sta_arrival_cone.py',D/'coordinated_repair_tree.py',D/'native_objective_stage_01/binding.json',
       D/'run_native_objective_state_analysis.py',D/'audit_native_objective_cached.py',D/'run_timing_cone_state_analysis_v2.py',
       D/'multiobjective_acceptance_v2.py',D/'endpoint_timing_policy.py']
for evidence in [protected,capacity,baselines]:
 assert evidence['passed'] and all(sha(p)==h for p,h in evidence['source_sha256'].items())
observations=read(D/'timing_cone_bnn_dev_02/completion.json');roles={};skipped=[];selection_receipts={}
for arm in ['Tf','R1']:
 state=Path(observations['roles'][arm]['state']);source=run_dir(state)
 cone=read(Path(observations['roles'][arm]['cone']));assert cone['passed']
 current_targets={(p['net'],p['pin']) for p in cone['routed_connections']}
 q=capacity if arm=='Tf' else read(D/'bnn_baseline_capacity_screens_01/R1/analysis.json')
 assert q['passed'] and all(sha(p)==h for p,h in q['source_sha256'].items())
 direct={(r['net'],r['pin']) for r in q['results'] if r['rr_capacity_feasible'] and r['improvement_ns']>1e-6}
 gaps=[r for r in protected['rows'] if r['gain_ns']>1e-6] if arm=='Tf' else []
 targets=sorted(direct|{tuple(r['target']) for r in gaps});assert set(targets)<=current_targets
 sta={}
 for line in (source/'native_sta_frontier.jsonl').open():
  p=json.loads(line)
  if p.get('type')=='pin' and not p['driver']:sta[p['net'],p['pin']]=p
 blockers=collections.defaultdict(set);scarce=collections.defaultdict(set)
 if gaps:
  manifest=read(source/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
  cache=GraphAuditCache(graph,D/'rr_audit_cache_bnn_01');traces=read_trace(source/'routed.route')
  owners=read(screen/'Tf_capacity/occupancy_owners.json')
  for r in gaps:
   for c in r['conflicts']:
    assert not c['protected_owners'] and c['required_releases']==1
    for net in c['releasable_noncritical_owners']:scarce[net].add(c['node'])
  for net,resources in scarce.items():
   tree=from_trace(traces[net]['trace'],cache.switches)
   for node in resources:blockers[net].update(downstream_pins(tree,node))
   assert blockers[net] and not (resources & nodes(prune_sinks(tree,blockers[net]))),'Pruning fails to release proposed resource'
   for pin in blockers[net]:
    p=sta[net,pin];assert not p['ignored'] and not p['global']
    assert p['setup_slack_s']>cone['worst_slack_s'],'Owner lacks screening slack'
 selection_receipts[arm]=dict(state=str(state),direct_targets=sorted(direct),protected_relaxed_targets=[r['target'] for r in gaps],
  selected_targets=targets,blocker_pins={str(n):sorted(pins) for n,pins in blockers.items()},scarce_nodes={str(n):sorted(ns) for n,ns in scarce.items()},
  rule='All strictly positive current-cone direct opportunities, plus protected-critical relaxed opportunities with positive owner slack. No manually selected path or historical best circuit configuration.')
 sourcefiles=[state/'completion.json',state/'endpoint_vector.json',source/'routed.route',source/'packed.net',source/'placed.place',source/'native_sta_frontier.jsonl',Path(observations['roles'][arm]['cone'])]
 files+=sourcefiles
 physical=read(source/'independent_audit.json')['physical_metrics'];v=read(state/'endpoint_vector.json')
 budget=dict(CPD_s=v['cpd_s'],wirelength=physical['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=physical['sb_pairs_used'],CB_sources=physical['cb_crossing_output_sources_used'])
 scopes=['combined','target_only','release_only'] if blockers else ['target_only']
 for scope in scopes:
  removed=collections.defaultdict(set)
  if scope!='release_only':
   for n,p in targets:removed[n].add(p)
  if scope!='target_only':
   for n,pins in blockers.items():removed[n].update(pins)
  ordered=sorted((x for x in targets if scope!='release_only'),key=lambda x:(sta[x]['setup_slack_s'],x))
  ordered += [(n,p) for n in sorted(removed) for p in sorted(removed[n]) if (n,p) not in ordered]
  assert len(ordered)==sum(map(len,removed.values())) and len(set(ordered))==len(ordered)
  request=b/f'{arm}_{scope}.txt'
  with request.open('w') as f:
   f.write(str(len(removed))+'\n')
   for n in sorted(removed):f.write(' '.join(map(str,[n,len(removed[n]),*sorted(removed[n])]))+'\n')
   f.write('0\n'+str(len(ordered))+'\n')
   for n,p in ordered:f.write(f"{n} {p} {sta[n,p]['setup_criticality_raw']:.17g}\n")
  files.append(request)
  for objective in ['weighted_soft','physical_capacity']:
   name=f'{arm}_{scope}_{objective}'
   roles[name]=dict(state=str(state),source=str(source),request=str(request),objective=objective,fixed_target_paths=False,
    targets=targets if scope!='release_only' else [],removed_pins={str(n):sorted(ps) for n,ps in removed.items()},scope=scope,baseline=arm,
    queries=[dict(net=n,pin=p,slack_s=sta[n,p]['setup_slack_s'],raw_criticality=sta[n,p]['setup_criticality_raw']) for n,p in ordered],
    original_budget=budget,source_sha256={str(p):sha(p) for p in sourcefiles+[request]})
# The same automatic direct-gain rule selects no A0 transaction. This is an
# explicit stage result, not a claim that A0 lacks resource/near-critical potential.
skipped.append(dict(baseline='A0',reason='No positive current-cone capacity gain in matched direct screen',queries=baselines['roles']['A0']['targets'],native_transactions=0))
write(b/'registration.json',dict(status='registered_before_native',roles=roles,selection=selection_receipts,skipped_stages=skipped,
 question='Can slack-owner branch release plus coordinated max-arrival-branch repair improve timing/resources, beyond equal-opportunity native repair and each isolated component?',
 accepted_state_policy='Four independent policy pointers per arm. Fixed original budgets; full candidate legality/FULLSTA before commit. New targets computed in each accepted state. No intermediate state accepted.',
 budget_rules=dict(timing_under_resources='CPD strictly decreases; wire<=ceil1.05initial,SB<=initial+1,CB<=initial+4',resources_under_timing='CPD<=1.01initial; wire strictly decreases and <=initial;SB<=initial+1,CB<=initial+4'),
 controls='Identical requests/objectives paired within each scope. All native paths free. Whole transaction updates occupancy after each route; if any failed, full rollback. Scope ablations all start from same pristine state. R1 receives its own current-state opportunities.',
 limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
 qualification='Development batch, not confirmation or research stop matrix. Pin slack screens releases but never substitutes for final STA. Soft native search can retry congestion pressure; attempts and failures remain counted.',
 source_sha256={str(p):sha(p) for p in files},preparation_seconds=time.monotonic()-started))
print({name:len(r['queries']) for name,r in roles.items()},flush=True)
