"""Explain actual release events using exact fixed-owner and directional cuts.

This proves only a conditional obstruction for a declared transaction/domain.
It does not predict unrestricted search quality or replace the queued ablation.
"""
import collections,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from resource_opportunity_census import stream_trace
from coordinated_repair_tree import from_trace,prune_sinks
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS

b=D/'robot_release_capacity_cut_01';b.mkdir(exist_ok=False);start=time.monotonic()
prior=D/'structural_input_screen_01/heldout_robot_rl_s21_hybrid_o_n60_w100_p0_a0'
screen=read(prior/'completion.json');assert screen['passed'] and all(sha(prior/n)==h for n,h in screen['artifact_sha256'].items())
domain=D/'complete_serial_additional_circuits_01/robot_rl_domain/flow/repair/round_000/candidate_00'
native=D/'complete_serial_additional_circuits_01/robot_rl_native/flow/repair/round_000/candidate_00'
role=read(domain/'registration.json')['roles']['reuse_on'];source=Path(role['source']);manifest=read(source/'manifest.json')
assert route_body(source/'routed.route')==screen['route_body_sha256']
assert all(sha(path)==h for path,h in role['source_sha256'].items())
graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);cache=FullRouteGraphCache(graph,D/'complete_serial_additional_circuits_01/robot_rl_native/flow/full_graph_cache');g=cache.g
assert sha(graph)==screen['graph_sha256']
log=domain/'reuse_on/runs/state/vertical_domain.log';logs=[line.split() for line in log.read_text().splitlines()]
assert logs[-1][0]=='COMPLETE' and logs[-1][-1]=='occupancy_restored'
releases={int(r[1]):int(r[2]) for r in logs if r[0]=='RELEASE'};certs={c['net']:c for c in read(prior/'owner_certificates.json')}
assert len(releases)==sum(r[0]=='RELEASE' for r in logs)
selected=set(map(int,role['removed_pins']));traces={r['net']:r['trace'] for r in stream_trace(source/'routed.route') if r['net'] in selected}
def adj(u):
    lo,hi=__import__('numpy').searchsorted(g.edges,[u*g.n*g.stride,(u+1)*g.n*g.stride]);return list(map(int,(g.edges[lo:hi]//g.stride)%g.n))
def layer(node):return int(g.nodes[node,4])
def kind(node):return KINDS[int(g.nodes[node,1])]
owners=collections.defaultdict(set)
for row in stream_trace(source/'routed.route'):
    for node in {n.inode for n in row['trace']}:owners[node].add(row['net'])
native_audit=read(native/'reuse_off_audit/analysis.json');domain_audit=read(domain/'reuse_on_audit/analysis.json')
assert native_audit['passed'] and domain_audit['passed']
candidates={label:{r['net']:r['trace'] for r in stream_trace(audit['candidate_route']) if r['net'] in selected} for label,audit in [('native',native_audit),('domain_release',domain_audit)]}
rows=[]
for net,pin in sorted(releases.items()):
    cert=certs[net];tree=from_trace(traces[net],g.switches);retained=prune_sinks(tree,role['removed_pins'][str(net)])
    z=cert['source_layer'];children=adj(cert['source']);assert children==[cert['only_OPIN']]
    neighbors=adj(cert['only_OPIN']);local=[n for n in neighbors if layer(n)==z];cross=[n for n in neighbors if layer(n)!=z]
    assert set(local)=={x['node'] for x in cert['local_exits']} and set(cross)==set(cert['cross_exits'])
    assert all(kind(n) in ['CHANX','CHANY'] for n in neighbors)
    for exit in cert['local_exits']:
        node,owner=exit['node'],exit['owner_net'];assert int(g.nodes[node,0])==1 and owners[node]=={owner}
        assert owner not in selected,'Proof requires blocker trees outside the entire joint transaction'
    expected={up for node,(up,sw,delay) in retained['edges'].items() if layer(node)!=layer(up)}
    logged=next(r for r in logs if r[0]=='ALLOW' and int(r[1])==net and int(r[2])==pin)
    assert len(expected)==int(logged[3]) and expected==set(map(int,logged[4:]))
    assert expected and all(layer(n)==z for n in expected),'No permitted opposite-layer crossing source is required for this certificate'
    assert all(layer(n)==z for n in [cert['source'],cert['only_OPIN']])
    assert pin in role['removed_pins'][str(net)] and layer(tree['sinks'][pin])==z
    assert not any(kind(n) in ['CHANX','CHANY'] and layer(n)==z for n in retained['edges']), 'Retained same-layer anchors require a more general proof'
    final=[]
    for label,trees in candidates.items():
        trace=trees[net];edges={(a.inode,c.inode,a.switch) for a,c in zip(trace,trace[1:]) if a.switch!=-1}
        g.require_edges(edges);crossings={u for u,v,sw in edges if layer(u)!=layer(v)}
        assert len(crossings)>=2
        final.append(dict(arm=label,crossing_sources=sorted(crossings),crossing_count=len(crossings)))
    rows.append(dict(net=net,first_released_pin=pin,source_layer=z,retained_allowed_crossing_sources=sorted(expected),fixed_external_blockers=cert['local_exits'],removed_target_pin_layer=z,conditional_domain_infeasible=True,conditional_minimum_unrestricted_crossings=2,actual_candidates=final,proof='Every same-layer OPIN exit remains occupied at capacity by a net outside the joint transaction. Any legal target path must first cross away. Its sink is on the source layer, but the retained domain permits only sources on that source layer, so a return crossing is forbidden. Releasing the domain removes that restriction without freeing the external owners.'))
assert {r['net'] for r in rows}==set(releases)==set(certs)
write(b/'cuts.json',rows)
files=[Path(__file__).resolve(),prior/'completion.json',prior/'owner_certificates.json',domain/'registration.json',source/'routed.route',source/'manifest.json',log,native/'reuse_off_audit/analysis.json',domain/'reuse_on_audit/analysis.json',Path(native_audit['candidate_route']),Path(domain_audit['candidate_route']),cache.directory/'completion.json',D/'robot_domain_first_scope_analysis_02/completion.json']
write(b/'completion.json',dict(passed=True,actual_initial_route_body_matches_structural_screen=True,actual_releases=len(releases),certified_domain_obstructions=len(rows),fixed_external_owners_verified=True,actual_candidates_respect_frozen_owner_bound=True,native_calls_new=0,new_independent_inputs=0,source_sha256={str(f):sha(f) for f in files},artifact_sha256={'cuts.json':sha(b/'cuts.json')},complete_read_only_seconds=time.monotonic()-start,qualification='Conditional impossibility for the exact declared retained-source domain and fixed outside-owner scope, not mathematical infeasibility of unrestricted routing or a proof of why a heuristic internally stopped. Both released nets retain at least two crossings in actual native/domain-release candidates. Domain benefit on net3140 and blocked-owner escape are distinct mechanisms. Registered no-release native ablation remains necessary and unexecuted. No complete cost or universal applicability claim.'))
print(dict(passed=True,released_nets=sorted(releases),conditional_cut_certificates=len(rows),native_calls_new=0),flush=True)
