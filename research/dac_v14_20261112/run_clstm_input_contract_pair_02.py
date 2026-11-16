"""Measure and verify each fixed clstm arm, without repeating any output directory."""
import os,subprocess,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from packed_input_contract_v1 import classify_initial_failure
root=D/'clstm_input_contract_pair_02';plan=read(root/'plan.json');w=Path(plan['workspace']);runtime=Path(plan['runtime']);results={}
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
for arm in plan['fixed_order']:
    assert all(sha(f)==h for f,h in plan['source_sha256'].items())
    case=w/arm;case.mkdir(exist_ok=False);(case/'queue').mkdir();(case/'config.json').write_bytes(Path(plan['cases'][arm]).read_bytes())
    command=['/usr/bin/python3',str(runtime/'measure_process_tree_v1.py'),'--output',str(case/'measurement'),'--','/usr/bin/python3',str(runtime/'supervise_method_phase.py'),'--receipt',str(case/'supervision.json'),'--','/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/'run_complete_unified_method_v1.py'),'--config',str(case/'config.json'),'--output',str(case/'flow')]
    with (case/'launcher.log').open('x') as log:
        child=subprocess.Popen(command,cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT)
        write(case/'queue/registration.json',dict(**process_identity(child.pid),command=command,source_sha256={f:h for f,h in plan['source_sha256'].items() if not Path(f).resolve().is_relative_to(D.parents[1])}));write(root/'active_child.json',dict(arm=arm,**process_identity(child.pid)));code=child.wait()
    measurement=read(case/'measurement/completion.json');supervision=read(case/'supervision.json')
    assert not measurement['live_descendants_after_command_exit'] and not supervision['residual_descendants'],'Do not start another arm over surviving work'
    verified=False
    if code==0 and supervision['passed']:
        with (case/'verification.log').open('x') as log:
            check=subprocess.run(['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/'verify_complete_unified_method_v1.py'),'--root',str(case)],cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT)
        verified=check.returncode==0 and (case/'completion.json').exists() and read(case/'completion.json')['passed']
    status='complete_legal_verified' if verified else 'execution_or_verification_failed'
    initial=case/'flow/resource_flow/initial/runs/state/manifest.json'
    if code and initial.exists():
        m=read(initial)
        status=classify_initial_failure(m,(initial.parent/'stdout.log').read_text())
    results[arm]=dict(status=status,case=str(case),command_returncode=code,quality=None if not verified else {k:read(case/'completion.json')[k] for k in ['CPD_ns','resources']},complete_seconds=measurement['complete_command_wall_seconds'],measurement=str(case/'measurement/completion.json'),supervision=str(case/'supervision.json'))
    write(root/'results.json',results);print(arm,results[arm],flush=True)
assert all(sha(f)==h for f,h in plan['source_sha256'].items())
subprocess.run([sys.executable,str(D/'compare_clstm_input_contract_pair_02.py')],check=True)
