"""Compare complete cache-mode trajectories, including all rejected candidates."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir

root=D/'complete_serial_reusable_graph_dev_01';assert read(root/'queue/completion.json')['passed']
assert read(root/'config_verification_aliases.json')['passed']
comparisons={};files=[Path(__file__).resolve(),root/'queue/completion.json',root/'config_verification_aliases.json']
for mode,name in [('unrestricted','complete_serial_resource_measurement_dev_01'),('paired','complete_serial_resource_measurement_paired_dev_01')]:
    cold,warm=D/name,root/mode;a,b=read(cold/'completion.json'),read(warm/'completion.json')
    assert a['passed'] and b['passed'] and a['complete_configuration_verified'] and b['complete_configuration_verified']
    assert all(sha(p)==h for p,h in b['source_sha256'].items())
    ca,cb=read(cold/'config.json'),read(warm/'config.json')
    assert ca['route_command']==cb['route_command'] and ca['domain_mode']==cb['domain_mode']==mode
    assert all(cb['input_sha256'][p]==h for p,h in ca['input_sha256'].items())
    assert ca['cache_mode']=='build_inside_flow' and cb['cache_mode']=='reusable_graph_only'
    def equal_state(sa,sb):
        va,vb=read(sa/'endpoint_vector.json'),read(sb/'endpoint_vector.json')
        assert all(va[k]==vb[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
        assert route_body(run_dir(sa)/'routed.route')==route_body(run_dir(sb)/'routed.route')
    equal_state(Path(a['initial_state']),Path(b['initial_state']))
    equal_state(Path(a['final_state']),Path(b['final_state']))
    assert a['resources']==b['resources'] and a['CPD_ns']==b['CPD_ns']
    aa,bb=[read(r/'flow/repair/attempts.json') for r in [cold,warm]];assert len(aa)==len(bb)
    for x,y in zip(aa,bb):
        assert all(x[k]==y[k] for k in ['round','candidate_rank','removed_pins'])
        tx,ty=Path(x['transaction']),Path(y['transaction'])
        assert sha(tx/'request.txt')==sha(ty/'request.txt') and sha(tx/'domain.txt')==sha(ty/'domain.txt')
        px,py=read(tx/'progress.json'),read(ty/'progress.json');assert px.keys()==py.keys()
        for role in px:
            rx,ry=px[role],py[role];assert rx['status']==ry['status']=='legal_evaluated'
            assert all(rx[k]==ry[k] for k in ['resources','cpd_s','policies'])
            equal_state(Path(rx['evaluation']),Path(ry['evaluation']))
        files += [tx/'progress.json',ty/'progress.json',tx/'request.txt',ty/'request.txt',tx/'domain.txt',ty/'domain.txt']
    comparisons[mode]=dict(passed=True,all_initial_final_candidate_vectors_and_ordered_routes_exact=True,
        all_requests_scopes_and_decisions_exact=True,attempted_scopes=len(aa),
        build_inside_seconds=a['complete_wall_seconds'],graph_reuse_seconds=b['complete_wall_seconds'],
        observed_seconds_difference=b['complete_wall_seconds']-a['complete_wall_seconds'],
        initial_CPD_ns=read(Path(b['initial_state'])/'endpoint_vector.json')['cpd_s']*1e9,
        final_CPD_ns=b['CPD_ns'],resources=b['resources'],
        preprocessing_component_seconds=sum(s['complete_process_seconds'] for s in read(cold/'flow/stages.json') if s['phase'].startswith('build_')),
        reuse_memory={k:b[k] for k in ['waited_process_RSS_high_water_kib','sampled_tree_RSS_peak_kib','sampled_tree_PSS_peak_kib','missing_memory_observations']})
    files += [cold/'completion.json',warm/'completion.json',cold/'config.json',warm/'config.json',cold/'flow/repair/attempts.json',warm/'flow/repair/attempts.json']
write(D/'complete_serial_cache_comparison_01.json',dict(passed=True,comparisons=comparisons,
    source_sha256={str(p):sha(p) for p in files},
    qualification='All actual candidate, decision and final-state equivalence across graph-cache modes verified, including rejected outcomes. Cache reuse supplies graph-only preprocessing and excludes its measured construction cost; it does not reuse route/query/candidate results. One fixed-input development observation per configuration, opposite policy order across cache modes, concurrent shared host and uncontrolled OS cache. No statistical speedup or comparison to other implementation versions.'))
print(dict(passed=True,comparisons=comparisons),flush=True)
