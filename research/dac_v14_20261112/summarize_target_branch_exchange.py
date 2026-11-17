"""Apply the registered resource policy to the two observed TPU routes."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from resource_opportunity_census import stream_trace
from multiobjective_acceptance_v2 import decide
from endpoint_timing_policy_streaming_v2 import compare

base = D/'structural_p1_sta_01'
x = base/'tpu_target_branch_exchange_01'
p = read(x/'plan.json')
native = x/'native'
build = read(x/'completion.json')
reg = read(native/'registration.json')['roles']['joint_native']
assert set(map(tuple,build['allowed_changed_connections'])) == {
    (int(n),pin) for n,pins in reg['removed_pins'].items() for pin in pins}
g = p['group']
assert reg['queries'] == g['queries']
root = Path(reg['state'])
obs = x/'observation'
nat = native/'joint_native_evaluation'
paths = [x/'plan.json', x/'completion.json', native/'registration.json', native/'completion.json',
         native/'joint_native_audit/analysis.json', native/'joint_native_decisions.json',
         x/'observation_cost/completion.json', x/'native_cost/completion.json']
assert read(native/'completion.json')['passed']
assert all(read(obs/'completion.json')['checks'].values())
assert sha(obs/'runs/state/routed.route') == build['candidate_sha256']
before = read(root/'endpoint_vector.json')
frontier = read(base/'TPU_OWNER_FRONTIERS.json')['rows'][p['rank']]
gateway = next(e['node'] for edges in frontier['boundary'].values() for e in edges
               if e['occupants']==[g['target_net']] and e['node'] in frontier['retained_target']
               and e['node'] not in frontier['target_witness'])
cert = next(c for c in read(base/'tpu_like.small.os-owner/certificates.json') if c['net']==g['target_net'])
node_ids = set(cert['cross_exits']) | {g['escape_node'],gateway}
def occupancy(path):
    result = {n:[] for n in sorted(node_ids)}
    for row in stream_trace(path):
        for n in node_ids.intersection(t.inode for t in row['trace']):
            result[n].append(row['net'])
    return result

rows = {}
for label,state in [('native',nat), ('branch_exchange',obs)]:
    rd = state/'runs/state'
    for f in ['packed.net','placed.place']:
        assert sha(rd/f)==sha(root/'runs/state'/f)
    physical=read(rd/'independent_audit.json')
    assert physical['audit']['passed'] and read(state/'completion.json')['passed']
    m=physical['physical_metrics']
    axes=dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'],
              SB_pairs=m['sb_pairs_used'],CB_sources=m['cb_crossing_output_sources_used'])
    vec=read(state/'endpoint_vector.json')
    policy=decide('resources_under_timing',before,vec,build['original_resources'],axes,
                  cpd_limit_s=reg['original_budget']['CPD_s'],resource_limits=reg['fixed_resource_limits'],
                  native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
    if label=='native':
        assert policy==read(native/'joint_native_decisions.json')['resources_under_timing']
    else:
        assert axes==build['structural_full_route_resources']
    rows[label]=dict(cpd_ns=vec['cpd_s']*1e9,resources=axes,policy=policy,holders=occupancy(rd/'routed.route'))
    paths.extend([state/'completion.json',state/'endpoint_vector.json',rd/'routed.route',rd/'independent_audit.json'])
pair = compare(read(nat/'endpoint_vector.json'),read(obs/'endpoint_vector.json'))
assert pair['compatible']
assert rows['native']['holders'][gateway]==[g['target_net']]
assert rows['branch_exchange']['holders'][gateway]==[g['owner_net']]
assert rows['native']['holders'][g['escape_node']]==[g['owner_net']]
assert rows['branch_exchange']['holders'][g['escape_node']]==[g['target_net']]
res=dict(rank=p['rank'],scope=build['allowed_changed_connections'],rows=rows,
         native_to_exchange=pair,anchor=reg['original_budget'],caps=reg['fixed_resource_limits'],
         construction_seconds=build['complete_construction_seconds'],
         observation_command_seconds=read(x/'observation_cost/completion.json')['complete_command_wall_seconds'],
         native_command_seconds=read(x/'native_cost/completion.json')['complete_command_wall_seconds'],
         source_sha256={str(f):sha(f) for f in [*paths,base/'TPU_OWNER_FRONTIERS.json',Path(__file__)]},
         qualification='Selected two-net development contrast, shared input and permitted pins. Construction and connection order differ. Costs are scoped; neither historical total nor a paired full-flow ratio.')
write(x/'PAIR.json',res)
print({k:v for k,v in pair.items() if k!='changes'}, rows['branch_exchange']['holders'])
