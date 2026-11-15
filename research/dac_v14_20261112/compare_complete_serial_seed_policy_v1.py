"""Compare the three actual current-binary seed/domain configurations."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir

root=D/'complete_serial_seed_policy_dev_01';assert read(root/'queue/completion.json')['passed']
names=['native_seed_paired','delay_seed_native','delay_seed_paired']
results={};configs={};files=[Path(__file__).resolve(),root/'queue/completion.json',root/'plan.json']
for name in names:
    case=root/name;proof=read(case/'explicit_policy_verification.json');assert proof['passed']
    assert all(sha(p)==h for p,h in proof['source_sha256'].items())
    results[name]=proof;configs[name]=read(case/'config.json')
    files += [case/'explicit_policy_verification.json',case/'config.json']
first=results[names[0]];v0=read(Path(first['initial_state'])/'endpoint_vector.json');r0=route_body(run_dir(Path(first['initial_state']))/'routed.route')
for name in names[1:]:
    proof=results[name];vector=read(Path(proof['initial_state'])/'endpoint_vector.json')
    assert all(vector[k]==v0[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
    assert route_body(run_dir(Path(proof['initial_state']))/'routed.route')==r0
    assert proof['one_binary_sha256']==first['one_binary_sha256']
    assert configs[name]['route_command']==configs[names[0]]['route_command']
    assert configs[name]['input_sha256']==configs[names[0]]['input_sha256']
assert configs['native_seed_paired']['domain_mode']==configs['delay_seed_paired']['domain_mode']=='paired'
assert configs['native_seed_paired']['domain_feedback']==configs['delay_seed_paired']['domain_feedback'] is True
assert configs['delay_seed_native']['seed_order']==configs['delay_seed_paired']['seed_order']=='delay_rr_id'
comparisons={}
for label,before,after in [('seed_effect','native_seed_paired','delay_seed_paired'),('domain_effect','delay_seed_native','delay_seed_paired')]:
    a,b=results[before],results[after]
    comparisons[label]=dict(before=before,after=after,CPD_delta_ns=b['CPD_ns']-a['CPD_ns'],
        resource_delta={k:b['resources'][k]-a['resources'][k] for k in a['resources']},
        complete_wall_delta_seconds=b['complete_wall_seconds']-a['complete_wall_seconds'],
        scope='One recorded development pair; same initial physical input/current binary/options. Final quality changes and time deltas preserved without assuming a winner.')
summary={name:{k:p[k] for k in ['seed_order','domain_mode','domain_failure_release','CPD_ns','resources','complete_wall_seconds','waited_process_RSS_high_water_kib','sampled_tree_PSS_peak_kib','missing_memory_observations','actual_native_work']} for name,p in results.items()}
write(root/'comparison.json',dict(passed=True,initial_ordered_route_and_complete_vector_exact=True,
    one_binary_for_route_repair_candidate_STA=True,results=summary,comparisons=comparisons,
    source_sha256={str(f):sha(f) for f in files},
    qualification='Three development roles on one circuit, not three independent samples. Explicit seed effect isolated between paired roles; domain/failure-release effect isolated at fixed delay/RR-ID against own-current unrestricted control. All graph building, fresh routing, accepted/rejected candidates and final gates belong to each exact measured output. Shared host, uncontrolled OS cache and one observation per configuration; no statistical timing claim or transfer to pooled implementation costs.'))
print(dict(passed=True,results=summary,comparisons=comparisons),flush=True)
