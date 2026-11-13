#!/usr/bin/env python3
"""Independent RRG drivepoint admission and successful seed ledger checks."""
import collections,math,resource,signal
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import fields,graph_records,f32

def inside(node,bb,total_layers):
    x=node['xhigh'] if node['direction']=='DEC_DIR' else node['xlow'];y=node['yhigh'] if node['direction']=='DEC_DIR' else node['ylow']
    if not (int(bb['xmin'])<=x<=int(bb['xmax']) and int(bb['ymin'])<=y<=int(bb['ymax'])):return False
    if int(bb['layer_min'])==0 and int(bb['layer_max'])==total_layers-1:return True
    return int(bb['layer_min'])<=node['layer']<=int(bb['layer_max'])

def main():
    resource.setrlimit(resource.RLIMIT_AS,(16*1024**3,16*1024**3));signal.alarm(1200)
    b=D/'search_domain_eltwise_dev_01';assert read(b/'input_seal.json')['passed'];done=read(b/'completion.json');assert done['gate_passed'] and not done['missing_arms']
    c=b/'runs/eltwise_layer_C';t=b/'runs/eltwise_layer_T';lines=(t/'stdout.log').read_text().splitlines();assert not any(l.startswith('H3D_SEARCH_DOMAIN') for l in (c/'stdout.log').read_text().splitlines())
    for p in [c,t]:assert read(p/'trace_reproduction.json')['passed'] and read(p/'independent_audit.json')['audit']['passed'] and read(p/'final_guide_audit.json')['passed']
    rows=[fields(l) for l in lines if l.startswith('H3D_SEARCH_DOMAIN ')];seeds=[fields(l) for l in lines if l.startswith('H3D_SEARCH_DOMAIN_SEED ')];summary=fields(next(l for l in lines if l.startswith('H3D_SEARCH_DOMAIN_SUMMARY ')))
    assert len(rows)==int(summary['rows'])<=20000 and len(seeds)==int(summary['seed_rows'])<=6000
    assert int(summary['omitted'])==0 # required complete search-row coverage in this seen-input diagnostic
    wanted={int(s['node']) for s in seeds};prefs=set()
    for r in rows:
        if r['preferred']!='-':prefs.update(map(int,r['preferred'].split(',')))
        wanted.add(int(r['sink']))
    wanted|=prefs;m=read(t/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);bindings={str(p):sha(p) for p in [Path(__file__),graph,b/'registration.json',b/'completion.json',b/'input_seal.json',t/'stdout.log',c/'trace_reproduction.json',t/'trace_reproduction.json']}
    assert bindings[str(graph)]==m['shared_inputs'][str(graph)]['sha256']
    nodes={};cross=collections.defaultdict(list);layers=0
    for section,e in graph_records(graph):
        at=e.attrib
        if section=='rr_nodes':
            node=int(at['id']);v=e.find('loc').attrib;layer=int(v.get('layer_low',v.get('layer',0)));assert layer==int(v.get('layer_high',v.get('layer',0)));layers=max(layers,layer+1)
            # All nodes retained for independent preferred crossing-head layer and bbox tests.
            nodes[node]=dict(layer=layer,direction=at.get('direction','NONE'),**{k:int(v[k]) for k in ['xlow','xhigh','ylow','yhigh']})
        elif section=='rr_edges':
            u,v=int(at['src_node']),int(at['sink_node'])
            if u in prefs and nodes[u]['layer']!=nodes[v]['layer']:cross[u].append(v)
    grouped=collections.defaultdict(list)
    for s in seeds:
        assert nodes[int(s['node'])]['layer']==int(s['layer']);grouped[int(s['search'])].append(s)
    raw_checks=0;full_seed_groups=0;bykey={};observations=[]
    for r in rows:
        search=int(r['search']);assert search not in bykey;bykey[search]=r
        pref=[] if r['preferred']=='-' else list(map(int,r['preferred'].split(',')))
        assert int(r['sink_layer'])==nodes[int(r['sink'])]['layer']
        pi=sum(inside(nodes[n],r,layers) for n in pref);heads=sum(len(cross[n]) for n in pref);admitted=sum(inside(nodes[n],r,layers) and (int(r['rcv']) or inside(nodes[v],r,layers)) for n in pref for v in cross[n])
        assert (pi,heads,admitted)==tuple(int(r[k]) for k in ['preferred_inside','crossing_heads','admitted_heads'])
        ls=[item.split(',') for item in r['layers'].split(';')];assert len(ls)==layers
        raw=grouped.get(search,[]);total=sum(int(item[1]) for item in ls);assert total>0 and len(raw)<=total
        raw_by=collections.defaultdict(list)
        for s in raw:
            assert all(s[k]==r[k] for k in ['iter','attempt','search','net','pin','rcv']);raw_by[int(s['layer'])].append(s);assert f32(f32(float(r['criticality']))*f32(float(s['delay_seconds'])))==float(s['backward']);raw_checks+=1
        for layer,pushes,delay,backward,priority in ls:
            layer,pushes=int(layer),int(pushes);minima=list(map(float,[delay,backward,priority]));values=raw_by[layer]
            assert len(values)<=pushes
            for s in values:assert all(minima[j]<=float(s[k]) for j,k in enumerate(['delay_seconds','backward','total']))
            if len(raw)==total:
                assert len(values)==pushes
                if pushes:assert minima==[min(float(s[k]) for s in values) for k in ['delay_seconds','backward','total']]
        full_seed_groups+=bool(raw and len(raw)==total)
        sink_pushes=int(ls[int(r['sink_layer'])][1]);observations.append(dict(iter=int(r['iter']),attempt=int(r['attempt']),search=search,net=int(r['net']),pin=int(r['pin']),guide=bool(int(r['guide'])),criticality=float(r['criticality']),preferred_count=len(pref),preferred_inside=pi,admitted_heads=admitted,queued_pushes=total,sink_layer_pushes=sink_pushes,rcv=bool(int(r['rcv'])),layers=ls))
    assert set(grouped)<=set(bykey)
    guide=[r for r in observations if r['guide']];focus={(4674,9),(4674,21),(4675,23)}
    result=dict(status='sealed_actual_search_domain_diagnostic',passed=True,source_sha256=bindings,summary=summary,search_rows=len(rows),guided_search_rows=len(guide),guided_with_no_admitted_preferred_heads=sum(r['admitted_heads']==0 for r in guide),guided_with_sink_layer_seed_pushes=sum(r['sink_layer_pushes']>0 for r in guide),guided_with_no_preferred_source_in_bb=sum(r['preferred_inside']==0 for r in guide),raw_seed_checks=raw_checks,fully_recorded_seed_groups=full_seed_groups,focus=[r for r in observations if (r['net'],r['pin']) in focus],observations=observations,qualification='Successful native heap push calls, not a dump of surviving heap after build or proof each seed was popped. Layer aggregates include all successful pushes; raw focus quota explicitly bounded. Native drivepoint BB admission independently reconstructed from RRG, with RCV destination-BB bypass explicit; admitted crossing heads are necessary local box tests, not reachability/path/transaction legality certificates. Minima for delay/backward/priority are separate statistics and may belong to different nodes. HF subset/full-tree retries have distinct search IDs. Default0 frozen and trace1 route/guide/originalcost/query/heap/prefix/actualinfluence exact. No formal runtime or algorithm quality claim.')
    assert all(sha(p)==h for p,h in bindings.items());write(b/'search_domain_analysis.json',result)
    print({k:result[k] for k in ['passed','search_rows','guided_search_rows','guided_with_no_admitted_preferred_heads','guided_with_sink_layer_seed_pushes','raw_seed_checks','fully_recorded_seed_groups','focus']})
if __name__=='__main__':main()
