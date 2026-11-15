"""Preserve architecture-transfer denominators and compare only successful pairs."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir

root=D/'complete_serial_architecture_transfer_01';closed=read(root/'queue/completion.json')
plan=read(root/'plan.json');observed=read(root/'queue/results.json')
assert set(observed)==set(plan['fixed_order']) and len(observed)==4
files=[Path(__file__).resolve(),root/'plan.json',root/'queue/completion.json',root/'queue/results.json'];outcomes={};pairs={}
for name in plan['fixed_order']:
    case=root/name;config=read(case/'config.json');measure=read(case/'measurement/completion.json')
    assert all(sha(f)==h for f,h in config['input_sha256'].items())
    files += [case/'config.json',case/'measurement/completion.json']
    if observed[name]['passed']:
        proof=read(case/'explicit_policy_verification.json');assert proof['passed']
        assert all(sha(f)==h for f,h in proof['source_sha256'].items())
        outcomes[name]=dict(status='complete_legal_configuration',architecture=config['architecture_family'],
            **{k:proof[k] for k in ['CPD_ns','resources','complete_wall_seconds','accepted_steps','attempted_scopes','actual_native_work','sampled_tree_PSS_peak_kib','missing_memory_observations']})
        files.append(case/'explicit_policy_verification.json')
    else:
        manifest=case/'flow/initial/runs/state/manifest.json'
        outcome='command_or_verification_failure'
        if manifest.exists():
            m=read(manifest);files.append(manifest)
            if not m.get('metrics',{}).get('routing_success_reported',False):outcome='initial_routing_did_not_report_success'
        outcomes[name]=dict(status=outcome,architecture=config['architecture_family'],measured_failed_execution_seconds=measure['complete_command_wall_seconds'],quality=None,complete_legal_algorithm_time=None)
for family in ['sb','cb']:
    a,b=[root/f'{family}_{role}' for role in ['native','domain']]
    ca,cb=[read(case/'config.json') for case in [a,b]]
    assert ca['route_command']==cb['route_command'] and ca['input_sha256']==cb['input_sha256']
    assert ca['domain_mode']=='unrestricted' and cb['domain_mode']=='paired'
    if not all(observed[f'{family}_{role}']['passed'] for role in ['native','domain']):
        pairs[family]=dict(quality_comparison_available=False,reason='At least one configuration did not complete all legal-flow gates; failure retained in the four-role denominator.')
        continue
    pa,pb=[read(case/'explicit_policy_verification.json') for case in [a,b]]
    sa,sb=[Path(p['initial_state']) for p in [pa,pb]];va,vb=[read(s/'endpoint_vector.json') for s in [sa,sb]]
    assert all(va[k]==vb[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
    assert route_body(run_dir(sa)/'routed.route')==route_body(run_dir(sb)/'routed.route')
    pairs[family]=dict(quality_comparison_available=True,initial_full_vector_and_ordered_route_exact=True,
        initial_CPD_ns=va['cpd_s']*1e9,initial_resources=read(run_dir(sa)/'independent_audit.json')['physical_metrics'],
        domain_minus_native_resources={k:pb['resources'][k]-pa['resources'][k] for k in pa['resources']},
        domain_minus_native_CPD_ns=pb['CPD_ns']-pa['CPD_ns'],observed_seconds_difference=pb['complete_wall_seconds']-pa['complete_wall_seconds'])
write(root/'comparison.json',dict(passed=True,execution_cohort_all_legal=closed['passed'],registered_roles=4,
    successful_legal_roles=sum(r['status']=='complete_legal_configuration' for r in outcomes.values()),outcomes=outcomes,pairs=pairs,
    source_sha256={str(f):sha(f) for f in files},
    qualification='Verification of a prospectively fixed four-role alternate-3D-architecture transfer cohort; passed means records/identities verified, not that failed routing became legal. Failures retain their denominator and measured failed execution time without invented QoR. SB-only/CB-only share the pre-audited plane and fixed packing/placement; comparisons within each architecture use identical physical inputs/options and own-current branches. RR graphs are supplied upstream inputs; graph indexes, fresh routing and all actual repair/checking count inside each complete command. One known-circuit development observation per architecture/role, not held-out or statistical confirmation or equal silicon area.'))
print(dict(passed=True,outcomes=outcomes,pairs=pairs),flush=True)
