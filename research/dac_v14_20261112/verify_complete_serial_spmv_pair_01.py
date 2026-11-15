"""Preserve a complete measured zero-scope transfer result as a negative result."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir

root=D/'complete_serial_transfer_dev_01';files=[Path(__file__).resolve(),root/'plan.json'];results={}
initial=[]
for role in ['spmv_native','spmv_paired']:
    case=root/role;proof=read(case/'explicit_policy_verification.json');assert proof['passed']
    assert all(sha(f)==h for f,h in proof['source_sha256'].items())
    assert proof['accepted_steps']==proof['attempted_scopes']==0
    assert proof['initial_state']==proof['final_state']
    assert proof['actual_native_work']==dict(native_transactions=0,queries=0,search_attempts=0,domain_releases=0)
    selector=read(case/'flow/repair/round_000/selection/completion.json');assert selector['passed'] and selector['candidate_scopes']==0
    initial.append(Path(proof['initial_state']));results[role]={k:proof[k] for k in ['CPD_ns','resources','complete_wall_seconds','sampled_tree_PSS_peak_kib','missing_memory_observations','actual_native_work']}
    files += [case/'explicit_policy_verification.json',case/'config.json',case/'flow/repair/round_000/selection/completion.json']
a,b=map(lambda s:read(s/'endpoint_vector.json'),initial)
assert all(a[k]==b[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
assert route_body(run_dir(initial[0])/'routed.route')==route_body(run_dir(initial[1])/'routed.route')
ca,cb=[read(root/n/'config.json') for n in ['spmv_native','spmv_paired']]
assert ca['route_command']==cb['route_command'] and ca['input_sha256']==cb['input_sha256']
write(root/'spmv_pair_completion.json',dict(passed=True,cohort_complete=False,results=results,
    initial_ordered_route_and_complete_vector_exact=True,source_sha256={str(f):sha(f) for f in files},
    qualification='Both full fresh-route/graph-build/resource-selection configurations execute and seal, but this SPMV root has no eligible reusable-crossing cut. Neither policy executes a native repair or domain decision; no quality or fallback benefit is established and no global optimality inferred. Complete cost includes the empty selection pass. One development observation per role, not timing speedup. Softmax roles remain separate and unfinished.'))
print(dict(passed=True,results=results,cohort_complete=False),flush=True)
