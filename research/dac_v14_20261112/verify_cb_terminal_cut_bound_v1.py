"""Certify a CB occupancy bound from fixed terminal layers and unit capacities."""
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS
from resource_opportunity_census import stream_trace

case=D/'complete_serial_architecture_transfer_01/cb_native'
proof=read(case/'explicit_policy_verification.json');assert proof['passed']
assert all(sha(f)==h for f,h in proof['source_sha256'].items())
state=Path(proof['final_state']);rd=run_dir(state);m=read(rd/'manifest.json')
assert m['metrics']['native_full_check_passed'] and read(rd/'independent_audit.json')['audit']['passed']
cmd=m['command'];graph=Path(cmd[cmd.index('--read_rr_graph')+1]);cache=FullRouteGraphCache(graph,case/'flow/full_graph_cache');g=cache.g
assert np.array_equal(g.nodes[:,4],g.nodes[:,7]),'A layer-spanning node invalidates this cut proof'
assert set(map(int,np.unique(g.nodes[:,4])))=={0,1}
opin=KINDS.index('OPIN');cross_sources=set();cross_edges=0
for start in range(0,len(g.edges),500000):
    pair=g.edges[start:start+500000]//g.stride;u=(pair//g.n).astype(np.int64);v=(pair%g.n).astype(np.int64)
    mask=g.nodes[u,4]!=g.nodes[v,4];cu=u[mask];cv=v[mask]
    assert np.all(g.nodes[cu,1]==opin),'Non-CB layer crossing exists'
    assert np.all(np.isin(g.nodes[cv,1],[KINDS.index('CHANX'),KINDS.index('CHANY')]))
    assert np.all(g.nodes[cu,0]==1),'One crossing source could otherwise serve multiple nets'
    cross_sources.update(map(int,cu));cross_edges+=len(cu)
assert cross_edges>0
rows=[];all_used=set();mandatory=0;observed_occupancy=0
for record in stream_trace(rd/'routed.route'):
    trace=record['trace']
    if not trace:continue
    assert trace[0].kind=='SOURCE';root=trace[0].inode
    sinks=sorted({(n.pin,n.inode) for n in trace if n.kind=='SINK'})
    assert sinks and all(pin is not None and pin>0 for pin,_ in sinks)
    terminal_layers={int(g.nodes[root,4])}|{int(g.nodes[node,4]) for _,node in sinks}
    required=int(len(terminal_layers)>1);used=set()
    for first,second in zip(trace,trace[1:]):
        if first.switch!=-1 and g.nodes[first.inode,4]!=g.nodes[second.inode,4]:
            assert first.kind=='OPIN' and first.inode in cross_sources;used.add(first.inode)
    assert len(used)>=required
    assert not all_used.intersection(used),'Observed unit-capacity crossing sources are shared across nets'
    all_used.update(used);mandatory+=required;observed_occupancy+=len(used)
    rows.append(dict(net=record['net'],fixed_source=root,fixed_pin_sink_ids=sinks,terminal_layers=sorted(terminal_layers),required_crossing_sources=required,actual_crossing_sources=sorted(used)))
metrics=read(rd/'independent_audit.json')['physical_metrics']
assert mandatory==observed_occupancy==len(all_used)==metrics['cb_crossing_output_sources_used']==982
assert metrics['sb_pairs_used']==0
out=D/'cb_terminal_cut_bound_01';out.mkdir(exist_ok=False);write(out/'terminal_cut_witnesses.json',rows)
files=[Path(__file__).resolve(),case/'explicit_policy_verification.json',state/'completion.json',rd/'manifest.json',rd/'routed.route',rd/'independent_audit.json',case/'flow/graph_audit_cache/completion.json',case/'flow/full_graph_cache/completion.json',out/'terminal_cut_witnesses.json']
write(out/'completion.json',dict(passed=True,native_calls_new=0,fixed_terminal_nets=len(rows),nets_requiring_a_layer_crossing=mandatory,
    graph_crossing_edges=cross_edges,graph_crossing_sources=len(cross_sources),all_layer_crossings_are_unit_capacity_CB_sources=True,
    CB_occupancy_lower_bound=mandatory,observed_CB_occupancy=observed_occupancy,bound_attained=True,
    source_sha256={str(f):sha(f) for f in files},
    proof='Every counted non-global net with fixed terminals on both layers requires a layer-crossing edge. All graph crossings leave unit-capacity OPIN nodes, so different nets cannot share a counted CB source. At least one distinct source per crossing net is necessary. The actual legal route attains that sum,982, with zero SB resources in this graph.',
    qualification='Exact vertical-occupancy bound for the supplied two-layer CB-only graph, counted non-global net set and immutable packed/placed terminal RR mapping. This proves no vertical-count reduction under those fixed inputs; it is not a timing or wire bound, initial-routability guarantee, routing-global optimum, or bound after changing architecture, packing, placement or terminal mapping. Read-only one-time graph/route certificate, not measured algorithm work or a new benchmark sample.'))
print(dict(passed=True,mandatory_crossing_nets=mandatory,actual_CB=observed_occupancy,vertical_bound_attained=True),flush=True)
