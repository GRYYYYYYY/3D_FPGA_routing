"""Validate revised worker preparation and fresh-route command, without native work."""
import copy,os,shutil,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
report=D/'standalone_resource_controller_validation_02';report.mkdir(exist_ok=False)
w=Path(read(D/'standalone_resource_controller_validation_01/completion.json')['workspace']);package=D/'standalone_resource_controller_dev_02';runtime=w/'runtime_v2';shutil.copytree(package,runtime,ignore=shutil.ignore_patterns('__pycache__'))
for n in ['numpy','numpy.libs','lxml','lxml.libs']:
 if (w/'runtime'/n).exists():shutil.copytree(w/'runtime'/n,runtime/n,ignore=shutil.ignore_patterns('__pycache__'))
assert all(sha(runtime/n)==h for n,h in read(package/'artifact_manifest.json')['sha256'].items())
# Preserve the v1 failure and its completed resource preparation. No native call occurred.
write(D/'standalone_resource_worker_preflight_01/completion.json',dict(passed=False,completed_preparation=['resource'],failed_preparation='census',unexecuted_preparation=['owner'],error='Unported historical full_route_graph_cache_validation_01/completion.json lookup',native_calls_new=0,followup='standalone_resource_controller_validation_02'))
helper=w/'capture_worker_v2.py';code=(D/'capture_resource_worker_preparation_01.py').read_text().replace("('prepare_'+a.worker)","('prepare_v2_'+a.worker)").replace("(a.worker+'_inputs.json')","(a.worker+'_v2_inputs.json')").replace("(a.worker+'_worker_capture.json')","(a.worker+'_v2_worker_capture.json')");helper.write_text(code)
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def execute(script,args,label):
 cmd=['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/script),*map(str,args)];start=time.monotonic()
 with (report/(label+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 write(report/(label+'_execution.json'),dict(command=cmd,returncode=r.returncode,elapsed_seconds=time.monotonic()-start));assert r.returncode==0,label
for kind in ['resource','census','owner']:
 execute(str(helper),['--workspace',w,'--worker',kind],kind+'_preparation');assert read(w/(kind+'_v2_worker_capture.json'))['passed']
actor=w/'resource_flow_v2/repair';actor.parent.mkdir()
execute('run_unified_resource_repair_v1.py',['--runtime-config',w/'runtime_config.json','--initial-state',w/'state','--batch',actor,'--seed-order','delay_rr_id','--domain-feedback','--full-graph-cache',w/'full_cache','--domain-mode','paired','--bundle-size','8','--assert-no-native-work'],'no_cut_controller')
assert read(actor/'completion.json')['passed'] and read(actor/'completion.json')['attempted_scopes']==0
command=read(w/'source/manifest.json')['command'];cfg=read(w/'runtime_config.json');command[0]=cfg['phase_binaries']['resource']['path']
for key,i in [('architecture',1),('circuit',2)]:command[i]=cfg['physical_files'][key]['path']
for flag,key in [('--net_file','packed'),('--place_file','placement'),('--read_rr_graph','graph')]:command[command.index(flag)+1]=cfg['physical_files'][key]['path']
command[command.index('--route_file')+1]=str(w/'UNUSED_ROUTE_OUTPUT')
config=w/'fresh_resource_config_v2.json';write(config,dict(route_command=command,input_sha256={row['path']:row['sha256'] for row in cfg['physical_files'].values()},phase_runtime_config=str(w/'runtime_config.json'),initial_route_imported=False,cache_mode='reusable_graph_only',full_graph_cache=str(w/'full_cache'),domain_mode='paired',domain_feedback=True,seed_order='delay_rr_id',owner_escalation=True,owner_domain_mode='unrestricted_in_both_arms',owner_rank_windows=3))
# Reusable graph-only preflight must explicitly bind the existing cache receipt.
c=read(config);c['input_sha256'][str(w/'full_cache/completion.json')]=sha(w/'full_cache/completion.json');write(config,c)
fresh=w/'capture_fresh_route_v2.py';fresh.write_text('''import runpy,sys
from pathlib import Path
import runtime_io as io
from retained_prefix_workflow import read,write,sha
w=Path(sys.argv[1]);output=w/'fresh_route_preparation_v2'
class Captured(Exception):pass
def capture(name,command,**kw):
 assert '--route' in command and '--analysis' in command
 route=Path(command[command.index('--route_file')+1]);assert route==output/'initial/runs/state/routed.route' and not route.exists()
 assert Path(command[0])==Path(read(output/'initial/runtime_dependency_binding.json')['binary'])
 assert kw['timeout']==1800 and kw['tags']['initial_route_imported'] is False
 assert kw['environment']['VPR_H3D_FINAL_STA_TRACE']
 for flag,key in [('--net_file','packed'),('--place_file','placement')]:
  original=Path(read(w/'runtime_config.json')['physical_files'][key]['path']);assert sha(command[command.index(flag)+1])==sha(original)
 write(w/'fresh_route_v2_capture.json',dict(passed=True,command=command,environment=kw['environment'],input_route_absent=True,native_calls_new=0,stopped_before_io_run=True));raise Captured()
io.run=capture
sys.argv=[str(Path(io.__file__).parent/'run_complete_unified_resource_flow_v1.py'),'--config',str(w/'fresh_resource_config_v2.json'),'--output',str(output)]
try:runpy.run_path(sys.argv[0],run_name='__main__')
except Captured:pass
else:raise AssertionError('Fresh-route entry did not reach native boundary')
''')
execute(str(fresh),[w],'fresh_route_preparation');assert read(w/'fresh_route_v2_capture.json')['passed']
assert all(sha(runtime/n)==h for n,h in read(package/'artifact_manifest.json')['sha256'].items())
unchanged=['run_unified_resource_repair_v1.py','current_owner_transaction_v1.py','current_escape_owner_selector_v1.py','current_crossing_share_selector_v2.py','run_serial_lazy_resource_transactions_stream_v1.py','run_joint_crossing_source_transactions_v2.py','terminal_resource_handoff_v1.py','select_terminal_resource_alternative_v2.py']
assert all(sha(D/'standalone_resource_controller_dev_01'/n)==sha(package/n) for n in unchanged)
write(report/'completion.json',dict(passed=True,workspace=str(w),runtime=str(runtime),actual_three_worker_preparations_passed=True,actual_fresh_route_preparation_passed=True,fresh_route_input_absent=True,actual_no_cut_controller_passed=True,reused_R1_selection_preparation_evidence='standalone_resource_owner_preparation_01/completion.json',unchanged_controller_owner_selection_backend_terminal_files=unchanged,original_failure_preserved=True,native_calls_new=0,new_independent_inputs=0,full_method_frozen=False,actual_native_backend_execution_tested=False,positive_owner_commit_reentry_tested=False,source_sha256={str(package/'artifact_manifest.json'):sha(package/'artifact_manifest.json'),str(actor/'completion.json'):sha(actor/'completion.json'),str(w/'fresh_route_v2_capture.json'):sha(w/'fresh_route_v2_capture.json'),str(Path(__file__).resolve()):sha(__file__)},qualification='Real original no-cut state machine executed; three actual worker preparations and fresh-route entry stopped at explicit io.run capture. R1 selector/request checks reused only for byte-exact unchanged code. Cold graph-generation path not executed here; fresh-route preflight uses explicitly imported graph-only cache. Native routing/repair and whole timing-method results remain pending.'))
print(dict(passed=True,no_cut_controller=True,worker_preparations=3,fresh_route_preparation=True,native_calls_new=0),flush=True)
