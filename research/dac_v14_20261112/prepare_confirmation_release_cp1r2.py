"""New frozen release for vanished-proc handling; preserve CP1 and algorithm rules."""
import fcntl
import shutil
import subprocess
import os
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

home = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home')
old = home/'confirmation_releases/current_sta_cp1'
root = home/'confirmation_releases/current_sta_cp1r2'
out = D/'confirmation_release_cp1r2_01'
assert read(D/'execution_reconciliation_20261116_01/completion.json')['passed']
test = D/'method_phase_proc_race_validation_02/completion.json'
assert read(test)['passed']
parent = read(old/'release_manifest.json')
assert all(sha(old/p)==h for p,h in parent['files_sha256'].items())
assert not root.exists() and not out.exists()
shutil.copytree(old,root,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
root.chmod(0o755)
(root/'runtime').chmod(0o755)
out.mkdir()
# Match executable bits to original CP1, then execute its complete guard suite.
assert (root/'runtime/seccomp_thread_guard').stat().st_mode & 0o111
check=subprocess.run(['/usr/bin/python3',str(root/'runtime/test_seccomp_thread_guard.py')],capture_output=True,text=True,timeout=60,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
assert check.returncode==0,check.stderr
write(out/'guard_execution.json',dict(passed=True,returncode=check.returncode,stdout=check.stdout,source_sha256={str(root/'runtime'/name):sha(root/'runtime'/name) for name in ['seccomp_thread_guard','test_seccomp_thread_guard.py']},VPR_calls_new=0))


def replace(path, content):
    path.chmod(0o644)
    path.write_text(content)

supervisor = root/'runtime/supervise_method_phase.py'
replace(supervisor,(D/'supervise_method_phase_v2.py').read_text())
assert sha(supervisor)==sha(D/'supervise_method_phase_v2.py')
artifact = root/'runtime/artifact_manifest.json'
a = read(artifact)
a['sha256']['supervise_method_phase.py'] = sha(supervisor)
a['component_revision'] = 'complete_method_cp1r2_proc_lifecycle'
a['qualification'] = 'CP1 algorithm files and historical component manifests preserved. Only active supervisor handles vanished /proc reads; current artifact seal supersedes historical supervisor hash. No completed CP1r2 native result inferred.'
artifact.chmod(0o644);write(artifact,a)
assert all(sha(root/'runtime'/p)==h for p,h in a['sha256'].items())
changed_runtime = [p for p in parent['files_sha256'] if p.startswith('runtime/') and sha(root/p)!=parent['files_sha256'][p]]
assert set(changed_runtime)=={'runtime/supervise_method_phase.py','runtime/artifact_manifest.json'}

entry = root/'confirmation.py'
text = entry.read_text()
assert text.count("m['release_id']=='current_sta_cp1'")==1
replace(entry,text.replace("m['release_id']=='current_sta_cp1'", "m['release_id']=='current_sta_cp1r2'"))
entry_text=entry.read_text()
check_anchor="    contract_path=release_root/'contract.json';contract=read(contract_path)"
assert entry_text.count(check_anchor)==1
entry_text=entry_text.replace(check_anchor,"    for name,mode in m['executable_modes'].items():\n        executable=release_root/name\n        assert executable.stat().st_mode & 0o777 == mode and os.access(executable,os.X_OK),('Missing executable mode',name)\n"+check_anchor)
replace(entry,entry_text)
contract = read(old/'contract.json')
contract['release_id']='current_sta_cp1r2'
contract['internal_compatibility_tag']='Inherited development_v1 compatibility tag; CP1r2 changes only vanished-proc supervision, plus release seals. Algorithm and fixed rules identical to CP1.'
(root/'contract.json').chmod(0o644);write(root/'contract.json',contract)
prior_contract=read(old/'contract.json')
assert {k for k in contract if contract[k]!=prior_contract[k]}=={'release_id','internal_compatibility_tag'}

inventory=read(old/'dependency_inventory.json')
inventory['runtime_tree_sha256']={str(p.relative_to(root/'runtime')):sha(p) for p in (root/'runtime').rglob('*') if p.is_file()}
(root/'dependency_inventory.json').chmod(0o644);write(root/'dependency_inventory.json',inventory)
(root/'execution_evidence.json').chmod(0o644)
write(root/'execution_evidence.json',dict(parent_release_manifest_sha256=sha(old/'release_manifest.json'),
    parent_execution_evidence_sha256=sha(old/'execution_evidence.json'),
    actual_validation_sha256={str(test):sha(test)},
    algorithm_files_byte_identical_to_CP1=True,supervisor_process_tests_passed=True,
    complete_CP1r2_native_execution_verified=False,
    qualification='Inherited algorithm execution evidence remains scoped to CP1/dev03; new supervision tested with real processes and injected disappearance errors. No complete native rerun or new algorithm evidence is claimed.'))
write(root/'supervision_revision.json',dict(parent_release='current_sta_cp1',
    parent_manifest_sha256=sha(old/'release_manifest.json'),
    changed_runtime_files=changed_runtime,algorithm_configuration_unchanged=True,
    diagnosis='ProcessLookupError during proc stat or children read must be treated like FileNotFoundError. Permission and other errors remain visible.',
    validation=read(test),reconciliation_sha256=sha(D/'execution_reconciliation_20261116_01/completion.json')))
replace(root/'README.md','''# Current-STA confirmation CP1r2

CP1r2 is a new frozen release after a real Linux process-lifecycle defect interrupted five development arms. CP1 remains unchanged. The only executable runtime change catches ProcessLookupError alongside FileNotFoundError when reading process identity and descendants. Timeout, kill ownership, observation, selectors, route options, acceptance and terminal rules remain unchanged. confirmation.py admits the release identifier and checks required executable modes before native work. See supervision_revision.json for exact evidence and file changes.

Use the same check/run-arm/verification CLI and external physical inputs as CP1, binding this release_manifest.json and contract.json in both arm configs. CPython3.10 Linux x86_64 and the pinned NumPy2.2.6/lxml6.1.3 dependencies remain required. No historical route or candidate is imported. Every new cohort must freeze this release and its input/rule digests before outcomes. Initial legal states or interrupted trajectories are not complete-method evidence. Full paired confirmation is pending.

Historical component manifests inside runtime record previous packages; runtime/artifact_manifest.json and the outer release manifest identify the active bytes. The original CP1 archive remains an independently preserved historical release.
''')
write(root/'executable_modes.json',{'runtime/seccomp_thread_guard':0o555})
manifest=dict(release_id='current_sta_cp1r2',status='fixed_confirmation_source',
    parent_release_manifest_sha256=sha(old/'release_manifest.json'),
    runtime_byte_identical_to_executed_dev03=False,algorithm_byte_identical_to_CP1=True,
    runtime_files=116,public_evidence_base='9734eee',confirmation_results_available=False,
    executable_modes={'runtime/seccomp_thread_guard':0o555},
    files_sha256={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and p!=root/'release_manifest.json'})
(root/'release_manifest.json').chmod(0o644);write(root/'release_manifest.json',manifest)
assert all(sha(root/p)==h for p,h in manifest['files_sha256'].items())
assert all(sha(old/p)==h for p,h in parent['files_sha256'].items())
for name in ['release_manifest.json','contract.json','supervision_revision.json','execution_evidence.json','README.md']:
    shutil.copy2(root/name,out/name)
write(out/'completion.json',dict(passed=True,release=str(root),
    release_manifest_sha256=sha(root/'release_manifest.json'),
    original_CP1_preserved=True,algorithm_configuration_unchanged=True,
    changed_runtime_files=changed_runtime,actual_process_tests=str(test),
    native_calls_new=0,complete_native_confirmation_pending=True,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'supervise_method_phase_v2.py',test,old/'release_manifest.json']}))
for p in root.rglob('*'):
    if p.is_file():p.chmod(p.stat().st_mode & ~0o222)
    elif p.is_dir():p.chmod(0o555)
root.chmod(0o555)
print(dict(passed=True,release=str(root),changed_runtime_files=changed_runtime))
