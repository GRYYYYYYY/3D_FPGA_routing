"""Fixed confirmation admission and measured launch; no implicit research lookup."""
import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def write_new(p,value):
    with Path(p).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def options(command):
    assert len(command)>=3
    result={};i=3
    while i<len(command):
        key=command[i];assert key.startswith('--') and key not in result,key
        if key in ['--route','--analysis','--pack','--place','--partition_post_pack']:result[key]=None;i+=1
        else:
            assert i+1<len(command) and not command[i+1].startswith('--'),key
            result[key]=command[i+1];i+=2
    return result

def check(native,domain,packing_manifest,forbidden,release_root=ROOT):
    release_root=Path(release_root).resolve();manifest=release_root/'release_manifest.json'
    m=read(manifest);assert m['release_id']=='current_sta_cp1r6'
    for name,digest in m['files_sha256'].items():
        p=(release_root/name).resolve();assert p.is_relative_to(release_root) and sha(p)==digest,name
    for name,mode in m['executable_modes'].items():
        executable=release_root/name
        assert executable.stat().st_mode & 0o777 == mode and os.access(executable,os.X_OK),('Missing executable mode',name)
    contract_path=release_root/'contract.json';contract=read(contract_path)
    assert list(sys.version_info[:2])==contract['execution_environment']['python_major_minor'] and sys.platform==contract['execution_environment']['platform'] and platform.machine()==contract['execution_environment']['machine'], 'Execution environment differs from pinned native-extension package'
    paths=[Path(p).resolve() for p in [native,domain,packing_manifest]]
    forbidden=Path(forbidden).resolve()
    assert all(not p.is_relative_to(forbidden) for p in [release_root,*paths]),'Use declared inputs outside historical project'
    configs=[read(p) for p in paths[:2]]
    assert set(configs[0])==set(configs[1])==set(contract['fixed_configuration'])|{'route_command','phase_runtime_config','input_sha256','domain_mode','domain_feedback'}
    assert {k for k in configs[0] if configs[0][k]!=configs[1][k]}=={'domain_mode','domain_feedback'}
    assert [(c['domain_mode'],c['domain_feedback']) for c in configs]==[('unrestricted',False),('paired',True)]
    assert all(type(c['domain_feedback']) is bool for c in configs)
    source=read(paths[2]);source_options=options(source['command'])
    expected_merge=source_options.get('--merge_constant_generators',contract['native_defaults']['merge_constant_generators'])
    assert expected_merge in ['on','off']
    packed_sha=source['outputs']['packed.net']['sha256']
    expected_bindings={str(manifest):sha(manifest),str(contract_path):sha(contract_path),str(paths[2]):sha(paths[2])}
    for c in configs:
        for key,value in contract['fixed_configuration'].items():assert type(c[key]) is type(value) and c[key]==value,('Changed frozen rule',key)
        phase_path=Path(c['phase_runtime_config']).resolve();assert not phase_path.is_relative_to(forbidden)
        spec=read(phase_path)
        assert spec['format']=='explicit_unified_phase_runtime_v1'
        assert {k:r['sha256'] for k,r in spec['phase_binaries'].items()}==contract['phase_binary_sha256']
        assert {k:r['sha256'] for k,r in spec['query_engines'].items()}==contract['query_engine_sha256']
        assert {k:r['sha256'] for k,r in spec['query_validations'].items()}==contract['query_validation_sha256']
        assert spec['physical_files']['packed']['sha256']==packed_sha,'Packing provenance does not match input'
        opt=options(c['route_command'])
        assert set(opt)<=set(contract['route_fixed_options'])|set(contract['route_input_options'])|{'--route','--analysis','--merge_constant_generators'}
        assert '--route' in opt and '--analysis' in opt
        for key,value in contract['route_fixed_options'].items():assert opt.get(key)==value,('Changed frozen router opportunity',key)
        assert opt.get('--merge_constant_generators','on')==expected_merge,'Packed-netlist interpretation changed'
        assert opt.get('--merge_constant_generators') in [None,'off'],'Native observation supports explicit off or bound default on'
        assert int(opt['--seed'])>0 and int(opt['--route_chan_width'])>0 and opt['--device']
        assert Path(c['route_command'][0]).resolve()==Path(spec['phase_binaries']['resource']['path']).resolve()
        actual={'architecture':c['route_command'][1],'circuit':c['route_command'][2],
                'graph':opt['--read_rr_graph'],'packed':opt['--net_file'],'placement':opt['--place_file']}
        if '--sdc_file' in opt:actual['sdc']=opt['--sdc_file']
        assert set(actual)==set(spec['physical_files'])
        for key,path in actual.items():assert Path(path).resolve()==Path(spec['physical_files'][key]['path']).resolve(),key
        assert str(Path(opt['--route_file']).resolve()) not in c['input_sha256'] and not Path(opt['--route_file']).exists()
        assert all(not Path(p).resolve().is_relative_to(forbidden) for p in [*c['input_sha256'],*actual.values(),*expected_bindings])
        for path,digest in expected_bindings.items():assert c['input_sha256'].get(path)==digest,('Missing actual-run release/input binding',path)
        for group in ['physical_files','phase_binaries','query_engines','query_validations']:
            for row in spec[group].values():assert c['input_sha256'].get(str(Path(row['path']).resolve()))==row['sha256']
    return dict(passed=True,release_id=m['release_id'],release_manifest_sha256=sha(manifest),
        contract_sha256=sha(contract_path),configuration_sha256={arm:sha(p) for arm,p in zip(['native','domain'],paths[:2])},
        packing_manifest_sha256=sha(paths[2]),packed_sha256=packed_sha,
        merge_constant_generators=expected_merge,large_input_bytes_checked=False,
        native_calls=0,qualification='Rule, provenance and command admission only. Actual physical/binary byte hashes, FULL/STA and output gates execute within each measured algorithm command. No result inferred.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['check','run-arm'])
    p.add_argument('--native',type=Path,required=True);p.add_argument('--domain',type=Path,required=True)
    p.add_argument('--packing-manifest',type=Path,required=True);p.add_argument('--forbid-prefix',type=Path,required=True)
    p.add_argument('--arm',choices=['native','domain']);p.add_argument('--case',type=Path);a=p.parse_args()
    result=check(a.native,a.domain,a.packing_manifest,a.forbid_prefix)
    if a.action=='check':print(json.dumps(result));return
    assert a.arm and a.case
    case=a.case.resolve();assert not case.is_relative_to(a.forbid_prefix.resolve())
    case.mkdir(parents=True,exist_ok=True)
    assert not (case/'flow').exists() and not (case/'config.json').exists() and not (case/'confirmation_input.json').exists()
    source=a.native if a.arm=='native' else a.domain
    shutil.copy2(source,case/'config.json')
    write_new(case/'confirmation_input.json',dict(**result,arm=a.arm,measured_entry=True))
    for key in list(os.environ):
        if key.startswith('VPR_') or key in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']:os.environ.pop(key)
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    runtime=ROOT/'runtime'
    command=[sys.executable,str(runtime/'guarded_entry.py'),'--forbid-prefix',str(a.forbid_prefix.resolve()),
             '--script',str(runtime/'run_complete_unified_method_v1.py'),'--config',str(case/'config.json'),'--output',str(case/'flow')]
    os.chdir(runtime);os.execv(sys.executable,command)

if __name__=='__main__':main()
