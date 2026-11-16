"""Actual completed-role regression plus mismatched-input and failure-accounting guards."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import compare_query_reduction_terminal_03 as m
from retained_prefix_workflow import D, read, write, sha

out = D / 'query_reduction_terminal_03_validation.json'
assert not out.exists()
bound = {str(p): sha(p) for p in [Path(__file__).resolve(), Path(m.__file__),
    D / 'watch_query_reduction_analysis_03.py', m.PRIOR / 'rows.json']}
actual = m.compare_role('eltwise_A0_native', bound)
assert actual == next(r for r in read(m.PRIOR / 'rows.json') if r['role'] == 'eltwise_A0_native')
work = m.native_work(m.ROOT / 'eltwise_A0_native', bound)
assert work['observed_QUERY_rows'] == 94 and work['observed_ATTEMPT_rows'] == 154
assert work['query_count_is_complete']

original_read = m.read
def mismatched_read(path):
    result = original_read(path)
    if Path(path) == m.ROOT / 'eltwise_A0_native/registration.json':
        result = dict(result, seed_order='deliberately_mismatched_validation')
    return result
with patch.object(m, 'read', mismatched_read):
    try:
        m.compare_role('eltwise_A0_native', {})
    except AssertionError as exc:
        assert 'seed_order' in str(exc)
    else:
        raise AssertionError('Mismatched seed policy accepted')

with TemporaryDirectory(prefix='query_reduction_terminal_guard_') as temp:
    root = Path(temp)
    with patch.object(m, 'ROOT', root), patch.object(m, 'OUT', root / 'forbidden_output'):
        try:
            m.main()
        except FileNotFoundError:
            pass
        else:
            raise AssertionError('Nonterminal input accepted')
        assert not m.OUT.exists()
    pool = root / 'pool'
    pool.mkdir()
    native = root / 'native'
    native.mkdir()
    log = native / 'joint_native.log'
    log.write_text('ATTEMPT 1 2 1 1 0\nQUERY 1 2 0 0.5 10 8 0.125\n')
    job = dict(reused=False, native_child_seconds=0.4, complete_request_seconds=0.5,
        native_options=dict(operation='repair_fused'), native_directory=str(native),
        passed=False, artifact_sha256={str(log): sha(log)})
    write(pool / 'jobs.json', [job])
    write(pool / 'completion.json', dict(passed=True, artifacts_unchanged=True,
        static_inputs_unchanged=True, source_sha256={str(pool / 'jobs.json'): sha(pool / 'jobs.json')},
        jobs=1, reuse_hits=2))
    failed = m.native_work(root, {})
    assert failed['failed_children'] == 1 and failed['observed_QUERY_rows'] == 1
    assert failed['query_log_seconds'] == 0.125 and failed['reuse_hits'] == 2
    assert failed['query_count_is_complete']
    log.unlink()
    missing = m.native_work(root, {})
    assert missing['failed_jobs_without_query_logs'] == 1 and not missing['query_count_is_complete']

write(out, dict(passed=True, source_sha256=bound, native_calls_new=0,
    checks=['completed_eltwise_native_row_exactly_matches_existing_comparison',
        'actual_QUERY_94_and_ATTEMPT_154_counted_separately', 'mismatched_seed_policy_rejected',
        'missing_terminal_creates_no_output', 'failed_native_QUERY_cost_preserved',
        'missing_failed_log_marks_query_count_incomplete'],
    qualification='Read-only comparator validation only; no new scientific input or native experiment. '
        'Fourth role still requires its real terminal and context seals.'))
print(dict(passed=True, actual_query_rows=94, actual_attempt_rows=154, native_calls_new=0))
