"""Register a current-root union intervention after independent CP1 confirmation."""
import copy
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from compose_current_scope_union_v1 import compose
from seed_census_analysis_pool_v2 import process_identity
root=D/'robot_union_mechanism_01';assert not root.exists()
sharing=D/'complete_serial_additional_circuits_01/robot_rl_domain/flow/repair/round_000/candidate_00/registration.json'
owner=D/'robot_owner_scope_pair_01/transaction/registration.json'
s=read(sharing)['roles']['reuse_on'];old=read(owner);o=old['roles']['target_plus_owner'];union=compose(s,o)
assert len(union['queries'])==25 and len(union['removed_pins'])==5
assert read(D/'robot_mechanism_composition_screen_01/completion.json')['passed'] and read(D/'robot_union_mechanism_validation_01/completion.json')['passed']
prior=D/'cp1_cross_circuit_cohort_01/queue';identity=read(prior/'registration.json');live=process_identity(identity['pid']);assert live and live['state']!='Z' and live['start_ticks']==identity['start_ticks']
root.mkdir();request=root/'union_request.txt';request.write_text(union['request']);domain=root/'shared_only_domain.txt';domain.write_text(union['domain_text'])
files=[Path(__file__).resolve(),D/'queue_robot_union_mechanism_01.py',D/'verify_robot_union_mechanism_01.py',D/'compose_current_scope_union_v1.py',D/'run_joint_crossing_source_transactions_v3.py',D/'audit_selected_retained_domain_v1.py',D/'robot_union_mechanism_validation_01/completion.json',D/'robot_mechanism_composition_screen_01/completion.json',sharing,owner,request,domain]
for f in files:
 if f.suffix=='.py':compile(f.read_text(),str(f),'exec')
bound=old['source_sha256'].copy();bound.update({str(f):sha(f) for f in files})
roles={}
for name,enabled,release in [('union_native',False,False),('union_domain_no_release',True,False),('union_domain_release',True,True)]:
 role=copy.deepcopy(o);role.update(scope='same_current_owner_and_sharing_union',request=str(request),queries=union['queries'],removed_pins=union['removed_pins'],crossing_reuse_enabled=enabled,domain_failure_release=release,crossing_domain=str(domain),explicit_crossings=None,allowed_resource_kind=None,source_sha256=bound);roles[name]=role
reg=copy.deepcopy(old);reg.update(roles=roles,source_sha256=bound,current_resource_selector_after_commit=True)
write(root/'prepared_transaction_registration.json',reg)
plan=dict(passed=True,registered_before_native=True,source_state=o['state'],sharing_registration=str(sharing),owner_registration=str(owner),fixed_order=list(roles),original_budget=o['original_budget'],fixed_resource_limits=o['fixed_resource_limits'],union_connections=25,union_nets=5,restricted_nets=union['domain_nets'],unrestricted_owner_nets=sorted(map(int,o['removed_pins'])),predecessor=str(prior),backend=str(D/'run_joint_crossing_source_transactions_v3.py'),supervisor=str(D/'standalone_unified_method_dev_03/supervise_method_phase.py'),source_sha256={**bound,str(root/'prepared_transaction_registration.json'):sha(root/'prepared_transaction_registration.json')},new_independent_inputs=0,CP1_modified=False,native_repair_workers_planned=3,shared_source_controls_planned=1,additional_STA_loads='Count actual receipts; do not infer a fixed total.',whole_method_time_cap=None,research_total_call_cap=None,qualification='Development union proposal from actual same-current owner and sharing selections, not an independent complete-method confirmation. Merge duplicate pins with exact current weights, globally order queries, leave all owner nets unrestricted and guide only sharing-exclusive nets. Identical scope/order/binary/objective/envelopes across3arms isolates domain(no release) and release(with same domains). Includes shared imported source control and actual native/FULL/STA/audits; costs not cold whole-flow or per-arm standalone. Keep no-gain/worse/rollback and gate failures. No original actor commits. CP1 cohort has priority; ordinary scientific negatives do not stop research.')
write(root/'plan.json',plan);print(dict(registered=True,roles=list(roles),connections=25,domain_nets=union['domain_nets'],new_native_calls=0))
