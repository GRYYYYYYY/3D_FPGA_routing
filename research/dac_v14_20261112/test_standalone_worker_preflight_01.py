"""Exercise actual worker preparation, stopping precisely before native invocation."""
import argparse,runpy,sys
from pathlib import Path
import runtime_io as io
from retained_prefix_workflow import read,write,sha

p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);a,args=p.parse_known_args()
class Captured(Exception):pass
def capture(name,command,**kw):
    dependency=read(io.BASE/'runtime_dependency_binding.json')
    assert Path(command[0]).resolve()==Path(dependency['binary']).resolve()
    assert sha(command[0])==dependency['binary_sha256']
    assert '--analysis' in command and '--route' not in command
    env=kw['environment'];assert env['VPR_H3D_MODE']=='off'
    assert env['VPR_JOINT_NATIVE_SEED_ORDER']=='delay_rr_id'
    assert env['VPR_JOINT_NATIVE_CANDIDATE_DIRECTORY']
    assert Path(env['VPR_JOINT_NATIVE_REQUEST']).read_text().split()==['0','0','0']
    assert kw['timeout']==1800
    write(a.capture,dict(passed=True,command=command,environment=env,exact_runtime_binary_binding=True,
        native_calls_new=0,stopped_before_io_run=True,candidate_or_restoration_results=None,
        qualification='Actual descriptor/admission/file/runtime-library/command preparation only; io.run replaced by an explicit capture that never launches VPR.'))
    raise Captured()
io.run=capture
sys.argv=[str(Path(__file__).with_name('run_native_transaction_worker.py')),*args]
try:runpy.run_path(sys.argv[0],run_name='__main__')
except Captured:pass
else:raise AssertionError('Worker did not reach native invocation boundary')
