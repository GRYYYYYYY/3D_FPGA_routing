#!/usr/bin/env python3
"""Archive actual seed-policy observations, never nominate them as a complete algorithm."""
import collections
import copy
import csv
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from pareto_archive_dimensions import annotate
from actual_route_tree_identity import tree_identity

started=time.monotonic()
parent=D/'multiobjective_archive_52'
out=D/'multiobjective_seed_order_diag_01'
out.mkdir(exist_ok=False)
pc=read(parent/'completion.json');assert pc['passed'] and all(sha(parent/name)==digest for name,digest in pc['artifact_sha256'].items())
points=read(parent/'points.json')
experiment=D/'repair_seed_order_eltwise_01'
c=read(experiment/'completion.json');assert c['passed'] and all(sha(path)==digest for path,digest in c['source_sha256'].items())
reg=read(experiment/'registration.json');assert all(sha(path)==digest for path,digest in reg['source_sha256'].items())
bound={str(path):sha(path) for path in [Path(__file__).resolve(),D/'pareto_archive_dimensions.py',parent/'completion.json',parent/'points.json',experiment/'registration.json',experiment/'completion.json',experiment/'results.json']}
added=[]
for name,row in read(experiment/'results.json').items():
    state=Path(row['independent_candidate_state']);rd=run_dir(state)
    sc=read(state/'completion.json');m=read(rd/'manifest.json');v=read(state/'endpoint_vector.json')
    assert sc['passed'] and read(state/'input_seal.json')['passed'] and m['metrics']['native_full_check_passed']
    audit=read(rd/'independent_audit.json');assert audit['audit']['passed']
    source=Path(reg['sources'][row['source_kind']]);origin=next(point for point in points if point.get('state')==str(source))
    worker=Path(row['native_source_observation']);native=run_dir(worker)
    assert read(worker/'completion.json')['passed'] and read(worker/'input_seal.json')['passed']
    assert read(native/'manifest.json')['environment']['VPR_JOINT_NATIVE_SEED_ORDER']==row['policy']
    assert all(sha(path)==digest for path,digest in row['native_artifact_sha256'].items())
    assert (native/'candidate/native_state_gate.txt').read_text()=='candidate FULL fresh_STA actual_installed_trees\n'
    assert sha(row['actual_candidate'])==sha(rd/'routed.route')
    assert v['constraints_sha256']==read(source/'endpoint_vector.json')['constraints_sha256']
    graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
    assert m['shared_inputs'][str(graph)]['sha256']==origin['physical_identity']['graph']
    assert sha(rd/'packed.net')==origin['physical_identity']['packed'] and sha(rd/'placed.place')==origin['physical_identity']['placed']
    ident=str(rd.relative_to(D));assert not any(point['id']==ident for point in points)
    point=copy.deepcopy(origin)
    for key in ['actor_final_state','actor_final_context_seal','native_analysis_parent_provenance','native_analysis_execution_scope',
        'registered_root_requirements','registered_bundle_size','registered_domain_mode','registered_domain_failure_release',
        'committed_in_this_actor','native_transaction_manifest','native_parameters','acceptance','reused_evaluation_source',
        'reused_evaluation_creation_timing','crossing_domain_audit']:
        point.pop(key,None)
    physical=audit['physical_metrics'];cpd=v['cpd_s']*1e9
    log=(native/'joint_native.log').read_text().splitlines()
    point.update(id=ident,arm='explicit_seed_'+row['policy']+'_'+row['source_kind'],batch='repair_seed_order_eltwise_01',
        batch_full_path=str(experiment),state=str(state),source_state=str(source),record_kind='fixed_source_single_transaction_seed_policy_diagnostic',
        diagnostic_not_complete_algorithm_configuration=True,committed_in_this_actor=False,source_ordered_route_body_sha256=route_body(run_dir(source)/'routed.route'),
        run_manifest=str(rd/'manifest.json'),binary_sha256=sha(m['command'][0]),final_STA_binary_sha256=sha(m['command'][0]),
        native_transaction_binary_sha256=sha(read(native/'manifest.json')['command'][0]),native_transaction_manifest=str(native/'manifest.json'),
        native_parameters=dict(seed_order=row['policy'],source_representation=row['source_kind'],objective='weighted_soft',crossing_reuse_enabled=True,
            domain_failure_release=True,request_sha256=sha(reg['source_sha256'] and D/'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8/round_001/candidate_00/request.txt')),
        initial_routing_convergence=origin.get('initial_routing_convergence',origin['convergence']),convergence='one_fixed_current_state_transaction',
        opportunity='Fixed current source after one automatic guided repair; source representation and seed policy explicitly varied, not an automatic pristine-root run',
        command=m['command'],environment=m.get('environment'),route_sha256=sha(rd/'routed.route'),route_body_sha256=route_body(rd/'routed.route'),
        CPD_ns=cpd,CPD_interval_ns=[cpd,cpd],CPD_precision='complete full-precision native endpoint vector',
        wirelength=physical['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=physical['sb_pairs_used'],CB_sources=physical['cb_crossing_output_sources_used'],
        SB_net_occupancy=physical['sb_pair_net_occupancy'],CB_net_occupancy=physical['cb_crossing_output_source_net_occupancy'],
        iterations=None,initial_routing_iterations=origin.get('initial_routing_iterations'),
        complete_single_configuration_seconds=None,timing_cohort=None,analysis_only_native_seconds=sc['timing']['native_process_seconds'],
        observation_workflow=dict(validation_only_independent_candidate_FULLSTA=sc['timing'],actual_native_worker=read(worker/'completion.json')['timing']),
        shared_research_workflow=dict(kind='six_arm_mechanism_diagnostic',complete_validation_seconds=c['complete_mechanism_validation_seconds'],not_a_complete_method_time=True),
        native_repair_core_seconds=sum(float(line.split()[-1]) for line in log if line.startswith('QUERY ')),
        native_kernel_including_candidate_observation_seconds=float(log[-1].split()[4]),
        audit_provenance=str(rd/'independent_audit.json'),actual_candidate_native_fused=True,
        unknowns=['Complete cold route-plus-repair time; complete automatic global-policy performance; broader source/architecture transfer.'])
    points.append(point);added.append(ident)
    for path in [state/'completion.json',state/'input_seal.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'independent_audit.json',worker/'completion.json',native/'manifest.json']:
        bound[str(path)]=sha(path)
annotate(points)
write(out/'points.json',points)
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as stream:
    writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows({key:point.get(key) for key in fields} for point in points)
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=added,
    source_sha256=bound,artifact_sha256={name:sha(out/name) for name in ['points.json','points.csv']},
    quality_counts=dict(collections.Counter(point['quality_status'] for point in points)),retention_counts=dict(collections.Counter(point['candidate_retention'] for point in points)),
    native_calls=0,complete_extraction_seconds=time.monotonic()-started,
    qualification='Actual legal diagnostic observations retained with strong baselines; source/order policy, native worker and validation-only final STA remain distinct. No complete-method score or history-best configuration is nominated. This explicit archive branch must be merged with the separately registered resource-cohort archive after terminal; common ancestor records are not independent repeats.'))
print(dict(passed=True,records=len(points),added=len(added)),flush=True)
