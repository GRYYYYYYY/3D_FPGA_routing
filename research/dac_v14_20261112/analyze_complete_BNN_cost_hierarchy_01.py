"""Disjoint stage accounting and nested transaction diagnostics, no new routing."""
from collections import defaultdict
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
out=D/'complete_BNN_cost_hierarchy_01';assert not out.exists()
files=[Path(__file__).resolve()];arms={}
for arm in ['bnn_native','bnn_domain']:
 root=D/'complete_resource_timing_full_flow_01'/arm;flow=root/'flow';repair=flow/'resource_flow/repair';done=read(root/'completion.json');assert done['passed']
 whole=done['complete_wall_seconds'];stages=read(flow/'stages.json');assert all(r['status']=='completed' for r in stages)
 upper={r['phase']:r['complete_process_seconds'] for r in stages};assert sum(upper.values())<=whole
 resource=read(flow/'resource_flow/stages.json');middle={r['phase']:r['complete_process_seconds'] for r in resource};assert all(r['status']=='completed' for r in resource)
 assert sum(middle.values())<=upper['fresh_route_and_complete_resource']
 costs=read(repair/'process_costs.json');selections=[r for r in costs if r['tag'].endswith('_current_resource_selection')];transactions=[r for r in costs if r['tag'].endswith('_serial_native_transaction')]
 txsum=sum(r['complete_process_seconds'] for r in transactions);selsum=sum(r['complete_process_seconds'] for r in selections);assert txsum+selsum<=middle['resource_repair']
 inner=defaultdict(float);details=[];queries=attempts=0;core=0.
 for row in read(repair/'attempts.json'):
  tx=Path(row['transaction']);phase=read(tx/'process_costs.json');progress=read(tx/'progress.json');files += [tx/'process_costs.json',tx/'progress.json']
  for call in phase:
   key=next((s for s in ['FULL_STA','domain_audit','audit','native'] if call['tag'].endswith('_'+s)),call['tag']);inner[key]+=call['complete_process_seconds']
  for role,value in progress.items():
   if value['status']=='not_executed_domain_candidate_accepted':continue
   auditpath=tx/(role+'_audit/analysis.json');audit=read(auditpath);files.append(auditpath);assert audit['passed']
   q=len(audit['queries']);a=len(audit['attempts']);c=audit['native_transaction_seconds'];queries+=q;attempts+=a;core+=c
   details.append(dict(round=row['round'],candidate_rank=row['candidate_rank'],role=role,status=value['status'],accepted=row.get('accepted_role')==role,query_count=q,attempt_count=a,nested_native_transaction_seconds=c,quality_resources=value.get('resources'),CPD_s=value.get('cpd_s')))
 files += [root/'completion.json',root/'measurement/completion.json',flow/'stages.json',flow/'resource_flow/stages.json',repair/'process_costs.json',repair/'attempts.json']
 arms[arm]=dict(whole_seconds=whole,top_level_disjoint_seconds=upper,top_level_unallocated_seconds=whole-sum(upper.values()),resource_substages_seconds=middle,resource_selectors_seconds=selsum,resource_transactions_seconds=txsum,resource_other_seconds=middle['resource_repair']-txsum-selsum,transaction_child_category_seconds=dict(inner),transaction_child_other_seconds=txsum-sum(inner.values()),native_query_count=queries,native_attempt_count=attempts,nested_native_core_seconds=core,transaction_details=details)
n,d=arms['bnn_native'],arms['bnn_domain'];delta=d['whole_seconds']-n['whole_seconds'];transaction_delta=d['resource_transactions_seconds']-n['resource_transactions_seconds'];core_delta=d['nested_native_core_seconds']-n['nested_native_core_seconds']
select=read(D/'complete_resource_timing_full_flow_01/bnn_domain/flow/resource_flow/repair/round_009/selection/completion.json');assert select['candidate_scopes']==select['multi_crossing_nets']==0
last=read(D/'complete_resource_timing_full_flow_01/bnn_domain/flow/resource_flow/repair/process_costs.json')[-1];assert last['tag']=='009_current_resource_selection'
bound=read(D/'BNN_vertical_cut_bound_01/completion.json');assert bound['bound_attained'] and bound['actual_SB']+bound['actual_CB']==bound['SB_plus_CB_lower_bound']==5103
files += [D/'BNN_vertical_cut_bound_01/completion.json',D/'cb_terminal_cut_bound_01/completion.json',D/'complete_resource_timing_full_flow_01/bnn_domain/flow/resource_flow/repair/round_009/selection/completion.json',D/'current_crossing_share_selector_v2.py',D/'current_escape_owner_selector_v1.py',D/'terminal_resource_handoff_v1.py']
result=dict(passed=True,arms=arms,whole_domain_minus_native_seconds=delta,resource_transaction_delta_seconds=transaction_delta,transaction_delta_fraction_of_whole_delta=transaction_delta/delta,nested_native_core_delta_seconds=core_delta,terminal_empty_selector=dict(complete_process_seconds=last['complete_process_seconds'],fraction_of_domain_whole=last['complete_process_seconds']/d['whole_seconds'],hypothetical_saving_before_certificate_cost=True,actual_engineering_gain_demonstrated=False),native_calls_new=0,existing_rules_modified=False,source_sha256={str(f):sha(f) for f in files},qualification='Historical complete matched N/D commands only. Top-level stages are disjoint; resource/transaction/core rows are nested and MUST NOT be added to parent wall. Differences are descriptive single-run accounting, not causal speedup or cold independent sample evidence. Query count is connection-query executions across transactions, not globally unique connections or native process count. Empty-selector skip would require an in-command certificate and proof of empty sharing/owner menus while retaining the existing terminal archive; a resource objective lower bound alone is not a wire/CPD bound. No new guard enabled in CP1 or running arms.')
out.mkdir();write(out/'completion.json',result)
print(dict(passed=True,whole_delta=delta,transaction_delta=transaction_delta,transaction_delta_share_percent=100*transaction_delta/delta,native_queries=[n['native_query_count'],d['native_query_count']],nested_core=[n['nested_native_core_seconds'],d['nested_native_core_seconds']],last_empty_selector_percent=100*last['complete_process_seconds']/d['whole_seconds']))
