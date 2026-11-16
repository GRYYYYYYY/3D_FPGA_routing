"""Compare a measured prefix against independently verified quality with a lost observer."""
import hashlib,json
from pathlib import Path
from retained_prefix_workflow import read,sha,route_body
from run_native_scope_policy_v4 import run_dir

KEYS=['cpd_s','setup','hold','endpoint_ids','constraints_sha256']


def state_identity(state):
 state=Path(state);vector=read(state/'endpoint_vector.json')
 vector_hash=hashlib.sha256(json.dumps({k:vector[k] for k in KEYS},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return dict(full_endpoint_vector_sha256=vector_hash,ordered_route_body_sha256=route_body(run_dir(state)/'routed.route'))


def compare(actual,reference,reference_quality_receipt):
 actual,reference=Path(actual),Path(reference)
 reference_quality_receipt=Path(reference_quality_receipt).resolve()
 proofs=[read(actual/'completion.json'),read(reference_quality_receipt)]
 assert proofs[0]['passed'] and proofs[0]['complete_configuration_verified']
 assert proofs[1]['passed'] and proofs[1]['complete_configuration_quality_verified']
 assert proofs[1]['complete_observer_measurement_available'] is False
 assert not (reference/'measurement/completion.json').exists(), 'Use ordinary measured comparison when an actual observer receipt exists'
 original_flow=reference/'flow/completion.json'
 assert proofs[1]['source_sha256'][str(original_flow)]==sha(original_flow)
 original_done=read(original_flow)
 assert original_done['passed']
 for key in ['initial_state','resource_final_state','final_state']:
  assert proofs[1][key]==original_done[key], 'Qualified quality receipt belongs to another flow'
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
 resource_final=states(proofs[0].get('resource_policy_final_state',proofs[0]['resource_final_state']),proofs[1].get('resource_policy_final_state',proofs[1]['resource_final_state']))
 resource_actors=[p/'flow/resource_flow/repair' for p in [actual,reference]]
 attempts=[read(p/'attempts.json') for p in resource_actors]
 resource_exact=len(attempts[0])==len(attempts[1]);resource_rows=[]
 for i,(a,b) in enumerate(zip(*attempts)):
  scope=all(a.get(k)==b.get(k) for k in ['round','candidate_rank','removed_pins','accepted_role','native_transaction_complete'])
  source=states(a['current_state'],b['current_state'])
  tx=transaction(Path(a['transaction']),Path(b['transaction']))
  resource_exact &= scope and all(source.values()) and tx['exact']
  resource_rows.append(dict(index=i,scope_exact=scope,source=source,transaction=tx))
 for actor in resource_actors:files.extend([actor/'attempts.json',actor/'process_costs.json'])
 files.extend([actual/'completion.json',reference_quality_receipt,original_flow])
 tags=[[row['tag'] for row in read(actor/'process_costs.json')] for actor in resource_actors]
 exact=bool(all(initial.values()) and all(resource_final.values()) and resource_exact and tags[0]==tags[1])
 return dict(initial=initial,original_resource_policy_final=resource_final,resource_actual_attempts=len(attempts[0]),resource_reference_attempts=len(attempts[1]),resource_attempts_exact=bool(resource_exact),resource_process_tags_exact=tags[0]==tags[1],resource_prefix_actual_states_requests_and_native_work_exact=exact,resource_attempts=resource_rows,compared_files=list(dict.fromkeys(map(str,files))),qualification='Exact comparison of the common original resource prefix before optional wire retention. Full endpoint vectors and ordered actual source/candidate routes, requests/domain/options/decisions and native KEEP/NODE/retry/heap protocol excluding elapsed time. The new terminal selection and downstream timing are deliberately outside this equivalence claim; differing actual work or state is retained and disqualifies a single-change comparison.')
