"""Verify both completed local timing menus and compare actual own-current steps."""
import collections
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from seed_census_analysis_pool_v2 import process_identity
from endpoint_timing_policy_streaming_v2 import compare
from resource_opportunity_census import stream_trace
from coordinated_repair_tree import from_trace
root=D/'budget47_current_timing_composition_01';q=root/'queue';closed=read(q/'completion.json');plan=read(root/'plan.json');assert closed['passed'] and set(closed['results'])==set(plan['fixed_order'])
limits=read(root/'absolute_limits.json');files=[Path(__file__).resolve(),q/'completion.json',q/'results.json',q/'registration.json',root/'plan.json',root/'absolute_limits.json'];arms={};records={}
for name in plan['fixed_order']:
 actor=root/name/'timing';c=read(actor/'completion.json');r=read(actor/'registration.json');assert c['passed'] and c['operator_stop']=='no_admissible_candidate_in_current_portfolio'
 p=process_identity(r['pid']);assert not p or p['state']=='Z' or p['start_ticks']!=r['start_ticks']
 for v in [c,r]:assert all(sha(f)==h for f,h in v['source_sha256'].items())
 assert r['fixed_absolute_limits']==limits and r['policy']=='timing_under_resources' and r['fraction']==.9
 attempts=read(actor/'attempts.json');steps=read(actor/'steps.json');assert len(steps)==c['accepted_steps'] and len(attempts)==c['attempted_proposals']
 final=Path(c['final_state']);assert read(final/'completion.json')['passed'] and read(final/'input_seal.json')['passed'] and read(run_dir(final)/'independent_audit.json')['audit']['passed']
 delta=compare(read(Path(c['initial_state'])/'endpoint_vector.json'),read(final/'endpoint_vector.json'));assert delta['compatible'] and delta['hold_violation_regressions']==0
 arms[name]=dict(local_timing_menu_terminal=True,final_state=str(final),CPD_ns=c['final_CPD_s']*1e9,resources=c['final_resources'],accepted_steps=c['accepted_steps'],attempted_proposals=c['attempted_proposals'],actual_native_coordinators=c['native_transaction_coordinators_started'],source_reobservation_seconds=closed['results'][name]['source_reobservation_seconds'],complete_timing_segment_process_seconds=closed['results'][name]['complete_timing_segment_process_seconds'],complete_fresh_route_algorithm_seconds=None,full_endpoint_comparison=delta)
 records[name]=steps;files += [actor/'completion.json',actor/'registration.json',actor/'attempts.json',actor/'steps.json',actor/'process_costs.json',final/'completion.json',final/'input_seal.json',final/'endpoint_vector.json',run_dir(final)/'independent_audit.json']
rows=[]
for left,right in zip(*[records[n] for n in plan['fixed_order']]):
 per=[]
 for step in [left,right]:
  state=Path(step['evaluation']);tx=state.parent;reg=read(tx/'registration.json');role=reg['roles']['current_group'];audit=read(tx/'current_group_audit/analysis.json');assert audit['passed'] and read(tx/'completion.json')['passed'];assert read(state/'completion.json')['passed'] and read(state/'input_seal.json')['passed']
  nets=set(map(int,role['removed_pins']));trees={}
  for label,s in [('before',Path(step['before_state'])),('after',state)]:
   trees[label]={r['net']:from_trace(r['trace'],collections.defaultdict(float)) for r in stream_trace(run_dir(s)/'routed.route') if r['net'] in nets};assert trees[label].keys()==nets
  delta=compare(read(Path(step['before_state'])/'endpoint_vector.json'),read(state/'endpoint_vector.json'))
  per.append(dict(role=role,audit=audit,trees=trees,delta=delta));files += [tx/'registration.json',tx/'completion.json',tx/'current_group_audit/analysis.json',state/'completion.json',state/'input_seal.json',state/'endpoint_vector.json',Path(step['before_state'])/'endpoint_vector.json',Path(role['request'])]
 a,b=per;rows.append(dict(round=left['round'],same_round=left['round']==right['round'],same_request=sha(a['role']['request'])==sha(b['role']['request']),same_removed_pins=a['role']['removed_pins']==b['role']['removed_pins'],same_affected_complete_before_trees=a['trees']['before']==b['trees']['before'],same_affected_complete_after_trees=a['trees']['after']==b['trees']['after'],same_changed_native_connection_delays=a['audit']['changed_delays']==b['audit']['changed_delays'],same_endpoint_change_records=a['delta']['changes']==b['delta']['changes'],same_CPD=left['after_CPD_s']==right['after_CPD_s'],native_resources=left['after_resources'],guided_resources=right['after_resources'],guided_minus_native_wire=right['after_resources']['wirelength']-left['after_resources']['wirelength']))
native,guided=[arms[n] for n in plan['fixed_order']]
assert native['CPD_ns']==guided['CPD_ns']==13.228145689936355
assert native['resources']==dict(wirelength=2061249,SB_pairs=47,CB_sources=5060) and guided['resources']==dict(wirelength=2061076,SB_pairs=47,CB_sources=5060)
write(root/'comparison.json',dict(passed=True,whole_local_pair_terminal=True,registered_arms=2,arms=arms,matched_step_comparisons=rows,accepted_step_counts_equal=len(records['native_full462'])==len(records['guided_budget54']),guided_minus_native_final_resources={k:guided['resources'][k]-native['resources'][k] for k in native['resources']},guided_final_quality_dominates_local_native_final=True,complete_fresh_route_algorithm_seconds=None,source_sha256={str(f):sha(f) for f in files},qualification='Both registered local current-STA menus complete from two different resource-stage alternatives at a shared guided48SB ancestor. Same original absolute wire2061627/SB47/CB5060 caps and v5/fraction.9; own-current histories, all actual proposals/checks/restoration counted. Final guided point saves173wire at equal CPD/SB/CB; first-step177wire advantage is not incorrectly extrapolated through later steps. Requests/affected-tree/delay/endpoint changes compared step by step and differences retained. Imported source reobservation and timing-segment times are separate actual phases; prefix creation, initial routing and graph preprocessing excluded, so no cold full-algorithm time or statistical speedup or one-factor domain/grouping isolation is claimed.'))
print(dict(passed=True,arms={k:{f:v[f] for f in ['CPD_ns','resources','accepted_steps','attempted_proposals','complete_timing_segment_process_seconds']} for k,v in arms.items()},step_checks=rows),flush=True)
