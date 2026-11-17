"""Reconstruct the new checker-only owner identity release before any new confirmation arm."""
import argparse,json,os,re,subprocess,tarfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

def package(plan):
    release=Path(plan['release']);out=D/'confirmation_release_cp1r5_01'
    archive=out/'current_sta_cp1r5_source.tar.gz';assert not archive.exists()
    vendor={'numpy','numpy.libs','lxml'}
    with tarfile.open(archive,'w:gz',compresslevel=1) as tar:
        for p in sorted(release.rglob('*')):
            if not p.is_file():continue
            rel=p.relative_to(release)
            if len(rel.parts)>1 and rel.parts[0]=='runtime' and rel.parts[1] in vendor:continue
            tar.add(p,arcname=str(Path('current_sta_cp1r5')/rel))
    template=D/'restore_confirmation_cp1r3_dependencies.py'
    text=template.read_text().replace('current_sta_cp1r3','current_sta_cp1r5')
    text,count=re.subn(r"^SOURCE_SHA='[^']+'",f"SOURCE_SHA='{sha(archive)}'",text,flags=re.M);assert count==1
    text,count=re.subn(r"^MANIFEST_SHA='[^']+'",f"MANIFEST_SHA='{sha(release/'release_manifest.json')}'",text,flags=re.M);assert count==1
    restorer=D/'restore_confirmation_cp1r5_dependencies.py'
    with restorer.open('x') as f:f.write(text)
    home=release.parents[1];base=home/'confirmation_releases/cp1r5_public_source_restore_01';base.mkdir(exist_ok=False)
    rebuilt=base/'rebuilt';wheels=home/'confirmation_releases/cp1_public_source_restore_01/wheels'
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
    restored=subprocess.run(['/usr/bin/python3',str(restorer),'--source-archive',str(archive),'--wheel-dir',str(wheels),'--output',str(rebuilt)],capture_output=True,text=True,env=env,timeout=60)
    assert restored.returncode==0,restored.stderr;restoration=json.loads(restored.stdout);assert restoration['passed']
    guard=subprocess.run(['/usr/bin/python3',str(rebuilt/'runtime/test_seccomp_thread_guard.py')],capture_output=True,text=True,env=env,timeout=60)
    assert guard.returncode==0,guard.stderr
    code="import sys,json;from pathlib import Path;sys.path.insert(0,"+repr(str(rebuilt/'runtime'))+");import numpy,lxml.etree;import run_serial_census_state_analysis_stream_v1;import run_serial_seed_resource_state_analysis_stream_v1;import observation_timing_identity_v2;root=Path("+repr(str(rebuilt/'runtime'))+");assert Path(numpy.__file__).is_relative_to(root) and Path(lxml.etree.__file__).is_relative_to(root);print(json.dumps(dict(numpy=numpy.__version__,lxml=lxml.etree.LXML_VERSION,patched_workers_imported=True)))"
    imports=subprocess.run(['/usr/bin/python3','-I','-B','-c',code],capture_output=True,text=True,env=env,timeout=60)
    assert imports.returncode==0,imports.stderr
    checks={}
    for item in plan['inputs']:
        if item.get('admission_failure'):continue
        dest=base/('input_check_'+item['id']);dest.mkdir();provenance=dest/'packing_manifest.json';provenance.write_bytes(Path(item['packing_manifest']).read_bytes())
        for arm in ['native','domain']:
            c=read(item['configs'][arm]);b=c['input_sha256'];b[str(provenance)]=b.pop(item['packing_manifest'])
            for name in ['release_manifest.json','contract.json']:b[str(rebuilt/name)]=b.pop(str(release/name))
            write(dest/(arm+'.json'),c)
        result=subprocess.run(['/usr/bin/python3',str(rebuilt/'confirmation.py'),'check','--native',str(dest/'native.json'),'--domain',str(dest/'domain.json'),'--packing-manifest',str(provenance),'--forbid-prefix',str(D.parents[1])],cwd=base,env=env,capture_output=True,text=True,timeout=120)
        assert result.returncode==0,result.stderr;checks[item['id']]=json.loads(result.stdout)
        assert checks[item['id']]['passed'] and checks[item['id']]['release_id']=='current_sta_cp1r5'
    write(out/'public_source_reconstruction.json',dict(passed=True,source_archive_sha256=sha(archive),source_archive_bytes=archive.stat().st_size,
        restoration=restoration,actual_extension_and_worker_imports=json.loads(imports.stdout),actual_relocated_admission=checks,
        actual_restored_guard_execution=dict(passed=True,stdout=guard.stdout),executable_modes_preserved=True,
        used_full_runtime_archive=False,used_installed_runtime_dependencies=False,wheels_reused_from_previous_hash_verified_public_download=True,
        native_calls_new=0,original_release_unchanged=True,
        qualification='Exact source plus two pinned wheels; actual guard/import/admission tests. These are packaging checks, not rerouted experiments, worker execution or complete-controller confirmation.',
        source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),template,restorer,archive,release/'release_manifest.json',D/'cp1_public_source_restoration_01/wheel_sources.json']}))
    return out/'public_source_reconstruction.json'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cohort-plan',type=Path,required=True);a=p.parse_args();receipt=package(read(a.cohort_plan));print(dict(passed=True,receipt=str(receipt),native_calls_new=0))
