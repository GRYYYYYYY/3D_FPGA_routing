"""Compare complete separate-STA and callback trajectories without dropping rejects."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir

reference=D/'complete_serial_seed_policy_dev_01/delay_seed_paired'
root=D/'complete_serial_fused_dev_01';actual=root/'delay_seed_paired'
assert read(root/'queue/completion.json')['passed']
a,b=[read(r/'explicit_policy_verification.json') for r in [reference,actual]]
for v in [a,b]:assert v['passed'] and all(sha(f)==h for f,h in v['source_sha256'].items())
ca,cb=[read(r/'config.json') for r in [reference,actual]]
for key in ['route_command','cache_mode','domain_mode','domain_feedback','seed_order']:assert ca[key]==cb[key]
for f in ca['route_command'][:3]:assert ca['input_sha256'][f]==cb['input_sha256'][f]
files=[Path(__file__).resolve(),root/'queue/completion.json',reference/'explicit_policy_verification.json',actual/'explicit_policy_verification.json',reference/'config.json',actual/'config.json']
def equal_state(x,y):
    va,vb=[read(s/'endpoint_vector.json') for s in [x,y]]
    assert all(va[k]==vb[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
    assert route_body(run_dir(x)/'routed.route')==route_body(run_dir(y)/'routed.route')
    assert read(run_dir(x)/'independent_audit.json')['physical_metrics']==read(run_dir(y)/'independent_audit.json')['physical_metrics']
    files.extend([x/'completion.json',y/'completion.json',x/'endpoint_vector.json',y/'endpoint_vector.json'])
equal_state(Path(a['initial_state']),Path(b['initial_state']));equal_state(Path(a['final_state']),Path(b['final_state']))
aa,bb=[read(r/'flow/repair/attempts.json') for r in [reference,actual]];assert len(aa)==len(bb)
legal=0
for x,y in zip(aa,bb):
    assert all(x.get(k)==y.get(k) for k in ['round','candidate_rank','removed_pins','accepted_role'])
    tx,ty=Path(x['transaction']),Path(y['transaction'])
    assert sha(tx/'request.txt')==sha(ty/'request.txt') and sha(tx/'domain.txt')==sha(ty/'domain.txt')
    px,py=read(tx/'progress.json'),read(ty/'progress.json');assert px.keys()==py.keys()
    for role in px:
        rx,ry=px[role],py[role];assert rx['status']==ry['status']=='legal_evaluated'
        assert all(rx[k]==ry[k] for k in ['resources','cpd_s','policies'])
        equal_state(Path(rx['evaluation']),Path(ry['evaluation']));legal+=1
    files += [tx/'progress.json',ty/'progress.json',tx/'request.txt',ty/'request.txt',tx/'domain.txt',ty/'domain.txt']
assert a['actual_native_work']['queries']==b['actual_native_work']['queries']
assert a['actual_native_work']['search_attempts']==b['actual_native_work']['search_attempts']
result=dict(passed=True,all_initial_final_and_rejected_candidate_vectors_ordered_routes_physical_exact=True,
    all_requests_domains_scopes_decisions_exact=True,legal_candidates=legal,attempted_scopes=len(aa),
    reference_complete_wall_seconds=a['complete_wall_seconds'],callback_complete_wall_seconds=b['complete_wall_seconds'],
    observed_complete_seconds_difference=b['complete_wall_seconds']-a['complete_wall_seconds'],
    actual_native_work=b['actual_native_work'],CPD_ns=b['CPD_ns'],resources=b['resources'],
    memory={k:b[k] for k in ['waited_process_RSS_high_water_kib','sampled_tree_RSS_peak_kib','sampled_tree_PSS_peak_kib','missing_memory_observations']},
    source_sha256={str(f):sha(f) for f in files},
    qualification='Both actual full measured commands build graph indexes, generate fresh initial routes and complete identical own-current menus. Callback mode includes its independently executed empty source serialization controls, every physical/scope/domain audit, candidate FULL/fresh STA, reject/rollback and final gate. Persisted candidate traversal order is checked exactly; actual native callback tree identity is separately bound. One sequential development observation per backend on a shared host with uncontrolled OS cache, not statistical speedup or independent circuit transfer.')
write(root/'comparison.json',result);print({k:v for k,v in result.items() if k!='source_sha256'},flush=True)
