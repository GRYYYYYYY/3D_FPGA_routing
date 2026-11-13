#!/usr/bin/env python3
import collections,math,resource,signal,statistics
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import graph_records,f32
from analyze_search_domain_v2 import inside

def parse(path):
    rows={};edges=collections.defaultdict(list)
    for l in path.read_text().splitlines():
        v=l.split();key=(int(v[1]),int(v[2]))
        if v[0]=='RESULT':
            assert key not in rows
            opt=lambda x:None if x=='-' else float(x)
            rows[key]=dict(search=key[0],arm='Q0' if key[1]==0 else 'Qh',stop=int(v[3]),expansions=int(v[4]),labels=int(v[5]),peak_heap=int(v[6]),upper_seconds=opt(v[7]),physical_seconds=opt(v[8]),lower_seconds=opt(v[9]),query_seconds=float(v[10]),edges=int(v[11]))
        else:
            assert v[0]=='EDGE' and int(v[3])==len(edges[key]);edges[key].append((int(v[4]),int(v[5]),float(v[6]),float(v[7])))
    for key,r in rows.items():assert len(edges[key])==r['edges']
    return rows,edges

def near(a,b):return a==b or math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-24)
def main():
    resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
    b=D/'residual_query_offline_01';exec=read(b/'execution.json');assert all(sha(p)==h for p,h in exec['source_sha256'].items());assert all(sha(b/n)==h for n,h in exec['output_sha256'].items())
    rows,paths=parse(b/'query_stdout.log');cases={int(c['domain']['search']):c for c in read(b/'cases.json')};assert len(rows)==2*len(cases)==62
    wanted=set();wanted_edges=set();wanted_nodes=set()
    graph=Path(next(p for p in exec['source_sha256'] if p.endswith('rr_graph.xml')));nreal=read(b/'graph_binding.json')['nodes']
    for path in paths.values():
        for u,v,w,t in path:
            assert t==0
            if v!=nreal:wanted_edges.add((v,u,w));wanted_nodes.update([u,v])
            else:wanted_nodes.add(u)
    nodes={};found=set();switch={};total_layers=0
    for section,e in graph_records(graph):
        at=e.attrib
        if section=='switches':t=e.find('timing');v={} if t is None else t.attrib;switch[int(at['id'])]=f32(v.get('Tdel',0))
        elif section=='rr_nodes':
            n=int(at['id']);v=e.find('loc').attrib;layer=int(v.get('layer_low',v.get('layer',0)));total_layers=max(total_layers,layer+1)
            if n in wanted_nodes:nodes[n]=dict(layer=layer,direction=at.get('direction','NONE'),**{k:int(v[k]) for k in ['xlow','xhigh','ylow','yhigh']})
        elif section=='rr_edges':
            item=(int(at['src_node']),int(at['sink_node']),switch[int(at['switch_id'])])
            if item in wanted_edges:found.add(item)
    assert wanted_edges==found
    observations=[]
    for key,r in sorted(rows.items()):
        case=cases[r['search']];c=case['domain'];oracle=case['oracle'];seeds={}
        for s in case['seeds']:
            if s['layer']!=int(c['sink_layer']):continue
            seeds[s['node']]=min(seeds.get(s['node'],math.inf),s['delay'])
        opt=oracle['no_cross_BB_seconds'];path=paths[key];upper=r['upper_seconds'];lower=r['lower_seconds'];assert r['expansions']<=256 and r['labels']<=16384 and r['peak_heap']<=65536
        assert (upper is None)==(not path);r['chosen_seed']=None
        if upper is not None:
            assert opt is not None and upper+1e-24>=opt;assert near(upper,r['physical_seconds']);assert path[0][0]==int(c['sink']) and path[-1][1]==nreal
            assert len({p[0] for p in path})==len(path)
            assert all(a[1]==z[0] for a,z in zip(path,path[1:]));assert path[-1][0] in seeds and path[-1][2]==seeds[path[-1][0]]
            for u,v,w,t in path[:-1]:assert (v,u,w) in found and nodes[u]['layer']==nodes[v]['layer']==int(c['sink_layer']) and inside(nodes[u],c,total_layers) and inside(nodes[v],c,total_layers)
            assert near(sum(w for u,v,w,t in path),upper);r['chosen_seed']=path[-1][0]
        if lower is not None and opt is not None:assert lower<=opt+1e-24
        if r['stop']==0:assert upper is not None and near(upper,opt) and near(lower,opt)
        if r['stop']==2:assert opt is None and upper is None
        r.update(guide=oracle['guide'],criticality=oracle['criticality'],oracle_seconds=opt,relative_gap=(upper/opt-1) if upper is not None and opt else None,legacy4096_seconds=oracle['no_cross_legacy4096_seconds'],legacy_known_seeds=oracle['bounded_known_sink_layer_seeds']);observations.append(r)
    summaries={}
    for arm in ['Q0','Qh']:
        rs=[r for r in observations if r['arm']==arm];good=[r for r in rs if r['upper_seconds'] is not None];gs=[r for r in rs if r['guide']];summaries[arm]=dict(requests=len(rs),finite_oracle=sum(r['oracle_seconds'] is not None for r in rs),paths=len(good),exact=sum(r['stop']==0 for r in rs),stop_counts=dict(collections.Counter(r['stop'] for r in rs)),guided_requests=len(gs),guided_paths=sum(r['upper_seconds'] is not None for r in gs),expansions=sum(r['expansions'] for r in rs),labels=sum(r['labels'] for r in rs),query_seconds=sum(r['query_seconds'] for r in rs),gap_max=max((r['relative_gap'] for r in good if r['relative_gap'] is not None),default=None))
    binding={str(p):sha(p) for p in [Path(__file__),Path(parse.__code__.co_filename),b/'execution.json',b/'query_stdout.log',b/'cases.json',graph]};write(b/'analysis.json',dict(passed=True,status='sealed_actual_graph_residual_multitarget_query',source_sha256=binding,summaries=summaries,rows=observations,real_directed_edges_checked=len(found),native_route_calls=0,qualification='Fixed256 per actual seed-group; virtual terminal prefix is not an RR edge. Every actual returned real edge/weight independently checked on RRG, BB/layer and saved seed prefix checked; EXACT/lower claims compared to sealed independent full Dijkstra. Spatial heuristic only orders work. Thirty-one posthoc focus trajectory groups, one circuit; no native QoR/runtime/complete legal-extension or finalSTA claim. Labels/time include virtual prefix bookkeeping and UBSan; offline graph export excluded from query_seconds.'))
    print(summaries)
if __name__=='__main__':main()
