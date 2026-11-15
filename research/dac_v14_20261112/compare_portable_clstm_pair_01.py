"""Keep failures and report same-execution endpoint/resource/time results."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from endpoint_timing_policy_streaming_v2 import compare
root=D/'portable_clstm_pair_01';plan=read(root/'plan.json');results=read(root/'results.json');assert set(results)=={'native','domain'}
files=[root/'plan.json',root/'results.json',Path(__file__).resolve()];comparison=None
for row in results.values():files += [Path(row['measurement']),Path(row['supervision'])]
if all(row['status']=='complete_legal_verified' for row in results.values()):
    cases={arm:Path(row['case']) for arm,row in results.items()};done={arm:read(case/'flow/completion.json') for arm,case in cases.items()}
    initial={arm:Path(value['initial_state']) for arm,value in done.items()};final={arm:Path(value['final_state']) for arm,value in done.items()}
    run=lambda state:Path(read(state/'completion.json')['run'])
    assert route_body(run(initial['native'])/'routed.route')==route_body(run(initial['domain'])/'routed.route')
    assert read(initial['native']/'endpoint_vector.json')==read(initial['domain']/'endpoint_vector.json')
    metrics={arm:read(case/'completion.json')['resources'] for arm,case in cases.items()}
    vectors={arm:read(state/'endpoint_vector.json') for arm,state in final.items()}
    endpoint=compare(vectors['native'],vectors['domain']);assert endpoint['compatible']
    delta={key:metrics['domain'][key]-metrics['native'][key] for key in ['wirelength','SB_pairs','CB_sources']}
    delta['CPD_ns']=(vectors['domain']['cpd_s']-vectors['native']['cpd_s'])*1e9
    delta['complete_seconds']=results['domain']['complete_seconds']-results['native']['complete_seconds']
    denominator=metrics['native']['SB_pairs']+metrics['native']['CB_sources']
    comparison=dict(identical_fresh_initial_route=True,identical_full_initial_vector=True,root_route_body_sha256=route_body(run(initial['native'])/'routed.route'),delta_domain_minus_native=delta,endpoint_changes=endpoint,SB_reduction_percent=None if metrics['native']['SB_pairs']==0 else -100*delta['SB_pairs']/metrics['native']['SB_pairs'],SB_plus_CB_reduction_percent=None if denominator==0 else -100*(delta['SB_pairs']+delta['CB_sources'])/denominator)
    for arm in cases:files += [cases[arm]/'completion.json',cases[arm]/'flow/completion.json',initial[arm]/'endpoint_vector.json',final[arm]/'endpoint_vector.json']
write(root/'comparison.json',dict(passed=True,registered_roles=2,verified_legal_roles=sum(r['status']=='complete_legal_verified' for r in results.values()),results=results,matched_comparison=comparison,source_sha256={str(f):sha(f) for f in files},qualification='Actual results retained for both fixed development roles. Paired comparison only when both complete gates and identical newly routed roots pass. One circuit/placement input; two arms are not two independent samples. No application timing requirement or statistical/interleaved runtime claim. Combined domain+failure-release treatment does not isolate either mechanism.'))
