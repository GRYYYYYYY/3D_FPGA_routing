#!/usr/bin/env python3
"""Archive native resource-domain observations with explicit shared design requirements."""
import argparse,collections,copy,csv,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha as raw_sha,route_body
from run_native_scope_policy_v4 import run_dir,input_identity,native_config
from pareto_archive_dimensions import annotate
_digests={}
def sha(path):
 path=Path(path).resolve();st=path.stat();key=(str(path),st.st_size,st.st_mtime_ns,st.st_ino)
 if key not in _digests:_digests[key]=raw_sha(path)
 return _digests[key]
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--batch',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();started=time.monotonic();parent=a.parent.resolve();batches=[p.resolve() for p in a.batch];out=a.output.resolve();out.mkdir(exist_ok=False)
pc=read(parent/'completion.json');assert pc['passed'] and all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items());points=read(parent/'points.json');bound={str(p):sha(p) for p in [Path(__file__).resolve(),D/'pareto_archive_dimensions.py',parent/'completion.json',parent/'points.json']};added=[];updated=[];pending=[];terminal_nonlegal=[];shared=[]
def append_batch(batch):
 reg=read(batch/'registration.json');progress=read(batch/'progress.json');terminal=read(batch/'completion.json');assert terminal['passed']
 assert all(sha(path)==digest for path,digest in terminal['source_sha256'].items())
 bound.update({str(p):sha(p) for p in [batch/'registration.json',batch/'completion.json']})
 requirements=Path(reg['shared_design_requirements']).resolve() if reg.get('shared_design_requirements') else None
 if requirements:bound[str(requirements)]=sha(requirements)
 for name,role in reg['roles'].items():
  row=progress.get(name,{})
  if row.get('status')!='legal_evaluated':
   target=pending if row.get('status') in [None,'missing','running'] else terminal_nonlegal
   target.append(dict(batch=str(batch),role=name,status=row.get('status','missing')));continue
  state=Path(row['evaluation']).resolve();c=read(state/'completion.json');assert c['passed'];run=run_dir(state);decision=batch/(name+'_decisions.json');audit=batch/(name+'_audit/analysis.json');native=batch/name/'completion.json';assert read(native)['passed'];native_run=run_dir(batch/name);native_manifest=read(native_run/'manifest.json')
  source=Path(role['source']);assert input_identity(source)==input_identity(run) and native_config(source)==native_config(run)
  m=read(run/'manifest.json');assert m['status']=='completed' and m['metrics']['native_full_check_passed']
  for n in ['packed.net','placed.place','routed.route']:assert sha(run/n)==m['outputs'][n]['sha256']
  for path,record in m['shared_inputs'].items():assert sha(path)==record['sha256']
  pa=read(run/'independent_audit.json');assert pa['audit']['passed'];v=read(state/'endpoint_vector.json');assert v['constraints_sha256']==read(Path(role['state'])/'endpoint_vector.json')['constraints_sha256'];tx=read(audit);assert tx['passed'] and sha(tx['candidate_route'])==tx['candidate_sha256'] and route_body(tx['candidate_route'])==route_body(run/'routed.route')
  reused=bool(row.get('reused_FULL_STA'));ident=str(run.relative_to(D)) if not reused else str((batch/name).relative_to(D))+'/shared_evaluation_observation'
  existing=next((x for x in points if x['id']==ident),None)
  origin=next(x for x in points if x.get('state')==role['state']);point=copy.deepcopy(existing or origin);physical=pa['physical_metrics'];cpd=v['cpd_s']*1e9;d=read(decision)
  point.update(id=ident,arm=role.get('baseline',origin['arm'])+'_'+role['scope']+'_'+role['objective']+('_reserve_'+('on' if role['reservations_enabled'] else 'off') if 'reservations_enabled' in role else ''),batch=str(batch.relative_to(D)),batch_full_path=str(batch),state=str(state),source_state=role['state'],record_kind='native_configuration_observation_with_shared_STA' if reused else 'native_configuration_observation',
  run_manifest=str(run/'manifest.json'),binary_sha256=sha(m['command'][0]),final_STA_binary_sha256=sha(m['command'][0]),native_transaction_binary_sha256=sha(native_manifest['command'][0]),native_transaction_manifest=str(native_run/'manifest.json'),native_transaction_environment=native_manifest.get('environment'),native_parameters=dict(objective=role['objective'],fixed_target_paths=role['fixed_target_paths'],reservations_enabled=role.get('reservations_enabled'),order=role.get('order'),crossing_reuse_enabled=role.get('crossing_reuse_enabled'),crossing_domain=role.get('crossing_domain')),native_request=str(Path(role['request']).resolve()),native_request_sha256=sha(role['request']),native_objective=role['objective'],native_scope=role['scope'],native_role=name,
  initial_routing_convergence=origin.get('initial_routing_convergence',origin['convergence']),convergence='one_post_legal_native_transaction',opportunity='one native transaction from the explicitly recorded current source state',
  route_sha256=sha(run/'routed.route'),route_body_sha256=route_body(run/'routed.route'),command=m['command'],environment=m.get('environment'),CPD_ns=cpd,CPD_interval_ns=[cpd,cpd],CPD_precision='complete full-precision native endpoint vector',
  wirelength=physical['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=physical['sb_pairs_used'],CB_sources=physical['cb_crossing_output_sources_used'],SB_net_occupancy=physical['sb_pair_net_occupancy'],CB_net_occupancy=physical['cb_crossing_output_source_net_occupancy'],
  complete_single_configuration_seconds=None,timing_cohort=None,analysis_only_native_seconds=None if reused else m['wall_seconds'],observation_workflow=None if reused else c['timing'],reused_evaluation_source=str(state) if reused else None,reused_evaluation_creation_timing=c['timing'] if reused else None,shared_research_workflow=None,native_repair_core_seconds=tx['native_transaction_seconds'],audit_provenance=str(run/'independent_audit.json'),acceptance={k:r['accepted'] for k,r in d.items()},
  unknowns=['Complete single-configuration algorithm time and original routing/query construction cost. Shared FULLSTA creation belongs to its original observation, never copied as this configuration runtime.'])
  if 'crossing_reuse_enabled' in role:
   point['arm'] += '_reuse_'+('on' if role['crossing_reuse_enabled'] else 'off')
   domain_audit=batch/(name+'_domain_audit.json');assert read(domain_audit)['passed'];bound[str(domain_audit)]=sha(domain_audit);point['crossing_domain_audit']=str(domain_audit)
  if reg.get('resource_conditions'):
   point['registered_resource_conditions']=reg['resource_conditions']
  if requirements:
   point.update(shared_design_requirements=str(requirements),shared_design_requirements_sha256=sha(requirements),shared_design_requirement_values=read(requirements))
  if existing:points[points.index(existing)]=point;updated.append(ident)
  else:points.append(point);added.append(ident)
  if reused:shared.append(dict(native_role=name,record_id=ident,evaluation=str(state),native_request_sha256=point['native_request_sha256'],new_FULLSTA_calls=0,qualification='Separate native observation and code/config record with shared exact candidate quality; no borrowed timing or extra independent quality measurement.'))
  for path in [state/'completion.json',state/'endpoint_vector.json',run/'manifest.json',run/'independent_audit.json',decision,audit,native,native_run/'manifest.json',Path(role['request'])]:bound[str(path)]=sha(path)
for batch in batches:append_batch(batch)
assert added or updated
annotate(points);write(out/'points.json',points);write(out/'shared_evaluation_observations.json',shared)
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:p[k] for k in fields} for p in points)
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=added,metadata_updated=updated,pending_roles=pending,terminal_nonlegal_roles=terminal_nonlegal,shared_evaluation_observations=len(shared),quality_counts=dict(collections.Counter(p['quality_status'] for p in points)),retention_counts=dict(collections.Counter(p['candidate_retention'] for p in points)),source_sha256=bound,artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','shared_evaluation_observations.json']},native_calls=0,complete_process_seconds=time.monotonic()-started,
 qualification='Each native configuration has a separate observation, including those sharing an exact candidate FULLSTA. Initial router convergence and subsequent repair opportunity are separate. Shared observer time is never assigned to another configuration; missing complete time remains unknown. Quality-state reuse is not an independent experiment, a per-circuit history-best policy or whole-algorithm superiority.'))
print(dict(records=len(points),added=added,shared_observations=len(shared),pending=pending))
