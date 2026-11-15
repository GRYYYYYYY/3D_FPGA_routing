"""Freeze a single release-flag ablation from the actual first robot domain transaction."""
import copy
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
root=D/'robot_domain_release_ablation_01';root.mkdir(exist_ok=False)
reference=D/'complete_serial_additional_circuits_01/robot_rl_domain/flow/repair/round_000/candidate_00'
r=read(reference/'registration.json');role=copy.deepcopy(r['roles']['reuse_on'])
assert role['crossing_reuse_enabled'] and role['domain_failure_release'] and read(D/'robot_domain_first_scope_analysis_02/completion.json')['passed']
for f,h in role['source_sha256'].items():assert sha(f)==h
original=(D/'run_serial_lazy_resource_transactions_v1.py').read_text();new=(D/'run_serial_single_resource_scope_v1.py').read_text()
restored=new.replace('One explicitly registered resource scope with unchanged native/FULLSTA/audit gates.','Serial resource transactions with matched optional crossing domains and fixed envelopes.').replace("assert reg['execution_policy']=='single_registered_resource_scope'\nassert set(reg['roles'])=={'reuse_on'}\nfor name in reg['roles']:","assert reg['execution_policy']=='domain_first_stop_on_resource_accept'\nfor name in execution_order(reg['roles']):")
assert restored==original,'Single-role adapter changed more than scheduling/label'
for key,name in [('request','request.txt'),('crossing_domain','domain.txt')]:
 source=Path(role[key]);target=root/name;target.write_bytes(source.read_bytes());assert sha(target)==sha(source);role[key]=str(target);role['source_sha256'][str(target)]=sha(target)
role['domain_failure_release']=False
r['roles']={'reuse_on':role};r['execution_policy']='single_registered_resource_scope';r['current_resource_selector_after_commit']=True
prepared=[D/'run_serial_single_resource_scope_v1.py',D/'verify_robot_domain_release_ablation_v1.py',D/'queue_robot_domain_release_ablation_01.py',D/'robot_domain_first_scope_analysis_02/completion.json',D/'complete_serial_additional_circuits_01/comparison.json',reference/'registration.json',D/'native_resource_census_stage_01/binding.json']
r['source_sha256'].update({str(f):sha(f) for f in prepared});write(root/'prepared_transaction_registration.json',r)
plan=dict(passed=True,reference_domain_transaction=str(reference),reference_native_transaction=str(D/'complete_serial_additional_circuits_01/robot_rl_native/flow/repair/round_000/candidate_00'),predecessor=str(D/'BNN_wire_timing_native_validation_01/queue'),prepared_files=list(map(str,prepared)),native_repair_workers_planned=1,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),*prepared,root/'request.txt',root/'domain.txt',root/'prepared_transaction_registration.json']},qualification='New same-current single-flag ablation after all already registered engineering/BNN composition work: keep actual robot first source,23queries/four nets/current weights/order/seed/native binary and retained domain, disable only failure-triggered net release. Native and released-domain reference candidates already exist and are not rerun. Native input FULL/STA, source restoration, scope/domain/capacity/physical and candidate FULL/STA gates remain. Unexpected success is retained; failure has no candidate quality and is not a mathematical infeasibility proof. One shared imported component, never whole cold timing or historical speedup. No old actor or queue changes.')
write(root/'plan.json',plan);write(root/'preflight.json',dict(passed=True,adapter_diff_only_schedule_and_label=True,role_set=['reuse_on'],actual_source_and_request_preserved=True,release_flag_disabled=True,original_domain_and_native_controls_completed=True,new_native_calls_during_preflight=0,source_sha256=plan['source_sha256']))
print(dict(prepared=True,matched_actual_first_scope=True,native_repair_workers_planned=1,preflight_native_calls=0),flush=True)
