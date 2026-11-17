"""Publish actual GEMM native timeout, closed index receipts and separately registered CLSTM recovery without changing live inputs."""
import base64
import hashlib
import subprocess
import tempfile
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

repo = D.parents[1]
parent = 'afe8b018375dc89737d26ea2f7b3ee0f840061d0'
branch = 'research/dac-snapshot-20261113'

def git(*args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=repo).decode().strip()

assert git('ls-remote', 'origin', 'refs/heads/' + branch).split()[0] == parent
assert git('rev-parse', 'HEAD') == 'b132a1d13eec8351cfcdc371bfc03611f678291b'
assert sha(repo / '.git/index') == 'fa24adce1cf6f0f4b5da3210992aaac9eeae18b08c42df414aed562490d7574c'
for name in ['submission_candidate_01', 'submission_narrative_02', 'submission_narrative_03', 'submission_narrative_04', 'submission_narrative_05', 'submission_narrative_06']:
    proof = read(D / name / 'verification.json')
    assert proof['passed'] and proof['pages'] == 6
    assert all(sha(p) == h for p, h in proof['source_sha256'].items())
for name in ['confirmation_priority_handoff_02', 'confirmation_priority_handoff_03',
             'confirmation_priority_handoff_04', 'confirmation_priority_handoff_05']:
    assert all(sha(p) == h for p, h in read(D / name / 'plan.json')['protected_source_sha256'].items())
assert all(sha(p) == h for p, h in read(D / 'vertical_cost_baseline_dev_01/execution_plan.json')['source_sha256'].items())
for ref in ['9734eee', '279bdb4']:
    subprocess.run(['git', '-c', 'gc.auto=0', 'merge-base', '--is-ancestor', ref, parent], cwd=repo, check=True)
result = read(D / 'LSTM_complete_execution_01/verification_result.json')
assert result['formal_pair_ratio'] is None
assert all(not role['quality_admitted'] and role['original_verification'] == 'failed'
           for role in result['roles'].values())
dla = read(D / 'DLA_small_initial_failure_01/checkpoint.json')
assert dla['status'] == 'both_original_arms_initial_route_failed_no_legal_root'
assert dla['formal_pair_ratio'] is None
assert dla['failure_pair_matching']['initial_command_equal_after_output_arm_path_normalization']
assert all(dla[arm]['status'] == 'initial_route_failed' and not dla[arm]['quality_admitted'] for arm in ['native', 'domain'])
status = read(D / 'CURRENT_STATUS.json')
assert status['simple_vertical_cost_baseline_terminal']['zero_equivalence_passed']
assert status['simple_vertical_cost_confirmed_controls']['status']=='all_four_strengths_legal_independently_admitted_all_resource_policy_rejected'
assert read(D/'vertical_cost_admission_reconciliation_01/execution/completion.json')['all_three_roles_passed']
assert read(D/'CLSTM_domain_empty_supervision_audit_02/audit.json')['passed']
assert not read(D/'CLSTM_domain_empty_supervision_audit_02/audit.json')['complete_candidate_admitted']
assert all(sha(p)==h for p,h in read(D/'CLSTM_domain_empty_supervision_audit_02/execution_plan.json')['source_sha256'].items())
assert status['CP1r3_registered_admission_terminal']['quality_admitted_roles']==0
assert status['LSTM_complete_execution_verification']['formal_pair_ratio'] is None
assert status['reduction_domain_complete_recovery']['domain']['passed']
assert status['reduction_domain_complete_recovery']['formal_time_ratio'] is None
assert not read(D/'interrupted_flow_recovery_01/queue_priority_05/completion.json')['passed']
assert read(D/'planner_numeric_slack_replay_02/completion.json')['passed']
assert not read(D/'planner_numeric_slack_replay_01/completion.json')['passed']
assert read(D/'confirmation_release_cp1r4_01/completion.json')['passed']
assert read(D/'confirmation_release_cp1r4_01/public_source_reconstruction.json')['passed']
gemm=read(D/'cp1r4_gemm_pair_01/plan.json')
assert all(sha(p)==h for p,h in gemm['source_sha256'].items())
assert sha(Path(gemm['release'])/'release_manifest.json')==gemm['release_manifest_sha256']
assert sha(Path(gemm['release'])/'runtime/plan_current_critical_group.py')==read(D/'planner_numeric_slack_dev_01/registration.json')['development_planner_sha256']
assert read(D/'GEMM_complete_execution_01/checkpoint.json')['quality_admitted_roles']==0
assert read(D/'LSTM_necessary_readonly_02/queue/completion.json')['passed']
assert read(D/'LSTM_necessary_readonly_02/native_raw/completion.json')['quality_admitted']
assert not read(D/'LSTM_necessary_readonly_02/domain_failed_evaluation/audit.json')['whole_role_admitted']
assert read(D/'CLSTM_domain_recovery_failure_02/checkpoint.json')['actual_old_native_queries_consumed']==0
assert read(D/'CLSTM_domain_manifest_audit_03/audit.json')['passed']
assert read(D/'CLSTM_domain_recovery_03/first_reused_transaction_terminal_01/checkpoint.json')['old_native_queries_actually_reused']==23
for rel in ['CLSTM_domain_recovery_02/execution_plan.json','CLSTM_domain_recovery_03/execution_plan.json','LSTM_necessary_readonly_02/execution_plan.json']:
    assert all(sha(p)==h for p,h in read(D/rel)['source_sha256'].items())
files=[repo/'README.md',repo/'docs/GitHub_GEMM_LSTM_submission_20261117.md',repo/'docs/github_GEMM_native_timeout_publication_receipt_20261117.json']
files += [D/n for n in ['CURRENT_STATUS.json','CURRENT_STATUS.md','refresh_current_status_20261114.py','render_current_status_md_v1.py','prepare_GEMM_LSTM_submission_publication_55.py','cp1r3_supplemental_verifier_v2.py','audit_lstm_native_raw_02.py','audit_lstm_failed_evaluation_01.py','queue_lstm_necessary_readonly_02.py','audit_interrupted_clstm_domain_03.py','queue_CLSTM_domain_recovery_03.py']]
for name in ['CLSTM_domain_complete_recovery_03','GEMM_complete_execution_01','CLSTM_domain_recovery_failure_02','CLSTM_domain_manifest_audit_03','submission_narrative_06','LSTM_necessary_readonly_02','CP1r3_supplemental_verifier_02']:
    files += [p for p in (D/name).rglob('*') if p.is_file() and p.name!='memory_samples.jsonl' and (not p.is_relative_to(D/'submission_narrative_06/build') or p.name in ['main.pdf','text_check.json','build_receipt.json','contact_sheet.jpg','table_page_4.png','table_page_5.png'])]
root=D/'cp1r4_gemm_pair_01'
files += [root/n for n in ['gemm_results.json','gemm_comparison.json','comparison.json','queue/completion.json','queue/status.json']]
root=D/'CLSTM_domain_recovery_02'
files += [root/n for n in ['result.json','queue/completion.json','queue/status.json','byte_revalidation.json']]
root=D/'CLSTM_domain_recovery_03'
files += [root/n for n in ['STATUS.md','actual_source_stage_evidence.json','execution_plan.json','validation.json','arm/plan.json','queue/registration.json','byte_revalidation.json']]
files += [p for p in (root/'runtime_extension').glob('*.py')]
files += [p for p in (root/'first_reused_transaction_terminal_01').rglob('*') if p.is_file() and p.name!='12_independent_audit.json']
files += [root/n for n in ['result.json','queue/completion.json','queue/status.json']]
files += [p for p in (root/'publication_observation_01').rglob('*') if p.is_file()]
scratch=Path(tempfile.mkdtemp(prefix='GEMM-LSTM-submission55-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
known = {line.split()[2] for line in git('ls-tree', '-r', parent).splitlines()}
entries, manifest, binaries = [], [], {}
for path in sorted(set(files)):
    assert path.stat().st_size < 3_000_000
    data = path.read_bytes()
    relative = str(path.relative_to(repo))
    target = scratch / 'files' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    entry = dict(path=relative, mode='100644', type='blob')
    if blob in known:
        entry['sha'] = blob
    else:
        try:
            entry['content'] = data.decode('utf-8')
        except UnicodeDecodeError:
            entry['sha'] = blob
            binaries[blob] = dict(sha=blob, content=base64.b64encode(data).decode(), source=relative)
    entries.append(entry)
    manifest.append(dict(path=relative, git_blob=blob, sha256=sha(target), bytes=len(data)))
payload = dict(parent=parent, base_tree=git('rev-parse', parent + '^{tree}'),
               entries=entries, binary_uploads=list(binaries.values()))
write(scratch / 'payload.json', payload)
info = dict(parent=parent, base_tree=payload['base_tree'], scratch=str(scratch),
            files=len(manifest), bytes=sum(row['bytes'] for row in manifest),
            payload_chars=len((scratch / 'payload.json').read_text()), binary_blobs=len(binaries),
            live_head=git('rev-parse', 'HEAD'), index_sha256=sha(repo / '.git/index'),
            remote_main=git('ls-remote', 'origin', 'refs/heads/main').split()[0])
write(repo / 'docs/github_GEMM_LSTM_submission55_prepared_20261117.json', info)
write(repo / 'docs/github_GEMM_LSTM_submission55_manifest_20261117.json', manifest)
print(info, flush=True)
