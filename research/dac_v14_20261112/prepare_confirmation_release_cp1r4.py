"""Freeze only the actual-replayed numeric slack fix in a separate CP1r4 release."""
import fcntl
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

home = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home')
old = home / 'confirmation_releases/current_sta_cp1r3'
root = home / 'confirmation_releases/current_sta_cp1r4'
out = D / 'confirmation_release_cp1r4_01'


def main():
    started = time.monotonic()
    plan = read(out / 'plan.json')
    with (D / 'critical_scope_runner.lock').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert all(sha(p) == h for p, h in plan['source_sha256'].items())
        replay = read(D/'planner_numeric_slack_replay_02/completion.json')
        assert replay['passed'] and all(x['exact_original_nonplanner_input_bindings'] for x in replay['roles'])
        parent = read(old/'release_manifest.json')
        assert sha(old/'release_manifest.json') == plan['parent_manifest_sha256']
        assert all(sha(old/p) == h for p, h in parent['files_sha256'].items())
        assert not root.exists() and not (out/'completion.json').exists()
        shutil.copytree(old, root, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        root.chmod(0o755)
        (root/'runtime').chmod(0o755)

        def replace(path, text):
            path.chmod(0o644)
            path.write_text(text)

        planner = D/'planner_numeric_slack_dev_01/plan_current_critical_group.py'
        previous = (old/'runtime/plan_current_critical_group.py').read_text()
        revised = planner.read_text()
        assert revised.replace("float(sta[x]['setup_slack_s'])>float(cone['worst_slack_s'])",
                               "sta[x]['setup_slack_s']>cone['worst_slack_s']").replace(
                               "(float(sta[x]['setup_slack_s']),x)", "(sta[x]['setup_slack_s'],x)") == previous
        compile(revised, str(planner), 'exec')
        replace(root/'runtime/plan_current_critical_group.py', revised)
        artifact = read(old/'runtime/artifact_manifest.json')
        artifact['sha256']['plan_current_critical_group.py'] = sha(root/'runtime/plan_current_critical_group.py')
        artifact['component_revision'] = 'complete_method_cp1r4_numeric_slack'
        artifact['qualification'] = 'CP1r3 runtime with numeric slack comparison/sort normalization only. Actual +inf donor failure reproduced and both full planners replayed. No budget, native search, physical delay, acceptance or terminal policy change.'
        replace(root/'runtime/artifact_manifest.json', json.dumps(artifact, indent=2)+'\n')
        assert all(sha(root/'runtime'/p) == h for p, h in artifact['sha256'].items())
        changed = [p for p,h in parent['files_sha256'].items()
                   if p.startswith('runtime/') and sha(root/p) != h]
        assert set(changed) == {'runtime/artifact_manifest.json', 'runtime/plan_current_critical_group.py'}
        entry = (old/'confirmation.py').read_text()
        assert entry.count("m['release_id']=='current_sta_cp1r3'") == 1
        replace(root/'confirmation.py', entry.replace("m['release_id']=='current_sta_cp1r3'", "m['release_id']=='current_sta_cp1r4'"))
        contract = read(old/'contract.json')
        original_contract = read(old/'contract.json')
        contract.update(release_id='current_sta_cp1r4',
                        internal_compatibility_tag='CP1r3 complete method with numeric slack normalization at donor/cutoff comparison and target sorting; finite rules and all fixed budgets remain unchanged.',
                        current_execution_boundary='Actual SB-layout +inf donor token and two full planner replays verified; no CP1r4 native candidate or complete confirmation is inferred.')
        for key in plan['unchanged_contract_fields']:
            assert contract[key] == original_contract[key], key
        replace(root/'contract.json', json.dumps(contract, indent=2)+'\n')
        inventory = read(old/'dependency_inventory.json')
        inventory['runtime_tree_sha256'] = {str(p.relative_to(root/'runtime')):sha(p)
                                           for p in (root/'runtime').rglob('*') if p.is_file()}
        replace(root/'dependency_inventory.json', json.dumps(inventory, indent=2)+'\n')
        guard = root/'runtime/seccomp_thread_guard'
        assert guard.stat().st_mode & 0o777 == 0o555 and os.access(guard, os.X_OK)
        test = subprocess.run(['/usr/bin/python3', str(root/'runtime/test_seccomp_thread_guard.py')],
                              capture_output=True, text=True, timeout=60,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
        assert test.returncode == 0, (test.stdout, test.stderr)
        write(out/'guard_execution.json', dict(passed=True, returncode=0, stdout=test.stdout,
                                               guard_sha256=sha(guard), new_native_calls=0))
        evidence = dict(parent_release_manifest_sha256=sha(old/'release_manifest.json'),
                        actual_numeric_slack_replay_sha256=sha(D/'planner_numeric_slack_replay_02/completion.json'),
                        actual_token_values=['+inf'], full_original_nonplanner_bindings_exact=True,
                        original_diagnostic_failure_retained=True, original_CP1r3_failures_preserved=True,
                        guard_execution=True, native_calls_new=0, full_method_confirmation=False,
                        acceptance_native_physical_delay_and_terminal_bytes_unchanged=True)
        replace(root/'execution_evidence.json', json.dumps(evidence, indent=2)+'\n')
        write(root/'numeric_slack_revision.json', dict(parent='current_sta_cp1r3',
              changed_runtime_files=changed, source_sha256=plan['source_sha256'], evidence=evidence))
        replace(root/'README.md', '''# Current-STA confirmation CP1r4

Separate frozen successor to CP1r3. Only the planner's numeric donor/cutoff slack comparison and numeric target-sort key change; actual serialized +inf in both SB-layout arms and full original-input planner replays validate the correction. No native candidate or complete method outcome follows from those proposals. The failed diagnostic first attempt and all original CP1r3 failures/costs remain intact.

Native binaries, physical Tdel, search scope/order, resource root envelopes, per-net failure release, owner coordination, whole-group acceptance, terminal selection and phase guards retain CP1r3 bytes/rules. No empty-query or vertical-cost exploration patch is installed. New native/domain configs must both bind this fixed release. Physical input compatibility, fresh legal roots, full byte/request/FULL/STA/vector/physical checks and actual complete per-arm timing remain mandatory. A known historical GEMM input is a different circuit in the same architecture family, not an unseen source or new architecture.

Use the check/run-arm CLI with newly registered external inputs and pinned dependencies. Parent freeze/precision/supervision receipts are retained provenance. Current outer manifest and numeric_slack_revision bind this source. Source/wheel reconstruction and relocated admission are recorded separately before any new confirmation execution. Research has no date/call/matrix stopping condition.
''')
        manifest = dict(release_id='current_sta_cp1r4', status='fixed_confirmation_source',
                        public_evidence_base='9734eee', subsequent_public_evidence='279bdb4',
                        parent_release_manifest_sha256=sha(old/'release_manifest.json'),
                        runtime_files=len(artifact['sha256'])+1,
                        changed_runtime_files=changed, added_runtime_files=[],
                        fixed_configuration_acceptance_and_terminal_unchanged=True,
                        confirmation_results_available=False, executable_modes=parent['executable_modes'],
                        files_sha256={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*'))
                                      if p.is_file() and p != root/'release_manifest.json'})
        replace(root/'release_manifest.json', json.dumps(manifest, indent=2)+'\n')
        assert all(sha(root/p) == h for p,h in manifest['files_sha256'].items())
        assert all(sha(old/p) == h for p,h in parent['files_sha256'].items())
        for name in ['release_manifest.json', 'contract.json', 'numeric_slack_revision.json', 'execution_evidence.json', 'README.md']:
            shutil.copyfile(root/name, out/name)
        for p in root.rglob('*'):
            if p.is_file():p.chmod(p.stat().st_mode & ~0o222)
            elif p.is_dir():p.chmod(0o555)
        root.chmod(0o555)
        write(out/'completion.json', dict(passed=True, release=str(root),
              release_manifest_sha256=sha(root/'release_manifest.json'),
              original_CP1r3_preserved=True, changed_runtime_files=changed,
              algorithm_fixed_configuration_unchanged=True, new_native_calls=0,
              complete_freeze_scope_seconds=time.monotonic()-started,
              public_reconstruction_pending=True, complete_confirmation_pending=True,
              source_sha256=plan['source_sha256']))


if __name__ == '__main__':
    main()
