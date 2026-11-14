#!/usr/bin/env python3
"""Current-STA resource refinement with one native VPR at a time and no live pool."""
import argparse,fcntl,hashlib,json,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from full_route_graph_cache import FullRouteGraphCache
from current_crossing_share_selector_v2 import select
from current_resource_bundle_v2 import select_cuts,serialize_request
p=argparse.ArgumentParser();p.add_argument('--initial-state',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);p.add_argument('--domain-mode',choices=['paired','unrestricted'],required=True);p.add_argument('--bundle-size',type=int,default=4);a=p.parse_args();assert a.bundle_size>0;started=time.monotonic();b=a.batch.resolve();b.mkdir(exist_ok=False);lock=(b/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));initial=a.initial_state.resolve();r=run_dir(initial);assert read(initial/'completion.json')['passed']and read(r/'independent_audit.json')['audit']['passed'];root=read(initial/'endpoint_vector.json');physical=read(r/'independent_audit.json')['physical_metrics'];rootres=dict(wirelength=physical['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=physical['sb_pairs_used'],CB_sources=physical['cb_crossing_output_sources_used']);anchor=dict(CPD_s=root['cpd_s'],**rootres);limits=dict(rootres,wirelength=(rootres['wirelength']*1001+999)//1000);cache_dir=D/'full_route_graph_cache_bnn_01';m=read(r/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);cache=FullRouteGraphCache(graph,cache_dir);files=[Path(__file__).resolve(),D/'run_serial_resource_transactions.py',D/'run_independent_resource_state_analysis.py',D/'run_independent_timing_cone_analysis.py',D/'audit_native_objective_cached.py',D/'audit_retained_crossing_domain.py',D/'current_crossing_share_selector_v2.py',D/'current_resource_bundle_v2.py',D/'multiobjective_acceptance_v2.py',D/'resource_domain_stage_01/binding.json',D/'timing_cone_stage_03/binding.json',D/'strong_A0_fast_resource_screen_01/completion.json',initial/'completion.json',initial/'endpoint_vector.json',r/'routed.route',r/'manifest.json',r/'independent_audit.json',cache_dir/'completion.json'];bindings={str(f):sha(f)for f in files};write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],initial_state=str(initial),anchor=anchor,resource_limits=limits,bundle_size=a.bundle_size,domain_mode=a.domain_mode,source_sha256=bindings,question='Can the existing resource selector reduce actual SB/CB after the strong-A0 timing trajectory while preserving its exact CPD and low-wire advantage?',selection='First current rank windows of distinct-net K4 cuts, criticality-sorted restoration, fresh complete current STA/resource selector after each accepted whole transaction.',local_probe=dict(accepted_steps=2,rank_windows=3),limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),qualification='Independent diagnostic from a sealed automatically obtained timing state. Serial native workers at most one, concurrent main chain at most two. Different implementation backend costs are not a formal speedup comparison. Versions and roots fixed; local operator end does not finish research.'))
current=initial;steps=[];attempts=[];costs=[];seen=set();stop=None

def persist():
 write(b/'steps.json',steps);write(b/'attempts.json',attempts);write(b/'process_costs.json',costs);write(b/'current_state.json',dict(state=str(current),accepted_steps=len(steps),anchor=anchor,resource_limits=limits))
def invoke(tx,tag):
 assert shutil.disk_usage(D).free>=80*1024**3;t=time.monotonic();cmd=[sys.executable,str(D/'run_serial_resource_transactions.py'),'--batch',str(tx)]
 with (b/(tag+'.log')).open('w')as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);write(b/'active_child.json',dict(pid=proc.pid,start_ticks=Path('/proc',str(proc.pid),'stat').read_text().split(') ',1)[1].split()[19],tag=tag,command=cmd));code=proc.wait()
 costs.append(dict(tag=tag,status='completed'if code==0 else'failed',complete_process_seconds=time.monotonic()-t,returncode=code));persist();return code==0
persist()
while len(steps)<2:
 rd=b/f'round_{len(steps):03d}';rd.mkdir();t=time.monotonic();reused_selection=False
 if not steps and current==initial:
  screen=D/'strong_A0_fast_resource_screen_01';proof=read(screen/'completion.json');selection=read(screen/'selection/completion.json');assert proof['passed'] and Path(proof['source_state'])==current and selection['source_state']==str(current) and selection['route_sha256']==sha(run_dir(current)/'routed.route');assert all(sha(f)==h for f,h in proof['source_sha256'].items())and all(sha(f)==h for f,h in selection['source_sha256'].items());shutil.copytree(screen/'selection',rd/'selection');cuts=read(rd/'selection/candidates.json');reused_selection=True;write(rd/'selection_reuse.json',dict(source=str(screen/'selection/completion.json'),source_sha256=sha(screen/'selection/completion.json'),same_current_state=True,creation_cost_borrowed=False))
 else:cuts=select(current,cache,rd/'selection')
 costs.append(dict(tag=f'{len(steps):03d}_current_resource_selection',status='reused'if reused_selection else'completed',complete_process_seconds=time.monotonic()-t));advanced=False
 for ci in range(min(3,len(cuts))):
  selected=select_cuts(cuts,a.bundle_size,ci)
  if not selected:continue
  req,domain,queries=serialize_request(selected);key=hashlib.sha256(json.dumps([sha(run_dir(current)/'routed.route'),req,domain,a.domain_mode]).encode()).hexdigest()
  if key in seen:continue
  seen.add(key);tx=rd/f'candidate_{ci:02d}';tx.mkdir();request=tx/'request.txt';request.write_text(req);domain_file=tx/'domain.txt';domain_file.write_text(domain);roles={};removed={str(cut['net']):cut['pins']for cut in selected}
  for enabled in([False,True]if a.domain_mode=='paired'else[False]):
   name='reuse_'+('on'if enabled else'off');role=dict(state=str(current),source=str(run_dir(current)),baseline='strong_A0_fast',scope=f'own_current_resource_K{a.bundle_size}',request=str(request),queries=queries,removed_pins=removed,objective='weighted_soft',fixed_target_paths=False,crossing_reuse_enabled=enabled,crossing_domain=str(domain_file),original_budget=anchor,fixed_resource_limits=limits,source_sha256={str(f):sha(f)for f in[current/'completion.json',current/'endpoint_vector.json',run_dir(current)/'routed.route',request,domain_file]});roles[name]=role
  write(tx/'registration.json',dict(roles=roles,source_sha256={str(f):sha(f)for f in[rd/'selection/completion.json',b/'registration.json']},limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),current_resource_selector_after_commit=True,resource_conditions=dict(anchor=anchor,resource_limits=limits,resource_objectives=['SB_pairs','CB_sources'])));ok=invoke(tx,f'{len(steps):03d}_{ci:02d}_serial_native_transaction');progress=read(tx/'progress.json')if(tx/'progress.json').exists()else{};record=dict(round=len(steps),candidate_rank=ci,current_state=str(current),transaction=str(tx),native_transaction_complete=ok,removed_pins=removed,roles=progress);winner=None
  for name in['reuse_on','reuse_off']:
   row=progress.get(name,{})
   if row.get('status')=='legal_evaluated'and read(tx/(name+'_decisions.json'))['resources_under_timing']['accepted']:winner=Path(row['evaluation']);record['accepted_role']=name;break
  attempts.append(record)
  if winner is not None:
   # The independently computed fixed-envelope decision already checks full precision, hold, native legality and actual resources.
   assert read(winner/'endpoint_vector.json')['cpd_s']<=anchor['CPD_s'];record['committed_evaluation']=str(winner);steps.append(record);current=winner;advanced=True;persist();break
  persist()
 if not advanced:stop='no_admissible_candidate_in_registered_current_scope_probe';break
if stop is None:stop='two_accepted_steps_local_integration_probe'
assert all(sha(f)==h for f,h in bindings.items());persist();v=read(current/'endpoint_vector.json');p=read(run_dir(current)/'independent_audit.json')['physical_metrics'];write(b/'completion.json',dict(passed=True,operator_stop=stop,initial_state=str(initial),final_state=str(current),accepted_steps=len(steps),attempted_scopes=len(attempts),final_CPD_s=v['cpd_s'],final_resources=dict(wirelength=p['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=p['sb_pairs_used'],CB_sources=p['cb_crossing_output_sources_used']),complete_imported_state_workflow_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None,source_sha256={str(f):sha(f)for f in[b/'registration.json',b/'steps.json',b/'attempts.json',b/'process_costs.json',b/'current_state.json']},qualification='Current-state serial resource trajectory; every accepted whole candidate has native FULL/STA and independent physical/domain checks. Current sources are immutable; rejected/failed private candidates do not change occupancy/state. End of this local probe does not terminate ongoing research.'))
print(dict(accepted_steps=len(steps),CPD_ns=v['cpd_s']*1e9),flush=True)
