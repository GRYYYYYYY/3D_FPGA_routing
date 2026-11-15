"""Capture authoritative completed reports and verified active owner identities for publication."""
from datetime import datetime,timezone
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
ROOT=D.parents[1];out=ROOT/'docs/github_progress_status_20261115.json'
names=['native_checkpoint_recovery_03','partial_escape_owner_intervention_01','complete_serial_additional_circuits_01','connection_budget_resource_dev_02','complete_route_resource_measurements_03','vector_then_strict_comparison_04','complete_serial_lazy_source_snapshot_01','complete_BNN_joint_index_flow_01','complete_BNN_closed_stream_flow_01','BNN_wire_timing_native_validation_01','robot_domain_release_ablation_01']
owners={};files=[]
for name in names:
 q=D/name/'queue';reg=read(q/'registration.json');p=process_identity(reg['pid']);live=bool(p and p['state']!='Z' and p['start_ticks']==reg['start_ticks']);phase=read(q/'status.json');terminal=read(q/'completion.json') if (q/'completion.json').exists() else None
 child=None
 if 'pid' in phase and phase.get('start_ticks'):
  x=process_identity(phase['pid']);child=dict(recorded_pid=phase['pid'],recorded_start_ticks=phase['start_ticks'],verified_live=bool(x and x['state']!='Z' and x['start_ticks']==phase['start_ticks']),actual=x)
 owners[name]=dict(registration=str((q/'registration.json').relative_to(ROOT)),recorded_pid=reg['pid'],recorded_start_ticks=reg['start_ticks'],verified_owner_live=live,actual_owner=p,phase=phase,child=child,terminal_receipt=None if terminal is None else str((q/'completion.json').relative_to(ROOT)),terminal_passed=None if terminal is None else terminal['passed'],results=read(q/'results.json') if (q/'results.json').exists() else None)
 files += [q/'registration.json']
 if terminal is not None:files.append(q/'status.json')
 if terminal is not None:files.append(q/'completion.json')
reports={}
for rel in ['closed_seed_transfer_eight_roles_01.json','R1_owner_release_joint_probe_01/verification.json','partial_escape_owner_intervention_01/verification.json','R1_BFS_native_timing_prediction_01/analysis/completion.json','complete_resource_timing_full_flow_01/comparison.json','complete_serial_additional_circuits_01/comparison.json','robot_domain_first_scope_analysis_02/completion.json','terminal_timing_envelope_policy_01/verification.json','robot_terminal_wire_transfer_01/completion.json','complete_serial_lazy_source_snapshot_01/comparison.json','complete_BNN_joint_index_flow_01/comparison.json','multiobjective_partial_owner_01/verification.json']:
 p=D/rel;r=read(p);assert r['passed'];reports[rel]=dict(passed=True,path=str(p.relative_to(ROOT)),sha256=sha(p));files.append(p)
budget={}
for label in read(D/'connection_budget_resource_dev_02/queue/results.json'):
 p=D/'connection_budget_resource_dev_02'/label/'completion.json';r=read(p);assert r['passed'];budget[label]={k:r[k] for k in ['final_state','accepted_steps','attempted_scopes','final_CPD_s','final_resources','complete_imported_algorithm_workflow_seconds']};files.append(p)
strict={}
for label,row in read(D/'vector_then_strict_comparison_04/queue/results.json').items():
 p=Path(row['completion']);r=read(p);assert r['passed'];strict[label]=dict(quality={k:r[k] for k in ['final_CPD_s','final_resources','accepted_steps','attempted_proposals']},actual_new_phase_process_seconds=row['new_actor_process_seconds'],full_vector_plus_strict_cost_unknown=True);files.append(p)
measurements=read(D/'complete_route_resource_measurements_03/queue/completion.json');assert measurements['passed']
prototype=['run_complete_resource_terminal_wire_timing_v1.py','verify_complete_resource_terminal_wire_timing_v1.py','complete_resource_prefix_equivalence_v1.py','compare_BNN_terminal_wire_full_flow_v1.py']
write(out,dict(captured_at_utc=datetime.now(timezone.utc).isoformat(),research_complete=False,repository='GRYYYYYYY/3D_FPGA_routing',branch='research/dac-snapshot-20261113',public_parent='7b2834743007b36ce5890320e15a0ffa7dea1eb3',formal_manuscript_binding='research/dac_v14_20261112/R1_native_closure_paper_binding_01.json',formal_manuscript_archive_records=578,latest_verified_archive='research/dac_v14_20261112/multiobjective_partial_owner_01',latest_verified_archive_records=592,archive_successful_complete_configurations=26,archive_successful_known_circuits=5,archive_statistics_scope='These are the named verified archive counts. Additional completed budget/strict/measurement/combined-engineering reports are separately preserved pending archive/manuscript integration; do not add their candidate or configuration counts by inference.',owners=owners,reports=reports,budget64=budget,strict_comparison=strict,complete_measurement03=measurements,unregistered_prototype=dict(files=prototype,full_experiment_registered=False,native_execution_performed=False,qualification='Implementation in progress, not a queued or completed experiment.'),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},qualification='Publication-time owner/child PID and start-tick verification plus terminal receipts supersede stale human running labels. Reports are frozen completed evidence; active trials remain partial and cannot supply final quality or runtime. Shared-host one-observation timing is descriptive. No native jobs launched/stopped or original experiment rules modified for publication.'))
print(dict(captured=True,path=str(out),live=[n for n,v in owners.items() if v['verified_owner_live']],terminal=[n for n,v in owners.items() if v['terminal_receipt']]),flush=True)
