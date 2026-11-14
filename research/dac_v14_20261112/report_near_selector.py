#!/usr/bin/env python3
"""Account for every near-window branch decision and matched native control."""
import json,math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import compare,decide
from current_sta_selector import select

b=D/'current_sta_policy_R1_near_01';done=read(b/'completion.json');reg=read(b/'registration.json');events=read(b/'decisions.json')
initial=Path(reg['initial_state']);base=read(initial/'endpoint_vector.json');base_run=Path(read(initial/'completion.json')['run'])
threshold=min(x for x in base['setup'].values() if isinstance(x,(int,float)) and math.isfinite(x))+.2e-9
def near(vector,reference):
 keys=[k for k,v in vector['setup'].items() if isinstance(v,(int,float)) and math.isfinite(v) and v<=reference]
 return dict(components=len(keys),endpoints=len({tuple(json.loads(k)[:3]) for k in keys}),threshold_s=reference)
def metrics(state):
 completion=read(state/'completion.json');run=Path(completion['run']);vector=read(state/'endpoint_vector.json')
 return dict(state=str(state),cpd_ns=vector['cpd_s']*1e9,resources=read(run/'independent_audit.json')['physical_metrics'],
  fixed_initial_window=near(vector,threshold),current_window=near(vector,min(x for x in vector['setup'].values() if isinstance(x,(int,float)) and math.isfinite(x))+.2e-9),
  current_worst_selection=select(run/'native_sta_frontier.jsonl'),current_near_selection=select(run/'native_sta_frontier.jsonl',.2),
  endpoint_change={k:v for k,v in compare(base,vector).items() if k!='changes'})
final={policy:metrics(Path(result['state'])) for policy,result in done['outcomes'].items()}
plateaus=[]
for e in events:
 if e['policy']!='endpoint_vector' or not e.get('decision',{}).get('accepted'):continue
 before=read(Path(e['source_state'])/'endpoint_vector.json');after=read(Path(e['evaluated_state'])/'endpoint_vector.json');strict=decide('strict',before,after,True)
 plateaus.append(dict(step=e['step'],targets=e['candidate']['targets'],source_state=e['source_state'],evaluated_state=e['evaluated_state'],
  strict_rejects_same_before_after=not strict['accepted'],strict_reason=strict['reason'],cpd_before_ns=before['cpd_s']*1e9,cpd_after_ns=after['cpd_s']*1e9,
  setup_improved=e['decision']['comparison']['setup_improved'],setup_regressed=e['decision']['comparison']['setup_regressed'],
  changes=e['decision']['comparison']['changes'],reused_evaluation=e['reused_evaluation'],
  provenance='Actual endpoint branch transition; strict counterfactual uses these exact native before/after values. Strict branch stays on its own state.'))
queries=[read(p) for p in b.glob('queries_*/execution.json')];costs=read(b/'process_costs.json')
native=[];nb=D/'current_sta_near_native_dev_01';sources=[b/'registration.json',b/'completion.json',b/'decisions.json',b/'process_costs.json',D/'current_sta_near_selector_experiment_01.json']
sources += list(b.glob('queries_*/execution.json'))+list(b.glob('queries_*/analysis.json'))+list(b.glob('*_state_*.json'))+list(b.glob('evaluation_*/completion.json'))+list(b.glob('evaluation_*/endpoint_vector.json'))
for r in final.values():
 state=Path(r['state']);sources += [state/'completion.json',state/'endpoint_vector.json']
if (nb/'completion.json').exists():
 nc=read(nb/'completion.json');nr=read(nb/'registration.json');assert nc['all_roles_completed']
 for role,r in nr['roles'].items():
  evaluation=Path(nc['roles'][role].get('evaluation_state',str(nb/(role+'_evaluation'))));a=read(evaluation/'endpoint_vector.json');reference=read(Path(r['capacity_reference'])/'endpoint_vector.json')
  same=a['cpd_s']==reference['cpd_s'] and a['setup']==reference['setup'] and a['hold']==reference['hold']
  audit_path=nb/(role+'_audit')/'analysis.json';ar=read(audit_path if audit_path.exists() else nb/(role+'_reference_equivalence.json'));native.append(dict(role=role,target=r['targets'],cpd_ns=a['cpd_s']*1e9,exact_all_timing_components_same_as_capacity=same,reused_candidate_FULL_STA=nc['roles'][role].get('reused_candidate_FULL_STA',False),
    decisions=nc['roles'][role]['decisions'],native_queries=len(ar['queries']),native_attempts=len(ar['attempts']),native_transaction_seconds=ar['native_transaction_seconds'],
    resources=read(Path(read(evaluation/'completion.json')['run'])/'independent_audit.json')['physical_metrics']))
  sources += [audit_path if audit_path.exists() else nb/(role+'_reference_equivalence.json'),nb/(role+'_decision.json'),evaluation/'completion.json',evaluation/'endpoint_vector.json']
 sources += [nb/'registration.json',nb/'completion.json',nb/'process_costs.json']
result=dict(passed=True,research_complete=False,quality_promoted=False,initial=metrics(initial),final=final,plateau_transitions=plateaus,
 decisions={p:dict(accepted=sum(e.get('decision',{}).get('accepted',False) for e in events if e['policy']==p),rejected=sum(not e.get('decision',{}).get('accepted',False) for e in events if e['policy']==p)) for p in final},
 timing=dict(complete_orchestrator_seconds=done['complete_orchestrator_seconds'],complete_child_process_seconds=sum(x['complete_process_seconds'] for x in costs),
  candidate_generation_and_audit_seconds=sum(x['complete_process_seconds'] for x in costs if x['tag'].startswith('queries_')),
  native_evaluation_wrapper_seconds=sum(x['complete_process_seconds'] for x in costs if x['tag'].startswith('evaluation_')),
  measured_policy_rollback_seconds=sum(e.get('rollback_seconds',0.) for e in events),
  qualification='Shared exact-cache development orchestration, not two independent cold-start algorithm runtimes. Evaluation wrappers include native FULL/STA and independent physical audit. No historical U timing.'),
 execution=dict(new_capacity_queries=sum(q['new_queries'] for q in queries),reused_capacity_queries=sum(q['reused_queries'] for q in queries),query_states=len(queries),
  new_native_evaluations=sum(x['tag'].startswith('evaluation_') for x in costs),reuse_evaluations=sum(e.get('reused_evaluation',False) for e in events)),
 native_controls=native,native_control_complete=bool(native),native_control_timing=None if not native else dict(incremental_orchestrator_seconds=nc['complete_orchestrator_seconds'],candidate_FULL_STA_reused=sum(x.get('reused_candidate_FULL_STA',False) for x in native),native_connection_search_calls=sum(x['native_attempts'] for x in native),qualification='Incremental matched controls with explicit reuse; not independent cold-start algorithm timing.'),
 qualification='Continuation from the common automatically accepted frozen-R1-derived state. The 0.2ns window and single-only operator isolate selection and acceptance opportunities; local exhaustion is not an overall research limit. No claim that plateau steps eventually reduce CPD unless observed.',
 public_snapshot='f7167bd',new_work_pushed=False,source_sha256={str(p):sha(p) for p in dict.fromkeys(sources)})
write(D/'current_sta_near_selector_summary_01.json',result)
print(dict(decisions=result['decisions'],final={p:r['cpd_ns'] for p,r in final.items()},plateaus=len(plateaus),native=native,timing=result['timing'],execution=result['execution']),flush=True)
