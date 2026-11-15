"""Reproduce fixed decisions and inspect actual ownership transfer across the certified cut."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import compare
from multiobjective_acceptance_v2 import decide
from state_resource_assurance import resource_assurance,require_publication_proof
from run_native_scope_policy_v4 import run_dir
from resource_opportunity_census import stream_trace

archive=D/'multiobjective_R1_joint_owner_escape_01';out=archive/'verification.json';assert not out.exists()
c=read(archive/'completion.json');assert c['passed']
assert all(sha(archive/n)==h for n,h in c['artifact_sha256'].items())
assert all(sha(f)==h for f,h in c['source_sha256'].items())
points=read(archive/'points.json');old=read(Path(c['parent'])/'points.json');byid={r['id']:r for r in points};assert len(byid)==len(points)==576
keys={'quality_dominated_by','nominal_quality_dominated_by','matched_time_dominated_by','quality_projection_retained','quality_status','candidate_retention','archive_retained','record_preserved','five_dimensional_comparison_count','retention_qualification'}
for r in old:assert {k:v for k,v in r.items() if k not in keys}=={k:v for k,v in byid[r['id']].items() if k not in keys}
case=D/'R1_owner_release_joint_probe_01';reg=read(case/'transaction/registration.json');selection=read(case/'selection.json');added=[byid[i] for i in c['added']]
assert len(added)==2 and len({r['route_sha256'] for r in added})==1
for r in added:
 state=Path(r['state']);name=r['arm'].removeprefix('R1_owner_escape_');role=reg['roles'][name];source=Path(role['state'])
 before,after=[read(x/'endpoint_vector.json') for x in [source,state]]
 assert all(before[k]==after[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
 assert require_publication_proof(state)['passed']
 br=resource_assurance(source)['resource_axes'];ar=resource_assurance(state)['resource_axes']
 decision=decide('resources_under_timing',before,after,br,ar,cpd_limit_s=role['original_budget']['CPD_s'],resource_limits=role['fixed_resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
 assert decision==r['acceptance']['resources_under_timing'] and decision['accepted']
 assert ar==dict(wirelength=2070653,SB_pairs=32,CB_sources=5071)
 assert br==dict(wirelength=2070629,SB_pairs=33,CB_sources=5071)
 assert r['quality_status']=='nondominated_in_collected_population'
 assert r['complete_single_configuration_seconds'] is None and not r['committed_to_historical_actor']
cut=read(D/'R1_single_net_vertical_local_minimum_01/completion.json');assert cut['passed'] and cut['terminal_layer_lower_bound']==5103
source=Path(added[0]['source_state']);final=Path(added[0]['state']);target=selection['target_net'];owner=selection['selected']['owner_net'];escape=selection['selected']['escape_node']
footprints=[];terminals=[]
for state in [source,final]:
 footprints.append({});terminals.append({})
 for record in stream_trace(run_dir(state)/'routed.route'):
  if record['net'] not in [target,owner]:continue
  footprints[-1][record['net']]={n.inode for n in record['trace']}
  terminals[-1][record['net']]={(n.pin,n.inode) for n in record['trace'] if n.kind=='SINK'}
assert terminals[0]==terminals[1]
assert escape in footprints[0][owner] and escape not in footprints[0][target]
assert escape not in footprints[1][owner] and escape in footprints[1][target]
write(out,dict(passed=True,records=576,added=2,parent_non_derived_fields_exact=True,actual_full_vectors_exact_to_source=True,original_fixed_budget_decisions_reproduced=True,actual_route_bytes_same_in_both_arms=True,quality_nondominated=True,new_aggregate_vertical_resource_sum=5103,certified_terminal_lower_bound=5103,actual_escape_transfer=dict(node=escape,from_owner=owner,to_target=target,fixed_sinks_exact=True),complete_measured_configurations_total=24,native_calls_new=0,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),archive/'completion.json',case/'verification.json',case/'selection.json',D/'R1_single_net_vertical_local_minimum_01/completion.json',run_dir(source)/'routed.route',run_dir(final)/'routed.route']},qualification='Actual ownership transfer across the formerly saturated single-net cut, not only scope correlation. Both native/domain arms converge to identical routes and exact original vectors; no incremental domain benefit. Shared scope time remains outside per-arm complete costs; old actor unchanged.'))
print(dict(passed=True,records=576,nondominated=True,actual_escape_owner_transfer=True,vertical_bound_attained=True,native_calls_new=0),flush=True)
