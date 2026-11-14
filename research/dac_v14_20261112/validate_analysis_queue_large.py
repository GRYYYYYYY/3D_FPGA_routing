#!/usr/bin/env python3
"""Actual dynamic BNN FULLSTA requests with fresh same-binary references."""
import os,shutil,signal,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from native_analysis_pool import NativeAnalysisPool
b=D/'analysis_queue_equivalence_bnn_01';b.mkdir(exist_ok=False);start=time.monotonic();assert read(D/'analysis_queue_tiny_regression_01/completion.json')['passed'];assert read(D/'analysis_queue_static_compatibility_01/completion.json')['passed'];binary=D/'analysis_queue_stage_01/bin/vpr';assert sha(binary)==read(D/'analysis_queue_stage_01/binding.json')['binary_sha256'];steps=read(D/'portfolio_execution_dev_01/R1_strict/steps.json');states={'R1_root':D/'timing_cone_bnn_dev_02/R1','R1_repaired':Path(steps[-1]['evaluation'])};runs={k:run_dir(p) for k,p in states.items()}
for p in states.values():assert read(p/'completion.json')['passed']
assert len({sha(p/'packed.net') for p in runs.values()})==len({sha(p/'placed.place') for p in runs.values()})==1
source=runs['R1_root'];command=list(read(source/'manifest.json')['command']);command[0]=str(binary)
if '--route' in command:command.remove('--route')
assert '--analysis' in command;command[command.index('--check_route')+1]='full'
if '--verify_route_file_switch_id' not in command:command+=['--verify_route_file_switch_id','on']
else:command[command.index('--verify_route_file_switch_id')+1]='on'
for opt,name in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:command[command.index(opt)+1]=str(source/name)
static=[Path(command[1]),Path(command[2]),Path(command[command.index('--read_rr_graph')+1]),source/'packed.net',source/'placed.place'];files=[Path(__file__).resolve(),binary,D/'native_analysis_pool.py',D/'analysis_queue_stage_01/binding.json',D/'analysis_queue_tiny_regression_01/completion.json',D/'analysis_queue_static_compatibility_01/completion.json',*static]
for name,p in states.items():files += [p/'completion.json',p/'endpoint_vector.json',runs[name]/'routed.route',runs[name]/'native_sta_frontier.jsonl',runs[name]/'timing_graph.full_precision.echo',runs[name]/'independent_audit.json']
write(b/'registration.json',dict(status='before_native',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],states={k:str(v) for k,v in states.items()},command=command,source_sha256={str(p):sha(p) for p in files},question='Does dynamic native context loading preserve every FULLSTA/constraint/precision-graph result for pristine R1, a newly submitted repaired state, and return to pristine R1; does exact cache reuse avoid an extra child?',guards=dict(memory_bytes=64*1024**3,child_seconds=1800,startup_seconds=1800,epoch_seconds=1800,idle_seconds=300,disk_reserve_bytes=80*1024**3,max_VPR_processes_including_existing_quality_actor=3),route_flow_calls=0,qualification='Read-only engineering equivalence on sealed actual routes. Fresh same-binary standalone references required. Candidate file is created after first dynamic result. No new routing candidate, initial routability or whole-algorithm speedup claim.'))
guard=D.parents[1]/'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard';base={k:v for k,v in os.environ.items() if not k.startswith('VPR_')};base['VPR_H3D_MODE']='off';costs=[];references={}
for name,rd in runs.items():
 out=b/('standalone_'+name);out.mkdir();cmd=list(command);cmd[cmd.index('--route_file')+1]=str(rd/'routed.route');env=dict(base,VPR_H3D_FINAL_STA_TRACE=str(out/'native_sta_frontier.jsonl'),VPR_H3D_FINAL_TIMING_ECHO=str(out/'timing_graph.full_precision.echo'));t=time.monotonic()
 with (out/'stdout.log').open('w') as log:
  p=subprocess.Popen(['prlimit','--core=0:0','--as='+str(64*1024**3),'--',str(guard),*cmd],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);write(b/'active_child.json',dict(phase='fresh_reference',name=name,pid=p.pid,start_ticks=(Path('/proc')/str(p.pid)/'stat').read_text().split(') ',1)[1].split()[19]))
  try:code=p.wait(timeout=1800)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();raise
 costs.append(dict(name=name,returncode=code,complete_native_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs);assert code==0
 for f in ['native_sta_frontier.jsonl','timing_graph.full_precision.echo']:assert sha(out/f)==sha(rd/f),(name,f)
 references[name]=out;write(b/'progress.json',dict(status='same_binary_reference_complete',case=name))
pool=NativeAnalysisPool(b/'pool',command,static,guard)
def verify(result,reference):
 assert result['passed'] and not result['reused']
 for f in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','timing_graph.full_precision.echo']:assert sha(Path(result['native_directory'])/f)==sha(reference/f),(reference,f)
first=pool.analyze(runs['R1_root']/'routed.route');verify(first,references['R1_root']);write(b/'progress.json',dict(status='dynamic_first_complete',parent_pid=first['epoch_pid'],CPD_ns=read(states['R1_root']/'endpoint_vector.json')['cpd_s']*1e9))
new=b/'candidate_submitted_after_first.route';shutil.copy2(runs['R1_repaired']/'routed.route',new);second=pool.analyze(new);verify(second,references['R1_repaired']);assert second['epoch_pid']==first['epoch_pid'];write(b/'progress.json',dict(status='dynamic_new_state_complete',parent_pid=second['epoch_pid'],CPD_ns=read(states['R1_repaired']/'endpoint_vector.json')['cpd_s']*1e9))
third=pool.analyze(runs['R1_root']/'routed.route',reuse=False);verify(third,references['R1_root']);assert third['epoch_pid']==first['epoch_pid'];reuse=pool.analyze(new);assert reuse['reused'] and reuse['native_child_seconds'] is None and len(pool.jobs)==3
pool.close();pc=read(b/'pool/completion.json');assert pc['passed'] and pc['all_jobs_passed'] and pc['epochs']==1 and pc['jobs']==3 and pc['reuse_hits']==1
assert all(sha(p)==h for p,h in read(b/'registration.json')['source_sha256'].items())
write(b/'completion.json',dict(passed=True,reference_states=2,new_native_parent_processes=3,dynamic_children=3,reuse_hits=1,new_candidate_created_after_first_receipt=True,whole_native_precision_graph_STA_constraints_exact=True,default_off_matches_old_native=True,return_to_original_exact=True,static_inputs_unchanged=True,route_flow_calls=0,standalone_reference_costs=costs,pool_component_seconds=pc['complete_component_workflow_seconds'],pool_epochs=read(b/'pool/epochs.json'),child_costs=read(b/'pool/jobs.json'),complete_engineering_workflow_seconds=time.monotonic()-start,complete_single_configuration_seconds=None,formal_speedup=None,source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'process_costs.json',b/'pool/completion.json',Path(__file__).resolve()]},qualification='Actual dynamically submitted BNN analyses preserve fresh native physical timing/pin synchronization/FULL/STA, including return to an earlier state; exact reuse has no borrowed creation time. Fresh reference count differs from pooled job count, so no paired or cold algorithm speedup. Original quality cohorts unchanged.'))
print(dict(passed=True,dynamic_children=3,reuse_hits=1),flush=True)
