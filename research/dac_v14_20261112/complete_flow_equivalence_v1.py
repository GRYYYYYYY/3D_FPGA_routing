"""Compare actual serial states/work, preserving the distinction from final QoR."""
from pathlib import Path
from retained_prefix_workflow import read, sha, route_body
from run_native_scope_policy_v4 import run_dir

VECTOR_KEYS = ['cpd_s', 'setup', 'hold', 'endpoint_ids', 'constraints_sha256']
WORK_KEYS = ['optional_native_skipped', 'native_transactions', 'queries', 'search_attempts', 'domain_releases']

def equal_state(a, b):
    a, b = Path(a), Path(b)
    va, vb = read(a/'endpoint_vector.json'), read(b/'endpoint_vector.json')
    return dict(full_endpoint_vector_exact=all(va[k] == vb[k] for k in VECTOR_KEYS),
                ordered_route_body_exact=route_body(run_dir(a)/'routed.route') == route_body(run_dir(b)/'routed.route'))

def compare(actual, reference):
    actual, reference = Path(actual), Path(reference)
    a, b = [read(p/'explicit_policy_verification.json') for p in [actual, reference]]
    assert a['passed'] and b['passed']
    initial = equal_state(a['initial_state'], b['initial_state'])
    final = equal_state(a['final_state'], b['final_state'])
    aa, bb = [read(p/'flow/repair/attempts.json') for p in [actual, reference]]
    exact = len(aa) == len(bb)
    details = []
    files = []
    def bind_state(state):
        state=Path(state);files.extend([state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'routed.route',run_dir(state)/'manifest.json'])
    for state in [a['initial_state'],b['initial_state'],a['final_state'],b['final_state']]:bind_state(state)
    matched_legal, matched_skips, matched_rollbacks = 0, 0, 0
    for i, (x, y) in enumerate(zip(aa, bb)):
        tx, ty = Path(x['transaction']), Path(y['transaction'])
        same_scope = all(x.get(k) == y.get(k) for k in ['round', 'candidate_rank', 'removed_pins', 'accepted_role'])
        same_request = all(sha(tx/n) == sha(ty/n) for n in ['request.txt', 'domain.txt'])
        source = equal_state(x['current_state'], y['current_state'])
        bind_state(x['current_state']);bind_state(y['current_state'])
        px, py = read(tx/'progress.json'), read(ty/'progress.json')
        same = same_scope and same_request and all(source.values()) and px.keys() == py.keys()
        per_role = {}
        for role in sorted(px.keys() & py.keys()):
            rx, ry = px[role], py[role]
            role_same = rx['status'] == ry['status']
            result = dict(actual_status=rx['status'], reference_status=ry['status'])
            if rx['status'] == ry['status'] == 'legal_evaluated':
                state = equal_state(rx['evaluation'], ry['evaluation'])
                role_same &= all(rx[k] == ry[k] for k in ['resources', 'cpd_s', 'policies']) and all(state.values())
                result.update(state)
                matched_legal += int(role_same)
                bind_state(rx['evaluation']);bind_state(ry['evaluation'])
            elif rx['status'] == ry['status'] == 'not_executed_domain_candidate_accepted':
                role_same &= rx['acceptance_evaluated'] is ry['acceptance_evaluated'] is False
                matched_skips += int(role_same)
            elif rx['status'] == ry['status'] == 'transaction_failed_rolled_back':
                matched_rollbacks += 1
            result['exact_outcome'] = bool(role_same)
            per_role[role] = result
            same &= role_same
        details.append(dict(attempt=i, source=source, scope_exact=same_scope,
                            request_and_domain_exact=same_request, roles=per_role,
                            complete_attempt_exact=bool(same)))
        exact &= same
        files += [tx/'progress.json', ty/'progress.json', tx/'request.txt', ty/'request.txt', tx/'domain.txt', ty/'domain.txt']
    work_a, work_b = [p.get('actual_native_work', {}) for p in [a, b]]
    work_equal = all(work_a.get(k, 0) == work_b.get(k, 0) for k in WORK_KEYS)
    return dict(initial=initial, final=final, actual_attempts=len(aa), reference_attempts=len(bb),
                actual_work={k: work_a.get(k, 0) for k in WORK_KEYS},
                reference_work={k: work_b.get(k, 0) for k in WORK_KEYS}, native_work_exact=work_equal,
                matched_actual_legal_candidates=matched_legal, matched_explicit_skips=matched_skips,
                matched_rollbacks=matched_rollbacks, all_actual_attempts_exact=bool(exact),
                same_final_output=all(final.values()),
                same_complete_execution_states_and_workload=bool(all(initial.values()) and all(final.values()) and exact and work_equal),
                attempts=details, compared_files=list(dict.fromkeys(map(str, files))))
