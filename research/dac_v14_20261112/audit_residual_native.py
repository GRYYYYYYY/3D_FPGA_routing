#!/usr/bin/env python3
import collections,heapq,math,resource,signal,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import fields,graph_records,f32
from analyze_search_domain_v2 import inside
from analyze_native_reconvergence_v2 import observe
from audit_residual_query_offline import near

def main():
    resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
    b=D/'residual_native_eltwise_dev_01';reg=read(b/'registration.json');assert read(b/'input_seal.json')['passed'];done=read(b/'completion.json');assert done['gate_passed'] and not done['missing_arms']
    dirs={a:b/'runs'/('eltwise_layer_'+a) for a in reg['arms']};logs={a:(rd/'stdout.log').read_text().splitlines() for a,rd in dirs.items()};domains={};queries={};edges={};summaries={};wanted=set()
    bindings={str(p):sha(p) for p in [Path(__file__),Path(near.__code__.co_filename),Path(inside.__code__.co_filename),b/'registration.json',b/'completion.json',b/'input_seal.json',D/'residual_native_experiment_01.json']}
    for a,rd in dirs.items():
        assert read(rd/'trace_reproduction.json')['passed'];domains[a]={int(r['search']):r for r in [fields(l) for l in logs[a] if l.startswith('H3D_SEARCH_DOMAIN ')]};queries[a]={int(r['search']):r for r in [fields(l) for l in logs[a] if l.startswith('H3D_RESIDUAL_QUERY ')]};edges[a]=collections.defaultdict(list)
        for l in logs[a]:
            if l.startswith('H3D_RESIDUAL_EDGE '):r=fields(l);search=int(r['search']);assert int(r['index'])==len(edges[a][search]);edges[a][search].append((int(r['from']),int(r['to']),float(r['physical_seconds']),float(r['toll_seconds'])))
        sums=[fields(l) for l in logs[a] if l.startswith('H3D_RESIDUAL_SUMMARY ')];summaries[a]=sums[-1] if sums else None
        if a=='C':assert not queries[a] and not sums;continue
        assert domains[a]==domains['C']
        assert {s for s,r in domains[a].items() if r['guide']=='1' and r['rcv']=='0'}==set(queries[a])
        for q in queries[a].values():
            if q['seeds']!='-':wanted.update(int(x.split(',')[0]) for x in q['seeds'].split(';'))
            wanted.add(int(q['sink']))
        for path in edges[a].values():
            for u,v,w,t in path:wanted.update([u,v])
        for n in ['manifest.json','stdout.log','independent_audit.json','h3d_final_guides.csv','final_guide_audit.json','trace_reproduction.json']:bindings[str(rd/n)]=sha(rd/n)
    manifest=read(dirs['C']/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);assert sha(graph)==manifest['shared_inputs'][str(graph)]['sha256'];bindings[str(graph)]=sha(graph)
    nodes=[];rev=[];switch={};edge_weights=set();wanted_weights={(v,u,w) for arms in edges.values() for path in arms.values() for u,v,w,t in path};layers=0
    for section,e in graph_records(graph):
        at=e.attrib
        if section=='switches':
            t=e.find('timing');v={} if t is None else t.attrib;assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal']);switch[int(at['id'])]=f32(v.get('Tdel',0))
        elif section=='rr_nodes':
            assert int(at['id'])==len(nodes);v=e.find('loc').attrib;layer=int(v.get('layer_low',v.get('layer',0)));assert layer==int(v.get('layer_high',v.get('layer',0)));t=e.find('timing');assert t is None or all(float(t.attrib.get(k,0))==0 for k in ['R','C']);nodes.append(dict(layer=layer,direction=at.get('direction','NONE'),**{k:int(v[k]) for k in ['xlow','xhigh','ylow','yhigh']}));layers=max(layers,layer+1)
        elif section=='rr_edges':
            if not rev:rev=[[] for n in nodes]
            u,v=int(at['src_node']),int(at['sink_node']);w=switch[int(at['switch_id'])]
            if nodes[u]['layer']==nodes[v]['layer']:rev[v].append((u,w))
            if (u,v,w) in wanted_weights:edge_weights.add((u,v,w))
    nreal=len(nodes);checks=0;lower_checks=0;full_groups={};results={};observations=[]
    # One independent static reverse distance prefix per sink/BB; group maxima avoid repeated oracle work.
    bounds={};qkeys={}
    for a,qs in queries.items():
        for search,q in qs.items():
            domain=domains[a][search];key=(int(q['sink']),tuple(int(domain[k]) for k in ['xmin','xmax','ymin','ymax','layer_min','layer_max']));qkeys[a,search]=key
            if q['has_lower']=='1':bounds[key]=max(bounds.get(key,0.),float(q['lower_seconds']))
    oracle_work=0
    for key,bound in bounds.items():
        sink,box=key;bb=dict(zip(['xmin','xmax','ymin','ymax','layer_min','layer_max'],box));layer=nodes[sink]['layer'];best={sink:0.};settled={};queue=[(0.,sink)]
        while queue:
            d,n=heapq.heappop(queue)
            if n in settled or best.get(n)!=d:continue
            if d>bound+max(1e-24,abs(bound)*1e-12):break
            settled[n]=d;oracle_work+=1
            for u,w in rev[n]:
                if nodes[u]['layer']!=layer or not inside(nodes[u],bb,layers):continue
                nd=d+w
                if nd<best.get(u,math.inf):best[u]=nd;heapq.heappush(queue,(nd,u))
        full_groups[key]=settled
    source_set_focus_checks=0
    for a in reg['arms']:
        if a=='C':continue
        cache={};records=0;stops=0;rows=[];raw_seed=collections.defaultdict(list)
        for line in logs[a]:
            if line.startswith('H3D_SEARCH_DOMAIN_SEED '):
                r=fields(line);raw_seed[int(r['search'])].append(r)
        for search,q in sorted(queries[a].items()):
            checks+=1;domain=domains[a][search];sink=int(q['sink']);mode={'Q0':0,'Qh':1,'Qs':2}[a];assert int(q['mode'])==mode
            assert all(q[k]==domain[k] for k in ['iter','attempt','search','net','pin','sink','criticality'])
            assert int(q['source_rows'])==min(2048,int(q['sources']))
            src={} if q['seeds']=='-' else {int(s.split(',')[0]):float(s.split(',')[1]) for s in q['seeds'].split(';')}
            assert len(src)==int(q['source_rows']);assert all(nodes[n]['layer']==nodes[sink]['layer'] and math.isfinite(t) and t>=0 for n,t in src.items())
            sink_layer=nodes[sink]['layer'];pushes=int(domain['layers'].split(';')[sink_layer].split(',')[1]);assert len(src)<=pushes
            if search in raw_seed and len(raw_seed[search])==sum(int(z.split(',')[1]) for z in domain['layers'].split(';')):
                actual={}
                for z in raw_seed[search]:
                    if int(z['layer'])!=sink_layer:continue
                    n=int(z['node']);t=float(z['delay_seconds']);actual[n]=min(actual.get(n,math.inf),t)
                assert actual==src;source_set_focus_checks+=1
            path=edges[a].get(search,[]);assert len(path)==int(q['path_edges'])==int(q['edge_rows']);upper=float(q['upper_seconds']);has=q['has_path']=='1';status=int(q['status']);hit=q['hit']=='1'
            assert has==bool(path);assert int(q['expansions'])<=256 and int(q['labels'])<=16384 and int(q['peak_heap'])<=65536
            if status==-2:assert not src and not has and int(q['expansions'])==0
            if status==-3:assert int(q['sources'])>2048 and not has and int(q['expansions'])==0
            assert status!=-4
            if has:
                assert path[0][0]==sink and path[-1][1]==nreal and path[-1][0] in src and path[-1][2]==src[path[-1][0]]
                assert len({e[0] for e in path})==len(path) and all(e[3]==0 for e in path) and all(e[1]==z[0] for e,z in zip(path,path[1:]));assert near(sum(e[2] for e in path),upper)
                for u,v,w,t in path[:-1]:assert (v,u,w) in edge_weights and nodes[u]['layer']==nodes[v]['layer']==sink_layer and inside(nodes[u],domain,layers) and inside(nodes[v],domain,layers)
            if q['has_lower']=='1':
                lower_checks+=1;lower=float(q['lower_seconds']);dist=full_groups[qkeys[a,search]];minimum=min((t+dist[n] for n,t in src.items() if n in dist),default=math.inf);assert minimum+1e-24>=lower
                if status==0:assert has and near(upper,lower) and near(minimum,upper)
                if status==2:assert not has and math.isinf(minimum)
            if a=='Qs':
                best=math.inf;matching=[]
                for source,prefix in src.items():
                    for origin,p in cache.get((sink,source),[]):
                        assert origin<search
                        if any(not inside(nodes[n],domain,layers) for e in p for n in e[:2]):continue
                        cost=prefix+sum(e[2] for e in p);best=min(best,cost)
                        if p==path[:-1] and path and source==path[-1][0]:matching.append(origin)
                if len(src)>2048 or not src:assert not hit
                else:assert hit==math.isfinite(best)
                if hit:assert near(upper,best) and int(q['origin']) in matching and int(q['expansions'])==0 and q['has_lower']=='0'
                elif has:
                    assert int(q['origin'])==search
                    for count in range(len(path)):
                        source=path[count-1][1] if count else sink;p=path[:count];key=(sink,source)
                        variants=cache.get(key,[])
                        if any(prev==p for origin,prev in variants):continue
                        if len(variants)>=16 or records>=16384:stops+=1;continue
                        cache.setdefault(key,[]).append((search,p));records+=1
                assert records==int(q['cache_records']) and stops==int(q['cache_stops'])
            else:assert not hit and int(q['cache_records'])==int(q['cache_stops'])==0
            rows.append(dict(search=search,iter=int(q['iter']),net=int(q['net']),pin=int(q['pin']),criticality=float(q['criticality']),sources=int(q['sources']),status=status,hit=hit,has_path=has,upper_seconds=upper if has else None,expansions=int(q['expansions']),labels=int(q['labels']),seconds=float(q['seconds'])))
        summary=summaries[a];assert int(summary['requests'])==len(rows) and int(summary['hits'])==sum(r['hit'] for r in rows) and int(summary['paths'])==sum(r['has_path'] for r in rows) and int(summary['expansions'])==sum(r['expansions'] for r in rows) and int(summary['edge_omitted'])==0
        results[a]=dict(requests=len(rows),paths=sum(r['has_path'] for r in rows),hits=sum(r['hit'] for r in rows),queries=int(summary['queries']),expansions=int(summary['expansions']),labels=int(summary['labels']),probe_seconds=float(summary['seconds']),status_counts=dict(collections.Counter(r['status'] for r in rows)),cache_records=records,cache_stops=stops,rows=rows)
    # Exactly matched guided focus contexts must reproduce the prior generic-engine offline result for each noncached mode.
    from audit_residual_query_offline import parse
    off,offpaths=parse(D/'residual_query_offline_01/query_stdout.log');focus_checks=0
    for a,mode in [('Q0',0),('Qh',1)]:
        for search,q in queries[a].items():
            if (search,mode) not in off or int(q['sources'])==0:continue
            r=off[search,mode];assert r['expansions']==int(q['expansions']) and r['stop']==int(q['status']) and r['labels']==int(q['labels']);assert bool(r['upper_seconds'] is not None)==(q['has_path']=='1')
            if r['upper_seconds'] is not None:assert near(r['upper_seconds'],float(q['upper_seconds']))
            focus_checks+=1
    observations=[dict(observe(rd),arm=a,count=2,reused=False) for a,rd in dirs.items()]
    prior=D/'bounded_cap_range_eltwise_dev_02';original=read(prior/'recovery_binding_v2.json')['checks']
    for rd in [Path(p) for p in reg['references']['2'].values()]:
        for n in ['manifest.json','independent_audit.json','stdout.log','routed.route','time.txt','final_guide_audit.json','h3d_final_guides.csv']:
            p=rd/n
            if p.exists():assert str(p) in original and sha(p)==original[str(p)]['expected_sha256'];bindings[str(p)]=sha(p)
    bindings[str(prior/'recovery_binding_v2.json')]=sha(prior/'recovery_binding_v2.json')
    observations += [dict(observe(Path(p)),arm=a,count=2,reused=True) for a,p in reg['references']['2'].items()]
    assert all(sha(p)==h for p,h in bindings.items());write(b/'residual_native_analysis.json',dict(passed=True,status='sealed_readonly_residual_query_native',source_sha256=bindings,results=results,observations=observations,query_attempt_checks=checks,lower_certificate_checks=lower_checks,independent_oracle_groups=len(full_groups),independent_oracle_ordinary_settlements=oracle_work,focus_offline_matches=focus_checks,current_seed_set_focus_checks=source_set_focus_checks,real_directed_edge_weights_checked=len(edge_weights),qualification='Actual guided searches only; native complete route/guide/cost/query/heap/prefix/influence reproduction holds. All paths physical zeroRC graph-walk UBs, every real edge/delay, current sourceTdel/BB/layer and causal cache checked. Query frontier lower bounds independently checked against static reverse Dijkstra prefixes, including exact claims. Saved same-layer sources are native successful seed pushes; physical walk may intersect other non-seed tree branches and excludes native congestion, so no legal-extension or final STA certificate. Per-probe elapsed excludes source collection/deduplication and trace output; full native process time includes them. Ordered process times are diagnostic, not formal speed ratio or quality gain.'))
    print({a:{k:v for k,v in r.items() if k!='rows'} for a,r in results.items()})
if __name__=='__main__':main()
