"""Register one actual complete portable-method execution after all existing work."""
import os,shutil,subprocess
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
for name in ['standalone_unified_method_validation_01','standalone_timing_worker_preparation_01','method_phase_supervision_validation_01']:assert read(D/name/'completion.json')['passed']
root=D/'standalone_whole_method_check_01';root.mkdir(exist_ok=False)
home=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces')
w=home/'whole_method_01';w.mkdir(exist_ok=False);runtime=w/'runtime';package=D/'standalone_unified_method_dev_03'
shutil.copytree(package,runtime,ignore=shutil.ignore_patterns('__pycache__'))
for name in ['numpy','numpy.libs','lxml','lxml.libs']:
    old=home/'unified_method_01/runtime'/name
    if old.exists():shutil.copytree(old,runtime/name,ignore=shutil.ignore_patterns('__pycache__'))
spec=read(home/'unified_method_01/runtime_config.json')
tiny=read(home/'resource_controller_01/runtime_config.json');spec['physical_files']=tiny['physical_files'];spec.pop('full_graph_cache_completion_sha256',None)
phase=w/'phase_runtime.json';write(phase,spec)
cfg=read(home/'resource_controller_01/fresh_resource_config_v2.json')
cfg.update(cache_mode='joint_build_inside_flow',phase_runtime_config=str(phase),endpoint_loader_strategy='existing_streaming_v2_all_observations',metadata_cache_strategy='explicit_same_measured_flow_only',external_history_allowed=False,timing_fraction=.9,unified_controller_version='development_v1',final_state_policy='strict_timing_terminal_after_endpoint_wire_handoff',terminal_resource_policy='endpoint_wire_before_timing')
cfg.pop('full_graph_cache',None)
cfg['route_command'][0]=spec['phase_binaries']['resource']['path']
cfg['route_command'][cfg['route_command'].index('--route_file')+1]=str(w/'UNCREATED_INITIAL_ROUTE')
for flag,value in [('--router_max_convergence_count','8'),('--router_reconvergence_cpd_threshold','1.01')]:
    if flag in cfg['route_command']:cfg['route_command'][cfg['route_command'].index(flag)+1]=value
    else:cfg['route_command'] += [flag,value]
names={'route_and_resource':'resource','owner_coordination':'owner','timing_native_repair':'timing_repair','timing_candidate_STA':'timing_observer'}
cfg['phase_binary_sha256']={key:spec['phase_binaries'][phase]['sha256'] for key,phase in names.items()}
cfg['input_sha256']={r['path']:r['sha256'] for group in ['physical_files','phase_binaries','query_engines','query_validations'] for r in spec[group].values()}
config=w/'config.json';write(config,cfg)
# Exercise actual outer admission and first phase command; deliberately stop
# before launching the fresh-route subprocess. No historical route/cache input.
helper=w/'capture_outer.py';helper.write_text('''import runpy,sys
from pathlib import Path
import phase_supervision
from retained_prefix_workflow import write,read
w=Path(sys.argv[1]);runtime=Path(phase_supervision.__file__).parent
class Captured(Exception):pass
def capture(command,directory,tag,timeout):
 assert tag=='fresh_route_and_complete_resource' and timeout is None
 assert Path(command[1])==runtime/'run_complete_unified_resource_flow_v1.py'
 cfg=read(w/'config.json');assert cfg['cache_mode']=='joint_build_inside_flow' and not cfg['initial_route_imported']
 assert not Path(cfg['route_command'][cfg['route_command'].index('--route_file')+1]).exists()
 write(w/'outer_capture.json',dict(passed=True,command=list(map(str,command)),native_calls_new=0,whole_method_time_cap=None));raise Captured()
phase_supervision.run_phase=capture
sys.argv=[str(runtime/'run_complete_unified_method_v1.py'),'--config',str(w/'config.json'),'--output',str(w/'outer_preflight')]
try:runpy.run_path(sys.argv[0],run_name='__main__')
except Captured:pass
else:raise AssertionError('Outer controller did not reach first phase')
''')
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
cmd=['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(helper),str(w)]
with (root/'outer_preflight.log').open('x') as log:r=subprocess.run(cmd,cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
write(root/'outer_preflight_execution.json',dict(command=cmd,returncode=r.returncode,native_calls_new=0));assert r.returncode==0 and read(w/'outer_capture.json')['passed']
files=[f for f in runtime.rglob('*') if f.is_file()]
files += [phase,config,helper,w/'outer_capture.json',Path(__file__).resolve(),D/'queue_standalone_whole_method_check_01.py',D/'run_standalone_whole_method_check_01.py']
files += [Path(row['path']) for group in ['physical_files','phase_binaries','query_engines','query_validations'] for row in spec[group].values()]
write(root/'plan.json',dict(passed=True,registered_before_native=True,workspace=str(w),package=str(package),predecessor=str(D/'standalone_transaction_native_check_01/queue'),input_sha256={str(f):sha(f) for f in files},input_kind='Existing tiny packing and placement; fresh routing and joint graph build inside measured method',new_independent_inputs=0,full_method_frozen=False,whole_method_time_cap=None,phase_native_seconds=1800,native_calls_planned='Data-dependent complete original method; no total count cap',expected='Native FULL/physical/endpoint gates and original unchanged complete-flow verifier must all pass; initial failures and rejected candidates retained.',qualification='First actual end-to-end execution check for the relocated complete serial method. It is not a repeated completed scientific batch, independent circuit evidence, held-out confirmation, or a speed comparison. Existing queue versions/order unchanged; this check is appended after them.'))
print(dict(registered=True,workspace=str(w),native_calls_new=0,input_files=len(files)),flush=True)
