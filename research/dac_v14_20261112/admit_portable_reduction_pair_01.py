"""Copy and verify sealed physical inputs only after the shared serial slot is held."""
import os
import shutil
import subprocess
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

root = D / 'portable_reduction_pair_01'
plan = read(root / 'plan.json')
w, runtime = Path(plan['workspace']), Path(plan['runtime'])
assert not (root / 'admission.json').exists()
begin = time.monotonic()
assert all(sha(path) == digest for path, digest in plan['source_sha256'].items())
assert sha(runtime / 'artifact_manifest.json') == plan['package_manifest_sha256']
manifest = read(runtime / 'artifact_manifest.json')
assert manifest['component_revision'] == 'complete_method_dev_03'
assert all(sha(runtime / path) == digest for path, digest in manifest['sha256'].items())
assert not (w / 'native').exists() and not (w / 'domain').exists()
assert shutil.disk_usage(w).free > 2 * sum(row['bytes'] for row in plan['physical_input_copies'].values())
for key, row in plan['physical_input_copies'].items():
    source, destination = Path(row['source']), Path(row['destination'])
    assert not destination.exists(), 'Do not overwrite a partially admitted input; reconcile it first'
    assert sha(source) == row['sha256'], key
    destination.parent.mkdir(exist_ok=True)
    shutil.copy2(source, destination)
    assert sha(destination) == row['sha256'], key
env = {k: v for k, v in os.environ.items()
       if k not in ['PYTHONPATH', 'PYTHONHOME', 'LD_PRELOAD', 'LD_AUDIT', 'LD_LIBRARY_PATH']
       and not k.startswith('VPR_')}
env.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
command = ['/usr/bin/python3', str(runtime / 'guarded_entry.py'), '--forbid-prefix', str(D.parents[1]),
           '--script', str(w / 'admit_pair.py'), str(w)]
with (root / 'admission.log').open('x') as log:
    result = subprocess.run(command, cwd=runtime, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=600)
assert result.returncode == 0 and read(w / 'admission.json')['passed']
assert all(sha(path) == digest for path, digest in plan['source_sha256'].items())
write(root / 'admission.json', dict(passed=True, native_calls_new=0,
    complete_preparation_seconds=time.monotonic() - begin,
    physical_inputs_rehashed_and_copied=True, guarded_runtime_admission=str(w / 'admission.json'),
    source_sha256={str(root / 'plan.json'): sha(root / 'plan.json'), str(w / 'admission.json'): sha(w / 'admission.json')},
    qualification='Input packaging and admission outside the measured route command, consistently with existing portable pairs. Each measured arm still performs its own registered fresh-route/index/repair work. No historical route imported; no parameter or runtime changed.'))
print(dict(passed=True, native_calls_new=0), flush=True)
