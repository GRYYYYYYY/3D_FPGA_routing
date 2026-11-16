"""Freeze a separate observation-precision correction after actual trace audit.

This script is invoked only by its registered serial-lock owner. It neither
modifies CP1r2 nor launches a VPR/query/STA experiment.
"""
import os,shutil,subprocess,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

home=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home')
old=home/'confirmation_releases/current_sta_cp1r2'
root=home/'confirmation_releases/current_sta_cp1r3'
out=D/'confirmation_release_cp1r3_01';plan=read(out/'plan.json')
assert os.environ.get('H3D_CP1R3_SERIAL_OWNER')==str(os.getppid())
assert all(sha(f)==h for f,h in plan['source_sha256'].items())
parent=read(old/'release_manifest.json');assert sha(old/'release_manifest.json')==plan['parent_manifest_sha256']
assert all(sha(old/f)==h for f,h in parent['files_sha256'].items())
patch=D/'observation_precision_patch_02';prep=read(patch/'preparation.json')
audit=read(D/'robot_owner_reentry_audit_02/completion.json')
assert audit['passed'] and audit['existing_reload_exact_identity']['passed']
assert all(audit['existing_reload_exact_identity']['checks'].values())
assert read(D/'observation_timing_identity_validation_02/completion.json')['passed']
assert not root.exists() and not (out/'completion.json').exists()
shutil.copytree(old,root,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
root.chmod(0o755);(root/'runtime').chmod(0o755)
def replace(path,text):
    if path.exists():path.chmod(0o644)
    path.write_text(text)

workers=prep['patched_workers_sha256']
for name,digest in workers.items():
    assert sha(old/'runtime'/name)==prep['parent_workers_sha256'][name]
    assert sha(patch/name)==digest
    compile((patch/name).read_text(),name,'exec');replace(root/'runtime'/name,(patch/name).read_text())
helper='observation_timing_identity_v2.py';assert sha(patch/helper)==prep['helper_sha256']
replace(root/'runtime'/helper,(patch/helper).read_text())
a=read(old/'runtime/artifact_manifest.json')
for name in [*workers,helper]:a['sha256'][name]=sha(root/'runtime'/name)
a['component_revision']='complete_method_cp1r3_exact_observation_identity'
a['qualification']='Active CP1r3 observation workers normalize only displayed CPD fields and require exact fresh-STA CPD/setup/hold/endpoint/constraint identity. Selectors, transactions, acceptance and terminal rules retain CP1r2 bytes. Historical component manifests remain provenance.'
replace(root/'runtime/artifact_manifest.json',__import__('json').dumps(a,indent=2)+'\n')
assert all(sha(root/'runtime'/f)==h for f,h in a['sha256'].items())
changed=[f for f,h in parent['files_sha256'].items() if f.startswith('runtime/') and sha(root/f)!=h]
assert set(changed)=={'runtime/artifact_manifest.json',*['runtime/'+n for n in workers]}
added={str(f.relative_to(root)) for f in root.rglob('*') if f.is_file()}-set(parent['files_sha256'])-{'release_manifest.json'}
assert added=={'runtime/'+helper},added

entry=(old/'confirmation.py').read_text();assert entry.count("m['release_id']=='current_sta_cp1r2'")==1
replace(root/'confirmation.py',entry.replace("m['release_id']=='current_sta_cp1r2'","m['release_id']=='current_sta_cp1r3'"))
contract=read(old/'contract.json');fixed=contract['fixed_configuration'].copy()
contract.update(release_id='current_sta_cp1r3',internal_compatibility_tag='Inherited development_v1 runtime contract; CP1r3 corrects observation display comparison while requiring exact actual timing identity. No algorithm or fixed-rule change.',
    observation_identity='Only six-significant-digit displayed CPD fields are normalized; full CPD/setup/hold/ordered endpoint IDs/constraints remain exact. Trace-off is report-only.',
    current_execution_boundary='Parent CP1r2 has one prospectively fixed no-op pair and one initial timeout pair. Actual robot-p1 reload-vector audit validates this precision diagnosis on a partial development trajectory; no CP1r3 worker or complete-controller result yet.')
assert contract['fixed_configuration']==fixed
replace(root/'contract.json',__import__('json').dumps(contract,indent=2)+'\n')
inventory=read(old/'dependency_inventory.json')
inventory['runtime_tree_sha256']={str(f.relative_to(root/'runtime')):sha(f) for f in (root/'runtime').rglob('*') if f.is_file()}
replace(root/'dependency_inventory.json',__import__('json').dumps(inventory,indent=2)+'\n')
guard=root/'runtime/seccomp_thread_guard'
assert guard.stat().st_mode&0o777==0o555 and os.access(guard,os.X_OK)
environment={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
test=subprocess.run(['/usr/bin/python3',str(root/'runtime/test_seccomp_thread_guard.py')],capture_output=True,text=True,timeout=60,env=environment)
assert test.returncode==0,(test.stdout,test.stderr)
write(out/'guard_execution.json',dict(passed=True,returncode=0,stdout=test.stdout,VPR_calls_new=0,guard_sha256=sha(guard)))
smoke=subprocess.run([sys.executable,'-I','-B','-c',"import sys;sys.path.insert(0,sys.argv[1]);import run_serial_census_state_analysis_stream_v1;import run_serial_seed_resource_state_analysis_stream_v1;import observation_timing_identity_v2;print('patched workers imported')",str(root/'runtime')],capture_output=True,text=True,timeout=60,env=environment)
assert smoke.returncode==0,(smoke.stdout,smoke.stderr)
write(out/'import_execution.json',dict(passed=True,stdout=smoke.stdout,new_native_calls=0,worker_execution=False))
execution=dict(parent_release_manifest_sha256=sha(old/'release_manifest.json'),
    actual_existing_trace_audit_sha256=sha(D/'robot_owner_reentry_audit_02/completion.json'),
    numerical_and_representation_regression_sha256=sha(D/'observation_timing_identity_validation_02/completion.json'),
    guard_execution=True,worker_imports=True,new_native_calls=0,patched_worker_native_execution=False,
    full_method_confirmation=False,algorithm_selection_acceptance_terminal_unchanged=True,
    qualification='Existing native trace reused in prior readonly audit; new worker integration and full-method confirmation require separately registered execution. No completed route/STA is repeated here.')
replace(root/'execution_evidence.json',__import__('json').dumps(execution,indent=2)+'\n')
write(root/'precision_revision.json',dict(parent='current_sta_cp1r2',changed_runtime_files=changed,added_runtime_files=sorted(added),
    source_vector_or_trace_bound_in_worker_registration=True,display_only_normalization=True,actual_vector_equality_exact=True,
    source_sha256=plan['source_sha256'],evidence=execution))
replace(root/'README.md','''# Current-STA confirmation CP1r3

Separate frozen source after an actual robot-p1 reload audit exposed a display/full-precision comparison defect. CP1r2 and its prospective no-op/timeout cohort remain unchanged. Only the two observation workers and a new exact-identity helper change; artifact, admission identifier and outer seals bind the active bytes. Selectors, search/transaction policy, root envelopes, acceptance and terminal rules keep CP1r2 bytes. Empty-query engineering is not included.

Actual CPD/setup/hold/ordered endpoint identities/constraints must match exactly for observation-only FULL/STA. Normalization applies solely to six-significant-digit report fields. Required source vectors/traces join each worker input seal; trace-off remains report-only. No acceptance tolerance is added.

Use the same check/run-arm CLI, pinned dependencies and explicitly bound external physical inputs as CP1r2, with newly registered configs bound to this manifest/contract. Guard execution and worker imports are tested; patched-worker native execution, public dependency reconstruction and positive complete-controller confirmation remain pending. This preparation does not reroute/reexecute completed phases. Historical freeze_receipt/supervision manifests retain parent provenance and do not assert current execution. Any checkpoint recovery requires a separate adapter retaining original roots, budgets and legal archives; suffix costs cannot become fresh whole-flow costs.
''')
manifest=dict(release_id='current_sta_cp1r3',status='fixed_confirmation_source',public_evidence_base='9734eee',
    parent_release_manifest_sha256=sha(old/'release_manifest.json'),runtime_files=len(a['sha256'])+1,
    algorithm_selection_acceptance_terminal_byte_identical_to_CP1r2=True,
    changed_runtime_files=changed,added_runtime_files=sorted(added),confirmation_results_available=False,
    executable_modes=parent['executable_modes'],files_sha256={str(f.relative_to(root)):sha(f) for f in sorted(root.rglob('*')) if f.is_file() and f!=root/'release_manifest.json'})
replace(root/'release_manifest.json',__import__('json').dumps(manifest,indent=2)+'\n')
assert all(sha(root/f)==h for f,h in manifest['files_sha256'].items())
assert all(sha(old/f)==h for f,h in parent['files_sha256'].items())
for name in ['release_manifest.json','contract.json','precision_revision.json','execution_evidence.json','README.md']:shutil.copy2(root/name,out/name)
for f in root.rglob('*'):
    if f.is_file():f.chmod(f.stat().st_mode&~0o222)
    elif f.is_dir():f.chmod(0o555)
root.chmod(0o555)
assert guard.stat().st_mode&0o777==0o555
write(out/'completion.json',dict(passed=True,release=str(root),release_manifest_sha256=sha(root/'release_manifest.json'),
    original_CP1r2_preserved=True,algorithm_configuration_unchanged=True,new_native_calls=0,
    worker_native_execution_pending=True,public_reconstruction_pending=True,complete_confirmation_pending=True,
    source_sha256=plan['source_sha256']))
print(dict(passed=True,release=str(root),core_files=manifest['runtime_files'],new_native_calls=0))
