#!/usr/bin/env python3
"""First-admissible current-state proposal portfolio with fixed-root budgets.

A rejected primary candidate does not end the menu. Exact historical transactions
may be reused, while every decision uses this policy's own current state. No
accepted update retains a stale initial target list or a rolling tolerance.
"""
import argparse,fcntl,hashlib,json,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from fixed_anchor_acceptance import decisions
from multiobjective_acceptance_v2 import decide as budget_decide
from explicit_envelope_timing_policy import decide as envelope_decide
from current_group_feedback_cached import commands
from current_native_reuse_resource import match,failed_match
p=argparse.ArgumentParser()
for n in ['initial-state','batch','query-graph','audit-cache']:p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--policy',choices=['strict','endpoint_vector','timing_under_resources','resources_under_timing','endpoint_under_resources'],required=True)
p.add_argument('--budget-mode',choices=['legacy','zero_headroom','vertical_fixed_wire_0p1','explicit_absolute'],default='legacy');p.add_argument('--fixed-limits',type=Path)
p.add_argument('--native-mode',choices=['execute','reuse_only'],default='execute');p.add_argument('--resume-from',type=Path);p.add_argument('--fraction',type=float,default=.9)
for n in ['reuse-plan','reuse-portfolio','reuse-native-batch','reuse-query-batch','reuse-exchange']:p.add_argument('--'+n,type=Path,action='append',default=[])
a=p.parse_args();started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));initial=a.initial_state.resolve();current=initial;b=a.batch.resolve();b.mkdir(exist_ok=False);lock=(b/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert read(initial/'completion.json')['passed'];proof=D/'current_portfolio_validation_01/completion.json';assert read(proof)['passed']
assert all(sha(path)==digest for path,digest in read(proof)['source_sha256'].items())
def resources(state):
 x=read(run_dir(state)/'independent_audit.json');assert x['audit']['passed'];v=x['physical_metrics'];return dict(wirelength=v['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=v['sb_pairs_used'],CB_sources=v['cb_crossing_output_sources_used'])
def state_key(state):return (route_body(run_dir(state)/'routed.route'),read(state/'endpoint_vector.json')['constraints_sha256'])
fixed_limits=None
if a.budget_mode=='explicit_absolute':
 assert a.fixed_limits is not None,'Explicit absolute envelope is required'
 fixed_limits=read(a.fixed_limits.resolve());assert set(fixed_limits)=={'wirelength','SB_pairs','CB_sources'}
 assert all(isinstance(x,int)and not isinstance(x,bool)and x>=0 for x in fixed_limits.values())
 assert all(resources(initial)[k]<=fixed_limits[k]for k in fixed_limits),'Initial state outside declared absolute envelope'
else:assert a.fixed_limits is None
if a.policy=='endpoint_under_resources':assert a.budget_mode=='explicit_absolute', 'Vector envelope policy requires explicit original absolute limits'
anchor=dict(CPD_s=read(initial/'endpoint_vector.json')['cpd_s'],**resources(initial));attempts=[];accepted=[];costs=[];replays=[];round_number=0;visited={state_key(initial)};prior_child_seconds=0.
plans=[p.resolve() for p in a.reuse_plan];portfolios=[p.resolve() for p in a.reuse_portfolio];native_history=[p.resolve() for p in a.reuse_native_batch];query_history=[p.resolve() for p in a.reuse_query_batch]
files=[D/'current_rejection_feedback_v1.py',D/'make_current_exchange_portfolio_v2.py',D/'query_critical_owner_exchange.py',D/'expand_critical_owner_scope.py',D/'run_current_graph_relaxed_queries_v2.py',D/'conditional_distance_certificate.py',D/'current_exchange_portfolio_validation_02.json',Path(__file__).resolve(),D/'current_proposal_portfolio.py',D/'make_current_proposal_portfolio.py',D/'current_group_feedback_cached.py',D/'current_native_reuse_resource.py',D/'fixed_anchor_acceptance.py',D/'prepare_native_group_step_v2.py',D/'run_registered_independent_transactions.py',proof,initial/'completion.json',initial/'endpoint_vector.json',*plans,*portfolios]
if a.resume_from:
 prior=a.resume_from.resolve();old=read(prior/'registration.json');assert Path(old['initial_state'])==initial and old['policy']==a.policy and old['fraction']==a.fraction and old['objective']=='weighted_soft'
 assert old.get('budget_mode','legacy')==a.budget_mode,'Budget changes require a new independent initial-state batch'
 if a.budget_mode=='explicit_absolute':assert old.get('fixed_absolute_limits')==fixed_limits,'Resume cannot alter absolute budgets'
 assert all(sha(p)==h for p,h in old['source_sha256'].items())
 saved=read(prior/'resume_state.json');current=Path(saved['current_state']).resolve();assert read(current/'completion.json')['passed'];assert saved['anchor']==anchor
 attempts=read(prior/'attempts.json');accepted=read(prior/'steps.json');visited=set(map(tuple,saved['visited_states']));round_number=saved['round_number'];prior_child_seconds=sum(x['complete_process_seconds'] for x in read(prior/'process_costs.json'))
 if saved.get('portfolio'):portfolios.append(Path(saved['portfolio']).resolve())
 plans += list(prior.glob('round_*/feedback/proposal/plan.json'));query_history+=list(prior.glob('round_*/feedback/capacity'));native_history+=list(prior.glob('round_*/proposal_*/transaction'))
 replays.append(dict(kind='resume_completed_work',source=str(prior),accepted_steps=len(accepted),prior_child_seconds=prior_child_seconds));files += [prior/'registration.json',prior/'resume_state.json',prior/'attempts.json',prior/'steps.json']
exchange_history=[p.resolve() for p in a.reuse_exchange]
if a.resume_from:exchange_history+=list(prior.glob('round_*/exchange_expansion/completion.json'))
assert read(D/'current_exchange_portfolio_validation_02.json')['passed']
files += [D/'native_problem_identity.py']
assert read(D/'explicit_envelope_timing_policy_validation_01.json')['passed']
files += [D/'explicit_envelope_timing_policy.py',D/'endpoint_timing_policy_streaming_v2.py',D/'explicit_envelope_timing_policy_validation_01.json']
files += [a.fixed_limits.resolve()] if a.fixed_limits else []
bindings={str(p):sha(p) for p in files};write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],initial_state=str(initial),policy=a.policy,budget_mode=a.budget_mode,fixed_absolute_limits=fixed_limits,fraction=a.fraction,objective='weighted_soft',native_mode=a.native_mode,anchor=anchor,source_sha256=bindings,explicit_endpoint_policy='All fixed endpoint/launch/capture setup components nonworse, at least one improves; CPD nonworse at full precision; no increased hold violation; immutable absolute resource and original CPD caps. No tolerance.',limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
 question='Does a fixed current-state portfolio admit useful vector/resource moves rejected by the primary winning-path group, and do fresh targets after those moves eventually improve final timing/resource quality?',
 qualification='Independent resource-stage native binary and per-job lock names, same complete native/physical/STA gates. All scripts use private outputs; one independent VPR at a time coexists with the original at-most-two-VPR owner. Fixed original vertical budgets with optional registered wire 0.1 percent; no rolling tolerances. Same fixed proposal order for all circuits/policies; no history-best selection. Imported-state development workflow, not complete cold router runtime. Action-derived alternatives are followed lazily by current critical-owner dependency closure, then by same-source rejection feedback excluding delay-increasing donors while covering tied paths. Neither tier covers every near-critical/resource opportunity.'))
completed={x['attempt_key'] for x in attempts};reason=None;pending=None;portfolio_path=None;native_coordinators=0

def invoke(script,args,tag):
 if shutil.disk_usage(D).free<80*1024**3:
  costs.append(dict(tag=tag,status='disk_guard',complete_process_seconds=0));write(b/'process_costs.json',costs);return False
 command=[sys.executable,str(D/script),*map(str,args)];start=time.monotonic();status='completed'
 with (b/(tag+'.log')).open('w') as log:
  proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);write(b/'active_child.json',dict(pid=proc.pid,tag=tag,command=command))
  try:code=proc.wait(timeout=None if script=='run_registered_independent_transactions.py' else 1800)
  except subprocess.TimeoutExpired:
   status='timeout';os.killpg(proc.pid,signal.SIGTERM)
   try:code=proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
 costs.append(dict(tag=tag,status=status if not code or status=='timeout' else 'failed',returncode=code,command=command,complete_process_seconds=time.monotonic()-start));write(b/'process_costs.json',costs);return code==0

def persist():
 write(b/'attempts.json',attempts);write(b/'steps.json',accepted);write(b/'reuse_receipts.json',replays);write(b/'process_costs.json',costs)
 write(b/'resume_state.json',dict(current_state=str(current),anchor_state=str(initial),anchor=anchor,round_number=round_number,portfolio=None if portfolio_path is None else str(portfolio_path),visited_states=sorted(visited),pending=pending))
 write(b/'current_state.json',dict(state=str(current),anchor_state=str(initial),policy=a.policy,accepted_steps=len(accepted)))

def reuse_current_cone(args):
 """Reuse a completed identical-state compact selector, with explicit lineage."""
 for batch in native_history:
  if not (batch/'progress.json').exists():continue
  for name,row in read(batch/'progress.json').items():
   if row.get('status')!='legal_evaluated' or Path(row['evaluation']).resolve()!=current:continue
   cone=batch/(name+'_successor_cone.json')
   if not cone.exists():continue
   value=read(cone)
   if not value['passed'] or Path(value['source_state']).resolve()!=current or value['near_ns']!=0:continue
   if value['source_sha256'].get(str(D/'current_sta_arrival_cone_compact.py'))!=sha(D/'current_sta_arrival_cone_compact.py'):continue
   assert all(sha(path)==digest for path,digest in value['source_sha256'].items())
   destination=Path(args[args.index('--output')+1]);shutil.copy2(cone,destination)
   replays.append(dict(kind='same_current_state_compact_cone',source=str(cone),sha256=sha(cone),creation_time_excluded=True));return True
 return False


def exchange_items(directory,menu):
 """Lazily add free native exchange proposals only after the first tier fails."""
 expansion=None;feedback=None
 for path in exchange_history:
  path=path/'completion.json' if path.is_dir() else path
  candidate=read(path)
  candidate_state=candidate.get('input_state')
  if candidate_state is None and (path.parent/'registration.json').exists():
   registration=read(path.parent/'registration.json')
   if registration.get('source_sha256')==candidate.get('source_sha256'):candidate_state=registration.get('input_state')
  if candidate_state is None or Path(candidate_state).resolve()!=current:continue
  assert candidate['passed'] and all(sha(p)==h for p,h in candidate['source_sha256'].items())
  if not candidate['rows']:
   replays.append(dict(kind='same_current_empty_exchange_query',path=str(path),sha256=sha(path)));return [],None
  if 'expanded_removed_pins' not in candidate['rows'][0]:continue
  expansion=path;feedback=next(Path(p).parent.parent for p in candidate['source_sha256'] if p.endswith('/owners/completion.json'))
  replays.append(dict(kind='same_current_exchange_expansion',path=str(path),sha256=sha(path)));break
 if expansion is None:
  base=Path(menu['base_plan']);feedback=base.parent.parent
  if not (feedback/'owners/completion.json').exists() or not (feedback/'cone.json').exists():
   feedback=directory/'exchange_feedback';feedback.mkdir()
   for script,args,tag in commands(current,feedback,a.query_graph.resolve(),a.audit_cache.resolve(),query_history,a.fraction):
    if tag=='current_STA_selection' and reuse_current_cone(args):continue
    if not invoke(script,args,f'{round_number:03d}_exchange_{tag}'):raise RuntimeError('exchange_feedback_failed')
   query_history.append(feedback/'capacity')
  diagnostic=directory/'exchange_query'
  if not invoke('query_critical_owner_exchange.py',['--feedback',feedback,'--output',diagnostic,'--audit-cache',a.audit_cache.resolve(),'--query-graph',a.query_graph.resolve()],f'{round_number:03d}_exchange_query'):raise RuntimeError('exchange_diagnostic_failed')
  if not read(diagnostic/'completion.json')['rows']:return [],None
  expanded=directory/'exchange_expansion'
  if not invoke('expand_critical_owner_scope.py',['--diagnostic',diagnostic,'--feedback',feedback,'--output',expanded,'--audit-cache',a.audit_cache.resolve()],f'{round_number:03d}_exchange_expand'):raise RuntimeError('exchange_expansion_failed')
  expansion=expanded/'completion.json';exchange_history.append(expansion)
 out=directory/'exchange_portfolio'
 if not invoke('make_current_exchange_portfolio_v2.py',['--expansion',expansion,'--feedback',feedback,'--output',out],f'{round_number:03d}_exchange_menu'):raise RuntimeError('exchange_menu_failed')
 generated=read(out/'portfolio.json');assert Path(generated['source_state']).resolve()==current
 return generated['proposals'],out/'portfolio.json'

while True:
 rd=b/f'round_{round_number:03d}';rd.mkdir();before=read(current/'endpoint_vector.json');portfolio_path=None;base_plan=None
 for candidate in portfolios:
  v=read(candidate)
  if Path(v['source_state']).resolve()!=current:continue
  if read(v['base_plan'])['selection'].get('fraction',a.fraction)!=a.fraction:continue
  if v.get('rejection_feedback_checked') and v.get('rejection_feedback_generator_sha256')!=sha(D/'current_rejection_feedback_v1.py'):
   plans.append(Path(v['base_plan']).resolve());continue
  if v.get('exchange_checked') and v.get('exchange_generator_sha256')!=sha(D/'make_current_exchange_portfolio_v2.py'):
   plans.append(Path(v['base_plan']).resolve());continue
  assert v['passed'] and all(sha(p)==h for p,h in v['source_sha256'].items());portfolio_path=candidate;replays.append(dict(kind='same_current_state_portfolio',path=str(candidate),sha256=sha(candidate)));break
 if portfolio_path is None:
  for candidate in plans:
   v=read(candidate)
   if Path(v['source_state']).resolve()!=current or v['selection'].get('fraction',a.fraction)!=a.fraction:continue
   assert v['passed'] and all(sha(p)==h for p,h in v['source_sha256'].items());base_plan=candidate;replays.append(dict(kind='same_current_state_plan',path=str(candidate),sha256=sha(candidate)));break
  if base_plan is None:
   feedback=rd/'feedback';feedback.mkdir();ok=True
   for script,args,tag in commands(current,feedback,a.query_graph.resolve(),a.audit_cache.resolve(),query_history,a.fraction):
    if tag=='current_STA_selection' and reuse_current_cone(args):continue
    if not invoke(script,args,f'{round_number:03d}_{tag}'):ok=False;break
   if not ok:reason='feedback_failed_or_process_guard';persist();break
   base_plan=feedback/'proposal/plan.json';plans.append(base_plan);query_history.append(feedback/'capacity')
  if not invoke('make_current_proposal_portfolio.py',['--plan',base_plan,'--output',rd/'portfolio'],f'{round_number:03d}_portfolio_generation'):
   reason='portfolio_generation_failed';persist();break
  portfolio_path=rd/'portfolio/portfolio.json';portfolios.append(portfolio_path)
 menu=read(portfolio_path);assert menu['passed'] and Path(menu['source_state']).resolve()==current
 advanced=False
 proposal_list=list(menu['proposals']);exchange_checked=menu.get('exchange_checked',False);feedback_checked=menu.get('rejection_feedback_checked',False);index=0
 while True:
  if index>=len(proposal_list):
   if exchange_checked:
    if feedback_checked:break
    feedback_checked=True;persist();out=rd/'rejection_feedback'
    if not invoke('current_rejection_feedback_v1.py',['--base-plan',menu['base_plan'],'--attempts',b/'attempts.json','--portfolio',portfolio_path,'--output',out],f'{round_number:03d}_rejection_feedback'):
     reason='rejection_feedback_generation_failed';break
    generated=read(out/'portfolio.json');assert Path(generated['source_state']).resolve()==current
    if not generated['proposals']:break
    combined=dict(menu,proposals=proposal_list+generated['proposals'],rejection_feedback_checked=True,rejection_feedback_generator_sha256=sha(D/'current_rejection_feedback_v1.py'),source_sha256={str(portfolio_path):sha(portfolio_path),str(out/'portfolio.json'):sha(out/'portfolio.json')})
    portfolio_path=rd/'portfolio_with_rejection_feedback.json';write(portfolio_path,combined);menu=combined;proposal_list=combined['proposals'];portfolios.append(portfolio_path)
    continue
   exchange_checked=True
   try:extra,exchange_menu=exchange_items(rd,menu)
   except RuntimeError as error:reason=str(error);break
   if not extra:continue
   combined=dict(menu,proposals=proposal_list+extra,exchange_checked=True,exchange_generator_sha256=sha(D/'make_current_exchange_portfolio_v2.py'),source_sha256={str(portfolio_path):sha(portfolio_path),str(exchange_menu):sha(exchange_menu)})
   portfolio_path=rd/'portfolio_with_exchange.json';write(portfolio_path,combined);menu=combined;proposal_list=combined['proposals'];portfolios.append(portfolio_path)
  item=proposal_list[index];index+=1
  plan=Path(item['plan']).resolve();attempt_key=hashlib.sha256(json.dumps([state_key(current),item['request_sha256'],a.policy,anchor,'weighted_soft']+([] if a.budget_mode=='legacy' else [a.budget_mode,fixed_limits]),sort_keys=True).encode()).hexdigest()
  if attempt_key in completed:replays.append(dict(kind='already_evaluated_current_proposal',proposal=item['name'],attempt_key=attempt_key));continue
  directory=rd/f'proposal_{index:02d}';directory.mkdir();transaction=directory/'transaction'
  if not invoke('prepare_native_group_step_v2.py',['--plan',plan,'--anchor-state',initial,'--output',transaction,'--objective','weighted_soft'],f'{round_number:03d}_{index:02d}_prepare'):
   reason='transaction_preparation_failed';break
  role=read(transaction/'registration.json')['roles']['current_group'];assert sha(role['request'])==item['request_sha256'];hit=match(role,native_history);evaluation=None;failed=None
  if hit:
   evaluation=Path(hit['evaluation']).resolve();write(directory/'native_reuse.json',hit);replays.append(dict(kind='exact_native_transaction_and_FULLSTA',**hit))
  else:
   failed=failed_match(role,native_history)
   if failed:write(directory/'native_failure_reuse.json',failed);replays.append(dict(kind='exact_completed_native_failure',**failed))
   elif a.native_mode=='reuse_only':
    pending=dict(state=str(current),proposal=item['name'],plan=str(plan),transaction=str(transaction),attempt_key=attempt_key);write(b/'pending_native.json',pending);reason='uncached_native_proposal_not_submitted';break
   else:
    native_coordinators+=1
    ok=invoke('run_registered_independent_transactions.py',['--batch',transaction,'--selector','compact'],f'{round_number:03d}_{index:02d}_native')
    if ok and read(transaction/'progress.json')['current_group']['status']=='legal_evaluated':evaluation=Path(read(transaction/'progress.json')['current_group']['evaluation']).resolve();native_history.append(transaction)
    else:failed=dict(status='native_transaction_failed_or_rolled_back',transaction=str(transaction))
  if failed:
   attempts.append(dict(attempt_key=attempt_key,round=round_number,proposal=item['name'],before_state=str(current),accepted=False,reason=failed['status'],native_failure=failed));completed.add(attempt_key);persist();continue
  after=read(evaluation/'endpoint_vector.json');d=decisions(before,after,resources(current),resources(evaluation),anchor)
  if a.budget_mode in ['zero_headroom','vertical_fixed_wire_0p1','explicit_absolute']:
   for mode in ['timing_under_resources','resources_under_timing']:
    limits={k:anchor[k] for k in ['wirelength','SB_pairs','CB_sources']}
    if a.budget_mode=='vertical_fixed_wire_0p1':limits['wirelength']=(anchor['wirelength']*1001+999)//1000
    if a.budget_mode=='explicit_absolute':limits=dict(fixed_limits)
    d[mode]=budget_decide(mode,before,after,resources(current),resources(evaluation),cpd_limit_s=anchor['CPD_s'],resource_limits=limits,native_valid=True,transaction_complete=True,resource_objectives=('wirelength',))
  if a.budget_mode=='explicit_absolute':
   d['endpoint_under_resources']=envelope_decide('endpoint_vector',before,after,resources(evaluation),cpd_limit_s=anchor['CPD_s'],resource_limits=fixed_limits,native_valid=True,transaction_complete=True)
  write(directory/'policy_decisions.json',d);allowed=d[a.policy]['accepted'];key=state_key(evaluation);visited_again=key in visited
  record=dict(attempt_key=attempt_key,round=round_number,proposal=item['name'],before_state=str(current),evaluation=str(evaluation),accepted=bool(allowed and not visited_again),policy_accepted=allowed,already_visited=visited_again,reason='Previously visited state' if visited_again else d[a.policy]['reason'],before_CPD_s=before['cpd_s'],after_CPD_s=after['cpd_s'],before_resources=resources(current),after_resources=resources(evaluation),reused_native=bool(hit))
  attempts.append(record);completed.add(attempt_key)
  if record['accepted']:
   assert before['constraints_sha256']==after['constraints_sha256'];accepted.append(record);current=evaluation;visited.add(key);advanced=True;persist();break
  persist()
 if reason:break
 if advanced:round_number+=1;portfolio_path=None;persist();continue
 reason='no_admissible_candidate_in_current_portfolio';persist();break
assert all(sha(p)==h for p,h in bindings.items());persist()
write(b/'completion.json',dict(passed=reason not in ['feedback_failed_or_process_guard','portfolio_generation_failed','transaction_preparation_failed','exchange_feedback_failed','exchange_diagnostic_failed','exchange_expansion_failed','exchange_menu_failed','rejection_feedback_generation_failed'],operator_stop=reason,native_mode=a.native_mode,policy=a.policy,budget_mode=a.budget_mode,initial_state=str(initial),final_state=str(current),accepted_steps=len(accepted),attempted_proposals=len(attempts),initial_CPD_s=anchor['CPD_s'],final_CPD_s=read(current/'endpoint_vector.json')['cpd_s'],final_resources=resources(current),native_transaction_coordinators_started=native_coordinators,complete_current_segment_seconds=time.monotonic()-started,prior_child_seconds=prior_child_seconds,complete_imported_state_workflow_seconds=None if a.resume_from else time.monotonic()-started,complete_single_configuration_algorithm_seconds=None,
 source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'resume_state.json',b/'attempts.json',b/'steps.json',b/'reuse_receipts.json',b/'process_costs.json']},qualification='Local fixed-menu operator outcome only. Every rejection/failure preserved; first admissible candidate advances that policy and triggers current-state feedback. Historical creation/initial routing/caches excluded from time. No complete cold-run speedup, exhaustive resource search or research completion claim.'))
print(dict(accepted_steps=len(accepted),attempted_proposals=len(attempts),operator_stop=reason,final_state=str(current),native_coordinators=native_coordinators),flush=True)
