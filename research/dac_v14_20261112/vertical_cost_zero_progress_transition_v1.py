"""Prove the exact registered zero-progress transition without changing history."""
import copy
import hashlib
import json


def reconcile(zero, progress, terminal, progress_path):
    assert zero['passed'] and zero['zero_equivalence_passed']
    assert zero['mode'] == 'zero' and zero['positive_weights_permitted']
    assert terminal['status'] == 'four_strength_scope_terminal'
    assert terminal['all_roles_accounted'] and terminal['zero_equivalence_passed']
    assert list(progress) == ['weight_0', 'weight_05', 'weight_1', 'weight_2']
    assert progress == terminal['roles']
    row = progress['weight_0']
    assert set(row) == {'status', 'evaluation', 'resources', 'cpd_s', 'policies',
                        'verification_status', 'quality_admitted', 'rollback_verified'}
    assert row['status'] == 'legal_evaluated'
    assert row['verification_status'] == 'passed'
    assert row['quality_admitted'] is True and row['rollback_verified'] is False
    prior = copy.deepcopy(row)
    del prior['verification_status']
    del prior['rollback_verified']
    prior['quality_admitted'] = False
    serialized = (json.dumps({'weight_0': prior}, indent=2) + '\n').encode()
    original = zero['source_sha256'][progress_path]
    assert hashlib.sha256(serialized).hexdigest() == original
    immutable = dict(zero['source_sha256'])
    del immutable[progress_path]
    return dict(immutable_source_sha256=immutable,
                original_progress_sha256=original,
                reconstructed_original_progress_sha256=hashlib.sha256(serialized).hexdigest(),
                transition='Append three registered roles; update zero audit-status fields only',
                original_zero_or_weighted_failures_rewritten=False,
                quality_admission=False)
