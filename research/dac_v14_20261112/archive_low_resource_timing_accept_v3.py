#!/usr/bin/env python3
"""Extend the merged legal-state population with locally sealed composition states."""
import collections
import copy
import csv
from pathlib import Path
import time
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from native_problem_identity import problem_identity
from pareto_archive_dimensions import annotate,dominates

started=time.monotonic();parent=D/'multiobjective_low_resource_timing_02'
out=D/'multiobjective_low_resource_timing_03';out.mkdir(exist_ok=False)
pc=read(parent/'completion.json');assert pc['passed'] and all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
points=read(parent/'points.json');proof=read(D/'low_resource_timing_accept_03.json');assert proof['passed']
origin=next(p for p in points if (p.get('state') or '').endswith('native_extra_opportunity_bnn_01/A0_observation'))
anchor=Path(origin['state']);expected=problem_identity(run_dir(anchor))
resource_phase=D/'fused_resource_development_01/bnn_A0_feedback_K8'
assert read(resource_phase/'completion.json')['passed'] and read(resource_phase/'evaluation_context/input_seal.json')['passed']
states=[('strict_current_STA_native_repair_final',Path(proof['immutable_accepted_step']['evaluation']))]
files=[Path(__file__).resolve(),parent/'completion.json',parent/'points.json',D/'pareto_archive_dimensions.py',
       D/'low_resource_timing_accept_03.json',resource_phase/'completion.json',resource_phase/'evaluation_context/input_seal.json']
added=[]
for label,state in states:
    c=read(state/'completion.json');assert c['passed'] and read(state/'input_seal.json')['passed']
    rd=run_dir(state);m=read(rd/'manifest.json');assert m['metrics']['native_full_check_passed']
    assert problem_identity(rd)==expected
    for n in ['packed.net','placed.place','routed.route']:assert sha(rd/n)==m['outputs'][n]['sha256']
    audit=read(rd/'independent_audit.json');assert audit['audit']['passed'];axes=audit['physical_metrics'];vector=read(state/'endpoint_vector.json')
    assert vector['constraints_sha256']==read(anchor/'endpoint_vector.json')['constraints_sha256']
    ident=str(rd.relative_to(D));assert not any(p['id']==ident for p in points)
    row={key:copy.deepcopy(origin[key]) for key in ['circuit','physical_identity','quality_cohort','initial_routing_convergence']}
    cpd=vector['cpd_s']*1e9
    row.update(id=ident,arm=label,batch='low_resource_dual_timing_02',batch_full_path=str(D/'low_resource_dual_timing_02'),
        state=str(state),status='legal',source_state=proof['immutable_accepted_step']['before_state'] if label.startswith('strict') else str(D/'fused_resource_development_01/bnn_A0_feedback_K8/round_006/candidate_00/reuse_on_evaluation'),
        record_kind='input_sealed_native_composition_diagnostic_observation',run_manifest=str(rd/'manifest.json'),
        binary_sha256=sha(m['command'][0]),final_STA_binary_sha256=sha(m['command'][0]),route_sha256=sha(rd/'routed.route'),
        route_body_sha256=route_body(rd/'routed.route'),command=m['command'],environment=m.get('environment'),
        convergence='registered_seven_accept_resource_prefix_then_'+('three_native_timing_transactions' if label.startswith('strict') else 'analysis_only_observation'),
        opportunity='Explicit registered resource-prefix composition diagnostic; fresh current-STA selector, not final whole-algorithm confirmation',
        resource_phase_prefix_accepts=7,resource_phase_parent_sealed=True,resource_phase_parent_final_accepts=9,
        resource_phase_prefix_is_not_parent_final=True,timing_phase_complete=True,
        CPD_ns=cpd,CPD_interval_ns=[cpd,cpd],CPD_precision='Full-precision native endpoint vector',
        wirelength=axes['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=axes['sb_pairs_used'],CB_sources=axes['cb_crossing_output_sources_used'],
        SB_net_occupancy=axes['sb_pair_net_occupancy'],CB_net_occupancy=axes['cb_crossing_output_source_net_occupancy'],
        iterations=None,initial_router_iterations=origin.get('iterations'),
        complete_single_configuration_seconds=None,timing_cohort=None,
        analysis_only_native_seconds=c['timing']['native_process_seconds'],observation_workflow=c['timing'],shared_research_workflow=None,
        native_repair_core_seconds=proof['native_transaction_seconds'] if label.startswith('strict') else None,
        audit_provenance=str(rd/'independent_audit.json'),input_seal=str(state/'input_seal.json'),
        acceptance=proof['policy_acceptance'] if label.startswith('strict') else None,
        fixed_resource_limits=proof['fixed_absolute_limits'],source_constraints_sha256=vector['constraints_sha256'],
        unknowns=['Complete cold single-configuration routing-plus-repair time; full own-current timing and secondary trajectories. No historical/native core/shared/recovery time is borrowed.'])
    points.append(row);added.append(ident)
    files.extend([state/'completion.json',state/'input_seal.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'independent_audit.json'])
annotate(points);write(out/'points.json',points)
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:p.get(k) for k in fields} for p in points)
latest=next(p for p in points if p['id']==added[-1])
strong=[p for p in points if p['quality_cohort']==latest['quality_cohort'] and p['arm'] in ['A0','R1']]
summary=dict(passed=True,point=latest['id'],CPD_ns=latest['CPD_ns'],wirelength=latest['wirelength'],SB_pairs=latest['SB_pairs'],CB_sources=latest['CB_sources'],
    quality_status=latest['quality_status'],strong_baseline_dominators=[p['id'] for p in strong if dominates(p,latest)],
    strong_baselines_quality_dominated_by_this_observation=[p['id'] for p in strong if dominates(latest,p)],
    complete_single_configuration_seconds=None,
    qualification='Legal observation quality projection with strong baselines, not equal-compute/five-dimensional/configuration superiority. The registered resource prefix differs from the final43SB endpoint and is not retrospectively replaced.')
write(out/'composition_summary.json',summary)
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=added,
    quality_counts=dict(collections.Counter(p['quality_status'] for p in points)),
    retention_counts=dict(collections.Counter(p['candidate_retention'] for p in points)),
    native_calls=0,route_calls=0,complete_extraction_seconds=time.monotonic()-started,
    source_sha256={str(p):sha(p) for p in files},artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','composition_summary.json']},
    qualification='The third locally FULL/STA/independent-physical/input-sealed timing accept added after ancestor resource actor sealed. Branches and imported timings remain distinct, all old records preserved. No complete-route algorithm time, final timing-trajectory score or global optimum inferred.'))
print(dict(records=len(points),added=added,summary=summary),flush=True)
