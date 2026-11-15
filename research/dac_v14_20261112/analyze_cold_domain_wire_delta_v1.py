"""Explain actual checkpoint wire deltas without assigning whole cost or causes."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from actual_route_tree_identity import tree_identity
from resource_opportunity_census import stream_trace, wire_units
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof
from endpoint_timing_policy import compare

out=D/'cold_domain_wire_delta_analysis_01';out.mkdir(exist_ok=False)
protocol=D/'cold_domain_timing_protocol_identity_01/completion.json';observed=read(protocol)
assert observed['passed'] and observed['actual_transactions_compared']==3
old_actor=D/'completed_resource_timing_dev_01/paired'
new_actor=D/'complete_resource_timing_full_flow_01/bnn_domain/flow/timing'
states=dict(old_initial=Path(read(old_actor/'registration.json')['initial_state']),
    cold_initial=Path(read(new_actor/'registration.json')['initial_state']),
    old_after_three=old_actor/'round_002/proposal_01/transaction/current_group_evaluation',
    cold_after_three=new_actor/'round_002/proposal_01/transaction/current_group_evaluation')
cache_dir=D/'complete_resource_timing_full_flow_01/bnn_domain/flow/resource_flow/full_graph_cache'
run=run_dir(states['cold_initial']);m=read(run/'manifest.json')
graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);cache=FullRouteGraphCache(graph,cache_dir)
g=cache.g
initial_diff=set(observed['initial_source_physical_different_nets'])
after_diff=set(observed['after_three_actual_transactions_physical_different_nets'])
files=[Path(__file__).resolve(),D/'resource_opportunity_census.py',D/'actual_route_tree_identity.py',
       protocol,cache_dir/'completion.json']
axes={label:require_publication_proof(state)['resource_axes'] for label,state in states.items()}
vectors={label:read(state/'endpoint_vector.json') for label,state in states.items()}
wire={}
for label,state in states.items():
    run=run_dir(state);wanted=initial_diff if label.endswith('initial') else after_diff
    wire[label]={}
    for row in stream_trace(run/'routed.route'):
        if row['net'] not in wanted:continue
        units=0
        for node in {r.inode for r in row['trace']}:
            a=g.nodes[node]
            units+=wire_units(dict(kind=KINDS[int(a[1])],low=tuple(map(int,a[2:5])),high=tuple(map(int,a[5:8])),
                                   direction=cache.meta['directions'][int(cache.extra[node,0])]))
        wire[label][row['net']]=units
    assert set(wire[label])==wanted
    files += [state/'completion.json',state/'endpoint_vector.json',run/'manifest.json',run/'routed.route',run/'independent_audit.json']
# Independently recompute final serialized physical identities rather than
# relying exclusively on the incremental NODE-protocol reconstruction.
left,right=[tree_identity(run_dir(states[k])/'routed.route') for k in ['old_after_three','cold_after_three']]
assert left.keys()==right.keys()
actual_diff={net for net in left if left[net]!=right[net]}
assert actual_diff==after_diff
initial_rows=[dict(net=net,old_wire=wire['old_initial'][net],cold_wire=wire['cold_initial'][net],
                   delta_wire=wire['cold_initial'][net]-wire['old_initial'][net]) for net in sorted(initial_diff)]
after_rows=[dict(net=net,old_wire=wire['old_after_three'][net],cold_wire=wire['cold_after_three'][net],
                 delta_wire=wire['cold_after_three'][net]-wire['old_after_three'][net],
                 already_physically_different_at_timing_input=net in initial_diff) for net in sorted(after_diff)]
initial_delta=axes['cold_initial']['wirelength']-axes['old_initial']['wirelength']
after_delta=axes['cold_after_three']['wirelength']-axes['old_after_three']['wirelength']
assert sum(r['delta_wire'] for r in initial_rows)==initial_delta
assert sum(r['delta_wire'] for r in after_rows)==after_delta
write(out/'initial_net_deltas.json',initial_rows);write(out/'after_three_net_deltas.json',after_rows)
endpoint={label:compare(vectors[old],vectors[cold]) for label,old,cold in
          [('timing_input','old_initial','cold_initial'),('after_three','old_after_three','cold_after_three')]}
write(out/'endpoint_comparison.json',endpoint)
write(out/'completion.json',dict(passed=True,native_calls_new=0,
    actual_timing_transactions_compared=3,whole_cold_case_closed_not_required=True,
    initial_physical_different_nets=len(initial_diff),after_three_physical_different_nets=len(after_diff),
    actual_route_identities_match_protocol_reconstruction=True,
    cold_minus_old_input_wire=initial_delta,cold_minus_old_after_three_wire=after_delta,
    timing_segment_increment_old_wire=axes['old_after_three']['wirelength']-axes['old_initial']['wirelength'],
    timing_segment_increment_cold_wire=axes['cold_after_three']['wirelength']-axes['cold_initial']['wirelength'],
    new_physical_differences_added_by_timing=[r for r in after_rows if r['net'] not in initial_diff],
    input_endpoint_summary={k:v for k,v in endpoint['timing_input'].items() if k!='changes'},
    after_three_endpoint_summary={k:v for k,v in endpoint['after_three'].items() if k!='changes'},
    source_sha256={str(f):sha(f) for f in files},
    artifact_sha256={n:sha(out/n) for n in ['initial_net_deltas.json','after_three_net_deltas.json','endpoint_comparison.json']},
    qualification='Read-only exact per-net planar-wire decomposition from actual independently audited timing input and after-three checkpoint routes, plus independent final physical-tree hashes agreeing with NODE reconstruction. This does not close the cold whole workflow or attach any full time to a historical point. Different initial physical trees/vectors and occupancy persist; KEEP iteration order and request equality do not isolate serialization as a cause or prove hidden-state equivalence. Additional native heap/retry/path differences are observations, not a new seed-policy benefit. No original actor, native search or candidate rerun.'))
print(dict(passed=True,input_wire_delta=initial_delta,after_three_wire_delta=after_delta,
           timing_added_wire_delta=after_delta-initial_delta,new_physical_nets=[r for r in after_rows if r['net'] not in initial_diff]),flush=True)
