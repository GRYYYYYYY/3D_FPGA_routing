"""Diagnose owner registration seals without changing or certifying the run.

The frozen controller binds its already registered runtime configuration just
before execution. Preserve the original verifier failure, prove that precise
metadata transition, and leave full independent verification outstanding.
"""
import copy
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity


def audit_binding(actual_bytes, preparation, execution, controller, expected_runtime, runtime_digest):
    actual=json.loads(actual_bytes)
    assert preparation['passed'] and preparation['transaction_registered']
    assert actual['runtime_config']==str(expected_runtime)
    assert actual['source_sha256'][str(expected_runtime)]==runtime_digest
    assert controller['source_sha256'][str(expected_runtime)]==runtime_digest
    assert execution['registration_sha256']==hashlib.sha256(actual_bytes).hexdigest()
    before=copy.deepcopy(actual)
    del before['runtime_config'];del before['source_sha256'][str(expected_runtime)]
    before_bytes=(json.dumps(before,indent=2)+'\n').encode()
    assert hashlib.sha256(before_bytes).hexdigest()==preparation['registration_sha256']
    return before_bytes


def main():
    case=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/cp1r3_distinct_input_cohort_01/lstm/native')
    cohort=D/'cp1r3_distinct_input_cohort_01';repair=case/'flow/resource_flow/repair'
    out=D/'CP1r3_lstm_native_binding_failure_audit_01';assert not out.exists()
    release=Path(read(cohort/'plan.json')['release'])
    controller_code=release/'runtime/run_unified_resource_repair_v1.py'
    verifier_code=release/'runtime/verify_complete_unified_method_v1.py'
    executor_code=release/'runtime/run_joint_crossing_source_transactions_v2.py'
    text=controller_code.read_text()
    assert "registered['runtime_config']=str(a.runtime_config.resolve())" in text
    assert "registered['source_sha256'][str(a.runtime_config.resolve())]=sha(a.runtime_config)" in text
    assert text.index("write(tx/'registration.json',registered)")<text.index('proc,code,status=run_phase')
    assert "prep['registration_sha256']==sha(tx/'registration.json')" in verifier_code.read_text()
    out.mkdir()
    write(out/'registration.json',dict(kind='read_only_metadata_failure_diagnosis',
        registered_at=datetime.now(timezone.utc).isoformat(),case=str(case),
        rule='Reverse only the two documented pre-execution runtime bindings; require both the original preparation seal and the actual execution seal, anchored to the parent controller runtime binding.',
        original_files_may_be_modified=False,frozen_runtime_may_be_modified=False,
        new_native_or_STA_calls=0,whole_verification_or_confirmation_not_inferred=True))
    started=time.monotonic();controller=read(repair/'registration.json')
    runtime=case/'flow/resource_flow/phase_runtime.json';runtime_digest=sha(runtime)
    measurement=read(case/'measurement/completion.json');flow=read(case/'flow/completion.json')
    result=read(cohort/'lstm_results.json')['native']
    assert result['status']=='execution_or_verification_failed' and result['quality'] is None
    assert result['command_returncode']==0 and measurement['passed'] and measurement['returncode']==0
    assert not measurement['live_descendants_after_command_exit'] and flow['passed']
    live=[]
    for pid,ticks in measurement['process_identities'].items():
        actual=process_identity(int(pid))
        if actual and actual['state']!='Z' and actual['start_ticks']==str(ticks):live.append(actual)
    assert not live
    sources=[controller_code,verifier_code,executor_code,runtime,repair/'registration.json',
        case/'measurement/completion.json',case/'flow/completion.json',case/'verification.log',
        case/'confirmation_input.json',case/'supervision.json',cohort/'plan.json',Path(__file__).resolve()]
    rows=[];reconstructed=[]
    for rank in range(3):
        tx=repair/f'round_004/owner_{rank:02d}'
        prep=read(tx/'preparation.json');execution=read(tx/'execution_registration.json')
        data=(tx/'registration.json').read_bytes()
        before=audit_binding(data,prep,execution,controller,runtime,runtime_digest)
        # Guard the scope of the metadata-only diagnosis. Synthetic mutations
        # remain in memory and are never written as experiment artifacts.
        mutations=[]
        changed=json.loads(data);changed['roles']['joint_native']['queries'][0]['pin']+=1;mutations.append((changed,execution))
        changed=json.loads(data);changed['source_sha256'][str(runtime)]='0'*64;mutations.append((changed,execution))
        changed=json.loads(data);changed['unregistered_extra_field']=True;mutations.append((changed,execution))
        bad_execution=copy.deepcopy(execution);bad_execution['registration_sha256']='0'*64;mutations.append((json.loads(data),bad_execution))
        for changed,exec_receipt in mutations:
            rejected=False
            try:audit_binding((json.dumps(changed,indent=2)+'\n').encode(),prep,exec_receipt,controller,runtime,runtime_digest)
            except AssertionError:rejected=True
            assert rejected,'Semantic/unregistered mutation was accepted'
        rows.append(dict(owner_rank=rank,preparation_passed=prep['passed'],transaction_registered=prep['transaction_registered'],
            original_preparation_registration_sha256=prep['registration_sha256'],actual_registration_sha256=hashlib.sha256(data).hexdigest(),
            original_verifier_equality=False,reconstructed_pre_runtime_sha256=hashlib.sha256(before).hexdigest(),
            exact_preparation_preimage_match=True,actual_execution_registration_match=True,
            execution_registration_status=execution['status'],runtime_digest_matches_parent_and_current_bytes=True,
            only_documented_runtime_binding_changes=True,original_history_rewritten=False))
        reconstructed.append((rank,before))
        sources += [tx/n for n in ['preparation.json','registration.json','execution_registration.json','completion.json']]
    assert all(p.stat().st_size<4*1024**2 for p in sources)
    snapshots=out/'receipt_snapshots';snapshots.mkdir();origins=[]
    for i,source in enumerate(sorted(set(sources))):
        target=snapshots/f'{i:03d}_{source.name}';data=source.read_bytes();target.write_bytes(data)
        origins.append(dict(original=str(source),snapshot=str(target),sha256=sha(target)))
    for rank,data in reconstructed:
        (out/f'owner_{rank:02d}_reconstructed_pre_runtime_registration.json').write_bytes(data)
    write(out/'original_native_result.json',result)
    write(out/'owner_binding_rows.json',rows)
    payload=dict(passed=True,kind='metadata_audit_only',is_experiment_completion=False,
        observed_at=datetime.now(timezone.utc).isoformat(),case=str(case),
        status='documented_pre_execution_runtime_binding_explains_original_verifier_hash_failure',
        original_frozen_verifier_passed=False,original_native_result_status=result['status'],
        original_native_quality=result['quality'],complete_confirmation_passed=False,
        physical_full_request_full_vector_reverification_performed=False,whole_verifier_replayed=False,
        new_native_or_STA_calls=0,new_independent_complete_paired_outcomes=0,paper_benefit_claims_authorized=False,
        original_measured_complete_command_seconds=measurement['complete_command_wall_seconds'],
        original_sampled_tree_PSS_peak_kib=measurement['sampled_tree_PSS_peak_kib'],
        missing_memory_observations=measurement['missing_memory_observations'],observer_CPU_seconds=measurement['observer_CPU_seconds'],
        original_failed_independent_verification_seconds=result['independent_research_verification_seconds'],
        original_measured_identities_repolled=len(measurement['process_identities']),live_original_identities=live,
        original_files_unchanged=True,frozen_runtime_unchanged=True,rows=rows,
        synthetic_reader_guards='In-memory query-pin, runtime-digest, extra-field and execution-seal mutations rejected; not new experiments.',
        complete_metadata_audit_seconds=time.monotonic()-started,
        source_sha256={r['snapshot']:r['sha256'] for r in origins},receipt_origins=origins,
        qualification='The original controller seals preparation before adding its already parent-bound runtime path/hash and seals the augmented registration before native execution. Reversing exactly those documented additions reproduces all three preparation hashes; execution receipts bind the actual augmented bytes. This diagnosis does not replace the failed frozen whole verifier, complete remaining byte/request/STA/physical checks, relabel old completion, admit quality, or establish frozen-controller benefit. Reconstructed images are new audit artifacts, not claimed original historical files. Execution and independent verification costs remain separate; no component assembly or observer CPU subtraction.')
    write(out/'completion.json',payload)
    print(dict(metadata_diagnosis_passed=True,owners=len(rows),original_verifier_passed=False,
        original_native_status=result['status'],complete_command_seconds=measurement['complete_command_wall_seconds'],
        full_quality_admitted=False,native_or_STA_replays=0))


if __name__=='__main__':main()
