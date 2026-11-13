#!/usr/bin/env python3
"""Fresh RRG cost/cap checks, exact legacy map oracle and final guide provenance."""
import argparse,collections,csv,heapq,math,resource,signal,statistics
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from guide_influence_records import records
from verify_path_witnesses_v2 import fields,graph_records,f32
from analyze_native_reconvergence_v2 import observe

THRESHOLD=f32(.9)
def near(a,b):return a==b or math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-24)
def ids(text):return [] if text=='-' else list(map(int,text.split(',')))
def bin_id(c):return 0 if c<.7 else 1 if c<.9 else 2 if c<.95 else 3
FOCUS={(4674,9):0,(4674,21):1,(4675,23):2}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);args=ap.parse_args();b=args.batch.resolve()
    resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));signal.alarm(1800)
    assert read(b/'input_seal.json')['passed'];done=read(b/'completion.json');assert done['disabled_gate_passed'] and not done['missing_arms']
    dirs={a:b/'runs'/('eltwise_layer_'+a) for a in ['C','Z','K']};logs={a:(p/'stdout.log').read_text().splitlines() for a,p in dirs.items()}
    prior=D/'candidate_path_delay_eltwise_dev_01/runs/eltwise_layer_D0'
    assert records(logs['C'])==records((prior/'stdout.log').read_text().splitlines())
    assert route_body(dirs['C']/'routed.route')==route_body(prior/'routed.route') and sha(dirs['C']/'h3d_final_guides.csv')==sha(prior/'h3d_final_guides.csv')
    for a in dirs:
        m=read(dirs[a]/'manifest.json');env=m['environment']
        assert env['VPR_H3D_CANDIDATE_PATH_SCORE']==env['VPR_H3D_CANDIDATE_PATH_DELAY']=='0'
        assert env['VPR_H3D_SOURCE_EMPTY_REVERSE']==env['VPR_H3D_SOURCE_COVERAGE_SKIP']=='0'
        assert env['VPR_H3D_TRACE_GUIDE_INFLUENCE']=='1'
        assert env['VPR_H3D_BOUNDED_AFTER_LEGAL']=='0' and env['VPR_H3D_BOUNDED_CRITICAL_CAP_ONLY']==('1' if a=='K' else '0')
        if a=='C':assert 'VPR_H3D_BOUNDED_CRITICAL_GUIDE' not in env
        else:assert env['VPR_H3D_BOUNDED_CRITICAL_GUIDE']==('0' if a=='Z' else '0.25')
    m=read(dirs['K']/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);assert sha(graph)==m['shared_inputs'][str(graph.resolve())]['sha256']
    inputs=[Path(__file__),D/'bounded_critical_cap_experiment_01.json',D/'bounded_cap_implementation.json',D/'bounded_cap_unit_01/validation.json',b/'input_seal.json',b/'completion.json',b/'registration.json',graph]
    inputs += [p/n for p in dirs.values() for n in ['manifest.json','stdout.log','h3d_final_guides.csv','independent_audit.json','final_guide_audit.json']]
    bindings={str(p):sha(p) for p in inputs}
    edges={};applies={};guides={};finals={};summaries={};wanted=set();wanted_edges=set();oracle_endpoints=set()
    for a in dirs:
        edges[a]=[fields(l) for l in logs[a] if l.startswith('H3D_GUIDE_INFLUENCE_EDGE ')]
        applies[a]={int(r['event']):r for r in [fields(l) for l in logs[a] if l.startswith('H3D_BOUNDED_CRITICAL_APPLY ')]}
        guides[a]=[fields(l) for l in logs[a] if l.startswith('H3D_BOUNDED_CRITICAL_GUIDE ')]
        finals[a]=[fields(l) for l in logs[a] if l.startswith('H3D_FINAL_BOUNDED_GUIDE ')]
        summaries[a]=fields(next(l for l in reversed(logs[a]) if l.startswith('H3D_GUIDE_INFLUENCE_SUMMARY ')))
        for r in edges[a]:
            u,v,sw=int(r['from']),int(r['to']),int(r['switch']);wanted.update([u,v]);wanted.update(ids(r['preferred_ids']));wanted_edges.add((u,v,sw))
        for r in guides[a]:
            oracle_endpoints.add((int(r['source']),False))
            if int(r['reverse_present']):oracle_endpoints.add((int(r['sink']),True))
            for item in r['known'].split(';'):wanted.add(int(item.split(',')[0]))
    meta={};switches={};found=set();wanted_pairs={(u,v) for u,v,s in wanted_edges};layers=[];adj=[];rev=[];cross=[]
    for section,e in graph_records(graph):
        at=e.attrib
        if section=='switches':
            t=e.find('timing');v={} if t is None else t.attrib;assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal'])
            switches[int(at['id'])]=dict(delay=f32(v.get('Tdel',0)),configurable=at['type'].lower() not in ['short','buffer'])
        elif section=='rr_nodes':
            node=int(at['id']);assert node==len(layers);v=e.find('loc').attrib;layer=int(v.get('layer_low',v.get('layer',0)));assert layer==int(v.get('layer_high',v.get('layer',0)));layers.append(layer)
            t=e.find('timing');assert t is None or all(float(t.attrib.get(k,0))==0 for k in ['R','C'])
            if node in wanted:meta[node]=dict(layer=layer,kind=at['type'])
        elif section=='rr_edges':
            if not adj:adj=[[] for _ in layers];rev=[[] for _ in layers];cross=[False for _ in layers]
            u,v,sw=int(at['src_node']),int(at['sink_node']),int(at['switch_id']);weight=switches[sw]['delay']
            if layers[u]==layers[v]:adj[u].append((v,weight))
            else:cross[u]=True
            rev[v].append((u,weight))
            if (u,v) in wanted_pairs:found.add((u,v,sw))
    assert wanted_edges<=found and set(meta)==wanted
    unit=sum(s['delay'] for s in switches.values() if s['delay']>0)/sum(s['delay']>0 for s in switches.values())
    assert all(near(unit,float(s['unit_seconds'])) for s in summaries.values())
    virtual={node:len(layers)+i for i,node in enumerate(n for n,has in enumerate(cross) if has)};inverse={v:k for k,v in virtual.items()};oracles={};oracle_receipts=[]
    for endpoint,reverse in sorted(oracle_endpoints):
        best={endpoint:0.};queue=[(0.,endpoint)];settled=set();terminals=set();layer=layers[endpoint]
        while queue and len(settled)<4096:
            cost,node=heapq.heappop(queue)
            if node in settled or cost!=best[node]:continue
            settled.add(node)
            if node>=len(layers):terminals.add(inverse[node]);continue
            if reverse:
                neighbors=[]
                for pred,w in rev[node]:
                    if layers[pred]!=layers[node]:neighbors.append((virtual[pred],w))
                    elif layers[pred]==layer:neighbors.append((pred,w))
            else:
                neighbors=adj[node]
                if node in virtual:neighbors=neighbors+[(virtual[node],0.)]
            for next_node,w in neighbors:
                candidate=cost+w
                if candidate<best.get(next_node,math.inf):best[next_node]=candidate;heapq.heappush(queue,(candidate,next_node))
        oracles[endpoint,reverse]=terminals;oracle_receipts.append(dict(endpoint=endpoint,reverse=reverse,settled=len(settled),terminals=len(terminals)))
    del adj,rev,layers,cross,virtual,inverse
    results={};coverage_checks=0
    for a in dirs:
        beta=0 if a=='Z' else .25;signatures=set();metadata_by_shape=collections.defaultdict(set)
        for g in guides[a]:
            known=[tuple(map(int,x.split(','))) for x in g['known'].split(';')];source,sink=int(g['source']),int(g['sink']);reverse_present=int(g['reverse_present'])
            assert len(known)==int(g['preferred_count']) and len({e for e,s,t in known})==len(known)
            assert sum(s for e,s,t in known)==int(g['source_known']) and sum(t for e,s,t in known)==int(g['sink_known'])
            for entry,s,t in known:
                assert s in [0,1] and t in [0,1];assert bool(s)==(entry in oracles[source,False])
                assert bool(t)==bool(reverse_present and entry in oracles[sink,True]);coverage_checks+=2
            reliability=.5*sum(s+t for e,s,t in known)/len(known);assert near(reliability,float(g['reliability'])) and near(float(g['unit_seconds']),unit)
            assert float(g['beta'])==beta and float(g['penalty_seconds'])==f32(beta*reliability*unit)
            assert 0<=float(g['penalty_seconds'])<=beta*unit*(1+1e-6)
            pref=tuple(e for e,s,t in known);key=(int(g['net']),int(g['pin']),pref)
            sig=(float(g['reliability']),float(g['unit_seconds']),float(g['beta']),float(g['penalty_seconds']));metadata_by_shape[key].add(sig);signatures.add(key+sig)
        old_event=0;groups=collections.Counter();applied_count=0;sampled_extra=[];sampled_new=[];row_by_event={}
        for r in edges[a]:
            event=int(r['event']);assert event>old_event;old_event=event;row_by_event[event]=r
            net,pin=int(r['net']),int(r['pin']);crit=float(r['criticality']);bucket=bin_id(crit);focus=FOCUS.get((net,pin));group=focus if focus is not None else 3+bucket
            groups[group]+=1;assert int(r['group'])==group and int(r['group_row'])==groups[group]<= (2000 if focus is not None else 1000)
            u,v,sw=int(r['from']),int(r['to']),int(r['switch']);s=switches[sw];pref=u in ids(r['preferred_ids'])
            assert meta[u]['layer']!=meta[v]['layer'] and bool(int(r['configurable']))==s['configurable'] and bool(int(r['preferred']))==pref
            assert float(r['physical_seconds'])==s['delay']
            before,after,miss=float(r['before_congestion']),float(r['after_congestion']),float(r['miss_weight']);old=f32(before*f32(1+miss)) if s['configurable'] and not pref else before
            applied=a!='C' and s['configurable'] and not pref and not int(r['rcv']) and crit>=THRESHOLD
            if a=='K' and applied:
                key=(net,pin,tuple(ids(r['preferred_ids'])));assert len(metadata_by_shape[key])==1
                configured=next(iter(metadata_by_shape[key]));penalty=configured[-1]
                old_extra=(1-crit)*(old-before);bound=f32(crit*penalty)
                applied=old_extra>bound
            assert (event in applies[a])==applied
            if applied:
                p=applies[a][event];applied_count+=1
                assert all(p[k]==r[k] for k in ['iter','event','attempt','net','pin','from','to','criticality','before_congestion'])
                assert float(p['old_congestion'])==old and float(p['new_congestion'])==after==before
                signature=(float(p['reliability']),float(p['unit_seconds']),float(p['beta']),float(p['penalty_seconds']));key=(net,pin,tuple(ids(r['preferred_ids'])))
                assert signature in metadata_by_shape[key]
                assert float(r['timing_penalty_seconds'])==float(p['penalty_seconds'])
                assert near(crit*float(p['penalty_seconds']),float(p['weighted_timing_seconds']))
                sampled_extra.append((1-crit)*(old-before)/unit);sampled_new.append(crit*float(p['penalty_seconds'])/unit)
            else:assert after==old and float(r['timing_penalty_seconds'])==0
            analytic=(1-crit)*(after-before);physical=crit*s['delay'];timing=0 if int(r['rcv']) else crit*float(r['timing_penalty_seconds'])
            assert near(analytic,float(r['analytic_extra'])) and near(physical,float(r['weighted_physical_seconds'])) and near(timing,float(r['weighted_timing_seconds']))
            if a=='K':assert analytic+f32(crit*float(r['timing_penalty_seconds']))<=(1-crit)*(old-before)+max(1e-30,abs((1-crit)*(old-before))*1e-12)
        assert len(edges[a])==int(summaries[a]['rows'])<=10000
        if a!='C':
            ps=fields(next(l for l in reversed(logs[a]) if l.startswith('H3D_BOUNDED_CRITICAL_SUMMARY ')))
            assert float(ps['threshold'])==THRESHOLD and int(ps['sampled'])==applied_count==len(applies[a])
            assert int(ps['applications'])==int(ps['sampled'])+int(ps['omitted'])
        else:ps=None;assert not applies[a] and not guides[a] and not finals[a]
        final_csv={ (int(r['net']),int(r['pin'])):r for r in csv.DictReader((dirs[a]/'h3d_final_guides.csv').open())}
        if a!='C':assert len(finals[a])==len(final_csv)
        cap_meta=[fields(l) for l in logs[a] if l.startswith('H3D_BOUNDED_CAP_GUIDE ')]
        cap_final=[fields(l) for l in logs[a] if l.startswith('H3D_FINAL_BOUNDED_CAP ')]
        assert len(cap_meta)==(len(guides[a]) if a=='K' else 0) and len(cap_final)==(len(finals[a]) if a=='K' else 0)
        for r in finals[a]:
            net,pin=int(r['net']),int(r['pin']);key=(net,pin,tuple(ids(r['preferred'])));sig=(float(r['reliability']),float(r['unit_seconds']),float(r['beta']),float(r['penalty_seconds']))
            assert key+sig in signatures
            assert ids(r['preferred'])==[int(x) for x in final_csv[net,pin]['preferred'].split(';') if x]
        results[a]=dict(guide_metadata_records=len(guides[a]),final_guide_records=len(finals[a]),sampled_edges=len(edges[a]),sampled_applications=applied_count,summary=ps,sampled_old_extra_units_median=statistics.median(sampled_extra) if sampled_extra else None,sampled_new_timing_units_median=statistics.median(sampled_new) if sampled_new else None)
    rows=[dict(observe(Path(p)),arm=a,reused=True) for a,p in read(b/'registration.json')['references'].items()]+[dict(observe(p),arm=a,reused=False) for a,p in dirs.items()]
    paired={}
    for c,t in [('C','Z'),('Z','K'),('C','K'),('A0','K'),('R1','K')]:
        cr=next(r for r in rows if r['arm']==c);tr=next(r for r in rows if r['arm']==t);ok=cr['status']==tr['status']=='legal';paired[c+'->'+t]=dict(comparable=ok,cpd_improvement_pct=(1-tr['legal_cpd_ns']/cr['legal_cpd_ns'])*100 if ok else None,reference_cpd_ns=cr['legal_cpd_ns'],new_cpd_ns=tr['legal_cpd_ns'])
    assert all(sha(Path(p))==h for p,h in bindings.items())
    out=dict(status='sealed_bounded_critical_cap_audit',passed=True,source_sha256=bindings,observations=rows,comparisons=paired,results=results,oracle_receipts=oracle_receipts,oracle_endpoint_direction_count=len(oracles),exact_coverage_flags_checked=coverage_checks,directed_crossing_edges_checked=len(found),unit_seconds=unit,threshold=THRESHOLD,
        qualification='Cap-only policy: actual float bounded timing contribution never exceeds the analytical original method extra on audited rows; below bound old operation is exact. This is not a bound on native accumulated float path cost or full queue priority. One seen circuit. Default absent-flag control exact old cost behavior; independent fullRRG forward/reverse 4096-settlement oracles validate measured-side coverage. Capped actual crossing rows validate raw float congestion removal, reliability and seconds caps, actual criticality/RCV/configurable exclusions, physical Tdel and final saved guide provenance. Full native/independent route/guide/inputseal audits. Cumulative unrecorded costs not independently replayed; coverage heuristic is not physical/QoR confidence. Native congestion before method multiplier preserved; timing term excluded from physical delay/STA. Ordered traced costs not formal runtime.')
    write(b/'bounded_cap_analysis.json',out);print({k:out[k] for k in ['passed','comparisons','results','oracle_endpoint_direction_count','exact_coverage_flags_checked','directed_crossing_edges_checked']})

if __name__=='__main__':main()
