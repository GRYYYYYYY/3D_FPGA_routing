#!/usr/bin/env python3
"""Offline physical-walk oracle for actual fully recorded multi-source seeds."""
import collections,heapq,math,resource,signal
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import fields,graph_records,f32
from analyze_search_domain_v2 import inside

def main():
    resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
    out=D/'residual_seed_oracle_01';out.mkdir(exist_ok=False);b=D/'search_domain_eltwise_dev_01';report=read(b/'search_domain_analysis.json');assert report['passed']
    write(out/'registration.json',dict(status='registered_before_oracle',native_route_calls=0,question='For actual completely logged seed groups, does a physical same-layer continuation compete with a route through the planned crossing? How much ordinary-node residual distance would the existing4096 reverse search settle?',input=str(b),sampling='All31 fully recorded focus search seed groups, no new native runs; posthoc diagnostic, not independent circuit samples.',method='Full directed same-layer reverse Dijkstra within each actual native BB, zero-RC switches. Compare min seedTdel+residual no-cross walk vs min seedTdel+prefix+preferred-cross+suffix with exactly one additional layer crossing. Separately reproduce legacy4096 virtual crossing terminals and inspect settled ordinary distances without claiming these were retained at native runtime.',limits=dict(seconds=1800,memory_bytes=24*1024**3),qualification='Physical graph walks, not native congestion/criticality objective, legal route-tree extension, current dynamic transaction, or final STA prediction. No hard source filtering or algorithm change; unknown remains unknown.'))
    rd=b/'runs/eltwise_layer_T';lines=(rd/'stdout.log').read_text().splitlines();domains=[fields(l) for l in lines if l.startswith('H3D_SEARCH_DOMAIN ')];raw=collections.defaultdict(list)
    for l in lines:
        if l.startswith('H3D_SEARCH_DOMAIN_SEED '):
            r=fields(l);raw[int(r['search'])].append(r)
    cases=[r for r in domains if len(raw[int(r['search'])])==sum(int(z.split(',')[1]) for z in r['layers'].split(';')) and raw[int(r['search'])]];assert len(cases)==report['fully_recorded_seed_groups']==31
    m=read(rd/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);bindings={str(p):sha(p) for p in [Path(__file__),Path(inside.__code__.co_filename),b/'search_domain_analysis.json',b/'input_seal.json',rd/'stdout.log',rd/'manifest.json',graph]};assert bindings[str(graph)]==m['shared_inputs'][str(graph)]['sha256']
    nodes=[];sw={};rev=[];cross=collections.defaultdict(list);cross_sources=set();edge_checks=0
    for section,e in graph_records(graph):
        at=e.attrib
        if section=='switches':
            t=e.find('timing');v={} if t is None else t.attrib;assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal']);sw[int(at['id'])]=f32(v.get('Tdel',0))
        elif section=='rr_nodes':
            assert int(at['id'])==len(nodes);v=e.find('loc').attrib;layer=int(v.get('layer_low',v.get('layer',0)));assert layer==int(v.get('layer_high',v.get('layer',0)));t=e.find('timing');assert t is None or all(float(t.attrib.get(k,0))==0 for k in ['R','C']);nodes.append(dict(layer=layer,direction=at.get('direction','NONE'),**{k:int(v[k]) for k in ['xlow','xhigh','ylow','yhigh']}))
        elif section=='rr_edges':
            if not rev:rev=[[] for _ in nodes]
            u,v=int(at['src_node']),int(at['sink_node']);w=sw[int(at['switch_id'])];assert w>=0;rev[v].append((u,w));edge_checks+=1
            if nodes[u]['layer']!=nodes[v]['layer']:cross[u].append((v,w));cross_sources.add(u)
    layers=max(n['layer'] for n in nodes)+1;nreal=len(nodes);virtual={n:nreal+i for i,n in enumerate(sorted(cross_sources))};cache={};legacy={};work=[]
    def reverse(endpoint,box=None,budget=None):
        key=(endpoint,None if box is None else tuple(int(box[k]) for k in ['xmin','xmax','ymin','ymax','layer_min','layer_max']),budget)
        if key in cache:return cache[key]
        layer=nodes[endpoint]['layer'];best={endpoint:0.};settled={};q=[(0.,endpoint)];parents={}
        while q and (budget is None or len(settled)<budget):
            d,n=heapq.heappop(q)
            if n in settled or best.get(n)!=d:continue
            settled[n]=d
            if n>=nreal:continue
            for u,w in rev[n]:
                if nodes[u]['layer']!=layer:
                    if budget is None:continue
                    u=virtual[u]
                elif box is not None and not inside(nodes[u],box,layers):continue
                nd=d+w
                if nd<best.get(u,math.inf):best[u]=nd;parents[u]=(n,w);heapq.heappush(q,(nd,u))
        cache[key]=(settled,parents);work.append(dict(endpoint=endpoint,budget=budget,bbox=key[1],settled=len(settled)));return cache[key]
    rows=[]
    def finite(v):return v if math.isfinite(v) else None
    for c in cases:
        seed=raw[int(c['search'])];sink=int(c['sink']);layer=nodes[sink]['layer'];dist,parents=reverse(sink,c);full,_=reverse(sink);bounded,_=reverse(sink,budget=4096)
        source=[s for s in seed if int(s['layer'])==layer];best=min((float(s['delay_seconds'])+dist.get(int(s['node']),math.inf),int(s['node'])) for s in source) if source else (math.inf,-1)
        loose=min((float(s['delay_seconds'])+full.get(int(s['node']),math.inf) for s in source),default=math.inf)
        measured=min((float(s['delay_seconds'])+bounded[int(s['node'])] for s in source if int(s['node']) in bounded),default=math.inf)
        # Explicitly verify every directed edge of the winning no-new-cross walk.
        path=[];sumw=0.;node=best[1]
        if math.isfinite(best[0]):
            visited=set()
            while node!=sink:
                assert node not in visited and nodes[node]['layer']==layer and inside(nodes[node],c,layers);visited.add(node);n,w=parents[node];assert (node,w) in rev[n];path.append([node,n,w]);sumw+=w;node=n
            sd=next(float(s['delay_seconds']) for s in source if int(s['node'])==best[1]);assert math.isclose(sd+sumw,best[0],rel_tol=1e-12,abs_tol=1e-24)
        preferred=[] if c['preferred']=='-' else list(map(int,c['preferred'].split(',')));via=math.inf
        for p in preferred:
            if not inside(nodes[p],c,layers):continue
            if nodes[p]['layer']==layer:continue
            pd,_=reverse(p,c)
            prefix=min((float(s['delay_seconds'])+pd.get(int(s['node']),math.inf) for s in seed if int(s['layer'])==nodes[p]['layer']),default=math.inf)
            suffix=min((w+dist.get(v,math.inf) for v,w in cross[p] if nodes[v]['layer']==layer and inside(nodes[v],c,layers)),default=math.inf);via=min(via,prefix+suffix)
        rows.append(dict(iter=int(c['iter']),search=int(c['search']),net=int(c['net']),pin=int(c['pin']),guide=bool(int(c['guide'])),criticality=float(c['criticality']),seed_pushes=len(seed),sink_layer_seeds=len(source),bounded_known_sink_layer_seeds=sum(int(s['node']) in bounded for s in source),no_cross_BB_seconds=finite(best[0]),no_cross_unbounded_box_seconds=finite(loose),no_cross_legacy4096_seconds=finite(measured),preferred_one_cross_BB_seconds=finite(via),no_cross_better_or_equal=math.isfinite(best[0]) and best[0]<=via,no_cross_walk=path))
    assert all(sha(p)==h for p,h in bindings.items());guided=[r for r in rows if r['guide']];result=dict(passed=True,status='sealed_posthoc_residual_physical_walk_oracle',native_route_calls=0,source_sha256=bindings,graph_edges_verified_zeroRC=edge_checks,complete_seed_groups=len(rows),guided_groups=len(guided),finite_no_cross=sum(r['no_cross_BB_seconds'] is not None for r in rows),guided_finite_no_cross=sum(r['no_cross_BB_seconds'] is not None for r in guided),guided_no_cross_no_worse=sum(r['no_cross_better_or_equal'] for r in guided),rows=rows,oracle_work=work,qualification='Actual logged complete successful seed pushes; ordinary-node measurements from reconstructed static4096 query are potential reuse, not proof native cache retained them. Graph walk minima ignore native prices and self-intersection with unrecorded non-seed tree branches; no legal-extension or final STA certificate. Physical no-cross and exactly-one preferred-cross alternatives restricted to native drivepoint BB, RCV0 only. Separate independent unlimited offline work, not increased runtime router budget or formal cost. Multiple trajectory groups remain one seen circuit.')
    write(out/'analysis.json',result);print({k:v for k,v in result.items() if k not in ['source_sha256','rows','oracle_work','qualification']})
if __name__=='__main__':main()
