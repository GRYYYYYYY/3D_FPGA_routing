"""Admit actual whole-flow states while preserving the missing observer measurement."""
import copy,csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof
from endpoint_timing_policy_streaming_v2 import compare
from pareto_archive_dimensions import annotate
from orphaned_flow_time_evidence_v2 import recover_original_time

parent=D/'multiobjective_engineering_inventory_01'
out=D/'multiobjective_closed_stream_quality_01';assert not out.exists()
pc=read(parent/'completion.json');assert pc['passed'] and read(parent/'verification.json')['passed']
assert all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
case=D/'complete_BNN_closed_stream_flow_01/bnn_native_closed_stream'
proof_path=D/'orphaned_BNN_quality_analysis_02/completion.json';proof=read(proof_path)
equivalence_path=D/'orphaned_BNN_engineering_comparison_01/completion.json';equivalence=read(equivalence_path)
assert proof['passed'] and proof['complete_configuration_quality_verified'] and not proof['complete_observer_measurement_available']
assert equivalence['passed'] and equivalence['all_actual_work_comparisons_exact']
original_time=recover_original_time(case);assert original_time['exit_status']==0
assert original_time['elapsed_seconds']==proof['GNU_time_elapsed_seconds']==equivalence['GNU_time_elapsed_seconds']
assert not (case/'completion.json').exists() and not (case/'measurement/completion.json').exists()
config=read(case/'config.json');flow=case/'flow';done=read(flow/'completion.json');assert done['passed']
assert done['final_state']==proof['final_state']
hashed={}
def checked(path):
    key=str(Path(path).resolve())
    if key not in hashed:hashed[key]=sha(key)
    return hashed[key]
for receipt in [proof,equivalence]:
    assert all(checked(p)==h for p,h in receipt['source_sha256'].items())
points=read(parent/'points.json');oldpoints=copy.deepcopy(points)
origin=next(p for p in points if p['id']=='native_extra_opportunity_bnn_01/runs/A0')
files=[Path(__file__).resolve(),parent/'completion.json',parent/'verification.json',parent/'points.json',
       parent/'complete_configuration_inventory.json',proof_path,equivalence_path,case/'config.json',
       flow/'completion.json',flow/'resource_flow/repair/attempts.json',flow/'timing/attempts.json',
       D/'pareto_archive_dimensions.py',D/'orphaned_flow_time_evidence_v2.py']
files += list(map(Path,original_time['source_sha256']))
entries=[dict(state=proof['initial_state'],phase='fresh_initial',source_state=None,committed=False,acceptance=None)]
for attempt in read(flow/'resource_flow/repair/attempts.json'):
    tx=Path(attempt['transaction']);progress=read(tx/'progress.json')
    files += [tx/'progress.json',tx/'registration.json']
    for name,row in progress.items():
        if row['status']!='legal_evaluated':continue
        assert (attempt.get('committed_evaluation')==row['evaluation'])==(attempt.get('accepted_role')==name)
        decision=tx/(name+'_decisions.json');files.append(decision)
        entries.append(dict(state=row['evaluation'],phase='resource',source_state=attempt['current_state'],
                            committed=attempt.get('committed_evaluation')==row['evaluation'],acceptance=read(decision)))
entries.append(dict(state=done['timing_initial_state'],phase='handoff_LOAD',source_state=proof['resource_final_state'],committed=False,acceptance=None))
for attempt in read(flow/'timing/attempts.json'):
    if attempt.get('evaluation'):
        entries.append(dict(state=attempt['evaluation'],phase='timing',source_state=attempt['before_state'],committed=attempt['accepted'],acceptance=None))
assert len(entries)==len({r['state'] for r in entries})
root_vector=read(Path(proof['initial_state'])/'endpoint_vector.json')
added=[];summary=[]
for entry in entries:
    state=Path(entry['state']);assert read(state/'completion.json')['passed']
    assurance=require_publication_proof(state);assert assurance['passed']
    rd=run_dir(state);m=read(rd/'manifest.json');cmd=m['command']
    assert m['metrics']['native_full_check_passed']
    for n in ['packed.net','placed.place','routed.route']:assert checked(rd/n)==m['outputs'][n]['sha256']
    identity=dict(architecture=checked(cmd[1]),graph=checked(cmd[cmd.index('--read_rr_graph')+1]),netlist=checked(cmd[2]),
        packed=checked(rd/'packed.net'),placed=checked(rd/'placed.place'),clock_modeling=cmd[cmd.index('--clock_modeling')+1],
        sdc='native_generated_default_from_bound_netlist',seed=cmd[cmd.index('--seed')+1])
    assert identity==origin['physical_identity'] and '--sdc_file' not in cmd
    audit=read(rd/'independent_audit.json');assert audit['audit']['passed'];metrics=audit['physical_metrics']
    vector=read(state/'endpoint_vector.json');delta=compare(root_vector,vector);assert delta['compatible']
    final=str(state)==proof['final_state'];ident=str(rd.relative_to(D));assert all(p['id']!=ident for p in points)
    row={k:copy.deepcopy(origin[k]) for k in ['circuit','physical_identity','quality_cohort','initial_routing_convergence']}
    row.update(id=ident,arm='closed_stream_native_resource_then_current_STA' if final else 'closed_stream_'+entry['phase'],
        batch='complete_BNN_closed_stream_flow_01',batch_full_path=str(case),state=str(state),source_state=entry['source_state'],
        status='legal',record_kind='complete_quality_final_qualified_GNU_time' if final else 'sealed_intermediate_of_qualified_whole_flow',
        actor_final_selected=final,actor_terminal_claim=final,actual_whole_configuration_terminal=final,
        phase=entry['phase'],transition_committed=entry['committed'],committed_to_historical_actor=False,
        run_manifest=str(rd/'manifest.json'),binary_sha256=checked(cmd[0]),final_STA_binary_sha256=checked(cmd[0]),
        phase_binary_sha256=config['phase_binary_sha256'],route_sha256=checked(rd/'routed.route'),route_body_sha256=route_body(rd/'routed.route'),
        command=cmd,environment=m.get('environment'),CPD_ns=vector['cpd_s']*1e9,CPD_interval_ns=[vector['cpd_s']*1e9]*2,
        CPD_precision='Actual complete native endpoint vector',wirelength=metrics['planar_wirelength_excluding_sb_half_nodes'],
        SB_pairs=metrics['sb_pairs_used'],CB_sources=metrics['cb_crossing_output_sources_used'],
        SB_net_occupancy=metrics['sb_pair_net_occupancy'],CB_net_occupancy=metrics['cb_crossing_output_source_net_occupancy'],
        convergence='fresh_count8_complete_own_current_resource_then_current_STA_menu' if final else 'actual_whole_flow_intermediate',
        opportunity='Same supplied BNN inputs; complete fresh routing, current resource repair and current STA portfolio; no independent new root.',
        complete_single_configuration_seconds=original_time['elapsed_seconds'] if final else None,
        complete_time_scope='original_GNU_time_whole_invocation' if final else None,
        complete_time_display_resolution_seconds=original_time['display_resolution_seconds'] if final else None,
        complete_observer_wall_seconds=None,timing_cohort=None,
        complete_configuration_verification=str(proof_path),complete_configuration_measurement=None,
        complete_GNU_time_receipt=str(case/'measurement/gnu_time.txt') if final else None,
        original_observer_measurement_available=False,undisturbed_timing=False,
        memory_observation=dict(waited_process_RSS_high_water_kib=original_time['waited_process_RSS_high_water_kib'],
            sampled_tree_RSS_peak_kib=None,sampled_tree_PSS_peak_kib=None,observer_CPU_seconds=None) if final else None,
        endpoint_vector=str(state/'endpoint_vector.json'),endpoint_vector_sha256=checked(state/'endpoint_vector.json'),
        endpoint_changes_against_own_initial=delta,new_native_calls_for_archival=0,
        audit_provenance=str(rd/'independent_audit.json'),resource_assurance_kind=assurance['assurance_kind'],
        acceptance=entry['acceptance'],source_constraints_sha256=vector['constraints_sha256'],verification=str(proof_path),
        unknowns=['Original observer missing; PSS/observer wall/CPU unavailable; brief overlap; no matched timing cohort or optimized domain/native overhead.'] if final else ['No standalone complete runtime; whole elapsed not assigned to intermediate state.'])
    if final:
        assert row['CPD_ns']==proof['CPD_ns'] and {k:row[k] for k in ['wirelength','SB_pairs','CB_sources']}==proof['resources']
    points.append(row);added.append(ident)
    summary.append({k:row[k] for k in ['id','state','phase','actor_final_selected','transition_committed','CPD_ns','wirelength','SB_pairs','CB_sources','complete_single_configuration_seconds','endpoint_changes_against_own_initial']})
    files += [state/'completion.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'routed.route',rd/'independent_audit.json']
annotate(points)
derived={'quality_dominated_by','nominal_quality_dominated_by','matched_time_dominated_by','quality_projection_retained','quality_status','candidate_retention','archive_retained','record_preserved','five_dimensional_comparison_count','retention_qualification'}
assert [{k:v for k,v in p.items() if k not in derived} for p in points[:len(oldpoints)]]==[{k:v for k,v in p.items() if k not in derived} for p in oldpoints]
newfinals=[p for p in points if p['id'] in added and p['actor_final_selected']];assert len(newfinals)==1
final=newfinals[0];assert not final['matched_time_dominated_by'] and final['five_dimensional_comparison_count']==0
inventory=read(parent/'complete_configuration_inventory.json');rows=copy.deepcopy(inventory['configurations'])
assert len(rows)==len({r['case'] for r in rows})==pc['complete_measured_configurations_total']
for r in rows:
    primary=read(r['proof']);measurement=read(r['measurement'])
    assert primary['passed'] and primary['complete_configuration_verified'] and measurement['passed']
    assert r['state']==primary['final_state'] and r['complete_seconds']==primary['complete_wall_seconds']==measurement['complete_command_wall_seconds']
    files += [Path(r['proof']),Path(r['measurement'])]
assert str(case) not in {r['case'] for r in rows}
rows.append(dict(id=final['id'],case=str(case),circuit=final['circuit'],state=final['state'],cache_mode=config['cache_mode'],
    quality=dict(CPD_ns=final['CPD_ns'],**proof['resources']),complete_seconds=original_time['elapsed_seconds'],
    proof=str(proof_path),measurement=None,GNU_time_receipt=str(case/'measurement/gnu_time.txt'),
    time_scope='original_GNU_time_whole_invocation',time_display_resolution_seconds=1.,memory=final['memory_observation'],
    original_observer_measurement_available=False,undisturbed_timing=False))
observed=sum(r['measurement'] is not None for r in rows)
out.mkdir();write(out/'points.json',points);write(out/'added_observations.json',summary)
write(out/'complete_configuration_inventory.json',dict(passed=True,configurations=rows,count=len(rows),
    complete_quality_configurations=len(rows),complete_observer_measured_configurations=observed,
    qualified_GNU_only_configurations=len(rows)-observed,circuits=sorted({r['circuit'] for r in rows}),
    qualification='Enumerated unique actual full-flow final proofs. Quality-complete configurations and observer-complete measurements are different counts. GNU-only row retains actual elapsed, integer-second precision, RSS and all missing fields; no substituted measurement completion or independent-sample claim.'))
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','record_kind','actor_final_selected','complete_single_configuration_seconds','complete_time_scope','complete_time_display_resolution_seconds','timing_cohort']
with (out/'points.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:p.get(k) for k in fields} for p in points)
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=added,native_calls=0,
    complete_quality_configurations_total=len(rows),complete_measured_configurations_total=observed,
    qualified_GNU_only_configurations=len(rows)-observed,complete_known_circuits=len({r['circuit'] for r in rows}),
    complete_vertical_families=pc['complete_vertical_families'],new_independent_inputs=0,
    source_sha256={str(f):checked(f) for f in dict.fromkeys(files)},
    artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','added_observations.json','complete_configuration_inventory.json']},
    qualification='All actual root/legal rejected/accepted/handoff/final states of the completed stream flow. Original archive scientific fields preserved; only derived dominance annotations recomputed. Original case and observer completion remain absent. Qualified GNU time belongs to final only and has no matched timing cohort.'))
print(dict(passed=True,records=len(points),added=len(added),complete_quality_configs=len(rows),observer_complete_configs=observed,GNU_only_configs=len(rows)-observed),flush=True)
