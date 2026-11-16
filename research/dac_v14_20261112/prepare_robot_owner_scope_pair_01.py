"""Register a same-root scope intervention selected by the current generic selector."""
import ast, copy
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from current_owner_transaction_v1 import prepare
from current_resource_bundle_v2 import serialize_request

root=D/'robot_owner_scope_pair_01'; root.mkdir(exist_ok=False)
selection=D/'robot_current_owner_screen_01'; selected=read(selection/'completion.json')
state=Path(selected['state']); cache=D/'complete_serial_additional_circuits_01/robot_rl_native/flow/full_graph_cache'
prepared=prepare(state,state,selection,cache,root/'owner_preparation',domain_mode='unrestricted')
assert prepared['transaction_registered'] and prepared['rank']==0
original=read(root/'owner_preparation/registration.json'); joint=original['roles']['joint_native']
group=prepared['selected_group']; target=group['target_net']; owner=group['owner_net']
target_queries=[q for q in group['queries'] if q['net']==target]
request,_,queries=serialize_request([dict(net=target,pins=group['target_pins'],ordered_queries=target_queries)])
assert queries==target_queries
request_path=root/'target_only_request.txt'; request_path.write_text(request)
single=copy.deepcopy(joint); single.update(scope='same_current_target_without_releasing_external_owner',
    request=str(request_path),queries=queries,removed_pins={str(target):group['target_pins']})
joint=copy.deepcopy(joint); joint['scope']='same_current_target_plus_selected_blocking_owner'
reg=copy.deepcopy(original); reg['roles']={'target_only':single,'target_plus_owner':joint}
reg['current_resource_selector_after_commit']=True
supervisor=D/'standalone_unified_method_dev_03/supervise_method_phase.py'
files={Path(__file__).resolve(),D/'queue_robot_owner_scope_pair_01.py',D/'verify_robot_owner_scope_pair_01.py',
    D/'measure_process_tree_v1.py',supervisor,D/'crossing_source_stage_01/bin/vpr',request_path,
    D/'robot_release_capacity_cut_01/completion.json',root/'owner_preparation/preparation.json'}
# Freeze local imported modules and statically named Python workers, including
# inactive branches, without freezing unrelated status/publication scripts.
todo=[D/n for n in ['current_owner_transaction_v1.py','run_joint_crossing_source_transactions_v2.py',
    'current_sta_arrival_cone_compact.py','run_crossing_source_seed_analysis_v1.py',
    'audit_native_feedback_objective_cached.py','audit_retained_crossing_domain.py',
    'materialize_crossing_source_candidate_v1.py','current_escape_owner_selector_v1.py']]
seen=set()
while todo:
    f=todo.pop().resolve()
    if f in seen: continue
    seen.add(f); files.add(f)
    for node in ast.walk(ast.parse(f.read_text())):
        modules=[]
        if isinstance(node,ast.Import): modules=[a.name for a in node.names]
        elif isinstance(node,ast.ImportFrom) and node.module: modules=[node.module]
        for module in modules:
            dep=D/(module.split('.')[0]+'.py')
            if dep.exists(): todo.append(dep)
        if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value.endswith('.py'):
            dep=D/node.value
            if dep.is_file() and dep.is_relative_to(D): todo.append(dep)
old=D.parents[1]/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
files.update([old/'runtime_dependency_binding.json',old/'execution_scripts/flatland_timing_io_candidate.py',
    D.parents[1]/'scripts/flatland_benchmark.py'])
assert all(f.is_file() for f in files)
bound={**original['source_sha256'],**{str(f):sha(f) for f in files}}
reg['source_sha256']=bound
for role in reg['roles'].values(): role['source_sha256']=bound
write(root/'prepared_transaction_registration.json',reg)
write(root/'plan.json',dict(passed=True,registered_before_native=True,source_state=str(state),
    selector=str(selection),selector_rank=0,target_net=target,owner_net=owner,escape_node=group['escape_node'],
    fixed_order=list(reg['roles']),target_queries=target_queries,joint_queries=group['queries'],
    original_budget=joint['original_budget'],fixed_resource_limits=joint['fixed_resource_limits'],
    predecessor=str(D/'portable_clstm_pair_01/queue'),backend=str(D/'run_joint_crossing_source_transactions_v2.py'),
    supervisor=str(supervisor),source_sha256={**bound,str(root/'prepared_transaction_registration.json'):sha(root/'prepared_transaction_registration.json')},
    native_workers_planned=3,repair_workers_planned=2,shared_source_serialization_controls=1,
    no_external_native_reuse=True,full_method_frozen=False,new_independent_physical_inputs=0,
    qualification='Same known robot physical root, generic rank0 chosen before outcomes. Both roles unrestricted, same weighted objective/current target weights/relative target order/seed/binary/fixed root envelope. Only selected owner branch is added; no domain or release contrast. Source serialization control shared and counted; complete measured imported pair is not end-to-end algorithm or per-arm cold cost. Scope/order/load/STA/audit differences are not equal-work speedup evidence. Keep legal no-gain/worse, native rollback, gate failure and unexecuted outcomes; never commit to original actors. No required application SDC asserted.'))
print(dict(prepared=True,roles=list(reg['roles']),target=target,owner=owner,connections=[len(r['queries']) for r in reg['roles'].values()],frozen_files=len(bound),new_native_calls=0))
