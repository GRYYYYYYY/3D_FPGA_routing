#!/usr/bin/env python3
"""Compare read-only COW FULLSTA workers to fresh same-binary large analyses."""
import csv,os,shutil,signal,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
b=D/'analysis_fork_equivalence_bnn_01';b.mkdir(exist_ok=False);stage=D/'analysis_fork_stage_02';binary=stage/'bin/vpr';assert read(D/'analysis_fork_tiny_regression_02/completion.json')['passed'];assert sha(binary)==read(stage/'binding.json')['binary_sha256'];started=time.monotonic()
states={'A0':D/'timing_cone_bnn_dev_02/A0','A0_endpoint_bridge':D/'portfolio_execution_dev_01/A0_endpoint/round_001/proposal_03/transaction/current_group_evaluation'}
runs={k:run_dir(p) for k,p in states.items()}
for p in states.values():assert read(p/'completion.json')['passed']
assert len({sha(p/'packed.net') for p in runs.values()})==len({sha(p/'placed.place') for p in runs.values()})==1
base=read(runs['A0']/'manifest.json')['command'];cmd=list(base);cmd[0]=str(binary)
if '--route' in cmd:cmd.remove('--route')
assert '--analysis' in cmd and '--read_rr_graph' in cmd and cmd[cmd.index('--check_route')+1]=='full'
for opt,name in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(runs['A0']/name)
if '--verify_route_file_switch_id' not in cmd:cmd+=['--verify_route_file_switch_id','on']
else:cmd[cmd.index('--verify_route_file_switch_id')+1]='on'
files=[Path(__file__).resolve(),D/'analysis_fork_stage_02/binding.json',D/'analysis_fork_tiny_regression_02/completion.json',binary,Path(cmd[1]),Path(cmd[2]),Path(cmd[cmd.index('--read_rr_graph')+1])]
for name,p in states.items():files += [p/'completion.json',p/'endpoint_vector.json',runs[name]/'manifest.json',runs[name]/'independent_audit.json',runs[name]/'packed.net',runs[name]/'placed.place',runs[name]/'routed.route',runs[name]/'native_sta_frontier.jsonl',runs[name]/'timing_graph.full_precision.echo']
write(b/'registration.json',dict(status='before_native',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],question='Does loading shared BNN circuit/packing/placement/RRG once preserve FULLSTA, complete endpoint/clock-domain/constraint identity and native pin remapping for original/accepted owner-then-target routes, including return to the original state?',states={k:str(v) for k,v in states.items()},source_sha256={str(p):sha(p) for p in files},command_template=cmd,limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,max_concurrent_VPR_including_existing_quality_actor=3),route_search_calls=0,qualification='Independent read-only engineering equivalence cohort. Fresh same-binary standalone reference processes are required; timings include engineering validation/echo, not cold single-configuration algorithm or a formal speedup. Existing quality actors keep original binary/inputs/rules.'))
guard=D.parents[1]/'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard';env={k:v for k,v in os.environ.items() if not k.startswith('VPR_')};env['VPR_H3D_MODE']='off';costs=[]
def run(name,command,extra=None):
 directory=b/name;directory.mkdir();assert shutil.disk_usage(b).free>=80*1024**3;e=dict(env,VPR_H3D_FINAL_STA_TRACE=str(directory/'native_sta_frontier.jsonl'),VPR_H3D_FINAL_TIMING_ECHO=str(directory/'timing_graph.full_precision.echo'));e.update(extra or {});t=time.monotonic()
 with (directory/'stdout.log').open('w') as log:
  proc=subprocess.Popen(['prlimit','--core=0:0','--as='+str(64*1024**3),'--',str(guard),*command],cwd=directory,env=e,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);write(b/'active_child.json',dict(name=name,pid=proc.pid,start_ticks=(Path('/proc')/str(proc.pid)/'stat').read_text().split(') ',1)[1].split()[19],started_at=time.time()))
  try:code=proc.wait(timeout=1800)
  except subprocess.TimeoutExpired:
   os.killpg(proc.pid,signal.SIGKILL);code=proc.wait();costs.append(dict(name=name,returncode=code,timed_out=True,complete_native_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs);raise
 costs.append(dict(name=name,returncode=code,timed_out=False,complete_native_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs);assert code==0,(name,code)
 return directory
references={}
for name,source in runs.items():
 command=list(cmd);command[command.index('--route_file')+1]=str(source/'routed.route');rd=run('standalone_'+name,command);references[name]=rd
 for file in ['native_sta_frontier.jsonl','timing_graph.full_precision.echo']:
  assert sha(rd/file)==sha(source/file),(name,file,'New binary default-off differs from accepted frozen observer')
 stdout=(rd/'stdout.log').read_text();assert 'Completed routing consistency check successfully' in stdout and 'Synchronize the packed netlist to routing optimization' in stdout
 write(b/'progress.json',dict(status='same_binary_reference_complete',case=name,matched_old_native=True))
entries=[]
for i,name in enumerate(['A0','A0_endpoint_bridge','A0']):
 directory=b/('worker_'+str(i));directory.mkdir();entries.append((name,runs[name]/'routed.route',directory))
manifest=b/'manifest.txt';manifest.write_text(str(len(entries))+'\n'+''.join(__import__('json').dumps(str(route))+' '+__import__('json').dumps(str(directory))+' 1\n' for name,route,directory in entries))
parent=run('fork_parent',cmd,dict(VPR_H3D_ANALYSIS_FORK_MANIFEST=str(manifest),VPR_H3D_ANALYSIS_FORK_RESULTS=str(b/'workers.tsv')));rows=list(csv.DictReader((b/'workers.tsv').open(),delimiter='\t'));assert len(rows)==len(entries) and all(int(r['exit_code'])==0 and int(r['signal'])==0 and not int(r['timed_out']) for r in rows)
for i,(name,route,directory) in enumerate(entries):
 for file in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','timing_graph.full_precision.echo']:
  assert sha(directory/file)==sha(references[name]/file),(i,name,file)
 stdout=(directory/'stdout.log').read_text();assert 'Completed routing consistency check successfully' in stdout and 'Synchronize the packed netlist to routing optimization' in stdout
assert sum(l.startswith('# Load packing took') for l in (parent/'stdout.log').read_text().splitlines())==1
assert not(parent/'native_sta_frontier.jsonl').exists()
assert all(sha(p)==h for p,h in read(b/'registration.json')['source_sha256'].items())
write(b/'completion.json',dict(passed=True,native_parent_processes=3,full_analysis_workers=3,existing_accepted_states=2,precision_STA_constraints_and_graph_exact=True,default_off_old_native_exact=True,parent_never_loaded_or_synchronized_route=True,original_inputs_unchanged=True,route_search_calls=0,observed_native_processes=costs,child_observations=rows,complete_engineering_workflow_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None,matched_formal_speedup=None,source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'process_costs.json',b/'workers.tsv',manifest,Path(__file__).resolve()]},qualification='Large BNN native FULLSTA/state isolation validated against two fresh same-binary standalone references and existing sealed accepted observations. Read-only analyses do not add routing-quality candidates or initial routability evidence. Includes echo/validation costs; no whole-algorithm speedup claim.'))
print(dict(passed=True,workers=3,states=2),flush=True)
