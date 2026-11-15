"""Exact executed-state comparison with explicit unexecuted optional controls."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from resource_policy_scheduling_v1 import SKIPPED
root=D/'complete_serial_lazy_transfer_dev_01';assert read(root/'queue/completion.json')['passed']

def compare_pair(reference,actual):
    a,b=[read(r/'explicit_policy_verification.json') for r in [reference,actual]]
    for p in [a,b]:assert p['passed'] and all(sha(f)==h for f,h in p['source_sha256'].items())
    ca,cb=[read(r/'config.json') for r in [reference,actual]]
    for k in ['route_command','domain_mode','domain_feedback','seed_order','cache_mode']:assert ca[k]==cb[k]
    files=[Path(__file__).resolve(),root/'queue/completion.json',reference/'explicit_policy_verification.json',actual/'explicit_policy_verification.json',reference/'config.json',actual/'config.json']
    def equal_state(x,y):
        va,vb=[read(s/'endpoint_vector.json') for s in [x,y]]
        assert all(va[k]==vb[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
        assert route_body(run_dir(x)/'routed.route')==route_body(run_dir(y)/'routed.route')
        assert read(run_dir(x)/'independent_audit.json')['physical_metrics']==read(run_dir(y)/'independent_audit.json')['physical_metrics']
        files.extend([x/'completion.json',y/'completion.json',x/'endpoint_vector.json',y/'endpoint_vector.json'])
    equal_state(Path(a['initial_state']),Path(b['initial_state']));equal_state(Path(a['final_state']),Path(b['final_state']))
    aa,bb=[read(r/'flow/repair/attempts.json') for r in [reference,actual]];assert len(aa)==len(bb)
    executed=skipped=0
    for x,y in zip(aa,bb):
        assert all(x.get(k)==y.get(k) for k in ['round','candidate_rank','removed_pins','accepted_role'])
        tx,ty=Path(x['transaction']),Path(y['transaction'])
        for name in ['request.txt','domain.txt']:assert sha(tx/name)==sha(ty/name)
        px,py=read(tx/'progress.json'),read(ty/'progress.json');assert px.keys()==py.keys()
        for role,row in py.items():
            if row['status']==SKIPPED:
                assert role=='reuse_off' and py['reuse_on']['policies']['resources_under_timing']['accepted']
                assert not (ty/role).exists() and not row['acceptance_evaluated'];skipped+=1;continue
            original=px[role];assert row['status']==original['status']=='legal_evaluated'
            assert all(row[k]==original[k] for k in ['resources','cpd_s','policies'])
            equal_state(Path(row['evaluation']),Path(original['evaluation']));executed+=1
        files += [tx/'progress.json',ty/'progress.json',tx/'request.txt',ty/'request.txt',tx/'domain.txt',ty/'domain.txt']
    assert skipped==b['actual_native_work']['optional_native_skipped']
    assert b['actual_native_work']['native_transactions']+skipped==a['actual_native_work']['native_transactions']
    return dict(passed=True,all_executed_vectors_ordered_routes_physical_and_decisions_exact=True,
        initial_final_intermediate_selected_states_exact=True,executed_legal_candidates=executed,optional_OFF_controls_unexecuted=skipped,
        reference_complete_wall_seconds=a['complete_wall_seconds'],lazy_complete_wall_seconds=b['complete_wall_seconds'],
        observed_complete_seconds_difference=b['complete_wall_seconds']-a['complete_wall_seconds'],
        resources=b['resources'],CPD_ns=b['CPD_ns'],actual_native_work=b['actual_native_work'],
        source_sha256={str(f):sha(f) for f in files},
        qualification='Each actual complete command builds graph indexes and generates a new initial route. ON-first execution preserves the domain-first acceptance rule and complete source/target/scope/selected-state sequence; every actually computed candidate, including rejection, exactly matches the corresponding reference. Skipped OFF diagnostics have no inferred metric, native execution or decision. Old matched controls remain preserved. Single shared-host development pair with uncontrolled OS cache; observed elapsed difference is not a statistical speedup or a new independent circuit sample.')

pairs={c:compare_pair(D/'complete_serial_transfer_dev_01'/f'{c}_paired',root/f'{c}_paired') for c in ['spmv','softmax']}
write(root/'comparison.json',dict(passed=True,comparisons=pairs,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),root/'queue/completion.json',root/'plan.json']},qualification='Two known-circuit complete fresh-route policy-scheduling transfer checks. Every actual candidate/accepted trajectory is checked against its frozen paired reference; no skipped OFF output is inferred. SPMV zero-scope case retained. Each backend/circuit has one development observation, no statistical timing or unseen-test claim.'))
print({c:{k:p[k] for k in ['reference_complete_wall_seconds','lazy_complete_wall_seconds','optional_OFF_controls_unexecuted']} for c,p in pairs.items()},flush=True)
