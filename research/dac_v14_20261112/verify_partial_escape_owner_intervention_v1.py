"""Read-only native gates and fixed-envelope outcomes of the two-pin intervention."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof,resource_assurance
from multiobjective_acceptance_v2 import decide
from endpoint_timing_policy_streaming_v2 import compare

root=D/'partial_escape_owner_intervention_01';assert not (root/'verification.json').exists()
plan=read(root/'plan.json');execution=read(root/'queue/execution_receipt.json')
assert all(sha(p)==h for p,h in execution['source_sha256'].items())
state=Path(plan['source_state']);before=read(state/'endpoint_vector.json')
require_publication_proof(state);axes_before=resource_assurance(state)['resource_axes']
proposal=Path(plan['candidate_construction']);construction=read(proposal/'completion.json')
assert construction['passed'] and construction['state']==str(state)
assert all(sha(p)==h for p,h in construction['source_sha256'].items())
assert all(sha(proposal/n)==h for n,h in construction['artifact_sha256'].items())
assert sha(plan['candidate_route'])==plan['candidate_route_sha256']==construction['candidate_sha256']
assert construction['original_resources']==axes_before and construction['all_fixed_sinks_restored'] and construction['all_actual_RR_node_capacities_satisfied']
files=[Path(__file__).resolve(),root/'plan.json',root/'queue/execution_receipt.json',root/'queue/results.json',
 root/'prepared_transaction_registration.json',proposal/'completion.json',proposal/'candidate.route',
 state/'completion.json',state/'endpoint_vector.json',D/'R1_single_net_vertical_local_minimum_01/completion.json']
outcomes={}
def legal(state, kind):
 state=Path(state);closed=read(state/'completion.json');assert closed['passed']
 view=require_publication_proof(state);assert view['passed']
 run=run_dir(state);manifest=read(run/'manifest.json');assert manifest['metrics']['native_full_check_passed']
 for name in ['packed.net','placed.place','routed.route']:assert sha(run/name)==manifest['outputs'][name]['sha256']
 audit=read(run/'independent_audit.json');assert audit['audit']['passed']
 resources=resource_assurance(state)['resource_axes'];after=read(state/'endpoint_vector.json')
 decision=decide('resources_under_timing',before,after,axes_before,resources,
  cpd_limit_s=plan['original_budget']['CPD_s'],resource_limits=plan['fixed_resource_limits'],
  native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
 endpoint=compare(before,after);assert endpoint['compatible']
 files.extend([state/'completion.json',state/'endpoint_vector.json',run/'manifest.json',run/'independent_audit.json',run/'routed.route'])
 return dict(status='legal_evaluated',kind=kind,evaluation=str(state),CPD_ns=after['cpd_s']*1e9,resources=resources,
  original_envelope_decision=decision,endpoint_comparison=endpoint,policy_accepted=decision['accepted'],
  committed_to_original_actor=False,complete_single_configuration_seconds=None)
observed=execution['results'];bfs=root/'BFS_candidate_evaluation'
if observed['BFS_candidate_LOAD']['passed']:
 closed=read(bfs/'completion.json');assert all(closed['checks'].values()) and closed['native_analysis_calls']==1 and closed['route_search_calls']==0
 assert closed['checks']['inputs_sealed'] and read(bfs/'input_seal.json')['passed']
 reg=read(bfs/'registration.json');assert not reg['observation_only'] and reg['fresh_physical_audit']
 assert reg['candidate_route']==plan['candidate_route'] and all(sha(p)==h for p,h in reg['source_sha256'].items())
 assert sha(run_dir(bfs)/'routed.route')==construction['candidate_sha256']
 result=legal(bfs,'deterministic_same_layer_BFS_target_plus_owner')
 assert result['resources']==construction['structural_full_route_resources']
 manifest=read(run_dir(bfs)/'manifest.json')
 assert sha(manifest['command'][0])==read(D/'native_resource_census_stage_01/binding.json')['binary_sha256']
 result['actual_native_binary_sha256']=sha(manifest['command'][0])
 result['actual_imported_evaluation_timing']=closed['timing'];result['independent_physical_audit_reused']=False
 bound=read(D/'BNN_vertical_cut_bound_01/completion.json');assert bound['passed']
 # Same terminal mapping is inherited through exact per-net construction and
 # byte-identical unaffected nets; independent/native checks ran on this file.
 result['attains_same_fixed_terminal_total_vertical_bound']=sum(result['resources'][k] for k in ['SB_pairs','CB_sources'])==read(D/'R1_single_net_vertical_local_minimum_01/completion.json')['terminal_layer_lower_bound']
 outcomes['BFS_candidate_LOAD']=result
 files += [bfs/'registration.json',bfs/'input_seal.json']
else:
 outcomes['BFS_candidate_LOAD']=dict(status='native_FULL_STA_or_independent_gate_failed',quality=None,
  returncode=observed['BFS_candidate_LOAD']['returncode'],committed_to_original_actor=False)
 if (bfs/'completion.json').exists():
  outcomes['BFS_candidate_LOAD']['actual_failure_receipt']=read(bfs/'completion.json');files.append(bfs/'completion.json')
tx=root/'transaction';reg=read(tx/'registration.json');roles=reg['roles']
assert list(roles)==['native_2pins','retained_CB_2pins']
a,b=roles.values()
for key in ['state','source','request','queries','removed_pins','objective','seed_order','original_budget','fixed_resource_limits']:
 assert a[key]==b[key]
assert a['removed_pins']==plan['removed_pins'] and a['queries']==plan['queries'] and len(a['queries'])==2
assert not a['crossing_reuse_enabled'] and b['crossing_reuse_enabled'] and b['explicit_crossings']
files.append(tx/'registration.json')
if observed['native_two_connection_pair']['passed']:
 closed=read(tx/'completion.json');assert closed['passed']
 assert all(sha(p)==h for p,h in closed['source_sha256'].items())
 progress=read(tx/'progress.json');assert set(progress)==set(roles)
 binaries=set()
 for name,role in roles.items():
  worker=tx/name;wc=read(worker/'completion.json');assert wc['passed'] and all(wc['checks'].values())
  restored=read(worker/'endpoint_vector.json')
  assert all(restored[k]==before[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
  assert route_body(run_dir(worker)/'routed.route')==route_body(Path(role['source'])/'routed.route')
  manifest=read(run_dir(worker)/'manifest.json');binaries.add(sha(manifest['command'][0]))
  assert manifest['environment']['VPR_JOINT_NATIVE_SEED_ORDER']==role['seed_order']
  audit=read(tx/(name+'_audit/analysis.json'));domain=read(tx/(name+'_domain_audit.json'))
  assert audit['passed'] and domain['passed'] and domain['enabled']==role['crossing_reuse_enabled']
  for proof in [audit,domain]:assert all(sha(p)==h for p,h in proof['source_sha256'].items())
  if role['crossing_reuse_enabled']:
   assert domain['retained_crossing_resources_present_after_prune'] and domain['domain_equals_actual_retained_crossing_sources']
  expected_order=[(q['net'],q['pin']) for q in role['queries']]
  actual_order=[(q['net'],q['pin']) for q in audit['queries']]
  assert actual_order==expected_order[:len(actual_order)]
  row=progress[name]
  if row['status']=='transaction_failed_rolled_back':
   assert not audit.get('candidate_route')
   outcomes[name]=dict(status=row['status'],quality=None,policy_accepted=False,committed_to_original_actor=False)
  else:
   assert row['status']=='legal_evaluated' and actual_order==expected_order
   assert all(x['terminal_set_unchanged'] and x['other_branch_edges_unchanged'] for x in audit['scope'])
   result=legal(row['evaluation'],'native_weighted_same_partial_scope')
   assert result['resources']==row['resources'] and result['CPD_ns']==row['cpd_s']*1e9
   decision=read(tx/(name+'_decisions.json'))['resources_under_timing']
   assert decision==result['original_envelope_decision']
   result['actual_native_binary_sha256']=sha(manifest['command'][0]);outcomes[name]=result
   files.append(tx/(name+'_decisions.json'))
  outcomes[name].update(actual_native_queries=len(audit['queries']),actual_search_attempts=len(audit['attempts']))
  files += [worker/'completion.json',worker/'endpoint_vector.json',run_dir(worker)/'manifest.json',tx/(name+'_audit/analysis.json'),tx/(name+'_domain_audit.json')]
 assert binaries=={read(D/'crossing_source_stage_01/binding.json')['binary_sha256']}
 files += [tx/'completion.json',tx/'progress.json',tx/'process_costs.json']
else:
 for name in roles:outcomes[name]=dict(status='native_controller_or_gate_failed',quality=None,policy_accepted=False,committed_to_original_actor=False)
cohort=dict(registered_roles=3,legal_native_observations=sum(x['status']=='legal_evaluated' for x in outcomes.values()),
 failed_or_rolled_back_roles=sum(x['status']!='legal_evaluated' for x in outcomes.values()))
write(root/'verification.json',dict(passed=True,cohort=cohort,outcomes=outcomes,native_calls_new=0,
 original_budget=plan['original_budget'],fixed_resource_limits=plan['fixed_resource_limits'],
 complete_shared_imported_execution_seconds=execution['complete_shared_imported_execution_seconds'],
 offline_candidate_construction_seconds=construction['complete_construction_seconds'],
 source_sha256={str(p):sha(p) for p in files},
 qualification='Native observations only after their own successful FULL/freshSTA, independent complete physical/capacity audit, exact input seal and fixed-envelope checks. Failures/rollbacks retain the registered denominator without quality. Actual source vectors restored in both matched private-binary native controls; only target retained-CB domain differs. BFS uses different minimum-hop construction and explicit Census LOAD binary, so its improvement is a separate constructive algorithm intervention, not a one-factor domain attribution or equal-work timing comparison. Two-pin scope preserves other target branches; compare to original five-connection pair as a separate scope intervention. Original actor remains unchanged. Offline model/lookup timings are not full-flow speedups; whole configuration costs unknown.'))
print(dict(passed=True,cohort=cohort,outcomes={k:{kk:vv for kk,vv in v.items() if kk in ['status','resources','CPD_ns','policy_accepted','attains_same_fixed_terminal_total_vertical_bound']} for k,v in outcomes.items()}),flush=True)
