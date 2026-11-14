#!/usr/bin/env python3
"""Execute a sealed development batch with paired scopes and exact accept/rollback."""
import argparse,fcntl,math,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from fixed_anchor_acceptance import decisions as fixed_decisions
from multiobjective_acceptance_v2 import decide as budget_decide
from run_native_scope_policy_v4 import input_identity,native_config,run_dir

p=argparse.ArgumentParser();p.add_argument('--batch',type=Path,required=True);p.add_argument('--selector',choices=['full','compact'],default='compact');a=p.parse_args()
b=a.batch.resolve();started=time.monotonic();reg=read(b/'registration.json')
selector='current_sta_arrival_cone_compact.py' if a.selector=='compact' else 'current_sta_arrival_cone.py'
selector_files=[D/selector,D/'current_sta_arrival_cone.py',D/'fixed_anchor_acceptance.py',D/'multiobjective_acceptance_v2.py',D/'endpoint_timing_policy.py',D/'run_native_reservation_analysis_v2.py',D/'audit_pending_reservations.py',D/'native_reservation_stage_03/binding.json']
if a.selector=='compact':
 proof=D/'compact_cone_benchmark_01/completion.json';assert read(proof)['passed']
 selector_files += [D/'compact_timing_cone.py',D/'compact_timing_cone_validation_01/completion.json',proof]
 assert all(sha(path)==h for path,h in read(proof)['source_sha256'].items())
assert not (b/'execution_registration.json').exists(),'Existing owner or attempt: inspect receipts; do not restart blindly'
lock=(b/'controller.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert all(sha(path)==h for path,h in reg['source_sha256'].items())
resource.setrlimit(resource.RLIMIT_AS,(reg['limits']['memory_bytes'],reg['limits']['memory_bytes']))
write(b/'execution_registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
 registration_sha256=sha(b/'registration.json'),source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),*selector_files]},selector=a.selector,status='started',time=time.time()))
costs=[];results={};references=list(dict.fromkeys(Path(r['state']) for r in reg['roles'].values()))
references += list(dict.fromkeys(Path(r['reference_evaluation']) for r in reg['roles'].values()))
def invoke(script,args,tag):
 if shutil.disk_usage(D).free<reg['limits']['disk_reserve_bytes']:
  costs.append(dict(tag=tag,status='disk_guard',complete_process_seconds=0));write(b/'process_costs.json',costs);return False
 command=[sys.executable,str(D/script),*map(str,args)];t=time.monotonic();status='completed'
 with (b/(tag+'.log')).open('w') as log:
  proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  write(b/'active_child.json',dict(pid=proc.pid,tag=tag,command=command,phase='running'))
  try:code=proc.wait(timeout=reg['limits']['child_seconds'])
  except subprocess.TimeoutExpired:
   status='timeout';os.killpg(proc.pid,signal.SIGTERM)
   try:code=proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
 if code and status=='completed':status='failed'
 costs.append(dict(tag=tag,command=command,returncode=code,status=status,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs)
 write(b/'active_child.json',dict(pid=proc.pid,tag=tag,phase='terminal',status=status,returncode=code));return code==0

for name,role in reg['roles'].items():
 state=Path(role['state']);source=Path(role['source']);before=read(state/'endpoint_vector.json')
 results[name]=dict(status='running',scope=role['scope'],baseline=role['baseline']);write(b/'progress.json',results)
 assert all(sha(path)==h for path,h in role['source_sha256'].items())
 args=['--source',source,'--batch',b/name,'--native-cases',role['request'],'--objective',role['objective']]
 if role['reservations_enabled']:args+=['--reserve-targets',role['reserve_targets_file']]
 ok=invoke('run_native_reservation_analysis_v2.py',args,name+'_native')
 if ok:
  native_vector=read(b/name/'endpoint_vector.json')
  assert all(native_vector[k]==before[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']),'Diagnostic changed original state'
  ok=invoke('audit_native_objective_cached.py',['--batch',b,'--role',name,'--cache',D/'rr_audit_cache_bnn_01','--output',b/(name+'_audit')],name+'_audit')
 if ok:ok=invoke('audit_pending_reservations.py',['--batch',b,'--role',name],name+'_reservation_trace')
 if not ok:
  results[name].update(status='native_or_candidate_audit_failed',accepted=False);write(b/'progress.json',results);continue
 audit=read(b/(name+'_audit/analysis.json'))
 if not audit.get('candidate_route'):
  results[name].update(status='transaction_failed_rolled_back',accepted=False,audit=str(b/(name+'_audit/analysis.json')));write(b/'progress.json',results);continue
 candidate=Path(audit['candidate_route']);evaluation=None
 if not role['reservations_enabled']:
  reference=read(Path(role['reference_batch'])/(role['reference_role']+'_audit/analysis.json'))
  assert route_body(candidate)==route_body(reference['candidate_route']),'Default-off candidate differs; investigate new build before mechanism claims'

 for prior in references:
  run=run_dir(prior)
  if route_body(candidate)==route_body(run/'routed.route') and input_identity(source)==input_identity(run) and native_config(source)==native_config(run):
   assert read(prior/'completion.json')['passed'] and before['constraints_sha256']==read(prior/'endpoint_vector.json')['constraints_sha256'];evaluation=prior;break
 reused=evaluation is not None
 if not reused:
  evaluation=b/(name+'_evaluation')
  ok=invoke('run_timing_cone_state_analysis_v2.py',['--source',source,'--batch',evaluation,'--candidate-route',candidate,'--full-graph-cache',D/'full_route_graph_cache_bnn_01','--timing-echo'],name+'_FULL_STA')
  if not ok:
   results[name].update(status='FULL_STA_failed',accepted=False);write(b/'progress.json',results);continue
  references.append(evaluation)
 after=read(evaluation/'endpoint_vector.json');physical=read(run_dir(evaluation)/'independent_audit.json')['physical_metrics']
 newres=dict(wirelength=physical['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=physical['sb_pairs_used'],CB_sources=physical['cb_crossing_output_sources_used'])
 oldres={k:role['original_budget'][k] for k in newres}
 physical_before=read(source/'independent_audit.json')['physical_metrics']
 currentres=dict(wirelength=physical_before['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=physical_before['sb_pairs_used'],CB_sources=physical_before['cb_crossing_output_sources_used'])
 decisions=fixed_decisions(before,after,currentres,newres,role['original_budget'])
 write(b/(name+'_decisions.json'),decisions)
 results[name].update(status='legal_evaluated',evaluation=str(evaluation),reused_FULL_STA=reused,cpd_s=after['cpd_s'],resources=newres,
  native_core_seconds=audit['native_transaction_seconds'],changed_connections=audit['changed_delays'],policies={n:dict(accepted=d['accepted'],reason=d['reason']) for n,d in decisions.items()})
 for n,decision in decisions.items():
  selected=evaluation if decision['accepted'] else state
  write(b/(name+'_'+n+'_state.json'),dict(state=str(selected),accepted=decision['accepted'],source_state=str(state),decision=str(b/(name+'_decisions.json'))))
 # Accepted states receive a fresh selector; rejected branches retain their own
 # original state. No other policy's successor is imported into a strict branch.
 if any(d['accepted'] for d in decisions.values()):
  ok=invoke(selector,['--state',evaluation,'--output',b/(name+'_successor_cone.json')],name+'_successor_selection')
  results[name]['successor_selection_passed']=ok
 write(b/'progress.json',results);print(name,results[name],flush=True)
assert all(sha(path)==h for path,h in reg['source_sha256'].items())
assert all(sha(path)==h for path,h in read(b/'execution_registration.json')['source_sha256'].items())
if a.selector=='compact':assert all(sha(path)==h for path,h in read(D/'compact_cone_benchmark_01/completion.json')['source_sha256'].items())
paths=[b/'registration.json',b/'execution_registration.json',b/'process_costs.json',b/'progress.json',*b.glob('*_decisions.json'),*b.glob('*_state.json')]
write(b/'completion.json',dict(status='development_batch_terminal',passed=all(r['status'] in ['legal_evaluated','transaction_failed_rolled_back'] for r in results.values()),roles=results,
 complete_orchestrator_seconds=time.monotonic()-started,complete_child_process_seconds=sum(c['complete_process_seconds'] for c in costs),source_sha256={str(p):sha(p) for p in paths},
 qualification='Complete shared multi-arm development workflow cost, not a standalone configuration runtime. Individual failures do not stop other arms or the research goal. Further searches must use each accepted current state and updated occupancy/STA.'))
