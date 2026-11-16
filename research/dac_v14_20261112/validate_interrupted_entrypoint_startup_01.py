"""Execute source-only startup probes; no VPR, graph/STA parse or live mutation."""
import json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

root=D/'interrupted_entrypoint_startup_01';root.mkdir(exist_ok=False)
recovery=D/'interrupted_flow_recovery_01';protocol=read(recovery/'protocol.json')
assert all(sha(p)==h for p,h in protocol['source_sha256'].items())
parent=Path(protocol['parent_release']);runtime=parent/'runtime';patch=D/'observation_precision_patch_02';prep=read(patch/'preparation.json')
assert sha(parent/'release_manifest.json')==protocol['parent_release_manifest_sha256']
files=[Path(__file__).resolve(),recovery/'protocol.json',parent/'release_manifest.json',patch/'preparation.json']
bound={str(p):sha(p) for p in files}
for name,digest in prep['patched_workers_sha256'].items():
    assert sha(runtime/name)==prep['parent_workers_sha256'][name] and sha(patch/name)==digest
    bound[str(runtime/name)]=sha(runtime/name);bound[str(patch/name)]=digest
helper='observation_timing_identity_v2.py';assert sha(patch/helper)==prep['helper_sha256'];bound[str(patch/helper)]=prep['helper_sha256']
env={k:v for k,v in os.environ.items() if not k.startswith('VPR_') and k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']}
env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
probes=[];failure=None;started=time.monotonic()
with tempfile.TemporaryDirectory(prefix='recovery-source-startup-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home') as temporary:
    temporary=Path(temporary);view=temporary/'source_view';view.mkdir();view_runtime=view/'runtime';view_runtime.mkdir()
    for p in runtime.iterdir():
        if p.name=='__pycache__':continue
        dest=view_runtime/p.name
        if p.is_dir():dest.symlink_to(p,target_is_directory=True)
        else:
            assert p.stat().st_size<4*1024**2,('Source-only view refuses large payload',str(p))
            bound[str(p)]=sha(p);shutil.copy2(p,dest)
    for name in [*prep['patched_workers_sha256'],helper]:
        dest=view_runtime/name
        if dest.exists():dest.chmod(0o644)
        shutil.copyfile(patch/name,dest)
    # Deliberately not a release: an isolated full driver must reject it before
    # any package/native work. This view is only an import-resolution fixture.
    write(view/'release_manifest.json',dict(release_id='source_only_negative_startup_fixture',not_a_frozen_release=True))
    env['H3D_RECOVERY_RUNTIME']=str(view_runtime)
    def probe(name,command,expected=0,needle=None):
        begin=time.monotonic()
        try:
            p=subprocess.run(command,capture_output=True,text=True,env=env,timeout=30)
            passed=p.returncode==expected and (needle is None or needle in p.stdout+p.stderr)
            result=dict(name=name,passed=passed,returncode=p.returncode,seconds=time.monotonic()-begin,stdout=p.stdout,stderr=p.stderr,
                command=command,native_calls=0,scope='Source-only startup fixture, no physical input execution')
        except Exception as error:result=dict(name=name,passed=False,error=repr(error),seconds=time.monotonic()-begin,native_calls=0)
        probes.append(result);write(root/'probes.json',probes)
        assert result['passed'],name
    try:
        for name in ['resume_resource_controller.py','resume_resource_transaction.py','resume_timing_controller.py','resume_timing_transaction.py']:
            script=recovery/'runtime_extension'/name;bound[str(script)]=sha(script)
            # Mirrors the actual driver's child launch: ordinary Python with
            # scrubbed environment; script directory supplies its adapters.
            probe(name,[sys.executable,'-B',str(script),'--help'],needle='usage:')
        driver=recovery/'runtime_extension/run_interrupted_full_flow_recovery_v1.py';bound[str(driver)]=sha(driver)
        probe('isolated_driver_help',[sys.executable,'-I','-B',str(driver),'--help'],needle='usage:')
        plan=temporary/'negative_plan.json';write(plan,dict(release=str(view),recovery_flow=str(temporary/'negative_flow')))
        probe('isolated_driver_imports_then_rejects_nonrelease',[sys.executable,'-I','-B',str(driver),'--plan',str(plan),'--output',str(temporary/'negative_flow')],
            expected=1,needle="manifest['release_id']=='current_sta_cp1r3'")
        code="import sys;sys.path.insert(0,sys.argv[1]);import run_serial_census_state_analysis_stream_v1;import run_serial_seed_resource_state_analysis_stream_v1;import observation_timing_identity_v2;print('precision worker imports passed')"
        probe('intended_precision_worker_imports',[sys.executable,'-I','-B','-c',code,str(view_runtime)],needle='precision worker imports passed')
    except Exception as error:failure=repr(error)
assert all(sha(p)==h for p,h in bound.items())
assert all(sha(p)==h for p,h in protocol['source_sha256'].items())
write(root/'completion.json',dict(passed=failure is None,failure=failure,probes=len(probes),passed_probes=sum(p['passed'] for p in probes),
    seconds=time.monotonic()-started,source_sha256=bound,original_parent_and_queued_sources_unchanged=True,
    source_only_overlay=True,actual_CP1r3_package_created=False,actual_CP1r3_package_validated=False,
    real_native_calls=0,graph_or_STA_parsing=False,actual_recovery_executed=False,
    qualification='Real Python entrypoint/import execution using a temporary parent-source view plus exactly the registered two precision workers/helper. Vendor directories referenced readonly; no new graph, route, STA, guard execution or package/admission result. Isolated driver is stopped at a deliberately invalid release id before native work. Actual CP1r3 packaging/guard/public reconstruction and stage audit remain queued.'))
print(dict(passed=failure is None,probes=len(probes),passed_probes=sum(p['passed'] for p in probes),native_calls=0))
if failure:raise SystemExit(1)
