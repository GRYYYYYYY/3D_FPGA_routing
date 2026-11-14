#!/usr/bin/env python3
"""Independent resource-repair integration cohort with a persistent STA context.

Two accepted steps / three candidates per current state are a local integration
probe, never an overall research termination condition. Every accepted state is
rescanned; OFF and ON see the same current state, sinks and opportunity.
"""
import argparse,fcntl,hashlib,json,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from native_analysis_pool_v2 import NativeAnalysisPool
from pool_state_evaluator import PoolStateEvaluator
from current_crossing_share_selector_v2 import select
from run_native_scope_policy_v4 import run_dir
from endpoint_timing_policy import compare,decide as timing_decide
from multiobjective_acceptance_v2 import decide
p=argparse.ArgumentParser();p.add_argument('--initial-state',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);a=p.parse_args();started=time.monotonic();b=a.batch.resolve();b.mkdir(exist_ok=False);lock=(b/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));initial=a.initial_state.resolve();source=run_dir(initial)
proof=D/'current_crossing_share_selector_validation_02/completion.json';assert read(proof)['passed'];assert read(D/'pool_state_evaluator_bnn_01/completion.json')['passed'];m=read(source/'manifest.json');command=list(m['command']);command[0]=str(D/'analysis_queue_stage_01/bin/vpr')
if '--route' in command:command.remove('--route')
for opt,n in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:command[command.index(opt)+1]=str(source/n)
if '--verify_route_file_switch_id' not in command:command+=['--verify_route_file_switch_id','on']
static=[Path(command[1]),Path(command[2]),Path(command[command.index('--read_rr_graph')+1]),source/'packed.net',source/'placed.place'];guard=D.parents[1]/'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard';files=[Path(__file__).resolve(),D/'native_analysis_pool_v2.py',D/'pool_state_evaluator.py',D/'current_crossing_share_selector_v2.py',proof,D/'pool_state_evaluator_bnn_01/completion.json',D/'run_resource_domain_state_analysis.py',D/'audit_native_objective_cached.py',D/'audit_retained_crossing_domain.py',D/'multiobjective_acceptance_v2.py',D/'endpoint_timing_policy.py',D/'resource_domain_stage_01/native_validation_binding_01.json',initial/'completion.json',initial/'endpoint_vector.json',source/'manifest.json',source/'routed.route',source/'independent_audit.json'];bindings={str(p):sha(p) for p in files}
def resources(state):
 x=read(run_dir(state)/'independent_audit.json')['physical_metrics'];return dict(wirelength=x['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=x['sb_pairs_used'],CB_sources=x['cb_crossing_output_sources_used'])
rootres=resources(initial);anchor=dict(CPD_s=read(initial/'endpoint_vector.json')['cpd_s'],resource_limits=dict(rootres,wirelength=(rootres['wirelength']*1001+999)//1000));write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],initial_state=str(initial),anchor=anchor,resource_objectives=['SB_pairs','CB_sources'],selection='Uniform current-state crossing rank; fresh own STA after every accepted state; at most first three scopes examined per current-state integration probe.',local_probe=dict(accepted_steps=2,ranked_candidates_per_state=3),paired_control='Same native weighted objective/current source, sinks, retained tree and full device search; crossing-source domain OFF/ON only. Both candidates evaluated before choosing ON if admissible else OFF. This domain-first order is fixed at registration, never chosen by circuit history.',source_sha256=bindings,question='Does resource sharing remain useful after fast timing repair and stronger native reconvergence, can two independently selected resource moves compose, and does dynamic native FULLSTA integrate without changing physical/acceptance semantics?',limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),qualification='Independent new version; original cohorts unchanged. Imported-state algorithm integration, not cold complete-configuration timing or generic performance confirmation. No research date/count/matrix stop. Legal rejected candidates preserved for later joint archive.'))
pool=NativeAnalysisPool(b/'pool',command,static,guard);evaluator=PoolStateEvaluator(pool,initial,D/'full_route_graph_cache_bnn_01',b/'evaluation_context');costs=[];attempts=[];steps=[];current=None;seen_requests=set();reason=None

def invoke(script,args,tag):
 if shutil.disk_usage(D).free<80*1024**3:costs.append(dict(tag=tag,status='disk_guard',complete_process_seconds=0));return False
 t=time.monotonic();cmd=[sys.executable,str(D/script),*map(str,args)]
 with (b/(tag+'.log')).open('w') as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);write(b/'active_child.json',dict(pid=proc.pid,start_ticks=(Path('/proc')/str(proc.pid)/'stat').read_text().split(') ',1)[1].split()[19],tag=tag,command=cmd));status='completed'
  try:code=proc.wait(timeout=1800)
  except subprocess.TimeoutExpired:
   status='timeout';os.killpg(proc.pid,signal.SIGTERM)
   try:code=proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
 costs.append(dict(tag=tag,status=status if not code or status=='timeout' else 'failed',returncode=code,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs);write(b/'active_child.json',dict(pid=proc.pid,tag=tag,status='terminal',returncode=code));return code==0

def persist():
 write(b/'attempts.json',attempts);write(b/'steps.json',steps);write(b/'process_costs.json',costs);write(b/'current_state.json',dict(state=None if current is None else str(current),accepted_steps=len(steps),fixed_anchor=anchor))

try:
 first=evaluator.evaluate(source/'routed.route',b/'initial',physical_reference=initial);assert first['passed'];current=b/'initial';original=read(initial/'endpoint_vector.json');observed=read(current/'endpoint_vector.json');assert all(original[k]==observed[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']),'New observer changed initial STA';persist()
 while len(steps)<2:
  round_dir=b/f'round_{len(steps):03d}';round_dir.mkdir();t=time.monotonic();candidates=select(current,evaluator.cache,round_dir/'selection');costs.append(dict(tag=f'{len(steps):03d}_current_resource_selection',status='completed',complete_process_seconds=time.monotonic()-t));before=read(current/'endpoint_vector.json');currentres=resources(current);advanced=False
  for ci,candidate in enumerate(candidates[:3]):
   tx=round_dir/f'candidate_{ci:02d}';tx.mkdir();net=candidate['net'];pins=candidate['pins'];request=tx/'request.txt';request.write_text('1\n'+' '.join(map(str,[net,len(pins),*pins]))+'\n0\n'+str(len(pins))+'\n'+''.join(f"{q['net']} {q['pin']} {q['raw_criticality']:.17g}\n" for q in candidate['ordered_queries']));domain=tx/'domain.txt';domain.write_text('1\n'+str(net)+'\n');roles={}
   for enabled in [False,True]:
    name='reuse_'+('on' if enabled else 'off');roles[name]=dict(state=str(current),source=str(run_dir(current)),request=str(request),objective='weighted_soft',fixed_target_paths=False,queries=candidate['ordered_queries'],removed_pins={str(net):pins},crossing_reuse_enabled=enabled,crossing_domain=str(domain),source_sha256={str(p):sha(p) for p in [current/'completion.json',current/'endpoint_vector.json',run_dir(current)/'routed.route',request,domain]})
   write(tx/'registration.json',dict(roles=roles,anchor=anchor,source_sha256={str(round_dir/'selection/completion.json'):sha(round_dir/'selection/completion.json')}));pair={}
   for name,role in roles.items():
    key=hashlib.sha256(json.dumps([sha(run_dir(current)/'routed.route'),sha(request),role['crossing_reuse_enabled'],sha(D/'resource_domain_stage_01/bin/vpr')]).encode()).hexdigest()
    if key in seen_requests:pair[name]=dict(status='duplicate_current_request_skipped');continue
    seen_requests.add(key);extra=['--crossing-domain',domain] if role['crossing_reuse_enabled'] else [];ok=invoke('run_resource_domain_state_analysis.py',['--source',run_dir(current),'--batch',tx/name,'--native-cases',request,'--objective','weighted_soft',*extra],f'{len(steps):03d}_{ci:02d}_{name}_native')
    if ok:
     unchanged=read(tx/name/'endpoint_vector.json');assert all(unchanged[k]==before[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']);ok=invoke('audit_native_objective_cached.py',['--batch',tx,'--role',name,'--cache',D/'rr_audit_cache_bnn_01','--output',tx/(name+'_audit')],f'{len(steps):03d}_{ci:02d}_{name}_transaction_audit')
    if ok:ok=invoke('audit_retained_crossing_domain.py',['--batch',tx,'--role',name],f'{len(steps):03d}_{ci:02d}_{name}_domain_audit')
    if not ok:pair[name]=dict(status='failed_original_retained',accepted=False);continue
    audit=read(tx/(name+'_audit/analysis.json'))
    if not audit.get('candidate_route'):pair[name]=dict(status='infeasible_transaction_rolled_back',accepted=False);continue
    state=tx/(name+'_evaluation');t=time.monotonic();result=evaluator.evaluate(audit['candidate_route'],state);costs.append(dict(tag=f'{len(steps):03d}_{ci:02d}_{name}_pooled_FULL_STA',status='completed' if result['passed'] else 'failed',complete_process_seconds=time.monotonic()-t));persist()
    if not result['passed']:pair[name]=dict(status='FULL_STA_failed_original_retained',accepted=False,evaluation=str(state));continue
    after=read(state/'endpoint_vector.json');newres=resources(state);decision=decide('resources_under_timing',before,after,currentres,newres,cpd_limit_s=anchor['CPD_s'],resource_limits=anchor['resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'));alternatives={mode:timing_decide(mode,before,after,True) for mode in ['strict','endpoint_vector']};pair[name]=dict(status='legal_evaluated',accepted=decision['accepted'],evaluation=str(state),CPD_s=after['cpd_s'],resources=newres,decision=decision,strict_or_endpoint_control=alternatives,native_core_seconds=audit['native_transaction_seconds'],native_observer_request_seconds=result['timing']['complete_evaluation_request_seconds']);write(tx/(name+'_decisions.json'),pair[name])
   record=dict(round=len(steps),candidate_rank=ci,current_state=str(current),net=net,pins=pins,pair=pair);attempts.append(record);winner=next((pair[n] for n in ['reuse_on','reuse_off'] if pair.get(n,{}).get('accepted')),None)
   if winner is not None:
    record['committed_evaluation']=winner['evaluation'];steps.append(record);current=Path(winner['evaluation']);advanced=True;persist();break
   persist()
  if not advanced:reason='no_admissible_move_in_current_three_scope_integration_probe';break
 if reason is None:reason='two_accepted_resource_steps_integration_probe_terminal'
finally:
 persist();evaluator.close()
assert all(sha(p)==h for p,h in bindings.items());persist();write(b/'completion.json',dict(passed=True,operator_stop=reason,initial_state=str(initial),final_state=str(current),accepted_steps=len(steps),attempted_scopes=len(attempts),initial_CPD_s=anchor['CPD_s'],final_CPD_s=read(current/'endpoint_vector.json')['cpd_s'],final_resources=resources(current),complete_imported_algorithm_workflow_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None,native_analysis_children=len(pool.jobs),native_analysis_cache_hits=len(pool.reuse),source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'attempts.json',b/'steps.json',b/'current_state.json',b/'process_costs.json',b/'pool/completion.json',b/'evaluation_context/input_seal.json',b/'evaluation_context/completion.json']},qualification='Independent automatic selector→native paired transaction→real replacement→complete physical/FULLSTA→fixed-budget accept/rollback flow. Final states require successful context seal. Integration probe is neither full cold timing nor an overall research stop; unresolved or rejected legal tradeoffs remain preserved. Initial states were imported, not manually injected into frozen confirmation runs.'))
print(dict(accepted_steps=len(steps),final_CPD_ns=read(current/'endpoint_vector.json')['cpd_s']*1e9,resources=resources(current)),flush=True)
