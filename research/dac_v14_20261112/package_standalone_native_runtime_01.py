"""Seal and test a relocatable component archive; do not claim full-method freeze."""
import json,os,shutil,subprocess,tarfile,tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
package=D/'standalone_native_runtime_dev_01';out=D/'standalone_native_runtime_artifact_01';out.mkdir(exist_ok=False)
proofs=[D/'standalone_native_runtime_validation_01/completion.json',D/'standalone_physical_audit_validation_01/completion.json']
for p in proofs:
    receipt=read(p);assert receipt['passed']
    for source,digest in receipt['source_sha256'].items():assert sha(source)==digest,source
manifest=package/'artifact_manifest.json';assert not manifest.exists()
files=sorted(f for f in package.iterdir() if f.is_file())
for f in files:
    if f.suffix=='.py':compile(f.read_text(),str(f),'exec')
write(manifest,dict(format='standalone_native_runtime_component_v1',public_evidence_base='9734eee83b62fc012f0bb137f75aba919df514e4',
    full_method_frozen=False,scientific_algorithm_changed=False,sha256={f.name:sha(f) for f in files},
    environment=dict(platform='Linux x86-64',python_tested='3.10.12',lxml_audit_tested='6.1.3'),
    verification_receipts={str(p.relative_to(D)):sha(p) for p in proofs},
    qualification='Frozen component artifact only; selection, transaction, STA and complete confirmation dependencies remain separate.'))
archive=out/'standalone_native_runtime_component_01.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
    for f in [*files,manifest]:tar.add(f,arcname='runtime/'+f.name,recursive=False)
relocated=Path(tempfile.mkdtemp(prefix='standalone-runtime-archive-'))
with tarfile.open(archive,'r:gz') as tar:
    assert all(m.name.startswith('runtime/') and '..' not in Path(m.name).parts and m.isfile() for m in tar.getmembers())
    tar.extractall(relocated)
target=relocated/'runtime';assert sha(target/'artifact_manifest.json')==sha(manifest)
for name,digest in read(manifest)['sha256'].items():assert sha(target/name)==digest,name
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']};env['PYTHONDONTWRITEBYTECODE']='1'
command=['/usr/bin/python3',str(target/'selftest.py'),'--output',str(relocated/'selftest')]
r=subprocess.run(command,capture_output=True,text=True,cwd=target,env=env,timeout=60)
write(out/'selftest_execution.json',dict(command=command,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,(r.stdout,r.stderr)
shutil.copytree(relocated/'selftest',out/'selftest')
write(out/'completion.json',dict(passed=True,archive=str(archive),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
    artifact_manifest_sha256=sha(manifest),relocated_archive_selftest_passed=read(out/'selftest/completion.json')['passed'],
    full_method_frozen=False,VPR_calls_new=0,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),*proofs,manifest]},
    qualification='Actual sealed archive extraction and six-case standalone self-test passed; generic process and archived-route audit engineering evidence only.'))
print(dict(passed=True,archive=str(archive),bytes=archive.stat().st_size,VPR_calls_new=0,full_method_frozen=False))
