#!/usr/bin/env python3
"""Bind actual strict-study toolchain recipes without compiling or running VPR."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, re, subprocess

P=Path(__file__).resolve().parent;ROOT=P.parents[1]
A=ROOT/'results/architecture_flow_20261027';C=A/'single_thread_candidate_20261103';B=A/'serial_strict_reexecution_20261103'
bindings={};checks=[]
def raw(path):
    p=Path(path);data=p.read_bytes();bindings[str(p)]=hashlib.sha256(data).hexdigest();return data
def read(path):return json.loads(raw(path))
def check(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail))
def git(source,*args):return subprocess.check_output(['git','-C',str(source),*args],env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_OPTIONAL_LOCKS='0'),timeout=30).decode().strip()
snapshot=read(ROOT/'patches/snapshot_20261109/manifest.json')
artifacts=read(C/'serial_candidate_artifacts_20261103.json')
protocol=read(B/'benchmark_protocol.json');deps=read(B/'runtime_dependency_binding.json')
roles=[]
for role,build,source,label in [('A0','a0_serial_build',C/'a0_clean_source',None),('R1','r1_serial_build',ROOT/'vendor/vtr-architecture-src','architecture_r1'),('B2','b2_serial_build',ROOT/'vendor/lazagna-vtr9-buildfix-src','lazagna_b2'),('P1','vpr_serial_bridge_build',C/'vpr_serial_bridge_source',None)]:
    binary=ROOT/artifacts['artifacts'][role]['path'];digest=hashlib.sha256(raw(binary)).hexdigest()
    check('binary:'+role,digest==artifacts['artifacts'][role]['sha256']==protocol['binaries'][role]['sha256']==deps['sha256'][str(binary)])
    cache_path=C/build/'CMakeCache.txt';cache_text=raw(cache_path).decode();cache={}
    for line in cache_text.splitlines():
        if line and not line.startswith(('#','//')) and ':' in line and '=' in line:
            key,rest=line.split(':',1);cache[key]=rest.split('=',1)[1]
    check('build_source_directory:'+role,cache['CMAKE_HOME_DIRECTORY']==str(source))
    if role!='P1':
        check('git_root:'+role,git(source,'rev-parse','--show-toplevel')==str(source))
        head=git(source,'rev-parse','HEAD');check('base_commit:'+role,head==artifacts['source_commits'][role])
        changed=git(source,'diff','HEAD','--name-only','--no-ext-diff','--ignore-submodules=all').splitlines()
        if role=='A0':check('official_top_level_clean',not changed)
        if label:
            entry=snapshot['sources'][label]
            added=git(source,'ls-files','--others','--exclude-standard').splitlines()
            check('snapshot_file_set:'+role,set(changed+added)==set(entry['files_sha256']))
            check('snapshot_commit:'+role,head==entry['commit'])
            for name,expected in entry['files_sha256'].items():check('source_file:'+role+'/'+name,hashlib.sha256(raw(source/name)).hexdigest()==expected)
            check('exported_patch:'+role,hashlib.sha256(raw(P/'provenance'/(label+'.patch'))).hexdigest()==entry['patch_sha256'])
    else:
        head=artifacts['source_commits'][role]
        check('p1_copy_has_no_git_root',not (source/'.git').exists())
    if role=='P1':
        flag_path=C/build/'vpr/CMakeFiles/libvpr.dir/flags.make'
        flags_text=raw(flag_path).decode();flags=next(x.split('=',1)[1].strip() for x in flags_text.splitlines() if x.startswith('CXX_FLAGS ='))
        defines=next(x.split('=',1)[1].strip() for x in flags_text.splitlines() if x.startswith('CXX_DEFINES ='))
    else:
        flag_path=C/build/'build.ninja';lines=raw(flag_path).decode().splitlines()
        idx=next(i for i,x in enumerate(lines) if x.startswith('build ') and '/src/route/route_common.cpp.o:' in x)
        flags=next(x.split('=',1)[1].strip() for x in lines[idx+1:idx+10] if x.startswith('  FLAGS ='))
        defines=next(x.split('=',1)[1].strip() for x in lines[idx+1:idx+10] if x.startswith('  DEFINES ='))
    check('optimized_cpp:'+role,'-O3' in flags.split() and '-DNDEBUG' in flags.split())
    check('serial_tatum:'+role,cache.get('TATUM_EXECUTION_ENGINE')=='serial')
    compiler_files=list((C/build/'CMakeFiles').glob('*/CMakeCXXCompiler.cmake'));assert len(compiler_files)==1
    compiler_text=raw(compiler_files[0]).decode();compiler=re.search(r'set\(CMAKE_CXX_COMPILER_VERSION "([^"]+)"\)',compiler_text)[1]
    roles.append(dict(role=role,base_commit=head,binary=str(binary),binary_sha256=digest,build_directory=str(C/build),source_directory=str(source),source_is_git_checkout=role!='P1',compiler_version=compiler,build_type_cache=cache.get('CMAKE_BUILD_TYPE'),observed_cpp_flags=flags,observed_cpp_defines=defines,cache_options={k:cache.get(k) for k in ['CMAKE_GENERATOR','VTR_IPO_BUILD','VTR_ENABLE_CAPNPROTO','VPR_ENABLE_INTERCHANGE','WITH_PARMYS','WITH_ABC','WITH_ODIN','TATUM_EXECUTION_ENGINE','VPR_USE_SIGNAL_HANDLER']},reconstruction_patch=None if role=='A0' else 'provenance/'+('placement_p1_serial' if role=='P1' else label)+'.patch'))

p1=read(P/'data/p1_source_comparison.json');source=C/'vpr_serial_bridge_source'
check('p1_base',p1['base_commit']==artifacts['source_commits']['P1'])
source_mismatches=[]
for r in p1['rows']:
    path=source/r['path'];data=os.readlink(path).encode() if r['mode']=='120000' else path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=r['sha256']:source_mismatches.append(r['path'])
check('p1_source_inventory',not source_mismatches and p1['checked']==1688,source_mismatches)
check('p1_known_modifications',{r['path'] for r in p1['changed']}=={'libs/EXTERNAL/libtatum/libtatum/tatum/TimingReporter.hpp','vpr/CMakeLists.txt','vpr/src/base/partition_creator.cpp'})
check('p1_missing_disabled_build_files',all(not (source/name).exists() for name in p1['missing']) and len(p1['missing'])==2)
roundtrip=read(P/'data/p1_patch_roundtrip.json')
check('p1_patch_roundtrip_binding',roundtrip['passed'] and roundtrip['base_commit']==p1['base_commit'] and roundtrip['modified_files_sha256']=={r['path']:r['sha256'] for r in p1['changed']} and roundtrip['deleted_files']==p1['missing'] and hashlib.sha256(raw(P/'provenance/placement_p1_serial.patch')).hexdigest()==roundtrip['patch_sha256'])
for label in ['partition','bridge']:
    info=artifacts['artifacts'][label];file=ROOT/info['path']
    check('artifact:'+label,hashlib.sha256(raw(file)).hexdigest()==info['sha256'])
check('bridge_copy',raw(P/'provenance/run_serial_triton_bridge.py')==raw(C/'run_serial_triton_bridge.py'))
entry=snapshot['sources']['partition'];partition_source=ROOT/entry['local_source']
check('partition_base',git(partition_source,'rev-parse','HEAD')==entry['commit']==artifacts['source_commits']['partition'])
check('partition_patch',hashlib.sha256(raw(P/'provenance/partition.patch')).hexdigest()==entry['patch_sha256'])
for name,sha in entry['files_sha256'].items():check('partition_source:'+name,hashlib.sha256(raw(partition_source/name)).hexdigest()==sha)
runtime_mismatches=[]
for name,sha in deps['sha256'].items():
    if hashlib.sha256(raw(name)).hexdigest()!=sha:runtime_mismatches.append(name)
check('runtime_library_bindings',not runtime_mismatches and not deps['missing'],runtime_mismatches)
for path in [ROOT/'patches/snapshot_20261109/native.patch',ROOT/'patches/snapshot_20261109/placement_p1.patch',C/'a0_copied_submodules_verification.json',C/'a0_nested_submodules_verification.json',A/'native_router_dependencies.json',__file__]:raw(path)
result=dict(utc=datetime.now(timezone.utc).isoformat(),status='verified_with_reconstruction_limits' if all(c['passed'] for c in checks) else 'issues_found',checks=checks,roles=roles,source_sha256=bindings,p1_source_scope=p1['scope'],p1_source_missing=p1['missing'],p1_submodule_pins=p1['gitlinks'],p1_patch_roundtrip='Pinned base blobs for 3 modifications and 2 deletions reconstructed in temporary repository; git apply and byte comparison passed. Not a clean rebuild.',limitations=['A0 source has no top-level tracked changes; disabled/nested submodule differences remain documented in archived receipts.','P1 is a source copy without .git; querying git HEAD in it resolves to the parent project and is invalid provenance.','P1 inventory covers top-level tracked vpr/libs/CMake/cmake files, not submodule contents or all generated files.','The copied bridge contains original absolute workspace paths; a relocated rebuild needs explicit path adaptation and new identities.','Runtime dependency scope is recorded ldd resolution, not a complete observation of every possible dlopen.','No clean rebuild or bit-for-bit reproducible binary claim; timing comparisons retain different build options and R1-off control.','The historical native.patch is a modified development source, not the official strict A0 source patch.'])
(P/'data/toolchain_provenance.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['status'],len(checks),'checks;',len(bindings),'source files; P1',p1['checked'],'files rechecked')
for c in checks:
    if not c['passed']:print('FAILED',c)
raise SystemExit(0 if result['status']!='issues_found' else 1)
