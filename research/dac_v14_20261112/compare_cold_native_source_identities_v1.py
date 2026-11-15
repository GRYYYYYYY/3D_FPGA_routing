"""Distinguish ordered serialization, physical trees and native endpoint vectors."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from complete_flow_equivalence_v1 import equal_state
from actual_route_tree_identity import tree_identity
from run_native_scope_policy_v4 import run_dir

out=D/'cold_native_source_identity_analysis_01';out.mkdir(exist_ok=False)
case=D/'complete_resource_timing_full_flow_01/bnn_native';complete=read(case/'completion.json');assert complete['passed']
old_actor=D/'native_census_resource_equivalence_recovery_02/bnn_A0_native'
old_complete=read(old_actor/'completion.json');assert old_complete['passed']
old_point=next(p for p in read(D/'multiobjective_revalidated_native_checkpoints_01/points.json') if p['arm']=='complete_resource_native_then_current_STA_native')
files=[Path(__file__).resolve(),D/'actual_route_tree_identity.py',D/'complete_flow_equivalence_v1.py',case/'completion.json',old_actor/'completion.json']
comparisons={}
for name,left,right,physical in [
 ('fresh_initial',complete['initial_state'],str(old_actor/'initial'),False),
 ('resource_final',complete['resource_final_state'],old_complete['final_state'],True),
 ('timing_final',complete['final_state'],old_point['state'],True)]:
 pair=equal_state(left,right)
 if physical:
  trees=[tree_identity(run_dir(Path(s))/'routed.route') for s in [left,right]]
  assert trees[0].keys()==trees[1].keys()
  differing=[n for n in trees[0] if trees[0][n]!=trees[1][n]]
  pair.update(actual_edge_switch_terminal_trees_exact=not differing,differing_physical_nets=differing)
 else:
  assert all(pair.values());pair['actual_edge_switch_terminal_trees_exact']=True;pair['differing_physical_nets']=[]
 comparisons[name]=dict(left_state=left,right_state=right,**pair)
 for state in [left,right]:
  state=Path(state);files.extend([state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'manifest.json',run_dir(state)/'routed.route'])
 write(out/'progress.json',dict(completed_comparison=name))
write(out/'completion.json',dict(passed=True,comparisons=comparisons,native_calls_new=0,
 source_sha256={str(p):sha(p) for p in files},
 qualification='Read-only identities of actual sealed states: ordered route bytes, order-independent physical edges/switches/terminal mapping and complete native vectors are separate axes. Shared initial physical root is not a new independent sample. Final4wire difference and complete new cold cost remain attached to actual output; no whole-trajectory/one-factor cause, serialization equivalence, history effect or matched full runtime inferred from these endpoint comparisons.'))
print(dict(passed=True,comparisons=comparisons),flush=True)
