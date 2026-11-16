"""Validate public-source reconstruction without consulting the full runtime bundle."""
import json,os,subprocess,sys,copy,urllib.request
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
base=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/cp1_public_source_restore_01');rebuilt=base/'rebuilt';out=D/'cp1_public_source_restoration_01';assert not out.exists();out.mkdir()
restored=read(base/'restoration.json');assert restored['passed'] and restored['restored_dependency_files']==1166 and restored['verified_bound_files']==1289
wheels=[]
for name,digest in restored['wheel_sha256'].items():
 package,version=name.split('-')[:2]
 with urllib.request.urlopen('https://pypi.org/pypi/'+package+'/'+version+'/json',timeout=30) as response:metadata=json.load(response)
 record=next(row for row in metadata['urls'] if row['filename']==name);assert record['digests']['sha256']==digest==sha(base/'wheels'/name)
 wheels.append(dict(filename=name,sha256=digest,url=record['url'],bytes=record['size'],pypi_metadata_sha256_matches=True,download='pip download reported cache reuse; bytes verified against public PyPI release metadata, not copied from installed runtime.'))
write(out/'wheel_sources.json',wheels)
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')};env.update(PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
code="import sys,json;from pathlib import Path;sys.path.insert(0,"+repr(str(rebuilt/'runtime'))+");import numpy,lxml.etree;root=Path("+repr(str(rebuilt/'runtime'))+");assert Path(numpy.__file__).is_relative_to(root);assert Path(lxml.etree.__file__).is_relative_to(root);print(json.dumps(dict(numpy=numpy.__version__,lxml=lxml.etree.LXML_VERSION,numpy_path=numpy.__file__,lxml_path=lxml.etree.__file__)))"
imports=subprocess.run(['/usr/bin/python3','-I','-c',code],cwd=base,env=env,capture_output=True,text=True,timeout=60);assert imports.returncode==0,imports.stderr;imported=json.loads(imports.stdout);assert imported['numpy']=='2.2.6' and imported['lxml'][:3]==[6,1,3]
plan=read(D/'cp1_cross_circuit_cohort_01/plan.json');item=plan['inputs'][0];old=Path(plan['release']);configs=base/'input_check';configs.mkdir();provenance=configs/'packing_manifest.json';provenance.write_bytes(Path(item['packing_manifest']).read_bytes())
for arm in ['native','domain']:
 config=read(item['configs'][arm]);bindings=config['input_sha256'];bindings[str(provenance)]=bindings.pop(item['packing_manifest'])
 for name in ['release_manifest.json','contract.json']:bindings[str(rebuilt/name)]=bindings.pop(str(old/name))
 write(configs/(arm+'.json'),config)
command=['/usr/bin/python3',str(rebuilt/'confirmation.py'),'check','--native',str(configs/'native.json'),'--domain',str(configs/'domain.json'),'--packing-manifest',str(provenance),'--forbid-prefix',str(D.parents[1])]
check=subprocess.run(command,cwd=base,env=env,capture_output=True,text=True,timeout=120);(out/'admission.stdout').write_text(check.stdout);(out/'admission.stderr').write_text(check.stderr);assert check.returncode==0,check.stderr
admission=json.loads(check.stdout);assert admission['passed'] and not admission['large_input_bytes_checked']
assert all(sha(rebuilt/name)==digest for name,digest in read(rebuilt/'release_manifest.json')['files_sha256'].items())
# Existing output must reject before any extraction; pinned source/release untouched.
restorer=D/'restore_confirmation_cp1_dependencies.py';failure=subprocess.run(['/usr/bin/python3',str(restorer),'--source-archive',str(D/'confirmation_release_cp1_01/current_sta_cp1_source.tar.gz'),'--wheel-dir',str(base/'wheels'),'--output',str(rebuilt)],cwd=base,env=env,capture_output=True,text=True,timeout=30);assert failure.returncode!=0 and 'no overwrite' in failure.stderr
write(out/'restoration.json',restored)
files=[Path(__file__).resolve(),restorer,D/'confirmation_cp1_wheels_requirements.txt',D/'confirmation_release_cp1_01/current_sta_cp1_source.tar.gz',rebuilt/'release_manifest.json',rebuilt/'contract.json',out/'wheel_sources.json',configs/'native.json',configs/'domain.json',provenance]
write(out/'completion.json',dict(passed=True,source_archive_restored=True,used_full_runtime_archive=False,used_installed_runtime_dependencies=False,pinned_wheel_hashes_verified_against_PyPI=True,restored_dependencies=1166,verified_bound_files=1289,actual_extension_imports=imported,actual_relocated_fixed_admission=admission,existing_output_rejected=True,native_calls=0,CP1_changed=False,source_sha256={str(f):sha(f) for f in files},qualification='Public source plus two explicitly pinned wheels reconstruct all frozen bound bytes, and actual extension imports/fixed admission pass outside the project. Not a new native execution, independently confirmed benefit, binary build reproduction or complete physical-input admission. Phase binaries and physical inputs still explicit external prerequisites.'))
print(dict(passed=True,dependencies=1166,bound_files=1289,actual_imports=True,actual_admission=True,new_native_calls=0))
