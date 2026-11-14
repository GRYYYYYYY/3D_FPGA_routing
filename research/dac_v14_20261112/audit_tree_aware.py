#!/usr/bin/env python3
"""Audit real directed RRG witnesses and decision relevance of tree-aware queries."""
import collections
import json
import math
from pathlib import Path
import resource
import signal
import time
from retained_prefix_workflow import D, read, write, sha
from verify_path_witnesses_v2 import graph_records, f32
from analyze_search_domain_v2 import inside

resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3))
signal.alarm(1800)
started=time.monotonic()
b=D/'tree_aware_candidate_offline_01'
ex=read(b/'execution.json')
assert all(sha(p)==h for p,h in ex['source_sha256'].items())
assert all(sha(b/p)==h for p,h in ex['output_sha256'].items())
assert read(b/'unit_validation.json')['passed'] and read(b/'control_reproduction.json')['passed']
reg=read(b/'registration.json')
assert all(sha(p)==h for p,h in reg['input_sha256'].items())
raw=D/'actual_search_tree_eltwise_dev_01/actual_cases.jsonl'
cases={int(c['domain']['search']):c for c in map(json.loads,raw.open())}
rows={};paths=collections.defaultdict(list);lower_checks={};work={}
for line in (b/'query_stdout.log').open():
    v=line.split()
    if v[0]=='WORK':
        assert int(v[1]) not in work
        work[int(v[1])]=(int(v[2]),int(v[3]));continue
    key=(int(v[1]),int(v[2]))
    if v[0]=='RESULT':
        assert key not in rows
        opt=lambda x:None if x=='-' else float(x)
        rows[key]=dict(search=key[0],mode=key[1],stop=int(v[3]),expansions=int(v[4]),
            labels=int(v[5]),peak_heap=int(v[6]),upper_seconds=opt(v[7]),physical_seconds=opt(v[8]),
            lower_seconds=opt(v[9]),query_seconds=float(v[10]),edges=int(v[11]),
            seed_floor=float(v[12]),admissible_seeds=int(v[13]))
    elif v[0]=='LOWER':
        assert key not in lower_checks
        lower_checks[key]=(int(v[3]),float(v[4]))
    else:
        assert v[0]=='EDGE' and int(v[3])==len(paths[key])
        paths[key].append((int(v[4]),int(v[5]),float(v[6]),float(v[7])))
assert len(cases)==3809 and rows.keys()==lower_checks.keys()
assert rows.keys()=={(s,m) for s in cases for m in range(4)} and work.keys()==cases.keys()
nreal=read(D/'residual_query_offline_01/graph_binding.json')['nodes']
manifest=read(D/'actual_search_tree_eltwise_dev_01/runs/eltwise_layer_T2/manifest.json')
graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
assert sha(graph)==manifest['shared_inputs'][str(graph)]['sha256']
want_nodes=set();want_edges=set()
for c in cases.values():
    want_nodes.update(row[0] for row in c['tree'])
    want_nodes.add(int(c['domain']['sink']))
    want_nodes.update(map(int,c['domain']['preferred'].split(',')))
for path in paths.values():
    for u,v,w,t in path:
        assert t==0.;want_nodes.add(u)
        if v!=nreal:want_nodes.add(v);want_edges.add((v,u,w))
nodes={};switches={};found=set();layers=[];by_source=collections.Counter();crossing_count=0
for section,e in graph_records(graph):
    a=e.attrib
    if section=='switches':
        timing=e.find('timing');v={} if timing is None else timing.attrib
        assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal'])
        switches[int(a['id'])]=f32(v.get('Tdel',0))
    elif section=='rr_nodes':
        node=int(a['id']);v=e.find('loc').attrib
        layer=int(v.get('layer_low',v.get('layer',0)));assert node==len(layers);layers.append(layer)
        if node in want_nodes:
            nodes[node]=dict(layer=layer,direction=a.get('direction','NONE'),
                **{name:int(v[name]) for name in ['xlow','xhigh','ylow','yhigh']})
    elif section=='rr_edges':
        item=(int(a['src_node']),int(a['sink_node']),switches[int(a['switch_id'])])
        if layers[item[0]]!=layers[item[1]]:crossing_count+=1;by_source[item[0]]+=1
        if item in want_edges:found.add(item)
assert found==want_edges and len(layers)==nreal and set(layers)=={0,1}
near=lambda x,y:x==y or math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-24)
strict_less=lambda x,y:x+1e-24+1e-12*max(abs(x),abs(y))<y
case_metadata={}
for search,c in cases.items():
    dom=c['domain'];sink=int(dom['sink']);sl=nodes[sink]['layer'];preferred=set(map(int,dom['preferred'].split(',')))
    assert inside(nodes[sink],dom,2)
    assert work[search]==(crossing_count,sum(by_source[n] for n in preferred))
    tree={};ancestry={}
    for node,expand,td,parent,sw,pin in c['tree']:
        assert node not in tree
        tree[node]=(expand,td,parent,sw,pin)
        ancestry[node]=parent>=0 and (ancestry[parent] or parent in preferred and nodes[parent]['layer']!=nodes[node]['layer'])
    seeds={}
    for node,layer,td in c['seeds']:
        assert node in tree and tree[node][0] and td==tree[node][1] and nodes[node]['layer']==layer
        if inside(nodes[node],dom,2):seeds[node]=min(seeds.get(node,math.inf),td)
    inherited={node for node in seeds if nodes[node]['layer']==sl and ancestry[node]}
    # Reuse an already physically audited native no-new-cross witness. Clip at
    # its first retained-tree node and use that actual queued seed's prefix.
    native=c['native_reverse_path'];alternative=None;alternative_anchor=None;native_satisfied=None
    if native:
        assert native[-1][1]==nreal
        index=next(i for i,e in enumerate(native) if e[0] in tree)
        anchor=native[index][0];assert anchor in seeds
        native_cost=seeds[anchor]+sum(e[2] for e in native[:index])
        native_satisfied=ancestry[anchor]
        if not native_satisfied:alternative=native_cost;alternative_anchor=anchor
    case_metadata[search]=dict(search=search,net=int(dom['net']),pin=int(dom['pin']),iteration=int(dom['iter']),
        criticality=float(dom['criticality']),high_criticality=float(dom['criticality'])>=f32(.9),
        inherited_seed_count=len(inherited),native_fixed_extension_satisfies_preferred=native_satisfied,
        actual_nonpreferred_extension_upper_seconds=alternative,actual_nonpreferred_anchor=alternative_anchor)
    for mode in range(4):
        key=(search,mode);r=rows[key];path=paths[key]
        admitted={node:td for node,td in seeds.items() if nodes[node]['layer']!=sl or (mode&1 and node in inherited)}
        assert len(admitted)==r['admissible_seeds'] and r['seed_floor']==0.
        assert len(path)==r['edges'] and r['expansions']<=256 and r['labels']<=16384 and r['peak_heap']<=65536
        r.update(case_metadata[search]);r['lower_audit_settlements'],r['lower_audit_seconds']=lower_checks[key]
        upper=r['upper_seconds'];lower=r['lower_seconds'];crosses=[];intersections=[];anchor=None
        if upper is not None:
            assert path and near(upper,r['physical_seconds']) and path[0][0]==sink and path[-1][1]==nreal
            anchor=path[-1][0];assert anchor in admitted and path[-1][2]==admitted[anchor]
            assert len({e[0] for e in path})==len(path)
            assert all(a[1]==z[0] for a,z in zip(path,path[1:]))
            for u,v,w,t in path[:-1]:
                assert (v,u,w) in found and inside(nodes[u],dom,2) and inside(nodes[v],dom,2)
                if nodes[u]['layer']!=nodes[v]['layer']:
                    assert nodes[u]['layer']==sl and v in preferred;crosses.append((v,u))
                if u in tree:intersections.append(u)
            assert len(crosses)==1 or (len(crosses)==0 and mode&1 and anchor in inherited)
            assert near(sum(e[2] for e in path),upper)
            if mode&2:assert not intersections
        else:assert not path
        assert (lower is None)==(r['lower_audit_settlements']==-1)
        if r['stop']==0:assert upper is not None and lower is not None and near(upper,lower)
        if r['stop']==4:assert lower is None
        if r['stop']==2:assert upper is None and lower==math.inf
        r.update(anchor=anchor,new_crossings=len(crosses),inherited_only_path=upper is not None and not crosses,
            fixed_tree_extension=upper is not None and not intersections,extra_tree_intersections=len(intersections),
            modeled_nonpreferred_better=alternative is not None and lower is not None and
                (math.isinf(lower) or strict_less(alternative,lower)),
            bound_relative_width=None if upper is None or lower is None or upper==0 else (upper-lower)/upper)

summaries={}
for mode,label in enumerate(['P','I','L','IL']):
    rs=[r for (s,m),r in rows.items() if m==mode]
    summaries[label]=dict(queries=len(rs),paths=sum(r['upper_seconds'] is not None for r in rs),
        fixed_tree_extensions=sum(r['fixed_tree_extension'] for r in rs),
        inherited_only_paths=sum(r['inherited_only_path'] for r in rs),
        high_criticality_paths=sum(r['high_criticality'] and r['upper_seconds'] is not None for r in rs),
        high_criticality_fixed_extensions=sum(r['high_criticality'] and r['fixed_tree_extension'] for r in rs),
        stop_counts=dict(collections.Counter(r['stop'] for r in rs)),exact=sum(r['stop']==0 for r in rs),
        expansions=sum(r['expansions'] for r in rs),query_seconds=sum(r['query_seconds'] for r in rs),
        lower_audit_settlements=sum(max(0,r['lower_audit_settlements']) for r in rs),
        lower_audit_seconds=sum(r['lower_audit_seconds'] for r in rs),
        modeled_nonpreferred_better=sum(r['modeled_nonpreferred_better'] for r in rs))
comparisons={}
for old,new,label in [(0,1,'P_to_I'),(0,2,'P_to_L'),(2,3,'L_to_IL'),(0,3,'P_to_IL')]:
    counts=collections.Counter();changed=[]
    for search in cases:
        x,y=rows[search,old],rows[search,new];a,z=x['upper_seconds'],y['upper_seconds']
        state='both_missing' if a is None and z is None else 'gained_path' if a is None else 'lost_path' if z is None else 'equal' if near(a,z) else 'lower_upper' if z<a else 'higher_upper'
        counts[state]+=1
        if state in ['gained_path','lost_path','lower_upper','higher_upper']:
            changed.append(dict(case_metadata[search],comparison=state,old_upper=a,new_upper=z,
                old_fixed_extension=x['fixed_tree_extension'],new_fixed_extension=y['fixed_tree_extension']))
    comparisons[label]=dict(counts=dict(counts),changed_contexts=len(changed),
        changed_high_criticality=sum(r['high_criticality'] for r in changed),
        changed_unique_connections=len({(r['net'],r['pin']) for r in changed}),rows=changed)
write(b/'case_metadata.json',list(case_metadata.values()))
source=[Path(__file__),b/'registration.json',b/'execution.json',b/'query_stdout.log',raw,
    raw.with_name('actual_tree_analysis.json'),raw.with_name('preferred_prefix_analysis.json'),graph]
assert all(sha(p)==h for p,h in ex['source_sha256'].items())
write(b/'analysis.json',dict(passed=True,native_route_calls=0,contexts=len(cases),
    summaries=summaries,comparisons=comparisons,rows=list(rows.values()),
    actual_nonpreferred_extension_contexts=sum(r['actual_nonpreferred_extension_upper_seconds'] is not None for r in case_metadata.values()),
    high_criticality_contexts=sum(r['high_criticality'] for r in case_metadata.values()),
    directed_physical_edges_checked=len(found),audit_seconds=time.monotonic()-started,
    source_sha256={str(p):sha(p) for p in source},quality_promoted=False,
    qualification='All3809 actual guided contexts on one seen circuit, not independent circuits. I includes retained-prefix preference; L forbids additional current-tree intersections only in the planner query graph. Bounds certified numerically by independent nonheuristic Dijkstra below the claimed frontier (1e-24 absolute +1e-12 relative tolerance), not a full-native/STA proof. Native no-cross alternatives are clipped to current actual queued seeds and excluded if their retained ancestry already satisfies the preferred crossing. Alternative dominance is only relative to the stated restricted preferred model. No dynamic congestion snapshot, native policy integration, CPD gain or formal runtime claim.'))
print(json.dumps(dict(summaries=summaries,comparisons={k:{n:v for n,v in x.items() if n!='rows'} for k,x in comparisons.items()}),indent=2),flush=True)
