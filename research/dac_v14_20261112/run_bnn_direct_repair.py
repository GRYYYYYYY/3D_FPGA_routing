#!/usr/bin/env python3
"""Matched native direct repair from audited current-STA capacity evidence."""
import copy,math,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from endpoint_timing_policy import decide as timing_decide
from multiobjective_acceptance_v2 import decide as budget_decide
from run_native_scope_policy_v4 import input_identity,native_config,run_dir

started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
spec=read(D/'bnn_direct_repair_experiment_01/registration.json');assert all(sha(p)==h for p,h in spec['source_sha256'].items())
q=D/'bnn_slack_release_screen_01/Tf_capacity';evidence=read(q/'analysis.json');assert evidence['passed'] and all(sha(p)==h for p,h in evidence['source_sha256'].items())
eligible=[r for r in evidence['results'] if r['rr_capacity_feasible'] and r['improvement_ns']>1e-6]
assert eligible;target=min(eligible,key=lambda r:(-r['improvement_ns'],r['net'],r['pin']))
state=Path(spec['input_state']);source=run_dir(state);b=D/'bnn_direct_repair_dev_01';b.mkdir(exist_ok=False)
costs=[];results={};references=[state];before=read(state/'endpoint_vector.json')
def invoke(script,args,tag):
 assert shutil.disk_usage(D).free>=80*1024**3
 command=[sys.executable,str(D/script),*map(str,args)];t=time.monotonic();status='completed'
 with (b/(tag+'.log')).open('w') as log:
  proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=proc.wait(timeout=1800)
  except subprocess.TimeoutExpired:
   status='timeout';os.killpg(proc.pid,signal.SIGTERM)
   try:code=proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
 if code and status=='completed':status='failed'
 costs.append(dict(tag=tag,command=command,returncode=code,status=status,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs);return code==0
assert invoke('prepare_native_scope_request.py',['--state',state,'--batch',b/'request','--single',target['net'],target['pin'],'--scope','target_only','--objective','weighted_soft'],'prepare_request')
template=read(b/'request/registration.json')['roles']['candidate'];roles={}
for mode in ['weighted_soft','physical_capacity']:
 roles[mode]=copy.deepcopy(template);roles[mode]['objective']=mode
files=[Path(__file__).resolve(),D/'bnn_direct_repair_experiment_01/registration.json',q/'analysis.json',b/'request/registration.json',D/'run_native_objective_state_analysis.py',D/'audit_native_objective_cached.py',D/'run_timing_cone_state_analysis_v2.py',D/'multiobjective_acceptance_v2.py',D/'endpoint_timing_policy.py',D/'current_sta_arrival_cone.py',state/'completion.json',state/'endpoint_vector.json']
bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(status='registered_before_native',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
 roles=roles,target=[target['net'],target['pin']],source_sha256=bindings,
 fixed_budget_modes=dict(timing_under_resources='CPD<=initial,wire<=ceil1.05initial,SB<=initial+1,CB<=initial+4; strict CPD improvement',resources_under_timing='CPD<=1.01initial,wire<=initial,SB<=initial+1,CB<=initial+4; strict wire reduction'),
 question=spec['question'],qualification='Identical initial state/request/scope; each native objective runs once. No candidate path injected. Original strict/endpoint policies preserved as controls. Independent fixed budgets selected uniformly from previously registered grid before native output. Joint diagnostic cost is not single-policy runtime.'))
res=spec['original_budget'];oldres={k:res[k] for k in ['wirelength','SB_pairs','CB_sources']}
for mode,role in roles.items():
 ok=invoke('run_native_objective_state_analysis.py',['--source',source,'--batch',b/mode,'--native-cases',role['request'],'--objective',mode],mode+'_native')
 if ok:
  native_vector=read(b/mode/'endpoint_vector.json')
  assert all(native_vector[k]==before[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']),'Original timing state changed during diagnostic native transaction'
  ok=invoke('audit_native_objective_cached.py',['--batch',b,'--role',mode,'--cache',D/'rr_audit_cache_bnn_01','--output',b/(mode+'_audit')],mode+'_audit')
 if not ok:
  results[mode]=dict(status='native_or_candidate_audit_failed',accepted=False);write(b/'progress.json',results);continue
 audit=read(b/(mode+'_audit/analysis.json'))
 if not audit.get('candidate_route'):
  results[mode]=dict(status='transaction_failed_rolled_back',accepted=False);write(b/'progress.json',results);continue
 candidate=Path(audit['candidate_route']);evaluation=None
 for prior in references:
  run=run_dir(prior)
  if route_body(candidate)==route_body(run/'routed.route') and input_identity(source)==input_identity(run) and native_config(source)==native_config(run):
   assert read(prior/'completion.json')['passed'] and before['constraints_sha256']==read(prior/'endpoint_vector.json')['constraints_sha256'];evaluation=prior;break
 reused=evaluation is not None
 if not reused:
  cache=D/'full_route_graph_cache_bnn_01/completion.json'
  if not cache.exists():
   results[mode]=dict(status='legal_candidate_pending_FULL_STA',candidate=str(candidate),reason='Required independent full-graph metadata cache not yet terminal; preserve completed native work for continuation')
   write(b/'progress.json',results);continue
  assert read(cache)['passed']
  evaluation=b/(mode+'_evaluation')
  ok=invoke('run_timing_cone_state_analysis_v2.py',['--source',source,'--batch',evaluation,'--candidate-route',candidate,'--full-graph-cache',cache.parent,'--timing-echo'],mode+'_FULL_STA')
  if not ok:
   results[mode]=dict(status='FULL_STA_failed',accepted=False);write(b/'progress.json',results);continue
  references.append(evaluation)
 after=read(evaluation/'endpoint_vector.json');physical=read(run_dir(evaluation)/'independent_audit.json')['physical_metrics']
 newres=dict(wirelength=physical['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=physical['sb_pairs_used'],CB_sources=physical['cb_crossing_output_sources_used'])
 decisions={name:timing_decide(name,before,after,True) for name in ['strict','endpoint_vector']}
 for name in ['timing_under_resources','resources_under_timing']:
  caps=dict(wirelength=math.ceil(oldres['wirelength']*(1.05 if name=='timing_under_resources' else 1)),SB_pairs=oldres['SB_pairs']+1,CB_sources=oldres['CB_sources']+4)
  decisions[name]=budget_decide(name,before,after,oldres,newres,cpd_limit_s=before['cpd_s']*(1. if name=='timing_under_resources' else 1.01),resource_limits=caps,native_valid=True,transaction_complete=True,resource_objectives=('wirelength',))
 write(b/(mode+'_decisions.json'),decisions)
 results[mode]=dict(status='legal_evaluated',evaluation=str(evaluation),reused_FULL_STA=reused,cpd_s=after['cpd_s'],resources=newres,
  native_core_seconds=audit['native_transaction_seconds'],changed_connections=audit['changed_delays'],policies={n:dict(accepted=d['accepted'],reason=d['reason']) for n,d in decisions.items()})
 # Each independent policy's state pointer is committed only after complete
 # physical/FULL/STA validation. Original source and other policies are immutable.
 for name,decision in decisions.items():
  selected=evaluation if decision['accepted'] else state
  write(b/(mode+'_'+name+'_state.json'),dict(state=str(selected),accepted=decision['accepted'],source_state=str(state),decision=str(b/(mode+'_decisions.json'))))
 if any(d['accepted'] for d in decisions.values()) and (run_dir(evaluation)/'timing_graph.full_precision.echo').exists():
  invoke('current_sta_arrival_cone.py',['--state',evaluation,'--output',b/(mode+'_successor_cone.json')],mode+'_successor_selection')
 write(b/'progress.json',results);print(mode,results[mode],flush=True)
assert all(sha(p)==h for p,h in bindings.items())
paths=[b/'registration.json',b/'process_costs.json',b/'progress.json',*b.glob('*_decisions.json'),*b.glob('*_state.json')]
write(b/'completion.json',dict(status='matched_direct_diagnostic_terminal',passed=all(r['status'] in ['legal_evaluated','transaction_failed_rolled_back'] for r in results.values()),roles=results,
 complete_orchestrator_seconds=time.monotonic()-started,complete_child_process_seconds=sum(c['complete_process_seconds'] for c in costs),source_sha256={str(p):sha(p) for p in paths},
 qualification='Complete cost of this shared two-arm diagnostic, not an automatic full single-configuration algorithm time. Failed/pending candidates remain explicit; no global research stop. Subsequent targets come from each accepted current state.'))
