"""Read only the exact independently audited empty CLSTM supervisor identities."""
from pathlib import Path
from retained_prefix_workflow import read
from recovery_prefix_v1 import live_identity
from empty_interrupted_supervision_identity_v1 import corroborate


def supervision_identity_view(path, plan, case, evidence, audited):
    path = Path(path).resolve()
    exception = plan['empty_supervision_identity_exception']
    expected = Path(exception['exact_empty_path']).resolve()
    if path != expected:
        return read(path)
    assert (plan['pair'], plan['arm']) == ('clstm_input_contract_pair_02', 'domain')
    assert (case['pair'], case['arm']) == (plan['pair'], plan['arm'])
    assert case['passed'] and case['complete_candidate_admitted'] is False
    assert case['full_method_complete'] is False and case['adoption_implemented'] is False
    assert plan['original_role'] == 'reuse_on'
    tx = Path(plan['original_transaction']).resolve()
    assert expected == tx/'reuse_on_native_supervision.json'

    def document(source):
        source = Path(source).resolve()
        assert str(source) in audited, ('Not covered by the actual audit', str(source))
        evidence.bind(source, audited[str(source)])
        return read(source)

    historical = document(exception['historical_failed_summary'])
    old_case = next(row for row in historical['rows']
                    if (row['pair'], row['arm']) == (plan['pair'], plan['arm']))
    assert not old_case['passed'] and 'JSONDecodeError' in old_case['error']
    historical_sha = historical['source_sha256'][str(path)]
    assert str(path) in audited
    current_sha = evidence.bind(path, audited[str(path)])
    active = document(tx/'reuse_on_native_supervision.active.json')
    worker = document(tx/'reuse_on/registration.json')
    done = document(tx/'reuse_on/completion.json')
    seal = document(tx/'reuse_on/input_seal.json')
    actor = document(Path(plan['original_resource_actor'])/'registration.json')
    dead = {k:not live_identity(active[k]['pid'], active[k]['start_ticks'])
            for k in ['supervisor', 'child']}
    dead.update(worker=not live_identity(worker['pid'], worker['start_ticks']),
                actor=not live_identity(actor['pid'], actor['start_ticks']))
    proof = corroborate(str(path), str(expected), current_sha, historical_sha,
                        active, worker, done, seal, dead)
    assert proof == case['supervision_corroboration']
    stage = case['stages']['native_source_control']
    request = case['stages']['exact_complete_ordered_native_request']
    assert request['success'] and request['ordered_prefix_or_full_match']
    assert request['requested'] == request['observed_queries'] == request['successful_queries'] == stage['query_count']
    # Only the original active-record identities go into the existing dead-
    # identity loop. No success status or supervisor exit/completion is supplied.
    return {k:active[k] for k in ['supervisor', 'child']}
