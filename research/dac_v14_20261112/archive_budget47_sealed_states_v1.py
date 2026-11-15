"""Retain actual sealed candidates while explicitly snapshotting a live trajectory."""
import argparse,collections,copy,csv,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from native_problem_identity import problem_identity
from multiobjective_acceptance_v2 import decide
from endpoint_timing_policy_streaming_v2 import compare
from pareto_archive_dimensions import annotate
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
parent=a.parent.resolve();out=a.output.resolve();out.mkdir(exist_ok=False);start=time.monotonic()
root=D/'budget47_current_timing_composition_01';plan=read(root/'plan.json');limits=read(root/'absolute_limits.json');pc=read(parent/'completion.json');assert pc['passed']
assert all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
points=read(parent/'points.json');files=[Path(__file__).resolve(),parent/'completion.json',parent/'points.json',root/'plan.json',root/'absolute_limits.json',D/'pareto_archive_dimensions.py',D/'multiobjective_acceptance_v2.py'];rows=[];added=[];failures=[]
hashed={}
def checked(f):
 f=Path(f).resolve()
 if str(f) not in hashed:hashed[str(f)]=sha(f)
 return hashed[str(f)]
def bindings(receipt):
 for f,h in receipt.get('source_sha256',{}).items():assert checked(f)==h,f

def resources(state):
 audit=read(run_dir(state)/'independent_audit.json');assert audit['audit']['passed'];m=audit['physical_metrics']
 return dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=m['sb_pairs_used'],CB_sources=m['cb_crossing_output_sources_used'])
for arm in plan['fixed_order']:
 actor=root/arm/'timing'
 if not (actor/'attempts.json').exists():continue
 observed=out/(arm+'_attempts_snapshot.json');observed.write_bytes((actor/'attempts.json').read_bytes());attempts=read(observed);reg=read(actor/'registration.json');bindings(reg)
 initial=Path(reg['initial_state']);current=initial;source=Path(plan['cases'][arm]);origin=next(x for x in points if x.get('state')==str(source))
 assert reg['policy']=='timing_under_resources' and reg['budget_mode']=='explicit_absolute' and reg['fixed_absolute_limits']==limits and reg['fraction']==.9
 initialv=read(initial/'endpoint_vector.json');sourcev=read(source/'endpoint_vector.json')
 assert all(initialv[k]==sourcev[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
 assert route_body(run_dir(initial)/'routed.route')==route_body(run_dir(source)/'routed.route')
 files += [observed,actor/'registration.json',initial/'completion.json',initial/'endpoint_vector.json',source/'endpoint_vector.json']
 for record in attempts:
  before=Path(record['before_state']);assert before==current
  if not record.get('evaluation'):
   assert not record['accepted'];failures.append(dict(arm=arm,record=record));continue
  state=Path(record['evaluation']);tx=state.parent;closed=read(tx/'completion.json');assert closed['passed'];bindings(closed)
  role=closed['roles']['current_group'];assert role['status']=='legal_evaluated' and role['evaluation']==str(state)
  assert Path(read(tx/'registration.json')['roles']['current_group']['state'])==before
  c=read(state/'completion.json');assert c['passed'];seal=read(state/'input_seal.json');assert seal['passed']
  for f,v in seal['inputs'].items():assert checked(f)==v['sha256']
  rd=run_dir(state);m=read(rd/'manifest.json');assert m['metrics']['native_full_check_passed']
  for n in ['packed.net','placed.place','routed.route']:assert checked(rd/n)==m['outputs'][n]['sha256']
  assert problem_identity(rd)==problem_identity(run_dir(source))==read(tx/'registration.json')['problem_identity']
  scope=read(tx/'current_group_audit/analysis.json');assert scope['passed'];bindings(scope)
  assert checked(scope['candidate_route'])==scope['candidate_sha256']
  bv,av=read(before/'endpoint_vector.json'),read(state/'endpoint_vector.json');br,ar=resources(before),resources(state)
  assert ar==role['resources']==record['after_resources'] and av['cpd_s']==role['cpd_s']==record['after_CPD_s']
  decision=decide('timing_under_resources',bv,av,br,ar,cpd_limit_s=initialv['cpd_s'],resource_limits=limits,native_valid=True,transaction_complete=True,resource_objectives=('wirelength',))
  assert decision['accepted']==record['policy_accepted']
  assert record['accepted']==bool(record['policy_accepted'] and not record['already_visited'])
  stored=read(state.parent.parent/'policy_decisions.json')['timing_under_resources'];assert stored==decision
  delta=compare(bv,av);assert delta['compatible'];ident=str(rd.relative_to(D))
  if any(x['id']==ident for x in points):
   if record['accepted']:current=state
   continue
  physical=read(rd/'independent_audit.json')['physical_metrics']
  row={k:copy.deepcopy(origin[k]) for k in ['circuit','physical_identity','quality_cohort','initial_routing_convergence']}
  row.update(id=ident,arm='budget47_'+arm+'_current_STA',batch='budget47_current_timing_composition_01',batch_full_path=str(root),state=str(state),source_state=str(before),status='legal',record_kind='sealed_intermediate_candidate_in_live_local_timing_operator',actor_final_selected=False,actor_terminal_claim=False,transition_committed=record['accepted'],policy_accepted=record['policy_accepted'],actual_transition_policy='timing_under_resources',run_manifest=str(rd/'manifest.json'),binary_sha256=checked(m['command'][0]),final_STA_binary_sha256=checked(m['command'][0]),route_sha256=checked(rd/'routed.route'),route_body_sha256=route_body(rd/'routed.route'),command=m['command'],environment=m.get('environment'),convergence='own_current_menu_still_live_at_attempt_snapshot',opportunity='Same-source resource-stage local alternatives followed by common v5/fraction0.9 timing menu under original absolute caps. Not whole pristine-native trajectory or a one-factor causal scope/domain isolation.',CPD_ns=av['cpd_s']*1e9,CPD_interval_ns=[av['cpd_s']*1e9]*2,CPD_precision='Full-precision native endpoint vector',**ar,SB_net_occupancy=physical['sb_pair_net_occupancy'],CB_net_occupancy=physical['cb_crossing_output_source_net_occupancy'],complete_single_configuration_seconds=None,timing_cohort=None,sealed_transaction_orchestrator_seconds=closed['complete_orchestrator_seconds'],transaction_cost_scope='Actual transaction only; excludes source resource-prefix creation, new source reobservation, prior/successor attempts and initial routing. No complete algorithm time.',audit_provenance=str(rd/'independent_audit.json'),input_seal=str(state/'input_seal.json'),source_constraints_sha256=av['constraints_sha256'],fixed_resource_limits=limits)
  summary=dict(arm=arm,point=ident,state=str(state),transition_committed=record['accepted'],CPD_ns=row['CPD_ns'],resources=ar,setup_improved=delta['setup_improved'],setup_regressed=delta['setup_regressed'],hold_violation_regressions=delta['hold_violation_regressions'],transaction_orchestrator_seconds=closed['complete_orchestrator_seconds'],whole_trajectory_terminal=False)
  points.append(row);rows.append(summary);added.append(ident)
  files += [tx/'completion.json',tx/'registration.json',tx/'current_group_audit/analysis.json',state/'completion.json',state/'input_seal.json',state/'endpoint_vector.json',before/'endpoint_vector.json',rd/'manifest.json',rd/'independent_audit.json',state.parent.parent/'policy_decisions.json']
  if record['accepted']:current=state
annotate(points)
for r in rows:r['quality_status']=next(x['quality_status'] for x in points if x['id']==r['point'])
write(out/'points.json',points);write(out/'sealed_timing_summaries.json',dict(passed=True,states=rows,nonlegal_outcomes=failures,native_calls_new=0,whole_trajectory_terminal_claim=False,qualification='Snapshot of completed actual transactions only; first-admissible transition acceptance independently recomputed. Live attempts copied before validation, never bound as immutable live files. Every observed legal accepted or rejected candidate retained, every recorded nonlegal outcome separate. Parent archive retained in full. No full algorithm cost or completed paired-arm comparison.'))
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','record_kind','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:x.get(k) for k in fields} for x in points)
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=added,native_calls=0,route_calls=0,complete_extraction_seconds=time.monotonic()-start,source_sha256={str(f):checked(f) for f in files},artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','sealed_timing_summaries.json']},whole_trajectory_terminal_claim=False))
print(dict(passed=True,records=len(points),states=rows),flush=True)
