"""Publishable CP1r1 source and exact-wheel reconstruction, without native work."""
import json
import os
import subprocess
import tarfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

home=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home')
release=home/'confirmation_releases/current_sta_cp1r1'
out=D/'confirmation_release_cp1r1_01'
archive=out/'current_sta_cp1r1_source.tar.gz';assert not archive.exists()
vendor={'numpy','numpy.libs','lxml'}
with tarfile.open(archive,'w:gz',compresslevel=1) as tar:
    for p in sorted(release.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(release)
        if len(rel.parts)>1 and rel.parts[0]=='runtime' and rel.parts[1] in vendor:continue
        tar.add(p,arcname=str(Path('current_sta_cp1r1')/rel))
old=D/'restore_confirmation_cp1_dependencies.py'
text=old.read_text().replace('current_sta_cp1','current_sta_cp1r1')
text=text.replace("SOURCE_SHA='c6dad6727dd8c9620cd8ea66e3289dc1b904477e923f708818303390119d8bdf'",f"SOURCE_SHA='{sha(archive)}'")
text=text.replace("MANIFEST_SHA='c970883e5e017a657c98455011b7d760944948d3116b5576927222d4665f72cb'",f"MANIFEST_SHA='{sha(release/'release_manifest.json')}'")
restorer=D/'restore_confirmation_cp1r1_dependencies.py'
with restorer.open('x') as f:f.write(text)
base=home/'confirmation_releases/cp1r1_public_source_restore_01';base.mkdir(exist_ok=False)
rebuilt=base/'rebuilt'
wheels=home/'confirmation_releases/cp1_public_source_restore_01/wheels'
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
command=['/usr/bin/python3',str(restorer),'--source-archive',str(archive),'--wheel-dir',str(wheels),'--output',str(rebuilt)]
r=subprocess.run(command,capture_output=True,text=True,env=env,timeout=60)
assert r.returncode==0,r.stderr
restored=json.loads(r.stdout);assert restored['passed']
write(base/'restoration.json',restored)
code="import sys,json;sys.dont_write_bytecode=True;from pathlib import Path;sys.path.insert(0,"+repr(str(rebuilt/'runtime'))+");import numpy,lxml.etree;root=Path("+repr(str(rebuilt/'runtime'))+");assert Path(numpy.__file__).is_relative_to(root) and Path(lxml.etree.__file__).is_relative_to(root);print(json.dumps(dict(numpy=numpy.__version__,lxml=lxml.etree.LXML_VERSION)))"
imp=subprocess.run(['/usr/bin/python3','-I','-c',code],capture_output=True,text=True,env=env,timeout=30);assert imp.returncode==0,imp.stderr
plan=read(D/'cp1r1_cross_circuit_cohort_01/plan.json');item=plan['inputs'][0]
configs=base/'input_check';configs.mkdir()
provenance=configs/'packing_manifest.json';provenance.write_bytes(Path(item['packing_manifest']).read_bytes())
for arm in ['native','domain']:
    c=read(item['configs'][arm]);b=c['input_sha256'];b[str(provenance)]=b.pop(item['packing_manifest'])
    for n in ['release_manifest.json','contract.json']:b[str(rebuilt/n)]=b.pop(str(release/n))
    write(configs/(arm+'.json'),c)
check=subprocess.run(['/usr/bin/python3',str(rebuilt/'confirmation.py'),'check','--native',str(configs/'native.json'),'--domain',str(configs/'domain.json'),'--packing-manifest',str(provenance),'--forbid-prefix',str(D.parents[1])],cwd=base,env=env,capture_output=True,text=True,timeout=60)
assert check.returncode==0,check.stderr
admission=json.loads(check.stdout);assert admission['passed'] and admission['release_id']=='current_sta_cp1r1'
write(out/'public_source_reconstruction.json',dict(passed=True,source_archive_sha256=sha(archive),
    source_archive_bytes=archive.stat().st_size,restoration=restored,
    actual_extension_imports=json.loads(imp.stdout),actual_relocated_admission=admission,
    used_full_runtime_archive=False,used_installed_runtime_dependencies=False,
    wheels_reused_from_previous_hash_verified_public_download=True,
    native_calls_new=0,original_release_unchanged=True,
    inherited_freeze_receipt='Archive freeze_receipt.json identifies original CP1 and its old hash explicitly; it is preserved provenance, not a CP1r1 execution claim. CP1r1 identity is its outer release_manifest.json and current confirmation_input.json.',
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),restorer,archive,release/'release_manifest.json',D/'cp1_public_source_restoration_01/wheel_sources.json']}))
print(dict(passed=True,source_bytes=archive.stat().st_size,verified_bound_files=restored['verified_bound_files'],actual_imports=True,actual_admission=True))
