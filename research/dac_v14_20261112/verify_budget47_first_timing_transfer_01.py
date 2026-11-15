"""Verify actual identical timing intervention across two resource-scope alternatives."""
import collections
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from native_problem_identity import problem_identity
from coordinated_repair_tree import from_trace
from resource_opportunity_census import stream_trace
from endpoint_timing_policy_streaming_v2 import compare
root=D/'budget47_current_timing_composition_01';plan=read(root/'plan.json');out=D/'budget47_first_timing_transfer_validation_01';out.mkdir(exist_ok=False)
files=[Path(__file__).resolve(),root/'plan.json',root/'absolute_limits.json',D/'coordinated_repair_tree.py',D/'resource_opportunity_census.py'];data={}
def axes(state):
 a=read(run_dir(state)/'independent_audit.json');assert a['audit']['passed'];m=a['physical_metrics'];return dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=m['sb_pairs_used'],CB_sources=m['cb_crossing_output_sources_used'])
for arm in plan['fixed_order']:
 actor=root/arm/'timing';step=read(actor/'steps.json')[0];assert step['accepted'] and step['round']==0 and not step['reused_native']
 snapshot=out/(arm+'_actual_first_commit.json');write(snapshot,step)
 source=Path(step['before_state']);state=Path(step['evaluation']);tx=state.parent;c=read(tx/'completion.json');assert c['passed'];assert all(sha(f)==h for f,h in c['source_sha256'].items())
 assert read(state/'completion.json')['passed'] and read(state/'input_seal.json')['passed']
 audit=read(tx/'current_group_audit/analysis.json');assert audit['passed'];assert all(sha(f)==h for f,h in audit['source_sha256'].items())
 assert sha(audit['candidate_route'])==audit['candidate_sha256']
 role=read(tx/'registration.json')['roles']['current_group'];critical_nets=set(map(int,role['removed_pins']))
 prefix=Path(plan['cases'][arm]);prefix_reg=read(prefix.parent/'registration.json');resource_nets=set()
 for r in prefix_reg['roles'].values():resource_nets.update(map(int,r['removed_pins']))
 assert not critical_nets&resource_nets
 trees={}
 for label,s in [('before',source),('after',state)]:
  trace=run_dir(s)/'routed.route';selected={r['net']:from_trace(r['trace'],collections.defaultdict(float)) for r in stream_trace(trace) if r['net'] in critical_nets}
  assert selected.keys()==critical_nets;trees[label]=selected;files += [trace,s/'endpoint_vector.json',run_dir(s)/'manifest.json',run_dir(s)/'independent_audit.json']
 before,after=read(source/'endpoint_vector.json'),read(state/'endpoint_vector.json');delta=compare(before,after);assert delta['compatible'] and not delta['hold_violation_regressions']
 data[arm]=dict(step=step,source=source,state=state,transaction=tx,role=role,audit=audit,critical_nets=critical_nets,resource_nets=resource_nets,trees=trees,before_axes=axes(source),after_axes=axes(state),before_vector=before,after_vector=after,delta=delta)
 files += [snapshot,actor/'registration.json',tx/'completion.json',tx/'registration.json',tx/'current_group_audit/analysis.json',state/'completion.json',state/'input_seal.json',prefix.parent/'registration.json']
x,y=[data[n] for n in plan['fixed_order']]
assert problem_identity(run_dir(x['source']))==problem_identity(run_dir(y['source']))
assert x['before_vector']['constraints_sha256']==y['before_vector']['constraints_sha256'] and x['before_vector']['endpoint_ids']==y['before_vector']['endpoint_ids']
request_equal=sha(x['role']['request'])==sha(y['role']['request']);assert request_equal
assert x['role']['removed_pins']==y['role']['removed_pins'] and x['trees']['before']==y['trees']['before'] and x['trees']['after']==y['trees']['after']
assert x['audit']['changed_delays']==y['audit']['changed_delays']
assert x['after_vector']['cpd_s']==y['after_vector']['cpd_s']==1.3421610489672275e-08
assert all(x['after_axes'][k]==y['after_axes'][k] for k in ['SB_pairs','CB_sources'])
before_diff=y['before_axes']['wirelength']-x['before_axes']['wirelength'];after_diff=y['after_axes']['wirelength']-x['after_axes']['wirelength'];assert before_diff==after_diff==-177
files += [Path(x['role']['request']),Path(y['role']['request'])]
write(out/'completion.json',dict(passed=True,native_calls_new=0,actual_first_timing_request_equal=True,all_affected_net_before_and_after_complete_physical_trees_equal=True,actual_changed_connection_delays_equal=True,affected_timing_nets=sorted(x['critical_nets']),resource_prefix_scope_nets={k:sorted(v['resource_nets']) for k,v in data.items()},timing_nets_disjoint_from_resource_prefix_nets=True,CPD_ns=y['after_vector']['cpd_s']*1e9,after_resources={k:v['after_axes'] for k,v in data.items()},guided_minus_native_wire_before=before_diff,guided_minus_native_wire_after=after_diff,endpoint_change_records_exact=x['delta']['changes']==y['delta']['changes'],selected_first_commit_states={k:str(v['state']) for k,v in data.items()},whole_paired_trajectory_terminal=False,complete_single_configuration_seconds=None,source_sha256={str(f):sha(f) for f in files},qualification='Both actual same-physical-input resource-stage alternatives receive the same current-STA request and modify exactly identical complete trees on four affected timing nets, disjoint from the resource scopes. Actual native physical delay changes and CPD/SB/CB agree, preserving the177wire resource advantage after the first timing commit. Full source states/vectors may differ and are not called identical roots. This is observed composition transfer across two different resource grouping/domain outcomes, not a one-factor causal domain isolation or final whole-algorithm ranking. Guided later trajectory remains live. No new native calls, unexecuted alternative inference, full algorithm cost or independent circuit sample claim.'))
print(dict(passed=True,CPD_ns=y['after_vector']['cpd_s']*1e9,guided_resources=y['after_axes'],wire_advantage_preserved=177,whole_pair_complete=False),flush=True)
