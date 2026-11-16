"""Seal source/rules after real core execution and actual relocated admission checks."""
import datetime
import os
import shutil
import tarfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

root=D/'confirmation_release_cp1_01';prep=read(root/'preparation.json');release=Path(prep['release'])
validation=read(root/'validation.json')
assert validation['passed'] and validation['tests']==23 and validation['native_calls']==0
assert all(sha(p)==h for p,h in validation['source_sha256'].items())
manifest=read(release/'release_manifest.json')
assert manifest['release_id']=='current_sta_cp1' and manifest['runtime_byte_identical_to_executed_dev03']
# Remove only interpreter caches produced by the release's own validation import.
for cache in release.rglob('__pycache__'):shutil.rmtree(cache)
assert {str(p.relative_to(release)) for p in release.rglob('*') if p.is_file()}==set(manifest['files_sha256'])|{'release_manifest.json'}
assert all(sha(release/p)==h for p,h in manifest['files_sha256'].items())
proof=read(release/'execution_evidence.json')
assert all(sha(p)==h for p,h in proof['evidence_sha256'].items())
whole=read(D/'standalone_whole_method_check_01/completion.json')
transaction=read(D/'standalone_transaction_native_check_01/completion.json')
assert whole['passed'] and whole['whole_method_executed_and_verified'] and transaction['passed']
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt=dict(passed=True,status='fixed_confirmation_source_sealed',release_id='current_sta_cp1',frozen_at=stamp,
    release=str(release),release_manifest_sha256=sha(release/'release_manifest.json'),
    contract_sha256=sha(release/'contract.json'),runtime_files=116,total_bound_files=len(manifest['files_sha256']),
    independently_executable_core_byte_identical=True,core_actual_whole_execution_passed=True,
    actual_release_admission_tests=23,new_native_calls=0,
    full_method_source_and_rules_frozen=True,confirmation_results_available=False,
    positive_integrated_owner_reentry_confirmed=False,positive_integrated_timing_feedback_confirmed=False,
    old_development_batches_reclassified=False,existing_queues_modified=False,
    external_binaries_and_physical_inputs_explicit=True,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),root/'preparation.json',root/'validation.json',release/'release_manifest.json',release/'contract.json',release/'execution_evidence.json']},
    qualification='Freeze identifies fixed executable source/input interpretation/mechanism/acceptance/terminal rules for prospective confirmation. It is not proof of independent benefits or full positive-branch coverage. The executed116-file core is unchanged; new admission/launch boundary is validated without another native run. Legacy internal development labels remain historical compatibility fields. Future changes require a new release and prospective cohort; existing batches stay on original rules.')
write(release/'freeze_receipt.json',receipt)
write(root/'freeze_receipt.json',receipt)
for name in ['contract.json','release_manifest.json','dependency_inventory.json','execution_evidence.json','binary_inputs.json','README.md']:
    shutil.copy2(release/name,root/name)
full=root/'current_sta_cp1_full.tar.gz';source=root/'current_sta_cp1_source.tar.gz'
assert not full.exists() and not source.exists()
with tarfile.open(full,'w:gz',compresslevel=1) as archive:archive.add(release,arcname='current_sta_cp1')
vendor={'numpy','lxml','numpy.libs'}
with tarfile.open(source,'w:gz',compresslevel=1) as archive:
    for p in sorted(release.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(release)
        if len(rel.parts)>1 and rel.parts[0]=='runtime' and rel.parts[1] in vendor:continue
        archive.add(p,arcname=str(Path('current_sta_cp1')/rel))
write(root/'archives.json',dict(full=dict(path=str(full),sha256=sha(full),bytes=full.stat().st_size,
      contents='Fixed source plus bundled NumPy/lxml/native-extension dependencies; exact external phase binaries and physical inputs still supplied explicitly.'),
    source=dict(path=str(source),sha256=sha(source),bytes=source.stat().st_size,
      contents='Public source archive excludes vendor NumPy/lxml/numpy.libs; complete dependency hashes and pinned environment remain. Restore exact bundled dependencies before execution.'),
    source_archive_is_not_complete_runtime=True,new_native_calls=0))
for p in sorted(release.rglob('*'),key=lambda p:len(p.parts),reverse=True):p.chmod(p.stat().st_mode & ~0o222)
release.chmod(release.stat().st_mode & ~0o222)
write(root/'completion.json',dict(**receipt,archives=str(root/'archives.json'),source_readonly=True,
    source_archive_sha256=sha(source),full_archive_sha256=sha(full)))
print(dict(passed=True,release_id='current_sta_cp1',bound_files=len(manifest['files_sha256']),admission_tests=23,new_native_calls=0,source_archive_bytes=source.stat().st_size,full_archive_bytes=full.stat().st_size))
