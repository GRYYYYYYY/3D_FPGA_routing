#!/usr/bin/env python3
"""Current resource refinement plus capacity-certified owner escalation; development integration."""
import argparse,fcntl,hashlib,json,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from full_route_graph_cache import FullRouteGraphCache
from current_crossing_share_selector_v2 import select
from current_resource_bundle_v2 import select_cuts,serialize_request
from current_escape_owner_selector_v1 import select as select_owners
from current_owner_transaction_v1 import prepare as prepare_owner
from controller_runtime import package_files,admit_controller
p=argparse.ArgumentParser();p.add_argument('--runtime-config',type=Path,required=True);p.add_argument('--initial-state',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);p.add_argument('--seed-order',choices=['native','rr_id','delay_rr_id'],required=True);p.add_argument('--domain-feedback',action='store_true');p.add_argument('--full-graph-cache',type=Path,required=True);p.add_argument('--domain-mode',choices=['paired','unrestricted'],required=True);p.add_argument('--bundle-size',type=int,default=4);p.add_argument('--reuse-native-batch',type=Path,action='append',default=[]);p.add_argument('--assert-no-native-work',action='store_true');p.add_argument('--disable-owner-escalation',action='store_true');p.add_argument('--owner-rank-windows',type=int,default=3);a=p.parse_args();assert not a.reuse_native_batch, 'No historical query/transaction reuse in unified controller';assert a.owner_rank_windows>0;assert a.bundle_size>0;started=time.monotonic();b=a.batch.resolve();b.mkdir(exist_ok=False);lock=(b/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));initial=a.initial_state.resolve();r=run_dir(initial);assert read(initial/'completion.json')['passed']and read(r/'independent_audit.json')['audit']['passed'];root=read(initial/'endpoint_vector.json');physical=read(r/'independent_audit.json')['physical_metrics'];rootres=dict(wirelength=physical['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=physical['sb_pairs_used'],CB_sources=physical['cb_crossing_output_sources_used']);anchor=dict(CPD_s=root['cpd_s'],**rootres);limits=dict(rootres,wirelength=(rootres['wirelength']*1001+999)//1000);cache_dir=a.full_graph_cache.resolve();m=read(r/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);cache=FullRouteGraphCache(graph,cache_dir);files=[*package_files(),a.runtime_config.resolve(),initial/'completion.json',initial/'endpoint_vector.json',r/'routed.route',r/'manifest.json',r/'independent_audit.json',cache_dir/'completion.json'];files += admit_controller(a.runtime_config,initial,cache_dir);bindings={str(f):sha(f)for f in files};write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],initial_state=str(initial),owner_escalation=not a.disable_owner_escalation,owner_rank_windows=a.owner_rank_windows,owner_domain_mode='unrestricted_in_both_arms',anchor=anchor,resource_limits=limits,bundle_size=a.bundle_size,domain_mode=a.domain_mode,seed_order=a.seed_order,domain_feedback=a.domain_feedback,reuse_native_batches=[str(p.resolve())for p in a.reuse_native_batch],source_sha256=bindings,question='Does the globally fixed seed policy improve complete fresh-route resource refinement under matched native controls and exact physical/FULLSTA checks?',selection='Registered seed policy and optional domain failure release. First current rank windows of distinct-net cuts, criticality-sorted restoration, fresh complete current STA/resource selector after each accepted whole transaction.',local_probe=dict(accepted_steps=0,rank_windows=3),limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),qualification='Independent diagnostic from a sealed automatically obtained timing state. Serial native workers at most one, concurrent main chain at most two. Full current-state menu to completion; no accepted-step cap. This backend uses registered seed order and optional domain failure release. Different implementation backend costs are not a formal speedup comparison. Versions and roots fixed; local operator end does not finish research.'))
assert all(sha(path)==h for path,h in bindings.items())
current=initial;steps=[];attempts=[];costs=[];seen=set();stop=None

def persist():
 write(b/'steps.json',steps);write(b/'attempts.json',attempts);write(b/'process_costs.json',costs);write(b/'current_state.json',dict(state=str(current),accepted_steps=len(steps),anchor=anchor,resource_limits=limits))
def invoke(tx,tag,backend='run_serial_lazy_resource_transactions_stream_v1.py'):
 assert not a.assert_no_native_work, 'Read-only preflight encountered a candidate requiring native execution'
 registered=read(tx/'registration.json');registered['runtime_config']=str(a.runtime_config.resolve());registered['source_sha256'][str(a.runtime_config.resolve())]=sha(a.runtime_config);write(tx/'registration.json',registered)
 assert shutil.disk_usage(D).free>=80*1024**3;t=time.monotonic();cmd=[sys.executable,str(D/backend),'--batch',str(tx)]
 for history in a.reuse_native_batch:cmd+=['--reuse-native-batch',str(history.resolve())]
 with (b/(tag+'.log')).open('w')as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);write(b/'active_child.json',dict(pid=proc.pid,start_ticks=Path('/proc',str(proc.pid),'stat').read_text().split(') ',1)[1].split()[19],tag=tag,command=cmd));code=proc.wait()
 costs.append(dict(tag=tag,status='completed'if code==0 else'failed',complete_process_seconds=time.monotonic()-t,returncode=code));persist();return code==0
persist()
while True:
 rd=b/f'round_{len(steps):03d}';rd.mkdir();t=time.monotonic();reused_selection=False
 cuts=select(current,cache,rd/'selection')
 costs.append(dict(tag=f'{len(steps):03d}_current_resource_selection',status='reused'if reused_selection else'completed',complete_process_seconds=time.monotonic()-t));advanced=False
 for ci in range(min(3,len(cuts))):
  selected=select_cuts(cuts,a.bundle_size,ci)
  if not selected:continue
  req,domain,queries=serialize_request(selected);key=hashlib.sha256(json.dumps([sha(run_dir(current)/'routed.route'),req,domain,a.domain_mode]).encode()).hexdigest()
  if key in seen:continue
  seen.add(key);tx=rd/f'candidate_{ci:02d}';tx.mkdir();request=tx/'request.txt';request.write_text(req);domain_file=tx/'domain.txt';domain_file.write_text(domain);roles={};removed={str(cut['net']):cut['pins']for cut in selected}
  for enabled in([False,True]if a.domain_mode=='paired'else[False]):
   name='reuse_'+('on'if enabled else'off');role=dict(state=str(current),source=str(run_dir(current)),baseline='fresh_serial_current',scope=f'own_current_resource_K{a.bundle_size}',request=str(request),queries=queries,removed_pins=removed,objective='weighted_soft',fixed_target_paths=False,crossing_reuse_enabled=enabled,domain_failure_release=enabled and a.domain_feedback,seed_order=a.seed_order,crossing_domain=str(domain_file),original_budget=anchor,fixed_resource_limits=limits,source_sha256={str(f):sha(f)for f in[current/'completion.json',current/'endpoint_vector.json',run_dir(current)/'routed.route',request,domain_file]});roles[name]=role
  write(tx/'registration.json',dict(roles=roles,execution_policy='domain_first_stop_on_resource_accept',full_graph_cache=str(cache_dir),audit_cache=read(cache_dir/'completion.json')['parent_cache'],source_sha256={str(f):sha(f)for f in[rd/'selection/completion.json',b/'registration.json']},limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),current_resource_selector_after_commit=True,resource_conditions=dict(anchor=anchor,resource_limits=limits,resource_objectives=['SB_pairs','CB_sources'])));ok=invoke(tx,f'{len(steps):03d}_{ci:02d}_serial_native_transaction');progress=read(tx/'progress.json')if(tx/'progress.json').exists()else{};record=dict(round=len(steps),candidate_rank=ci,current_state=str(current),transaction=str(tx),native_transaction_complete=ok,removed_pins=removed,roles=progress);winner=None
  for name in['reuse_on','reuse_off']:
   row=progress.get(name,{})
   if row.get('status')=='legal_evaluated'and read(tx/(name+'_decisions.json'))['resources_under_timing']['accepted']:winner=Path(row['evaluation']);record['accepted_role']=name;break
  attempts.append(record)
  if not ok:
   stop='execution_or_audit_failure';persist();break
  if winner is not None:
   # The independently computed fixed-envelope decision already checks full precision, hold, native legality and actual resources.
   assert read(winner/'endpoint_vector.json')['cpd_s']<=anchor['CPD_s'];record['committed_evaluation']=str(winner);steps.append(record);current=winner;advanced=True;persist();break
  persist()
 if stop=='execution_or_audit_failure':break
 if not advanced and not a.disable_owner_escalation:
  begin=time.monotonic();owner_selection=rd/'owner_selection'
  owner_receipt=select_owners(current,cache_dir,owner_selection,minimum_margin_ns=.2)
  costs.append(dict(tag=f'{len(steps):03d}_current_owner_selection',status='completed',complete_process_seconds=time.monotonic()-begin))
  groups=read(owner_selection/'groups.json');persist()
  for oi in range(min(a.owner_rank_windows,len(groups))):
   tx=rd/f'owner_{oi:02d}'
   prepared=prepare_owner(current,initial,owner_selection,cache_dir,tx,rank=oi,domain_mode='unrestricted',seed_order=a.seed_order)
   assert prepared['transaction_registered'] and prepared['anchor']==anchor and prepared['resource_limits']==limits
   # Owner expansion is the same unrestricted mechanism in both arms. Optional
   # target-CB owner restriction belongs to a separate attribution experiment.
   ok=invoke(tx,f'{len(steps):03d}_owner_{oi:02d}',backend='run_joint_crossing_source_transactions_v2.py')
   progress=read(tx/'progress.json') if (tx/'progress.json').exists() else {}
   record=dict(round=len(steps),candidate_rank=oi,mechanism='capacity_certified_owner_coordination',current_state=str(current),transaction=str(tx),native_transaction_complete=ok,removed_pins=read(tx/'registration.json')['roles']['joint_native']['removed_pins'],roles=progress)
   row=progress.get('joint_native',{});winner=None
   if ok and row.get('status')=='legal_evaluated' and read(tx/'joint_native_decisions.json')['resources_under_timing']['accepted']:
    winner=Path(row['evaluation']);record['accepted_role']='joint_native'
   attempts.append(record)
   if not ok:stop='execution_or_audit_failure';persist();break
   if winner is not None:
    assert read(winner/'endpoint_vector.json')['cpd_s']<=anchor['CPD_s']
    record['committed_evaluation']=str(winner);steps.append(record);current=winner;advanced=True;persist();break
   persist()
 if stop=='execution_or_audit_failure':break
 if not advanced:stop='no_admissible_candidate_in_registered_current_scope_probe';break
assert stop in ['no_admissible_candidate_in_registered_current_scope_probe','execution_or_audit_failure']
assert all(sha(f)==h for f,h in bindings.items());persist();v=read(current/'endpoint_vector.json');p=read(run_dir(current)/'independent_audit.json')['physical_metrics'];write(b/'completion.json',dict(passed=stop!='execution_or_audit_failure',operator_stop=stop,initial_state=str(initial),final_state=str(current),accepted_steps=len(steps),attempted_scopes=len(attempts),final_CPD_s=v['cpd_s'],final_resources=dict(wirelength=p['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=p['sb_pairs_used'],CB_sources=p['cb_crossing_output_sources_used']),complete_imported_state_workflow_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None,source_sha256={str(f):sha(f)for f in[b/'registration.json',b/'steps.json',b/'attempts.json',b/'process_costs.json',b/'current_state.json']},owner_commits=sum(row.get('mechanism')=='capacity_certified_owner_coordination' for row in steps),qualification='Current-state serial resource and owner trajectory; owner search is unrestricted in both arms, root envelopes never reset, and each owner commit returns to current resource selection; every accepted whole candidate has native FULL/STA and independent physical/domain checks. Current sources are immutable; rejected/failed private candidates do not change occupancy/state. End of this local probe does not terminate ongoing research.'))
print(dict(accepted_steps=len(steps),CPD_ns=v['cpd_s']*1e9),flush=True)
