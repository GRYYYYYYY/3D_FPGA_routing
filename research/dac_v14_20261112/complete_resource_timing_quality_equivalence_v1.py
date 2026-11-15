"""Compare downstream actual states/requests/native work after graph preparation."""
import hashlib,json
from pathlib import Path
from retained_prefix_workflow import read,sha,route_body
from run_native_scope_policy_v4 import run_dir

KEYS=['cpd_s','setup','hold','endpoint_ids','constraints_sha256']


def state_identity(state):
 state=Path(state);vector=read(state/'endpoint_vector.json')
 vector_hash=hashlib.sha256(json.dumps({k:vector[k] for k in KEYS},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return dict(full_endpoint_vector_sha256=vector_hash,ordered_route_body_sha256=route_body(run_dir(state)/'routed.route'))


def compare(actual,reference,actual_quality_receipt):
 actual,reference=Path(actual),Path(reference)
 actual_quality_receipt=Path(actual_quality_receipt).resolve()
 proofs=[read(actual_quality_receipt),read(reference/'completion.json')]
 assert proofs[0]['passed'] and proofs[0]['complete_configuration_quality_verified']
 assert proofs[1]['passed'] and proofs[1]['complete_configuration_verified']
 assert proofs[0]['source_sha256'][str(actual/'flow/completion.json')]==sha(actual/'flow/completion.json')
 actual_flow=read(actual/'flow/completion.json')
 for key in ['initial_state','resource_final_state','final_state']:assert proofs[0][key]==actual_flow[key]
 files=[];memo={}
 def signature(state):
  state=Path(state)
  if str(state) not in memo:
   memo[str(state)]=state_identity(state)
   files.extend([state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'manifest.json',run_dir(state)/'routed.route'])
  return memo[str(state)]
 def states(a,b):
  a,b=signature(a),signature(b)
  return dict(full_endpoint_vector_exact=a['full_endpoint_vector_sha256']==b['full_endpoint_vector_sha256'],
              ordered_route_body_exact=a['ordered_route_body_sha256']==b['ordered_route_body_sha256'])
 def protocol(path):
  rows=[]
  for line in path.read_text().splitlines():
   words=line.split()
   if words[0]=='QUERY':words[7]='ELAPSED'
   elif words[0]=='COMPLETE':words[-2]='ELAPSED'
   rows.append(words)
  files.append(path);return rows
 def transaction(txa,txb):
  regs=[read(p/'registration.json') for p in [txa,txb]];progress=[read(p/'progress.json') for p in [txa,txb]]
  exact=regs[0]['roles'].keys()==regs[1]['roles'].keys() and progress[0].keys()==progress[1].keys()
  per_role={}
  for name in progress[0].keys()&progress[1].keys():
   a,b=progress[0][name],progress[1][name];ra,rb=[r['roles'][name] for r in regs]
   role_inputs=all(ra.get(k)==rb.get(k) for k in ['objective','queries','removed_pins','fixed_target_paths','seed_order','crossing_reuse_enabled','domain_failure_release'])
   request=sha(ra['request'])==sha(rb['request']);files.extend(map(Path,[ra['request'],rb['request']]))
   if ra.get('crossing_domain') and rb.get('crossing_domain'):
    request &= sha(ra['crossing_domain'])==sha(rb['crossing_domain']);files.extend(map(Path,[ra['crossing_domain'],rb['crossing_domain']]))
   status=a['status']==b['status'];detail=dict(role_inputs_exact=role_inputs,request_and_domain_exact=request,status_exact=status)
   if a['status']==b['status']=='legal_evaluated':
    outcome=states(a['evaluation'],b['evaluation']);detail.update(outcome)
    detail['resources_policies_exact']=all(a[k]==b[k] for k in ['resources','policies','cpd_s'])
    status &= all(outcome.values()) and detail['resources_policies_exact']
   elif a['status']==b['status']=='not_executed_domain_candidate_accepted':
    status &= a['acceptance_evaluated'] is b['acceptance_evaluated'] is False
   elif a['status']==b['status']=='transaction_failed_rolled_back':pass
   else:status=False
   workers=[p/name for p in [txa,txb]]
   if all(p.exists() for p in workers):
    logs=[run_dir(p)/'joint_native.log' for p in workers]
    detail['native_protocol_without_runtime_exact']=protocol(logs[0])==protocol(logs[1])
    status &= detail['native_protocol_without_runtime_exact']
   exact &= bool(role_inputs and request and status);per_role[name]=detail
  for p in [txa,txb]:files.extend([p/'registration.json',p/'progress.json'])
  return dict(exact=bool(exact),roles=per_role)
 initial=states(proofs[0]['initial_state'],proofs[1]['initial_state'])
 final=states(proofs[0]['final_state'],proofs[1]['final_state'])
 resource_final=states(proofs[0]['resource_final_state'],proofs[1]['resource_final_state'])
 resource_actors=[p/'flow/resource_flow/repair' for p in [actual,reference]]
 attempts=[read(p/'attempts.json') for p in resource_actors]
 resource_exact=len(attempts[0])==len(attempts[1]);resource_rows=[]
 for i,(a,b) in enumerate(zip(*attempts)):
  scope=all(a.get(k)==b.get(k) for k in ['round','candidate_rank','removed_pins','accepted_role','native_transaction_complete'])
  source=states(a['current_state'],b['current_state'])
  tx=transaction(Path(a['transaction']),Path(b['transaction']))
  resource_exact &= scope and all(source.values()) and tx['exact']
  resource_rows.append(dict(index=i,scope_exact=scope,source=source,transaction=tx))
 timing_actors=[p/'flow/timing' for p in [actual,reference]]
 timed=[read(p/'attempts.json') for p in timing_actors]
 timing_exact=len(timed[0])==len(timed[1]);timing_rows=[]
 for i,(a,b) in enumerate(zip(*timed)):
  fields=['round','proposal','accepted','policy_accepted','already_visited','before_CPD_s','after_CPD_s','before_resources','after_resources','reused_native']
  scope=all(a.get(k)==b.get(k) for k in fields);source=states(a['before_state'],b['before_state'])
  outcome=states(a['evaluation'],b['evaluation']) if a.get('evaluation') and b.get('evaluation') else {}
  matched_txs=[]
  if not a.get('reused_native') and not b.get('reused_native') and outcome:
   txs=[]
   for actor,attempt in zip(timing_actors,[a,b]):
    choices=[]
    for proposal in (actor/f"round_{attempt['round']:03d}").glob('proposal_*'):
     progress=proposal/'transaction/progress.json'
     if progress.exists() and read(progress).get('current_group',{}).get('evaluation')==attempt['evaluation']:choices.append(proposal/'transaction')
    assert len(choices)==1,choices
    txs.append(choices[0])
   matched_txs.append(transaction(*txs))
  exact=bool(scope and all(source.values()) and outcome and all(outcome.values()) and all(x['exact'] for x in matched_txs))
  timing_exact &= exact;timing_rows.append(dict(index=i,scope_exact=scope,source=source,outcome=outcome,transactions=matched_txs,exact=exact))
 process_tags={}
 for phase,actors in [('resource',resource_actors),('timing',timing_actors)]:
  paths=[p/'process_costs.json' for p in actors];files.extend(paths)
  tags=[[row['tag'] for row in read(p)] for p in paths];process_tags[phase]=tags[0]==tags[1]
 handoff_states=[read(p/'flow/completion.json')['timing_initial_state'] for p in [actual,reference]]
 handoff=states(*handoff_states)
 for actor in [*resource_actors,*timing_actors]:files.append(actor/'attempts.json')
 files.extend([actual_quality_receipt,reference/'completion.json'])
 return dict(initial=initial,resource_final=resource_final,handoff=handoff,final=final,
  resource_actual_attempts=len(attempts[0]),resource_reference_attempts=len(attempts[1]),resource_attempts_exact=bool(resource_exact),
  timing_actual_attempts=len(timed[0]),timing_reference_attempts=len(timed[1]),timing_attempts_exact=bool(timing_exact),
  downstream_process_tag_sequences_exact=process_tags,
  downstream_actual_states_requests_and_native_work_exact=bool(all(initial.values()) and all(resource_final.values()) and all(handoff.values()) and all(final.values()) and resource_exact and timing_exact and all(process_tags.values())),
  resource_attempts=resource_rows,timing_attempts=timing_rows,compared_files=list(dict.fromkeys(map(str,files))),
  qualification='Full CPD/setup/hold/endpoint/constraint identities and ordered physical route bodies are compared for every actual source/candidate/handoff/final; native request/domain/policy and native KEEP/NODE/retry/heap-count protocols exclude only elapsed seconds. Downstream helper tag sequences are compared. Internal standalone non-native query counters are not separately compared. Graph-generation work intentionally differs; no claim that total execution work or binary source files are identical.')
