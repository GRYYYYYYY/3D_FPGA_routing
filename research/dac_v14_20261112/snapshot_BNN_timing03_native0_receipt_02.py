"""Snapshot the existing verified first timing arm without repeating its audit."""
import csv
from datetime import datetime,timezone
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'BNN_interleaved_timing_03';case=root/'native_0';out=D/'BNN_timing03_native0_receipt_02';out.mkdir(exist_ok=False)
snapshots=out/'receipt_snapshots';snapshots.mkdir()
done=read(case/'completion.json');flow=read(case/'flow/completion.json');measurement=read(case/'measurement/completion.json')
assert done['passed'] and done['complete_configuration_verified'] and flow['passed'] and measurement['passed']
assert measurement['returncode']==0 and not measurement['live_descendants_after_command_exit']
assert done['CPD_ns']==flow['final_CPD_s']*1e9 and done['resources']==flow['final_resources']
assert done['complete_wall_seconds']==measurement['complete_command_wall_seconds']
assert done['resource_accepted_steps']==flow['resource_accepted_steps']==5
assert done['timing_accepted_steps']==flow['timing_accepted_steps']==3
assert done['missing_memory_observations']==measurement['missing_memory_observations']
assert done['sampled_tree_PSS_peak_kib']==measurement['sampled_tree_PSS_peak_kib']
plan=read(root/'plan.json');reference=Path(plan['references']['native']);ref=read(reference/'completion.json')
coarse_equal=all(done[k]==ref[k] for k in ['CPD_ns','resources'])
assert coarse_equal
queue_rows=read(root/'queue/results.json');assert queue_rows['native_0']['complete_verified']
assert queue_rows['native_0']['verification_returncode']==0 and queue_rows['native_0']['quality'] is None
assert queue_rows['native_0']['complete_seconds']==done['complete_wall_seconds']
checked=0;live=[]
for pid,ticks in measurement['process_identities'].items():
    identity=process_identity(int(pid));checked+=1
    if identity and identity['state']!='Z' and identity['start_ticks']==str(ticks):live.append(identity)
assert not live,'Original native_0 measured descendant remains live'
qstatus=read(root/'queue/status.json');assert qstatus['case']=='domain_0' and qstatus['status']=='running'
child=process_identity(qstatus['pid']);assert child and child['state']!='Z' and child['start_ticks']==qstatus['start_ticks']
expected=read(root/'admission.json')['environment'];observed=[read(case/f'environment_{s}.json') for s in ['before','after']]
signature_keys=['host','kernel','platform','cpu_affinity','fixed_environment']
environment_signature_equal=all(all(x[k]==expected[k] for k in signature_keys) for x in observed)
assert environment_signature_equal
verifier=D/'verify_complete_resource_timing_joint_stream_v1.py'
assert sha(verifier)==done['source_sha256'][str(verifier)]
sources=[root/'plan.json',root/'admission.json',root/'queue/results.json',root/'queue/status.json',case/'completion.json',
    case/'measurement/completion.json',case/'flow/completion.json',case/'flow/stages.json',case/'flow/resource_flow/stages.json',
    case/'config.json',case/'metadata_consumers.json',case/'environment_before.json',case/'environment_after.json',verifier]
origin=[]
for i,path in enumerate(sources):
    assert path.stat().st_size<4*1024**2,('Unexpected large receipt',str(path))
    target=snapshots/(str(i).zfill(2)+'_'+path.name);data=path.read_bytes();target.write_bytes(data)
    origin.append(dict(original=str(path),snapshot=str(target),sha256=sha(target),original_mtime_utc=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()))
phases=[]
for scope,path in [('top_level_phase',case/'flow/stages.json'),('nested_resource_phase',case/'flow/resource_flow/stages.json')]:
    for row in read(path):
        assert row['status']=='completed' and ('returncode' not in row or row['returncode']==0)
        phases.append(dict(scope=scope,phase=row['phase'],complete_process_seconds=row['complete_process_seconds'],recorded_returncode=row.get('returncode'),returncode_recorded='returncode' in row))
with (out/'phase_costs.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['scope','phase','complete_process_seconds','recorded_returncode','returncode_recorded']);w.writeheader();w.writerows(phases)
payload=dict(passed=True,status='existing_verified_first_arm_receipt_snapshotted',observed_at=datetime.now(timezone.utc).isoformat(),
    batch=str(root),arm='native_0',actual_complete_verifier_passed=True,verifier_rerun=False,
    independent_new_inputs=0,new_native_calls_by_snapshot=0,new_graph_or_STA_parsing=False,
    quality=dict(CPD_ns=done['CPD_ns'],resources=done['resources']),complete_command_seconds=done['complete_wall_seconds'],
    complete_driver_seconds=flow['complete_driver_seconds'],sampled_tree_PSS_peak_kib=done['sampled_tree_PSS_peak_kib'],
    sampled_tree_PSS_peak_GiB=done['sampled_tree_PSS_peak_kib']/1024**2,sampled_tree_RSS_peak_kib=done['sampled_tree_RSS_peak_kib'],
    waited_process_RSS_high_water_kib=done['waited_process_RSS_high_water_kib'],missing_memory_observations=done['missing_memory_observations'],
    observer_CPU_seconds=done['observer_CPU_seconds'],resource_commits=5,timing_commits=3,
    resource_actual_work=done['resource_actual_work'],timing_attempted_proposals=done['timing_attempted_proposals'],
    phases=phases,nested_times_must_not_be_added_to_parent=True,observer_CPU_is_not_subtractable_wall_time=True,
    coarse_same_role_CPD_and_resources_equal=coarse_equal,reference=str(reference),
    exact_same_role_trajectory_requests_native_work_and_graph_payload_equivalence=None,
    own_root_endpoint_summary=None,paired_domain_over_native_ratio=None,all_four_timing_roles_complete=False,
    independent_research_verification_seconds=None,
    environment_signature_consistent=environment_signature_equal,exclusive_host_or_cold_OS_cache=False,
    measured_identities_rechecked=checked,live_original_identities=live,current_case=qstatus['case'],current_case_process=child,
    completion_timestamps=dict(flow=datetime.fromtimestamp((case/'flow/completion.json').stat().st_mtime,timezone.utc).isoformat(),
        existing_full_verifier=datetime.fromtimestamp((case/'completion.json').stat().st_mtime,timezone.utc).isoformat()),
    timestamp_interpretation='File receipt timestamps only; their difference is not a measured independent verification duration.',
    receipt_origins=origin,source_sha256={str(Path(__file__).resolve()):sha(Path(__file__).resolve()),**{r['snapshot']:r['sha256'] for r in origin}},
    artifact_sha256={'phase_costs.csv':sha(out/'phase_costs.csv')},
    qualification='First verified whole-command observation of the fixed N/D/D/N BNN timing batch, on one known physical input. Existing serial verifier checked actual same-command graphs, physical/FULL/STA and fixed-envelope decisions; snapshot does not repeat that heavy audit. Same-role exact trajectory/graph/request equivalence and own-root/paired full endpoint comparisons remain the original batch finish step after all4roles. No optimized paired ratio, statistical acceleration, independent sample, CP1r3 confirmation or replacement of original22.95percent overhead. New memory observation retains22missing samples; sample peak is not a continuous exact peak.')
write(out/'completion.json',payload)
print(dict(passed=True,CPD_ns=payload['quality']['CPD_ns'],complete_seconds=payload['complete_command_seconds'],PSS_GiB=payload['sampled_tree_PSS_peak_GiB'],identities_dead=checked,paired_ratio=None))
