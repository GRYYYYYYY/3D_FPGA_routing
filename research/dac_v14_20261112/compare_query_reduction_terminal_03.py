"""Read sealed development results; never execute routing or accept live checkpoints."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from endpoint_timing_policy_streaming_v2 import compare

ROOT = D / 'query_reduction_resource_dev_01'
PRIOR = D / 'query_reduction_completed_comparison_02'
OUT = D / 'query_reduction_completed_comparison_03'
ROLES = ['eltwise_A0_native', 'eltwise_A0_paired', 'bnn_A0_native', 'bnn_A0_paired']


def bind(path, bound):
    path = Path(path)
    bound[str(path)] = sha(path)


def terminal(path, bound):
    path = Path(path)
    c = read(path / 'completion.json')
    assert c['passed'], f'Unsuccessful terminal: {path}'
    assert all(sha(p) == h for p, h in c['source_sha256'].items()), path
    for name in ['completion.json', 'registration.json', 'attempts.json']:
        bind(path / name, bound)
    return c, read(path / 'registration.json'), read(path / 'attempts.json')


def semantics(path, attempts, bound):
    records = []
    proposed = 0
    for a in attempts:
        request = path / f"round_{a['round']:03d}" / f"candidate_{a['candidate_rank']:02d}" / 'request.txt'
        bind(request, bound)
        lines = request.read_text().splitlines()
        nets = int(lines[0])
        assert lines[nets + 1] == '0'
        count = int(lines[nets + 2])
        assert len(lines) == nets + 3 + count
        proposed += count
        row = {k: a[k] for k in ['round', 'candidate_rank', 'bundle_removed_pins', 'bundle_actual_nets']}
        row['request'] = request.read_text()
        row['roles'] = {name: {k: r.get(k) for k in
            ['status', 'accepted', 'CPD_s', 'resources', 'decision', 'strict_or_endpoint_control']}
            for name, r in a['pair'].items()}
        records.append(row)
    return records, proposed


def compare_role(role, bound):
    old = D / 'stable_seed_transfer_dev_01' / role
    new = ROOT / role
    a, ar, aa = terminal(old, bound)
    b, br, ba = terminal(new, bound)
    for k in ['initial_state', 'domain_mode', 'domain_failure_release', 'anchor',
              'resource_objectives', 'seed_order', 'graph_echo']:
        assert ar[k] == br[k], f'Mismatched {role}: {k}'
    vectors, routes = [], []
    for c in [a, b]:
        state = Path(c['final_state'])
        vector = state / 'endpoint_vector.json'
        route = Path(read(state / 'completion.json')['run']) / 'routed.route'
        bind(vector, bound)
        bind(route, bound)
        vectors.append(read(vector))
        routes.append(route_body(route))
    av, bv = vectors
    old_semantics, old_count = semantics(old, aa, bound)
    new_semantics, new_count = semantics(new, ba, bound)
    return dict(role=role, matched_initial_state=ar['initial_state'], final_resources=b['final_resources'],
        CPD_s=b['final_CPD_s'], accepted_steps=b['accepted_steps'], attempted_scopes=b['attempted_scopes'],
        endpoint_change=compare(av, bv), full_vector_exact=av == bv, route_body_exact=routes[0] == routes[1],
        scope_request_decision_sequence_exact=old_semantics == new_semantics,
        old_proposed_connections=old_count, new_proposed_connections=new_count,
        old_imported_workflow_seconds=a['complete_imported_algorithm_workflow_seconds'],
        new_imported_workflow_seconds=b['complete_imported_algorithm_workflow_seconds'],
        observed_time_difference_seconds=b['complete_imported_algorithm_workflow_seconds'] - a['complete_imported_algorithm_workflow_seconds'],
        complete_single_configuration_seconds=None, independent_new_input=False)


def native_work(path, bound):
    """Count actual executed QUERY rows, including failed/retried work; cache hits are separate."""
    pool = path / 'pool'
    c = read(pool / 'completion.json')
    assert c['passed'] and c['artifacts_unchanged'] and c['static_inputs_unchanged']
    assert all(sha(p) == h for p, h in c['source_sha256'].items())
    bind(pool / 'completion.json', bound)
    bind(pool / 'jobs.json', bound)
    jobs = read(pool / 'jobs.json')
    assert len(jobs) == c['jobs']
    query_count = attempts = transaction_jobs = missing_failed_logs = 0
    query_seconds = child_seconds = request_seconds = 0.0
    for j in jobs:
        assert not j['reused'], 'Executed jobs must not double-count reuse receipts'
        child_seconds += j['native_child_seconds']
        request_seconds += j['complete_request_seconds']
        if not j['native_options'].get('operation', '').startswith('repair'):
            continue
        transaction_jobs += 1
        log = Path(j['native_directory']) / 'joint_native.log'
        if not log.exists():
            assert not j['passed'], 'Successful native repair lacks query log'
            missing_failed_logs += 1
            continue
        expected = j['artifact_sha256'].get(str(log))
        assert expected and sha(log) == expected, log
        bind(log, bound)
        for line in log.open():
            if line.startswith('QUERY '):
                fields = line.split()
                assert len(fields) == 8, line
                query_count += 1
                query_seconds += float(fields[-1])
            elif line.startswith('ATTEMPT '):
                attempts += 1
    return dict(executed_children=len(jobs), repair_children=transaction_jobs,
        failed_children=sum(not j['passed'] for j in jobs), reuse_hits=c['reuse_hits'],
        observed_QUERY_rows=query_count, observed_ATTEMPT_rows=attempts,
        query_log_seconds=query_seconds, child_seconds_sum=child_seconds,
        worker_request_seconds_sum=request_seconds, failed_jobs_without_query_logs=missing_failed_logs,
        query_count_is_complete=missing_failed_logs == 0,
        qualification='QUERY counts actual native connection calls, ATTEMPT includes retries. '
            'Neither is the proposed-cut count. These costs overlap the complete imported workflow; '
            'do not add them to it or treat child/request sums as standalone cold runtime.')


def main():
    queue = ROOT / 'queue'
    # An absent terminal receipt must leave this output absent, not publish a partial success.
    qc = read(queue / 'completion.json')
    bound = {str(Path(__file__).resolve()): sha(__file__)}
    bind(queue / 'completion.json', bound)
    prior = read(PRIOR / 'completion.json')
    assert prior['passed'] and sha(PRIOR / 'rows.json') == prior['rows_sha256']
    assert all(sha(p) == h for p, h in prior['source_sha256'].items())
    bind(PRIOR / 'completion.json', bound)
    bind(PRIOR / 'rows.json', bound)
    # Reuse already audited roles rather than recomputing their endpoint comparisons.
    prior_rows = {r['role']: r for r in read(PRIOR / 'rows.json')}
    rows = []
    for role in ROLES:
        done = ROOT / role / 'completion.json'
        if not done.exists() or not read(done).get('passed'):
            rows.append(dict(role=role, status='terminal_failure' if done.exists() else 'unexecuted_or_missing_terminal',
                queue_receipt=qc.get('results', {}).get(role), complete_single_configuration_seconds=None,
                independent_new_input=False))
            if done.exists():
                bind(done, bound)
            continue
        row = dict(prior_rows[role]) if role in prior_rows else compare_role(role, bound)
        row['status'] = 'sealed_terminal_compared'
        row['reused_prior_comparison'] = role in prior_rows
        row['workload'] = {}
        for label, path in [('old', D / 'stable_seed_transfer_dev_01' / role), ('new', ROOT / role)]:
            c = read(path / 'completion.json')
            bind(path / 'completion.json', bound)
            row[label + '_final_resources'] = c['final_resources']
            row[label + '_CPD_s'] = c['final_CPD_s']
            row['workload'][label] = native_work(path, bound)
        rows.append(row)
    OUT.mkdir(exist_ok=False)
    write(OUT / 'rows.json', rows)
    write(OUT / 'completion.json', dict(passed=True, queue_passed=qc['passed'],
        roles=ROLES, source_sha256=bound, rows_sha256=sha(OUT / 'rows.json'),
        all_roles_sealed=all(r['status'] == 'sealed_terminal_compared' for r in rows),
        native_calls_new=0, new_independent_scientific_inputs=0,
        qualification='Known-input development comparison, including unsuccessful/unexecuted roles. '
            'Changed quality/workload is reported, never forced to equal K8. Complete imported workflow '
            'includes preparation, rejection, auditing and seals; it is not cold complete configuration time. '
            'Historical ordered observations do not establish causal or interleaved speedups. '
            'Eltwise native suspended-parent queue duration remains excluded.'))
    print([dict(role=r['role'], status=r['status']) for r in rows])


if __name__ == '__main__':
    main()
