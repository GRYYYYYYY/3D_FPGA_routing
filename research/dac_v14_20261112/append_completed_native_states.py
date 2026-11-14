#!/usr/bin/env python3
"""Append complete native candidate states without waiting for a whole live batch."""
import argparse,collections,copy,csv,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir,input_identity,native_config
from pareto_archive_dimensions import annotate

p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();started=time.monotonic()
parent=a.parent.resolve();batch=a.batch.resolve();out=a.output.resolve();out.mkdir(exist_ok=False)
pc=read(parent/'completion.json');assert pc['passed'] and all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
points=read(parent/'points.json');reg=read(batch/'registration.json')
bound={str(p):sha(p) for p in [Path(__file__).resolve(),D/'pareto_archive_dimensions.py',parent/'completion.json',parent/'points.json',batch/'registration.json']}
original=copy.deepcopy(points);annotate(points)
for old,new in zip(original,points):
 for k in ['quality_status','quality_dominated_by','matched_time_dominated_by','candidate_retention','archive_retained']:assert old[k]==new[k],(old['id'],k)
added=[];pending=[]
for name,role in reg['roles'].items():
 state=batch/(name+'_evaluation');decision=batch/(name+'_decisions.json');audit=batch/(name+'_audit/analysis.json')
 if not (state/'completion.json').exists() or not decision.exists():pending.append(name);continue
 c=read(state/'completion.json');assert c['passed'];run=run_dir(state);ident=str(run.relative_to(D))
 if any(x['id']==ident for x in points):continue
 source=Path(role['source']);assert input_identity(source)==input_identity(run) and native_config(source)==native_config(run)
 origin=next(x for x in points if x.get('state')==role['state']);point=copy.deepcopy(origin)
 m=read(run/'manifest.json');assert m['status']=='completed' and m['metrics']['native_full_check_passed']
 for n in ['routed.route','packed.net','placed.place']:assert sha(run/n)==m['outputs'][n]['sha256']
 for path,record in m['shared_inputs'].items():assert sha(path)==record['sha256']
 pa=read(run/'independent_audit.json');assert pa['audit']['passed'];physical=pa['physical_metrics'];v=read(state/'endpoint_vector.json')
 assert v['constraints_sha256']==read(Path(role['state'])/'endpoint_vector.json')['constraints_sha256']
 d=read(decision);tx=read(audit);assert tx['passed'] and sha(tx['candidate_route'])==tx['candidate_sha256'] and route_body(tx['candidate_route'])==route_body(run/'routed.route')
 cpd=v['cpd_s']*1e9;cmd=m['command']
 point.update(id=ident,arm=role['baseline']+'_'+role['scope']+'_'+role['objective'],batch=batch.name,state=str(state),run_manifest=str(run/'manifest.json'),binary_sha256=sha(cmd[0]),
  route_sha256=sha(run/'routed.route'),route_body_sha256=route_body(run/'routed.route'),command=cmd,environment=m.get('environment'),
  CPD_ns=cpd,CPD_interval_ns=[cpd,cpd],CPD_precision='full native endpoint-vector seconds converted to ns',
  wirelength=physical['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=physical['sb_pairs_used'],CB_sources=physical['cb_crossing_output_sources_used'],SB_net_occupancy=physical['sb_pair_net_occupancy'],CB_net_occupancy=physical['cb_crossing_output_source_net_occupancy'],
  complete_single_configuration_seconds=None,analysis_only_native_seconds=m['wall_seconds'],timing_cohort=None,observation_workflow=c['timing'],shared_research_workflow=None,
  native_repair_core_seconds=tx['native_transaction_seconds'],audit_provenance=str(run/'independent_audit.json'),acceptance={k:r['accepted'] for k,r in d.items()},
  unknowns=['Full standalone algorithm time; live shared-batch total not yet terminal and is not configuration runtime'])
 points.append(point);added.append(ident)
 for path in [state/'completion.json',state/'endpoint_vector.json',run/'manifest.json',run/'independent_audit.json',decision,audit]:bound[str(path)]=sha(path)
assert added,'No new completed candidate states; do not create an empty archive revision'
annotate(points);write(out/'points.json',points)
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:p[k] for k in fields} for p in points)
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=added,pending_roles=pending,quality_counts=dict(collections.Counter(p['quality_status'] for p in points)),retention_counts=dict(collections.Counter(p['candidate_retention'] for p in points)),
 source_sha256=bound,artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv']},native_calls=0,complete_process_seconds=time.monotonic()-started,
 qualification='All appended states have complete native FULL/STA and independent physical audit. Batch remains live; pending/failed roles cannot supply a point. Observation-level time ranking is not confirmation configuration selection. Original records preserved.'))
print(dict(records=len(points),added=added,pending=len(pending)),flush=True)
