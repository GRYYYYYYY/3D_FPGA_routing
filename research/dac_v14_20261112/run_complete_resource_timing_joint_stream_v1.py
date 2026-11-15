"""One measured fresh-route/resource/current-STA configuration with no external history."""
import argparse,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir

p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
start=time.monotonic();b=a.output.resolve();b.mkdir(exist_ok=False);config=read(a.config)
resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));assert shutil.disk_usage(b).free>=80*1024**3
assert config['endpoint_loader_strategy']=='existing_streaming_v2_all_observations'
assert config['metadata_cache_strategy']=='explicit_same_measured_flow_only'
assert config['cache_mode']=='joint_build_inside_flow' and config['initial_route_imported'] is False
assert config['external_history_allowed'] is False and config['timing_fraction']==.9
assert config['domain_mode'] in ['paired','unrestricted']
for k in list(os.environ):
 if k.startswith('VPR_'):del os.environ[k]
files={str(Path(f).resolve()):h for f,h in config['input_sha256'].items()}
assert all(sha(f)==h for f,h in files.items())
write(b/'registration.json',dict(config=str(a.config.resolve()),config_sha256=sha(a.config),source_sha256=files,initial_route_imported=False,external_history_allowed=False,phase_binary_sha256=config['phase_binary_sha256'],qualification='All graph-index/query-graph construction, new initial routing, complete resource repair, source handoff observation, complete current-STA timing portfolio, real candidates/rejections/restoration/checks/seals belong to this same command. Phase binaries are explicitly different frozen implementations; no old quality/time/route/query is spliced.'))
stages=[]
def invoke(tag,command,timeout=1800):
 t=time.monotonic()
 with (b/(tag+'.log')).open('w') as log:
  child=subprocess.Popen(list(map(str,command)),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  identity=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19]
  write(b/'active_child.json',dict(pid=child.pid,start_ticks=identity,phase=tag,command=list(map(str,command))))
  try:code=child.wait(timeout=timeout)
  except subprocess.TimeoutExpired:
   os.killpg(child.pid,signal.SIGTERM)
   try:code=child.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);code=child.wait()
   stages.append(dict(phase=tag,status='timeout',returncode=code,complete_process_seconds=time.monotonic()-t));write(b/'stages.json',stages);raise TimeoutError(tag)
 stages.append(dict(phase=tag,status='completed' if code==0 else 'failed',returncode=code,complete_process_seconds=time.monotonic()-t));write(b/'stages.json',stages)
 assert code==0,(tag,code)
def axes(state):
 audit=read(run_dir(state)/'independent_audit.json');assert audit['audit']['passed'];m=audit['physical_metrics']
 return dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=m['sb_pairs_used'],CB_sources=m['cb_crossing_output_sources_used'])
resource_flow=b/'resource_flow'
invoke('fresh_route_and_complete_resource',[sys.executable,D/'run_complete_serial_joint_stream_flow_v1.py','--config',a.config.resolve(),'--output',resource_flow],timeout=None)
resource_done=read(resource_flow/'completion.json');assert resource_done['passed']
initial=Path(resource_done['initial_state']);resource_final=Path(resource_done['final_state'])
root_vector=read(initial/'endpoint_vector.json');root_axes=axes(initial);resource_axes=axes(resource_final)
assert read(resource_final/'endpoint_vector.json')['cpd_s']<=root_vector['cpd_s']
limits=dict(wirelength=(root_axes['wirelength']*1001+999)//1000,SB_pairs=resource_axes['SB_pairs'],CB_sources=resource_axes['CB_sources'])
assert all(resource_axes[k]<=limits[k] for k in limits)
write(b/'absolute_timing_limits.json',limits)
graph=Path(config['route_command'][config['route_command'].index('--read_rr_graph')+1]);query=b/'physical_query_graph'
begin=time.monotonic();joint=resource_flow/'joint_graph_indexes';generated=read(joint/'completion.json')
assert generated['passed'] and generated['XML_traversals']==1 and generated['graph_sha256']==sha(graph)
query.symlink_to(joint/'query_graph',target_is_directory=True)
assert query.resolve().is_relative_to(b)
query_proof=read(query/'completion.json')
assert query_proof['passed'] and query_proof['source_rrg_sha256']==generated['graph_sha256']
assert sha(query/'graph.bin')==query_proof['binary_graph_sha256']
stages.append(dict(phase='bind_same_run_joint_query_graph',status='completed',returncode=0,complete_process_seconds=time.monotonic()-begin));write(b/'stages.json',stages)
handoff=b/'timing_initial'
invoke('resource_final_handoff_FULL_STA',[sys.executable,D/'run_serial_census_state_analysis_stream_v1.py','--source',run_dir(resource_final),'--batch',handoff,'--full-graph-cache',resource_flow/'full_graph_cache','--timing-echo','--fresh-physical-audit'])
assert read(handoff/'completion.json')['passed']
x,y=[read(s/'endpoint_vector.json') for s in [resource_final,handoff]]
assert all(x[k]==y[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
assert route_body(run_dir(resource_final)/'routed.route')==route_body(run_dir(handoff)/'routed.route')
assert axes(resource_final)==axes(handoff)
timing=b/'timing'
invoke('complete_current_STA_timing',[sys.executable,D/'run_complete_flow_critical_portfolio_stream_v1.py','--initial-state',handoff,'--batch',timing,'--query-graph',query,'--audit-cache',resource_flow/'graph_audit_cache','--full-graph-cache',resource_flow/'full_graph_cache','--policy','timing_under_resources','--budget-mode','explicit_absolute','--fixed-limits',b/'absolute_timing_limits.json','--fraction',str(config['timing_fraction'])],timeout=None)
timed=read(timing/'completion.json');assert timed['passed'] and timed['operator_stop']=='no_admissible_candidate_in_current_portfolio'
final=Path(timed['final_state']);assert read(final/'completion.json')['passed']
assert all(sha(f)==h for f,h in files.items())
write(b/'completion.json',dict(passed=True,initial_state=str(initial),resource_final_state=str(resource_final),timing_initial_state=str(handoff),final_state=str(final),config=str(a.config.resolve()),config_sha256=sha(a.config),domain_mode=config['domain_mode'],resource_accepted_steps=resource_done['accepted_steps'],timing_accepted_steps=timed['accepted_steps'],initial_CPD_s=root_vector['cpd_s'],final_CPD_s=read(final/'endpoint_vector.json')['cpd_s'],final_resources=axes(final),absolute_timing_limits=limits,resource_phase_CPDSB_CB=[resource_done['final_CPD_s'],resource_axes['SB_pairs'],resource_axes['CB_sources']],complete_driver_seconds=time.monotonic()-start,complete_outer_measurement='Sibling measurement/completion.json',phase_binary_sha256=config['phase_binary_sha256'],external_history_allowed=False,backend='serial_fresh_route_resource_then_current_STA_joint_indexes',source_sha256={str(f):sha(f) for f in [a.config.resolve(),resource_flow/'completion.json',query/'completion.json',handoff/'completion.json',timing/'completion.json',b/'absolute_timing_limits.json',b/'stages.json']},qualification='Single actually measured configuration from supplied architecture/RRG/BLIF/packed netlist/placement through fresh count8 routing and complete own-current resource plus timing repair. Audit/full/timing graph payloads jointly built inside in one XML traversal; query graph is a same-command output, not supplied reusable state. Explicit phase binary versions and all actual accepted/rejected candidates/checks/STA/restoration are included. Only within-command query/transaction reuse, no external route/candidate/query history; no algorithmic result borrowed from research references. Source graph generation, packing/placement generation and source compilation are upstream. OS cache/shared-host concurrency uncontrolled; full time/memory descriptive and inseparable from this exact output, not statistical speedup.'))
print(dict(passed=True,final_CPD_s=timed['final_CPD_s'],resources=axes(final)),flush=True)
