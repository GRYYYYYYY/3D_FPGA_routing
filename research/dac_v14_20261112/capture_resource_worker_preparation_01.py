"""Exercise the original serial worker command path without launching a native child."""
import argparse,runpy,sys
from pathlib import Path
import runtime_io as io
from retained_prefix_workflow import read,write,sha
from controller_runtime import worker_descriptor
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--worker',required=True);a=p.parse_args();w=a.workspace
mapping={'resource':'run_serial_seed_resource_state_analysis_stream_v1.py','census':'run_serial_census_state_analysis_stream_v1.py','owner':'run_crossing_source_seed_analysis_v1.py'};name=mapping[a.worker];phase='owner' if a.worker=='owner' else 'resource'
b=w/('prepare_'+a.worker);descriptor=worker_descriptor(w/'runtime_config.json',w/'source',w/'full_cache',phase,w/(a.worker+'_inputs.json'))
empty=w/'empty_request.txt'
if not empty.exists():empty.write_text('0\n0\n0\n')
args=['--inputs',str(descriptor),'--source',str(w/'source'),'--batch',str(b)]
if a.worker=='census':args+=['--full-graph-cache',str(w/'full_cache'),'--timing-echo']
else:args+=['--seed-order','delay_rr_id','--native-cases',str(empty)]
if a.worker=='owner':args+=['--candidate-full-sta']
class Captured(Exception):pass
def capture(n,command,**kw):
 spec=read(descriptor);binding=read(b/'runtime_dependency_binding.json')
 assert Path(command[0])==Path(spec['files']['binary']['path'])==Path(binding['binary'])
 assert sha(command[0])==binding['binary_sha256']==spec['files']['binary']['sha256']
 assert '--analysis' in command and '--route' not in command
 assert kw['timeout']==1800 and kw['environment']['VPR_H3D_MODE']=='off'
 if a.worker=='census':assert kw['environment']['VPR_H3D_FINAL_TIMING_ECHO']
 else:
  assert kw['environment']['VPR_JOINT_NATIVE_SEED_ORDER']=='delay_rr_id'
  assert kw['environment']['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE']=='0'
  assert Path(kw['environment']['VPR_JOINT_NATIVE_REQUEST']).read_text()==empty.read_text()
 if a.worker=='owner':assert kw['environment']['VPR_JOINT_NATIVE_CANDIDATE_DIRECTORY']
 write(w/(a.worker+'_worker_capture.json'),dict(passed=True,worker=name,phase=phase,command=command,environment=kw['environment'],native_calls_new=0,actual_runtime_binding=True,stopped_before_io_run=True));raise Captured()
io.run=capture
sys.argv=[str(Path(io.__file__).parent/name),*args]
try:runpy.run_path(sys.argv[0],run_name='__main__')
except Captured:pass
else:raise AssertionError('Worker never reached actual native boundary')
