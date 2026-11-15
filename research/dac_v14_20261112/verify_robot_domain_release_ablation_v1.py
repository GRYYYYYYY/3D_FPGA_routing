"""Read actual no-release outcome against the completed same-current release/native arms."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from endpoint_timing_policy_streaming_v2 import compare

root=D/'robot_domain_release_ablation_01';plan=read(root/'plan.json');tx=root/'transaction';c=read(tx/'completion.json');assert c['passed']
reg=read(tx/'registration.json');role=reg['roles']['reuse_on'];oldtx=Path(plan['reference_domain_transaction']);oldrole=read(oldtx/'registration.json')['roles']['reuse_on']
assert all(role[k]==oldrole[k] for k in ['state','source','queries','removed_pins','objective','seed_order','original_budget','fixed_resource_limits','crossing_reuse_enabled','fixed_target_paths'])
assert oldrole['domain_failure_release'] and not role['domain_failure_release']
assert sha(role['request'])==sha(oldrole['request']) and sha(role['crossing_domain'])==sha(oldrole['crossing_domain'])
worker=tx/'reuse_on';wc=read(worker/'completion.json');assert wc['passed']
run=run_dir(worker);source=Path(role['source']);oldrun=run_dir(oldtx/'reuse_on')
assert sha(read(run/'manifest.json')['command'][0])==sha(read(oldrun/'manifest.json')['command'][0])
assert all(sha(run/name)==sha(source/name) for name in ['packed.net','placed.place','routed.route'])
before=read(Path(role['state'])/'endpoint_vector.json');observed=read(worker/'endpoint_vector.json');assert all(before[k]==observed[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
log=(run/'joint_native.log').read_text().splitlines();assert log[-1].split()[0]=='COMPLETE' and log[-1].split()[-1]=='occupancy_restored'
domain=(run/'vertical_domain.log').read_text().splitlines();assert not any(line.startswith('RELEASE ') for line in domain)
assert read(tx/'reuse_on_domain_audit.json')['passed']
row=read(tx/'progress.json')['reuse_on'];audit=read(tx/'reuse_on_audit/analysis.json');assert audit['passed']
if row['status']=='transaction_failed_rolled_back':
 assert audit['candidate_route'] is None and log[-1].split()[1]=='0';quality=None
else:
 assert row['status']=='legal_evaluated' and audit['candidate_route'] is not None
 state=Path(row['evaluation']);assert read(state/'completion.json')['passed'] and read(run_dir(state)/'independent_audit.json')['audit']['passed'];quality=dict(CPD_s=read(state/'endpoint_vector.json')['cpd_s'],resources=row['resources'],accepted=row['policies']['resources_under_timing']['accepted'])
write(root/'verification.json',dict(passed=True,matched_source_request_cuts_weights_binary_and_seed=True,only_domain_failure_release_flag_changed=True,actual_status=row['status'],quality=quality,all_original_source_bytes_and_full_vector_restored=True,no_domain_release_executed=True,actual_queries=audit['queries'],actual_attempts=audit['attempts'],component_process_costs=read(tx/'process_costs.json'),complete_workflow_seconds=read(root/'queue/execution_receipt.json')['complete_imported_component_seconds'],native_repair_workers_new=1,candidate_LOADs_new=sum(r['tag']=='reuse_on_FULL_STA' for r in read(tx/'process_costs.json')),native_calls_new=1+sum(r['tag']=='reuse_on_FULL_STA' for r in read(tx/'process_costs.json')),committed_to_original_actor=False,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),root/'plan.json',tx/'registration.json',tx/'completion.json',worker/'completion.json',run/'joint_native.log',run/'vertical_domain.log',tx/'reuse_on_audit/analysis.json',tx/'reuse_on_domain_audit.json',oldtx/'registration.json']},qualification='Single same-current prospective release-flag ablation against previously executed native and domain-with-release first scopes. Operational search failure is not mathematical domain infeasibility. Failed transaction has no legal quality, while source remains exact. Shared imported component time cannot be used as full cold algorithm time or speedup against historical measured configurations.'))
print(dict(passed=True,status=row['status'],quality=quality,native_repair_workers_new=1),flush=True)
