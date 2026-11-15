"""Reach actual relocated timing worker native boundary without executing VPR."""
import argparse,runpy,sys
from pathlib import Path
import runtime_io as io
from controller_runtime import worker_descriptor
from retained_prefix_workflow import read,write,sha
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--phase',choices=['timing_repair','timing_observer'],required=True);a=p.parse_args();w=a.workspace
phase=a.phase;name='run_independent_resource_state_analysis_stream_v1.py' if phase=='timing_repair' else 'run_independent_timing_cone_analysis_stream_v1.py'
b=w/('prepare_'+phase);descriptor=worker_descriptor(w/'runtime_config.json',w/'source',w/'full_cache',phase,w/(phase+'_inputs.json'))
args=['--inputs',str(descriptor),'--source',str(w/'source'),'--batch',str(b)]
empty=w/'empty_request.txt'
if not empty.exists():empty.write_text('0\n0\n0\n')
if phase=='timing_repair':args+=['--native-cases',str(empty),'--objective','weighted_soft']
else:args+=['--candidate-route',str(w/'source/routed.route'),'--full-graph-cache',str(w/'full_cache'),'--timing-echo']
class Captured(Exception):pass
def capture(name,command,**kw):
    spec=read(descriptor);binding=read(b/'runtime_dependency_binding.json')
    assert Path(command[0])==Path(spec['files']['binary']['path'])==Path(binding['binary'])
    assert sha(command[0])==binding['binary_sha256']==spec['files']['binary']['sha256']
    assert '--analysis' in command and '--route' not in command and kw['timeout']==1800
    assert kw['environment']['VPR_H3D_FINAL_STA_TRACE']
    if phase=='timing_repair':
        assert kw['environment']['VPR_JOINT_NATIVE_OBJECTIVE']=='weighted_soft'
        assert kw['environment']['VPR_JOINT_NATIVE_REQUEST']==str(empty)
    else:assert kw['environment']['VPR_H3D_FINAL_TIMING_ECHO']
    write(w/(phase+'_capture.json'),dict(passed=True,command=command,environment=kw['environment'],native_calls_new=0,actual_runtime_binding=True,stopped_before_io_run=True));raise Captured()
io.run=capture
sys.argv=[str(Path(io.__file__).parent/name),*args]
try:runpy.run_path(sys.argv[0],run_name='__main__')
except Captured:pass
else:raise AssertionError('Worker did not reach native execution boundary')
