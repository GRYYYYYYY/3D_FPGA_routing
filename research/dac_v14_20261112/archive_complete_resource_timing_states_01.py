"""Archive real sealed timing states after complete resource menus, including the native control."""
import collections
import copy
import csv
from pathlib import Path
import time
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from native_problem_identity import problem_identity
from endpoint_timing_policy_streaming_v2 import compare
from pareto_archive_dimensions import annotate,dominates

t=time.monotonic();parent=D/'multiobjective_low_resource_timing_03'
out=D/'multiobjective_complete_resource_timing_01';out.mkdir(exist_ok=False)
pc=read(parent/'completion.json');assert pc['passed']
assert all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
points=read(parent/'points.json')
origin=next(p for p in points if (p.get('state') or '').endswith('native_extra_opportunity_bnn_01/A0_observation'))
expected=problem_identity(run_dir(Path(origin['state'])))
files=[Path(__file__).resolve(),parent/'completion.json',parent/'points.json',D/'pareto_archive_dimensions.py']
added=[];proofs={};vectors={}
for label,resource_name in [('native','bnn_A0_native_only_K8'),('paired','bnn_A0_feedback_K8')]:
    actor=D/'completed_resource_timing_dev_01'/label
    resource=D/'fused_resource_development_01'/resource_name
    rc=read(resource/'completion.json');assert rc['passed']
    assert read(resource/'evaluation_context/input_seal.json')['passed']
    steps=read(actor/'steps.json');assert len(steps)==3
    step=steps[-1];assert step['accepted'] and step['policy_accepted']
    state=Path(step['evaluation']);c=read(state/'completion.json')
    assert c['passed'] and read(state/'input_seal.json')['passed']
    rd=run_dir(state);m=read(rd/'manifest.json');assert m['metrics']['native_full_check_passed']
    assert problem_identity(rd)==expected
    for n in ['packed.net','placed.place','routed.route']:assert sha(rd/n)==m['outputs'][n]['sha256']
    audit=read(rd/'independent_audit.json');assert audit['audit']['passed']
    axes=audit['physical_metrics'];v=read(state/'endpoint_vector.json');vectors[label]=v
    resources=dict(wirelength=axes['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=axes['sb_pairs_used'],CB_sources=axes['cb_crossing_output_sources_used'])
    assert resources==step['after_resources'] and v['cpd_s']==step['after_CPD_s']
    reg=read(actor/'registration.json');caps=reg['fixed_absolute_limits']
    assert all(resources[k]<=caps[k] for k in caps)
    assert v['constraints_sha256']==read(Path(origin['state'])/'endpoint_vector.json')['constraints_sha256']
    policy=read(state.parent.parent/'policy_decisions.json');assert policy['timing_under_resources']['accepted']
    terminal=read(actor/'completion.json') if (actor/'completion.json').exists() else None
    if terminal:assert terminal['passed'] and terminal['final_state']==str(state)
    ident=str(rd.relative_to(D));assert not any(p['id']==ident for p in points)
    row={k:copy.deepcopy(origin[k]) for k in ['circuit','physical_identity','quality_cohort','initial_routing_convergence']}
    row.update(id=ident,arm='complete_resource_'+label+'_then_current_STA_native',circuit=origin['circuit'],
        batch='completed_resource_timing_dev_01',batch_full_path=str(actor.parent),state=str(state),status='legal',
        source_state=step['before_state'],record_kind='input_sealed_actual_timing_state_after_complete_resource_menu',
        run_manifest=str(rd/'manifest.json'),binary_sha256=sha(m['command'][0]),final_STA_binary_sha256=sha(m['command'][0]),
        route_sha256=sha(rd/'routed.route'),route_body_sha256=route_body(rd/'routed.route'),command=m['command'],environment=m.get('environment'),
        convergence='complete_own_current_resource_menu_then_three_strict_current_STA_accepts',
        opportunity='Same strong A0 root/current selectors/native timing menu; each branch retains its completed resource envelope. Paired resource arm has additional constrained searches, fully accounted; not equal compute.',
        resource_phase_prefix_is_not_parent_final=False,resource_phase_parent_sealed=True,resource_phase_final_accepts=rc['accepted_steps'],
        timing_phase_complete=terminal is not None,CPD_ns=v['cpd_s']*1e9,CPD_interval_ns=[v['cpd_s']*1e9]*2,
        CPD_precision='Full-precision native endpoint vector',**resources,
        SB_net_occupancy=axes['sb_pair_net_occupancy'],CB_net_occupancy=axes['cb_crossing_output_source_net_occupancy'],
        iterations=None,initial_router_iterations=origin.get('iterations'),complete_single_configuration_seconds=None,timing_cohort=None,
        analysis_only_native_seconds=c['timing']['native_process_seconds'],observation_workflow=c['timing'],shared_research_workflow=None,
        imported_resource_phase_seconds=rc['complete_imported_algorithm_workflow_seconds'],
        imported_timing_phase_seconds=None if terminal is None else terminal['complete_imported_state_workflow_seconds'],
        audit_provenance=str(rd/'independent_audit.json'),input_seal=str(state/'input_seal.json'),
        acceptance=policy,fixed_resource_limits=caps,source_constraints_sha256=v['constraints_sha256'],
        unknowns=['Complete cold single-configuration route-plus-repair time; interrupted paired trajectory final closure pending. No historical, core, shared or recovery times spliced.'])
    points.append(row);added.append(ident)
    proofs[label]=dict(point=ident,CPD_ns=row['CPD_ns'],resources=resources,
        timing_trajectory_terminal=terminal is not None,imported_timing_seconds=row['imported_timing_phase_seconds'],
        imported_resource_seconds=row['imported_resource_phase_seconds'])
    files += [actor/'registration.json',actor/'steps.json',resource/'completion.json',resource/'evaluation_context/input_seal.json',
        state/'completion.json',state/'input_seal.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'independent_audit.json',state.parent.parent/'policy_decisions.json']
annotate(points)
for label,p in proofs.items():
    row=next(x for x in points if x['id']==p['point']);p['quality_status']=row['quality_status']
    p['strong_baseline_dominators']=[x['id'] for x in points if x['quality_cohort']==row['quality_cohort'] and x['arm'] in ['A0','R1'] and dominates(x,row)]
delta=compare(vectors['native'],vectors['paired'])
write(out/'points.json',points)
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:p.get(k) for k in fields} for p in points)
summary=dict(passed=True,states=proofs,paired_minus_native_resources={k:proofs['paired']['resources'][k]-proofs['native']['resources'][k] for k in ['wirelength','SB_pairs','CB_sources']},
    full_endpoint_comparison_native_to_paired=delta,complete_single_configuration_seconds=None,
    qualification='Both real actual states are independently legal/FULL/STA/input sealed at the same CPD after complete automatic resource endpoints. Native phase is terminal; paired recovery still determines its final menu closure. Different resource limits are explicit; not equal-compute, timing-only frontier or complete cold runtime evidence.')
write(out/'composition_summary.json',summary)
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=added,native_calls=0,route_calls=0,
    quality_counts=dict(collections.Counter(p['quality_status'] for p in points)),retention_counts=dict(collections.Counter(p['candidate_retention'] for p in points)),
    source_sha256={str(p):sha(p) for p in files},artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','composition_summary.json']},
    complete_extraction_seconds=time.monotonic()-t,complete_single_configuration_algorithm_seconds=None))
print(dict(records=len(points),states=proofs,resource_delta=summary['paired_minus_native_resources'],setup_improved=delta['setup_improved'],setup_regressed=delta['setup_regressed']),flush=True)
