"""Compare the three genuinely terminal development roles to their own K8 control."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from endpoint_timing_policy_streaming_v2 import compare

out=D/'query_reduction_completed_comparison_02';out.mkdir(exist_ok=False)
roles=['eltwise_A0_native','eltwise_A0_paired','bnn_A0_native']
rows=[];bound={str(Path(__file__).resolve()):sha(__file__)}
def registered(path):
    c=read(path/'completion.json');assert c['passed']
    assert all(sha(p)==h for p,h in c['source_sha256'].items()),'Completed source changed'
    for name in ['completion.json','registration.json','attempts.json']:
        bound[str(path/name)]=sha(path/name)
    return c,read(path/'registration.json'),read(path/'attempts.json')
def run(state):return Path(read(Path(state)/'completion.json')['run'])
def semantic_attempts(path,attempts):
    records=[]
    for a in attempts:
        tx=path/f"round_{a['round']:03d}"/f"candidate_{a['candidate_rank']:02d}"
        request=tx/'request.txt';bound[str(request)]=sha(request)
        entry={k:a[k] for k in ['round','candidate_rank','bundle_removed_pins','bundle_actual_nets']}
        entry['request']=request.read_text();entry['roles']={}
        for name,r in a['pair'].items():
            entry['roles'][name]={k:r.get(k) for k in ['status','accepted','CPD_s','resources','decision','strict_or_endpoint_control']}
        records.append(entry)
    return records
for role in roles:
    old=D/'stable_seed_transfer_dev_01'/role;new=D/'query_reduction_resource_dev_01'/role
    a,ar,aa=registered(old);b,br,ba=registered(new)
    for k in ['initial_state','domain_mode','domain_failure_release','anchor','resource_objectives','seed_order','graph_echo']:
        assert ar[k]==br[k],k
    av,bv=[read(Path(c['final_state'])/'endpoint_vector.json') for c in [a,b]]
    for c in [a,b]:
        for p in [Path(c['final_state'])/'endpoint_vector.json',run(c['final_state'])/'routed.route']:
            bound[str(p)]=sha(p)
    old_semantics=semantic_attempts(old,aa);new_semantics=semantic_attempts(new,ba)
    semantics=old_semantics==new_semantics
    def query_count(records):
        total=0
        for row in records:
            lines=row['request'].splitlines();nets=int(lines[0]);assert lines[nets+1]=='0';count=int(lines[nets+2]);assert len(lines)==nets+3+count;total+=count
        return total
    body_equal=route_body(run(a['final_state'])/'routed.route')==route_body(run(b['final_state'])/'routed.route')
    full_vector_equal=av==bv
    rows.append(dict(role=role,matched_initial_state=ar['initial_state'],final_resources=b['final_resources'],CPD_s=b['final_CPD_s'],
        accepted_steps=b['accepted_steps'],attempted_scopes=b['attempted_scopes'],
        endpoint_change=compare(av,bv),full_vector_exact=full_vector_equal,route_body_exact=body_equal,
        scope_request_decision_sequence_exact=semantics,old_proposed_connections=query_count(old_semantics),
        new_proposed_connections=query_count(new_semantics),
        old_imported_workflow_seconds=a['complete_imported_algorithm_workflow_seconds'],
        new_imported_workflow_seconds=b['complete_imported_algorithm_workflow_seconds'],
        observed_time_difference_seconds=b['complete_imported_algorithm_workflow_seconds']-a['complete_imported_algorithm_workflow_seconds'],
        complete_single_configuration_seconds=None,independent_new_input=False))
write(out/'rows.json',rows)
write(out/'completion.json',dict(passed=True,roles=roles,source_sha256=bound,rows_sha256=sha(out/'rows.json'),
    bnn_domain_status='still_running_at_registration_of_this_readonly_comparison',native_calls_new=0,new_independent_scientific_inputs=0,
    qualification='Three completed known-input development roles only. Exact route/vector/request/decision checks reported individually. Times are historical imported-state observations, not matched interleaved cold flows or causal speedups. Eltwise native queue actor_process_seconds includes suspended parent observation and is excluded; child workflow time is used. The active domain role and later batches are not repeated.'))
print([{k:r[k] for k in ['role','full_vector_exact','route_body_exact','scope_request_decision_sequence_exact','old_proposed_connections','new_proposed_connections','observed_time_difference_seconds']} for r in rows])
