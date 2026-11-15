"""Matched fresh inputs, quality/time tradeoffs and scope of the transfer cohort."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
root=D/'complete_serial_transfer_dev_01';assert read(root/'queue/completion.json')['passed']
files=[Path(__file__).resolve(),root/'plan.json',root/'queue/completion.json'];results={};pairs={}
for circuit in ['spmv','softmax']:
    proofs=[];configs=[]
    for mode in ['native','paired']:
        case=root/f'{circuit}_{mode}';p=read(case/'explicit_policy_verification.json')
        assert p['passed'] and all(sha(f)==h for f,h in p['source_sha256'].items())
        config=read(case/'config.json');assert config['seed_order']=='delay_rr_id'
        assert config['domain_mode']==('paired' if mode=='paired' else 'unrestricted')
        assert read(case/'flow/repair/registration.json')['local_probe']==dict(accepted_steps=0,rank_windows=3)
        assert config['initial_route_imported'] is False and config['cache_mode']=='build_inside_flow'
        results[f'{circuit}_{mode}']={k:p[k] for k in ['CPD_ns','resources','complete_wall_seconds','accepted_steps','attempted_scopes','actual_native_work','sampled_tree_PSS_peak_kib','missing_memory_observations']}
        proofs.append(p);configs.append(config);files += [case/'explicit_policy_verification.json',case/'config.json']
    a,b=proofs;ca,cb=configs
    assert ca['route_command']==cb['route_command'] and ca['input_sha256']==cb['input_sha256']
    sa,sb=[Path(p['initial_state']) for p in proofs];va,vb=[read(s/'endpoint_vector.json') for s in [sa,sb]]
    assert all(va[k]==vb[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
    assert route_body(run_dir(sa)/'routed.route')==route_body(run_dir(sb)/'routed.route')
    pairs[circuit]=dict(initial_ordered_route_and_complete_vector_exact=True,
        root_CPD_ns=va['cpd_s']*1e9,root_resources=read(run_dir(sa)/'independent_audit.json')['physical_metrics'],
        paired_minus_native_resources={k:b['resources'][k]-a['resources'][k] for k in a['resources']},
        paired_minus_native_CPD_ns=b['CPD_ns']-a['CPD_ns'],observed_seconds_difference=b['complete_wall_seconds']-a['complete_wall_seconds'])
write(root/'comparison.json',dict(passed=True,registered_roles=4,completed_roles=4,results=results,pairs=pairs,
    source_sha256={str(f):sha(f) for f in files},
    qualification='Two additional circuits with the prospectively fixed current-binary K8/rank3/delay-RR-ID policy, count2 fresh routing and actual own-current native/domain branches. Complete graph build, route, selection, every actual repair and final gate counted. Prior circuit diagnostics were known; this is transfer development rather than unseen held-out confirmation. Zero-scope/no-commit and rejected results retained. Per-configuration one shared-host observation with uncontrolled OS cache; no statistical speedup or generalization from circuit/role counts.'))
print(dict(passed=True,results=results,pairs=pairs),flush=True)
