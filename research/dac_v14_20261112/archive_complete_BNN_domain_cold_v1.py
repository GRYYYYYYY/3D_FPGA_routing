"""Append actual domain-case observations, never inferred/pending route quality."""
import argparse
import copy
import csv
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from state_resource_assurance import require_publication_proof, resource_assurance
from run_native_scope_policy_v4 import run_dir
from pareto_archive_dimensions import annotate

p=argparse.ArgumentParser()
for n in ['case','parent','cost','output']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();case,parent,cost,out=[getattr(a,n).resolve() for n in ['case','parent','cost','output']]
assert not out.exists()
proof=read(case/'completion.json');assert proof['passed'] and proof['complete_configuration_verified']
config=read(case/'config.json');assert config['domain_mode']=='paired'
pc=read(parent/'completion.json');assert pc['passed']
assert all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
cc=read(cost/'completion.json');cs=read(cost/'summary.json')
assert cc['passed'] and all(sha(cost/n)==h for n,h in cc['artifact_sha256'].items())
assert cs['complete_wall_seconds']==proof['complete_wall_seconds']
flow=case/'flow';done=read(flow/'completion.json');assert done['passed']
points=read(parent/'points.json');assert len(points)==pc['records']
assert not any(row.get('batch_full_path')==str(case) for row in points)
origin=next(row for row in points if row['id']=='native_extra_opportunity_bnn_01/runs/A0')
files=[Path(__file__).resolve(),parent/'completion.json',parent/'points.json',case/'completion.json',case/'config.json',
       case/'measurement/completion.json',flow/'completion.json',flow/'resource_flow/repair/attempts.json',
       flow/'timing/attempts.json',cost/'completion.json',cost/'summary.json',D/'pareto_archive_dimensions.py']
hashed={}
def checked(path):
    path=str(Path(path).resolve())
    if path not in hashed:hashed[path]=sha(path)
    return hashed[path]
assert all(checked(f)==h for f,h in proof['source_sha256'].items())
events=[dict(state=proof['initial_state'],phase='fresh_initial',source_state=None,committed=False,acceptance=None)]
for attempt in read(flow/'resource_flow/repair/attempts.json'):
    tx=Path(attempt['transaction']);progress=read(tx/'progress.json')
    for name,row in progress.items():
        if row['status']!='legal_evaluated':continue
        committed=attempt.get('committed_evaluation')==row['evaluation']
        assert committed==(attempt.get('accepted_role')==name)
        events.append(dict(state=row['evaluation'],phase='resource',source_state=attempt['current_state'],
                           committed=committed,acceptance=read(tx/(name+'_decisions.json'))))
events.append(dict(state=done['timing_initial_state'],phase='handoff_LOAD',source_state=proof['resource_final_state'],
                   committed=False,acceptance=None))
for attempt in read(flow/'timing/attempts.json'):
    if attempt.get('evaluation'):
        events.append(dict(state=attempt['evaluation'],phase='timing',source_state=attempt['before_state'],
                           committed=attempt['accepted'],acceptance=None))
entries={}
for entry in events:entries.setdefault(entry['state'],[]).append(entry)
assert proof['final_state'] in entries
added=[];summary=[]
for state_name,provenances in entries.items():
    state=Path(state_name);closed=read(state/'completion.json');assert closed['passed']
    assurance=require_publication_proof(state);rd=run_dir(state);manifest=read(rd/'manifest.json');cmd=manifest['command']
    assert manifest['metrics']['native_full_check_passed']
    for name in ['packed.net','placed.place','routed.route']:
        assert checked(rd/name)==manifest['outputs'][name]['sha256']
    identity=dict(architecture=checked(cmd[1]),graph=checked(cmd[cmd.index('--read_rr_graph')+1]),
        netlist=checked(cmd[2]),packed=checked(rd/'packed.net'),placed=checked(rd/'placed.place'),
        clock_modeling=cmd[cmd.index('--clock_modeling')+1],sdc='native_generated_default_from_bound_netlist',
        seed=cmd[cmd.index('--seed')+1])
    assert identity==origin['physical_identity'] and '--sdc_file' not in cmd
    if (state/'input_seal.json').exists():assert read(state/'input_seal.json')['passed'];files.append(state/'input_seal.json')
    vector=read(state/'endpoint_vector.json');metrics=resource_assurance(state)['physical_metrics']
    final=state_name==proof['final_state'];ident=str(rd.relative_to(D));assert not any(row['id']==ident for row in points)
    row={k:copy.deepcopy(origin[k]) for k in ['circuit','physical_identity','quality_cohort','initial_routing_convergence']}
    primary=provenances[0]
    row.update(id=ident,arm='cold_full_domain_resource_then_current_STA' if final else 'cold_domain_'+primary['phase']+'_observation',
        batch='complete_resource_timing_full_flow_01',batch_full_path=str(case),state=state_name,
        source_state=primary['source_state'],observation_provenances=provenances,status='legal',
        record_kind='measured_whole_configuration_final' if final else 'sealed_intermediate_of_measured_whole_configuration',
        actor_final_selected=final,actor_terminal_claim=final,phase=primary['phase'],
        transition_committed=any(e['committed'] for e in provenances),committed_to_historical_actor=False,
        run_manifest=str(rd/'manifest.json'),binary_sha256=checked(cmd[0]),final_STA_binary_sha256=checked(cmd[0]),
        phase_binary_sha256=config['phase_binary_sha256'],route_sha256=checked(rd/'routed.route'),
        route_body_sha256=route_body(rd/'routed.route'),command=cmd,environment=manifest.get('environment'),
        CPD_ns=vector['cpd_s']*1e9,CPD_interval_ns=[vector['cpd_s']*1e9]*2,
        CPD_precision='Actual native endpoint vector from this complete measured domain case',
        wirelength=metrics['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=metrics['sb_pairs_used'],
        CB_sources=metrics['cb_crossing_output_sources_used'],SB_net_occupancy=metrics['sb_pair_net_occupancy'],
        CB_net_occupancy=metrics['cb_crossing_output_source_net_occupancy'],
        convergence='fresh_count8_complete_own_current_resource_then_current_STA_menu' if final else 'intermediate_actual_stage_of_fresh_count8_full_case',
        opportunity='Same explicit physical inputs and fresh count8/1.01/seed11 root as the complete native case; domain-first resource repair and own-current timing feedback retain actual calls/skips/rejections. Combined treatment, not equal-work or one-factor attribution.',
        complete_single_configuration_seconds=proof['complete_wall_seconds'] if final else None,
        timing_cohort='complete_fresh_BNN_resource_timing_pair_01' if final else None,
        complete_configuration_verification=str(case/'completion.json'),actual_whole_configuration_terminal=final,
        complete_configuration_measurement=str(case/'measurement/completion.json') if final else None,
        memory_observation={k:proof[k] for k in ['waited_process_RSS_high_water_kib','sampled_tree_RSS_peak_kib',
            'sampled_tree_PSS_peak_kib','missing_memory_observations','observer_CPU_seconds']} if final else None,
        whole_case_actual_work={k:proof[k] for k in ['resource_actual_work','resource_accepted_steps',
            'timing_accepted_steps','timing_attempted_proposals']} if final else None,
        new_native_calls_for_archival=0,audit_provenance=str(rd/'independent_audit.json'),
        resource_assurance_kind=assurance['assurance_kind'],acceptance=primary['acceptance'],
        source_constraints_sha256=vector['constraints_sha256'],verification=str(case/'completion.json'),
        unknowns=['Legacy timing metadata aliases are additional static runtime dependencies; byte identity to generated payloads is checked in the actual cost analysis.',
                  'Shared-host/OS-cache effects uncontrolled; repeated historical physical root is not an independent benchmark sample.',
                  'Imported historical domain/native complete costs remain unknown; no old-quality/new-time splice.']
                  if final else ['Intermediate observations have no standalone whole-configuration runtime.'])
    if final:
        assert {k:row[k] for k in ['wirelength','SB_pairs','CB_sources']}==proof['resources']
        assert row['CPD_ns']==proof['CPD_ns']
    points.append(row);added.append(ident)
    summary.append(dict(id=ident,state=state_name,phase=row['phase'],actor_final_selected=final,
        transition_committed=row['transition_committed'],CPD_ns=row['CPD_ns'],
        resources={k:row[k] for k in ['wirelength','SB_pairs','CB_sources']},
        complete_single_configuration_seconds=row['complete_single_configuration_seconds']))
    files += [state/'completion.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'routed.route',rd/'independent_audit.json']
annotate(points)
for row in summary:row['quality_status']=next(p['quality_status'] for p in points if p['id']==row['id'])
final=next(row for row in points if row['id'] in added and row['actor_final_selected'])
old=next(row for row in points if row['arm']=='complete_resource_paired_then_current_STA_native')
comparison=dict(actual_cold_domain={k:final[k] for k in ['CPD_ns','wirelength','SB_pairs','CB_sources','quality_status']},
    historical_imported_domain={k:old[k] for k in ['CPD_ns','wirelength','SB_pairs','CB_sources','quality_status']},
    cold_minus_imported_wire=final['wirelength']-old['wirelength'],
    imported_has_unknown_complete_cost=old['complete_single_configuration_seconds'] is None,
    historical_point_in_actual_quality_dominators=old['id'] in final['quality_dominated_by'])
out.mkdir()
write(out/'events.json',events);write(out/'points.json',points)
write(out/'complete_domain_case_summary.json',dict(passed=True,observations=summary,complete_case=proof,
    historical_comparison=comparison,registered_pair_roles=2,completed_legal_pair_roles=2,
    qualification='All actual independently validated domain observations appended to the immutable native-case parent. Reused exact state evaluations deduplicate by actual state path while every event remains recorded. Only actual domain final receives this run\'s whole time/memory. Parent observations, legal policy rejects, dominated points and imported unknown costs remain; quality annotation is recomputed. No pending structural proposal or model prediction is made legal by this archive. Actual cache-runtime alias boundaries stay explicit.'))
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','record_kind',
        'actor_final_selected','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
    writer.writerows({k:row.get(k) for k in fields} for row in points)
write(out/'completion.json',dict(passed=True,records=len(points),parent=str(parent),added=added,native_calls=0,
    actual_observation_events=len(events),new_unique_actual_states=len(entries),
    complete_measured_configurations_total=pc['complete_measured_configurations_total']+1,
    complete_known_circuits=pc['complete_known_circuits'],complete_vertical_families=pc['complete_vertical_families'],
    source_sha256={str(f):checked(f) for f in dict.fromkeys(files)},
    artifact_sha256={n:sha(out/n) for n in ['events.json','points.json','points.csv','complete_domain_case_summary.json']}))
print(dict(passed=True,records=len(points),added=len(added),final=comparison['actual_cold_domain']),flush=True)
