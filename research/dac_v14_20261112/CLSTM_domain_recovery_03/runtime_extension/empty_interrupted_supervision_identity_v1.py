"""Corroborate an exact empty historical receipt without inventing its exit."""
import hashlib


def corroborate(path, expected_path, empty_sha, historical_sha,
                active, worker, completion, seal, original_identities_dead):
    assert path == expected_path
    assert empty_sha == historical_sha == hashlib.sha256(b'').hexdigest()
    assert set(active) >= {'supervisor', 'child'}
    assert set(original_identities_dead) == {'supervisor', 'child', 'worker', 'actor'}
    assert all(value is True for value in original_identities_dead.values())
    child = active['child']
    assert child['pid'] == worker['pid']
    assert str(child['start_ticks']) == str(worker['start_ticks'])
    assert active['supervisor']['pid'] != child['pid']
    for identity in [active['supervisor'], child]:
        assert isinstance(identity['pid'], int) and identity['pid'] > 0
        assert str(identity['start_ticks']).isdigit() and int(identity['start_ticks']) > 0
    assert completion['passed'] is True
    assert completion['observation_only'] is True
    assert completion['process_status'] == 'completed'
    required = {'completed', 'native_FULL', 'inputs_unchanged', 'route_loaded',
                'physical_audit', 'native_control_complete', 'inputs_sealed'}
    assert required <= set(completion['checks'])
    assert all(v is True for k,v in completion['checks'].items()
               if k != 'CPD_matches_original')
    assert seal['passed'] is True
    return dict(kind='independent_dead_identity_corroboration',
                original_empty_sha256=empty_sha,
                supervisor_identity=active['supervisor'], worker_identity=child,
                original_supervisor_exit_status='unknown',
                original_supervisor_completion_created=False,
                complete_actual_byte_and_candidate_admission=False)
