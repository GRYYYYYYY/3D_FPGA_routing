"""Execute and fully verify the registered relocated whole method exactly once."""
import os,subprocess,time,traceback
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'standalone_whole_method_check_01';plan=read(root/'plan_v2.json');w=Path(plan['workspace']);runtime=w/'runtime'
case=w/'execution';case.mkdir(exist_ok=False);(case/'queue').mkdir();(case/'config.json').write_bytes((w/'config.json').read_bytes())
assert all(sha(f)==h for f,h in plan['input_sha256'].items())
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
command=['/usr/bin/python3',str(runtime/'measure_process_tree_v1.py'),'--output',str(case/'measurement'),'--','/usr/bin/python3',str(runtime/'supervise_method_phase.py'),'--receipt',str(case/'supervision.json'),'--','/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/'run_complete_unified_method_v1.py'),'--config',str(case/'config.json'),'--output',str(case/'flow')]
try:
    with (case/'launcher.log').open('x') as log:
        child=subprocess.Popen(command,cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT)
        write(case/'queue/registration.json',dict(**process_identity(child.pid),command=command,source_sha256={f:h for f,h in plan['input_sha256'].items() if not Path(f).resolve().is_relative_to(D.parents[1])}));write(root/'active_child.json',process_identity(child.pid));code=child.wait()
    assert code==0 and read(case/'supervision.json')['passed']
    assert not read(case/'measurement/completion.json')['live_descendants_after_command_exit']
    with (case/'verification.log').open('x') as log:
        r=subprocess.run(['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/'verify_complete_unified_method_v1.py'),'--root',str(case)],cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert r.returncode==0 and read(case/'completion.json')['passed']
    assert all(sha(f)==h for f,h in plan['input_sha256'].items())
    actual=read(case/'completion.json');files=[root/'plan_v2.json',case/'completion.json',case/'measurement/completion.json',case/'supervision.json']
    write(root/'completion.json',dict(passed=True,workspace=str(w),whole_method_executed_and_verified=True,new_independent_inputs=0,full_method_frozen=False,result=actual,source_sha256={str(f):sha(f) for f in files},qualification='Actual whole-method portability check on existing tiny input. No positive owner reentry or independent multi-input benefit inferred. Cost belongs only to this exact supervised development execution.'))
except Exception as error:
    write(root/'completion.json',dict(passed=False,workspace=str(w),error=repr(error),new_independent_inputs=0,full_method_frozen=False,qualification='Actual receipts retained. Never retry completed native calls; diagnose remaining unmet checks or change the next independent test.'))
    traceback.print_exc();raise
