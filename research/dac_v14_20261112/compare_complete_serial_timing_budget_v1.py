"""Compare actual fresh-route fixed-102% trajectories with original fixed-100%."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from run_native_scope_policy_v4 import run_dir

root = D / 'complete_serial_timing_budget_01'
q = root / 'queue'
closed = read(q / 'completion.json')
observed = read(q / 'results.json')
plan = read(root / 'plan.json')
assert set(observed) == set(plan['fixed_order'])
files = [Path(__file__).resolve(), root / 'plan.json', q / 'completion.json', q / 'results.json']
cache = {}
def checked(p):
    p = str(Path(p).resolve())
    if p not in cache:
        cache[p] = sha(p)
    return cache[p]
def equal_state(x, y):
    a, b = [read(s / 'endpoint_vector.json') for s in [x, y]]
    return all(a[k] == b[k] for k in ['cpd_s', 'setup', 'hold', 'endpoint_ids', 'constraints_sha256']) and route_body(run_dir(x) / 'routed.route') == route_body(run_dir(y) / 'routed.route')

results = {}
for name in plan['fixed_order']:
    actual = root / name
    prior = D / 'complete_serial_architecture_transfer_01' / name
    measure = read(actual / 'measurement/completion.json')
    files += [actual / 'measurement/completion.json', actual / 'config.json', prior / 'config.json']
    if not observed[name]['passed']:
        results[name] = dict(status='configuration_failed', quality=None,
                             actual_failed_seconds=measure['complete_command_wall_seconds'])
        continue
    a, b = [read(p / 'explicit_policy_verification.json') for p in [actual, prior]]
    for proof in [a, b]:
        assert proof['passed'] and all(checked(p) == h for p, h in proof['source_sha256'].items())
    ca, cb = [read(p / 'config.json') for p in [actual, prior]]
    for k in ['route_command', 'cache_mode', 'domain_mode', 'domain_feedback', 'seed_order']:
        assert ca[k] == cb[k]
    assert ca['cpd_budget_percent'] == a['cpd_budget_percent'] == 102
    assert a['fixed_CPD_limit_s'] == a['initial_CPD_s'] * 102 / 100
    initial, old_initial = [Path(p['initial_state']) for p in [a, b]]
    assert equal_state(initial, old_initial)
    aa, bb = [read(p / 'flow/repair/attempts.json') for p in [actual, prior]]
    matched = []
    for x, y in zip(aa, bb):
        if not equal_state(Path(x['current_state']), Path(y['current_state'])):
            break
        tx, ty = Path(x['transaction']), Path(y['transaction'])
        assert all(checked(tx / n) == checked(ty / n) for n in ['request.txt', 'domain.txt'])
        px, py = read(tx / 'progress.json'), read(ty / 'progress.json')
        candidates = []
        for role in px.keys() & py.keys():
            nx, ny = px[role], py[role]
            if nx['status'] == ny['status'] == 'legal_evaluated':
                assert nx['resources'] == ny['resources'] and nx['cpd_s'] == ny['cpd_s']
                assert equal_state(Path(nx['evaluation']), Path(ny['evaluation']))
                candidates.append(dict(role=role, resources=nx['resources'], CPD_ns=nx['cpd_s'] * 1e9,
                                       original_100percent=ny['policies']['resources_under_timing'],
                                       fixed_102percent=nx['policies']['resources_under_timing']))
        matched.append(dict(round=x['round'], same_actual_source_requests_domains=True,
                            matched_actual_legal_candidates=candidates,
                            actual_accepted_role=x.get('accepted_role'), original_accepted_role=y.get('accepted_role')))
        files += [tx / 'progress.json', ty / 'progress.json', tx / 'request.txt', ty / 'request.txt', tx / 'domain.txt', ty / 'domain.txt']
    results[name] = dict(status='complete_legal_configuration', CPD_ns=a['CPD_ns'], resources=a['resources'],
                         complete_wall_seconds=a['complete_wall_seconds'], fixed_CPD_limit_ns=a['fixed_CPD_limit_s'] * 1e9,
                         original_root_CPD_ns=a['initial_CPD_s'] * 1e9, accepted_steps=a['accepted_steps'],
                         attempted_scopes=a['attempted_scopes'], actual_native_work=a['actual_native_work'],
                         sampled_tree_PSS_peak_kib=a['sampled_tree_PSS_peak_kib'], missing_memory_observations=a['missing_memory_observations'],
                         initial_route_and_full_vector_exact=True,
                         final_route_and_full_vector_equal_to_100percent=equal_state(Path(a['final_state']), Path(b['final_state'])),
                         original_100percent_resources=b['resources'], original_100percent_CPD_ns=b['CPD_ns'],
                         original_100percent_seconds=b['complete_wall_seconds'], matched_actual_source_prefix=matched)
    files += [actual / 'explicit_policy_verification.json', prior / 'explicit_policy_verification.json',
              actual / 'flow/repair/attempts.json', prior / 'flow/repair/attempts.json']
write(root / 'comparison.json', dict(passed=True, registered_roles=2,
      successful_legal_roles=sum(v['status'] == 'complete_legal_configuration' for v in results.values()),
      execution_cohort_all_legal=closed['passed'], results=results,
      source_sha256={str(f): checked(f) for f in files}, native_calls_new=0,
      qualification='Actual complete fresh-route native/domain pair under immutable102percent root CPD cap, with identical100percent input/root controls and matched same-source prefix candidates until real divergence. No rolling budgets. Development threshold chosen after earlier cap rejection, not held-out confirmation. Each full time/quality/memory belongs to its own actual command, no counterfactual costs or history-best selection. Shared-host single observations, not statistical speedups. Original100percent decisions and all rejected/failed outcomes retained.'))
print(dict(passed=True, results=results), flush=True)
