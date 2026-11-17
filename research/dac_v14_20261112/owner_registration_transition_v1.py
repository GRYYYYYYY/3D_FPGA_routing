"""Exact preparation-to-execution seal reconciliation, without mutating receipts.

This is a supplementary audit rule, not a change to the frozen confirmation
entry or an authorization to adopt a candidate or claim a method benefit.
"""
import copy
import hashlib
import json


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_transition(actual_bytes, preparation, execution, parent, runtime_path, runtime_bytes):
    assert preparation['passed'] is True and preparation['transaction_registered'] is True
    actual_digest=digest(actual_bytes)
    assert execution['registration_sha256']==actual_digest, 'Actual execution seal differs'
    actual=json.loads(actual_bytes)
    runtime_path=str(runtime_path);runtime_digest=digest(runtime_bytes)
    has_runtime='runtime_config' in actual or runtime_path in actual['source_sha256']
    if has_runtime:
        assert actual['runtime_config']==runtime_path
        assert actual['source_sha256'][runtime_path]==runtime_digest
        assert parent['source_sha256'][runtime_path]==runtime_digest
    if preparation['registration_sha256']==actual_digest:
        return dict(mode='unchanged_preparation_and_execution_bytes',
                    actual_registration_sha256=actual_digest,
                    preparation_registration_sha256=actual_digest)
    assert has_runtime, 'No documented late binding to reconcile'
    assert actual['runtime_config']==runtime_path
    assert actual['source_sha256'][runtime_path]==runtime_digest
    assert parent['source_sha256'][runtime_path]==runtime_digest
    before=copy.deepcopy(actual)
    del before['runtime_config']
    del before['source_sha256'][runtime_path]
    preimage=(json.dumps(before,indent=2)+'\n').encode()
    assert digest(preimage)==preparation['registration_sha256'], 'More than the documented runtime binding changed'
    return dict(mode='exact_documented_pre_execution_runtime_binding',
                actual_registration_sha256=actual_digest,
                preparation_registration_sha256=digest(preimage),
                runtime_sha256=runtime_digest,
                reconstructed_bytes_are_new_audit_evidence=True)
