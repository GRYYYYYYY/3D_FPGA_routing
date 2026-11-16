"""Consume the original domain_1 whole verifier; no native/STA/graph replay."""
import csv
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'BNN_interleaved_timing_03';case=root/'domain_1';out=D/'BNN_timing03_domain1_receipt_01'
assert not out.exists()
done=read(case/'completion.json');flow=read(case/'flow/completion.json');m=read(case/'measurement/completion.json')
assert done['passed'] and done['complete_configuration_verified'] and flow['passed'] and m['passed']
assert m['returncode']==0 and not m['live_descendants_after_command_exit']
assert done['CPD_ns']==flow['final_CPD_s']*1e9 and done['resources']==flow['final_resources']
assert done['complete_wall_seconds']==m['complete_command_wall_seconds']
assert done['resource_accepted_steps']==flow['resource_accepted_steps']==9
assert done['timing_accepted_steps']==flow['timing_accepted_steps']==3
assert done['sampled_tree_PSS_peak_kib']==m['sampled_tree_PSS_peak_kib']
assert done['missing_memory_observations']==m['missing_memory_observations']
reference=Path(read(root/'plan.json')['references']['domain']);ref=read(reference/'completion.json')
coarse_equal=all(done[k]==ref[k] for k in ['CPD_ns','resources']);assert coarse_equal
results=read(root/'queue/results.json')
assert list(results)==['native_0','domain_0','domain_1'] and all(r['complete_verified'] for r in results.values())
assert results['domain_1']['verification_returncode']==0 and results['domain_1']['quality'] is None
assert results['domain_1']['complete_seconds']==done['complete_wall_seconds']
live=[]
for pid,tick in m['process_identities'].items():
    identity=process_identity(int(pid))
    if identity and identity['state']!='Z' and identity['start_ticks']==str(tick):live.append(identity)
assert not live,'Original measured domain descendant remains live'
q=read(root/'queue/status.json');assert q['case']=='native_1' and q['status']=='running'
child=process_identity(q['pid']);assert child and child['state']!='Z' and child['start_ticks']==q['start_ticks']
expected=read(root/'admission.json')['environment'];keys=['host','kernel','platform','cpu_affinity','fixed_environment']
observed=[read(case/f'environment_{s}.json') for s in ['before','after']]
assert all(all(x[k]==expected[k] for k in keys) for x in observed)
verifier=D/'verify_complete_resource_timing_joint_stream_v1.py'
assert sha(verifier)==done['source_sha256'][str(verifier)]
sources=[root/'plan.json',root/'admission.json',root/'queue/results.json',root/'queue/status.json',case/'completion.json',
    case/'measurement/completion.json',case/'flow/completion.json',case/'flow/stages.json',case/'flow/resource_flow/stages.json',
    case/'config.json',case/'metadata_consumers.json',case/'environment_before.json',case/'environment_after.json',verifier]
assert all(p.stat().st_size<4*1024**2 for p in sources)
out.mkdir();snapshots=out/'receipt_snapshots';snapshots.mkdir();origins=[]
for i,p in enumerate(sources):
    target=snapshots/(str(i).zfill(2)+'_'+p.name);target.write_bytes(p.read_bytes())
    origins.append(dict(original=str(p),snapshot=str(target),sha256=sha(target),
        original_mtime_utc=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()))
phases=[]
for scope,p in [('top_level_phase',case/'flow/stages.json'),('nested_resource_phase',case/'flow/resource_flow/stages.json')]:
    for row in read(p):
        assert row['status']=='completed' and ('returncode' not in row or row['returncode']==0)
        phases.append(dict(scope=scope,phase=row['phase'],complete_process_seconds=row['complete_process_seconds'],
            recorded_returncode=row.get('returncode'),returncode_recorded='returncode' in row))
with (out/'phase_costs.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['scope','phase','complete_process_seconds','recorded_returncode','returncode_recorded']);w.writeheader();w.writerows(phases)
payload=dict(passed=True,status='existing_verified_third_arm_receipt_snapshotted',observed_at=datetime.now(timezone.utc).isoformat(),
    batch=str(root),arm='domain_1',actual_complete_verifier_passed=True,verifier_rerun=False,
    independent_new_inputs=0,new_native_calls_by_snapshot=0,new_graph_or_STA_parsing=False,
    quality=dict(CPD_ns=done['CPD_ns'],resources=done['resources']),complete_command_seconds=done['complete_wall_seconds'],
    complete_driver_seconds=flow['complete_driver_seconds'],sampled_tree_PSS_peak_kib=done['sampled_tree_PSS_peak_kib'],
    sampled_tree_PSS_peak_GiB=done['sampled_tree_PSS_peak_kib']/1024**2,sampled_tree_RSS_peak_kib=done['sampled_tree_RSS_peak_kib'],
    waited_process_RSS_high_water_kib=done['waited_process_RSS_high_water_kib'],missing_memory_observations=done['missing_memory_observations'],
    observer_CPU_seconds=done['observer_CPU_seconds'],resource_commits=9,timing_commits=3,
    resource_actual_work=done['resource_actual_work'],timing_attempted_proposals=done['timing_attempted_proposals'],
    phases=phases,nested_times_must_not_be_added_to_parent=True,observer_CPU_is_not_subtractable_wall_time=True,
    coarse_same_role_CPD_and_resources_equal=coarse_equal,reference=str(reference),
    exact_same_role_trajectory_requests_native_work_and_graph_payload_equivalence=None,
    own_root_endpoint_summary=None,paired_domain_over_native_ratio=None,all_four_timing_roles_complete=False,
    completed_verified_roles=['native_0','domain_0','domain_1'],independent_research_verification_seconds=None,
    environment_signature_consistent=True,exclusive_host_or_cold_OS_cache=False,
    measured_identities_rechecked=len(m['process_identities']),live_original_identities=live,
    current_case=q['case'],current_case_process=child,
    completion_timestamps=dict(flow=datetime.fromtimestamp((case/'flow/completion.json').stat().st_mtime,timezone.utc).isoformat(),
        existing_full_verifier=datetime.fromtimestamp((case/'completion.json').stat().st_mtime,timezone.utc).isoformat()),
    timestamp_interpretation='Receipt timestamps only; their difference is not a measured independent verification duration.',
    receipt_origins=origins,source_sha256={str(Path(__file__).resolve()):sha(Path(__file__).resolve()),**{r['snapshot']:r['sha256'] for r in origins}},
    artifact_sha256={'phase_costs.csv':sha(out/'phase_costs.csv')},
    qualification='Third verified whole-command observation of fixed N/D/D/N, not a new physical input. Original serial verifier checked actual graphs, physical/FULL/STA and acceptance; it is not repeated. Coarse same-role quality matches the prior domain reference, but exact trajectories/requests/native work/six graph bytes and own-root/paired full endpoint comparisons await original finish after all4roles. No paired ratio, statistical acceleration, independent sample, CP1r3 result, paper benefit or replacement of original22.95percent overhead.27missing memory samples retained; sampled PSS is not an exact continuous peak.')
write(out/'completion.json',payload)
print(dict(passed=True,complete_seconds=payload['complete_command_seconds'],CPD_ns=payload['quality']['CPD_ns'],
    resources=payload['quality']['resources'],PSS_GiB=payload['sampled_tree_PSS_peak_GiB'],identities_dead=len(m['process_identities']),paired_ratio=None))
