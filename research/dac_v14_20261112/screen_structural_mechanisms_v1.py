"""Current physical prerequisites for domain/owner work, without inventing STA.

This diagnostic does not replace the controller's current slack screen, native
search, whole-route legality/STA, or acceptance. Historical roots are diagnostic
inputs only; new full-method pairs still start with fresh routing.
"""
import argparse,collections,os,resource,time
from pathlib import Path
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import numpy as np
from retained_prefix_workflow import D,read,write,sha,route_body
from resource_opportunity_census import stream_trace,tree_data,release_scope,wire_units
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS

def screen(run,cache_directory,output):
    start=time.monotonic();run=Path(run).resolve();out=Path(output).resolve();out.mkdir(exist_ok=False)
    m=read(run/'manifest.json');files=[Path(__file__).resolve(),D/'resource_opportunity_census.py',run/'manifest.json',run/'packed.net',run/'placed.place']
    for name in ['packed.net','placed.place']:assert sha(run/name)==m['outputs'][name]['sha256']
    if not (m['status']=='completed' and m['metrics'].get('native_full_check_passed') and m['metrics'].get('routing_success_reported')):
        result=dict(passed=True,status='initial_route_failed_no_legal_repair_root',historical_returncode=m.get('returncode'),native_calls_new=0,legal_quality=None,mechanism_decision='No legal route available; no sharing/owner eligibility inferred',source_sha256={str(f):sha(f) for f in files})
        write(out/'completion.json',result);return result
    route=run/'routed.route';assert sha(route)==m['outputs']['routed.route']['sha256']
    original=read(run/'independent_audit.json');assert original['audit']['passed'] and original['audit']['inputs']['route_sha256']==sha(route)
    graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);cache=FullRouteGraphCache(graph,cache_directory);g=cache.g
    assert cache.receipt['parent']['graph_sha256']==m['shared_inputs'][str(graph)]['sha256']
    occupancy=np.zeros(g.n,dtype=np.uint32);owners=np.full(g.n,-1,dtype=np.int64)
    counters=collections.Counter();sb=collections.Counter();cb=collections.Counter();wire=0;scopes=[];potentials=[]
    def metadata(u):
        a=g.nodes[u];return dict(kind=KINDS[int(a[1])],low=tuple(map(int,a[2:5])),high=tuple(map(int,a[5:8])),direction=cache.meta['directions'][int(cache.extra[u,0])])
    def adj(u):
        lo,hi=np.searchsorted(g.edges,[u*g.n*g.stride,(u+1)*g.n*g.stride]);return sorted(set(map(int,(g.edges[lo:hi]//g.stride)%g.n)))
    for row in stream_trace(route):
        if not row['trace']:continue
        tree=tree_data(row['trace'],metadata);used=np.fromiter(tree['used'],dtype=np.int64)
        g.require_edges({(up,node,sw) for node,(up,sw) in tree['parent'].items()})
        occupancy[used]+=1;unit=used[g.nodes[used,0]==1]
        assert np.all(owners[unit]==-1),'Unit capacity overuse';owners[unit]=row['net']
        sb.update(tree['SB']);cb.update(tree['CB']);wire+=sum(wire_units(metadata(n)) for n in tree['used']);counters['routed_nets']+=1
        count=len(tree['SB'])+len(tree['CB']);reference=tree['layer_cut_reference']
        counters['terminal_cut_reference_sum']+=reference;counters['crossing_net_occupancy']+=count
        if count<=reference:continue
        counters['positive_crossing_excess_nets']+=1
        groups=collections.defaultdict(set)
        for node,edge in tree['crossing'].items():groups[edge['resource_kind'],edge['resource']].update(tree['descendants'][node])
        seen=set()
        for targets in groups.values():
            key=tuple(sorted(targets))
            if key in seen:continue
            seen.add(key);released=release_scope(tree,targets,metadata)
            freed=len(released['released_SB'])+len(released['released_CB']);kept=(tree['SB']-set(released['released_SB']))|(tree['CB']-set(released['released_CB']))
            if freed and kept:scopes.append(dict(net=row['net'],pins=sorted(targets),released_crossings=freed,retained_crossing_sources=sorted(kept),STA_screen='unavailable_not_assumed',final_feasibility='unverified'))
        z=metadata(tree['root'])['low'][2]
        if any(metadata(n)['low'][2]==z for n in tree['sinks'].values()):
            potentials.append(dict(net=row['net'],source=tree['root'],source_layer=z,current_crossings=count,terminal_cut_reference=reference,target_pins=sorted(tree['sinks'])))
    assert np.all(occupancy<=g.nodes[:,0]),'Actual current route exceeds capacity'
    actual=dict(planar_wirelength_excluding_sb_half_nodes=wire,sb_pairs_used=len(sb),sb_pair_net_occupancy=sum(sb.values()),cb_crossing_output_sources_used=len(cb),cb_crossing_output_source_net_occupancy=sum(cb.values()))
    assert all(original['physical_metrics'][key]==value for key,value in actual.items()),'Independent physical recount differs'
    certificates=[];classes=[]
    for candidate in potentials:
        source=candidate['source'];children=adj(source);label={k:candidate[k] for k in ['net','current_crossings','terminal_cut_reference']}
        if metadata(source)['kind']!='SOURCE' or len(children)!=1 or metadata(children[0])['kind']!='OPIN':
            classes.append(dict(label,status='unsupported_source_fanout'));continue
        opin=children[0];neighbors=adj(opin);z=candidate['source_layer']
        local=[n for n in neighbors if metadata(n)['low'][2]==z];cross=[n for n in neighbors if metadata(n)['low'][2]!=z]
        if not local or not cross or any(metadata(n)['kind'] not in ['CHANX','CHANY'] for n in neighbors) or any(int(g.nodes[n,0])!=1 for n in local):
            classes.append(dict(label,status='unsupported_OPIN_exit_cut'));continue
        if any(owners[n] in [-1,candidate['net']] for n in local):
            classes.append(dict(label,status='local_exit_not_entirely_blocked_by_others'));continue
        assert candidate['current_crossings']>=2
        cert=dict(candidate,only_OPIN=opin,local_exits=[dict(node=n,owner_net=int(owners[n]),capacity=1) for n in local],cross_exits=cross,minimum_frozen_other_route_crossings=2,STA_screen='unavailable_not_assumed')
        certificates.append(cert);classes.append(dict(label,status='frozen_other_routes_force_two_distinct_crossing_resources'))
    counts=dict(counters,structural_sharing_scopes=len(scopes),structural_sharing_nets=len({r['net'] for r in scopes}),supported_owner_escape_certificates=len(certificates),owner_topology_classifications=dict(collections.Counter(r['status'] for r in classes)))
    decision=dict(domain='needs_current_STA_screen' if scopes else 'no_structural_sharing_scope_on_this_root',owner='needs_target_and_owner_current_STA_screen' if certificates else 'no_supported_blocked_source_escape_cut_on_this_root',failure_release='only_after_actual_guided_search_failure_not_predictable_from_this_census',timing='needs_current_full_STA_and_current_path_feedback')
    write(out/'scopes.json',scopes);write(out/'owner_certificates.json',certificates);write(out/'owner_classifications.json',classes);write(out/'cache_identity.json',cache.receipt)
    files += [route,run/'independent_audit.json',graph,cache.directory/'completion.json',D/'full_route_graph_cache.py',D/'immutable_rr_audit_cache.py']
    result=dict(passed=True,status='legal_historical_root_structural_screen',input_run=str(run),route_sha256=sha(route),route_body_sha256=route_body(route),graph_sha256=sha(graph),physical_metrics=actual,counts=counts,mechanism_decision=decision,all_current_edges_and_capacities_checked=True,current_STA_available=(run/'native_sta_frontier.jsonl').exists(),STA_screen_performed=False,native_calls_new=0,new_full_method_outcomes=0,source_sha256={str(f):sha(f) for f in files},artifact_sha256={n:sha(out/n) for n in ['scopes.json','owner_certificates.json','owner_classifications.json','cache_identity.json']},complete_read_only_seconds=time.monotonic()-start,qualification='Structural/capacity prerequisites on exact historical legal roots. Slack eligibility, native replacement feasibility, failure-release usefulness and final improvements are not inferred. Removal counts overlap and are not additive savings. Current controller scheduling unchanged. This is not a full method or an independently routed confirmation result; no measured algorithm cost is assigned.')
    write(out/'completion.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--full-graph-cache',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3))
    r=screen(a.run,a.full_graph_cache,a.output);print({k:r[k] for k in ['passed','status','counts','mechanism_decision'] if k in r},flush=True)
