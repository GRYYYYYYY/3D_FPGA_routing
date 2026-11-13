#!/usr/bin/env python3
"""Fresh path/price audit and independent per-leaf delay and shared-objective replay."""
import argparse,collections,math,resource,signal,statistics,struct
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from compact_witness_records import records
from analyze_candidate_path_score import parse,close,fingerprint,optimum,assignment_cost
from verify_path_witnesses_v2 import fields,graph_records,f32
from verify_candidate_paths import nodes
from analyze_native_reconvergence_v2 import observe
from run_candidate_path_score import prefix
from routing_log_metrics import ROW
import heapq

def pre_cost_records(lines):
    return [l for l in lines if l.startswith(('H3D_TABLE ','H3D_PREFIX_'))]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);args=ap.parse_args();b=args.batch.resolve()
    resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));signal.alarm(1800)
    assert read(b/'input_seal.json')['passed'];done=read(b/'completion.json');assert done['disabled_gate_passed'] and not done['missing_arms']
    dirs={a:b/'runs'/('eltwise_layer_'+a) for a in ['F','G','E','N']};logs={a:(p/'stdout.log').read_text().splitlines() for a,p in dirs.items()}
    prior=D/'candidate_path_delay_eltwise_dev_01/runs/eltwise_layer_D1';control=prior
    assert records(logs['F'])==records((prior/'stdout.log').read_text().splitlines())
    assert route_body(dirs['F']/'routed.route')==route_body(prior/'routed.route') and sha(dirs['F']/'h3d_final_guides.csv')==sha(prior/'h3d_final_guides.csv')
    first_c=prefix(logs['F'],1);first_r=prefix(logs['N'],1)
    # Extra reverse work is intended from the initial planning pass. Check the
    # actual initial plan fingerprints and native row, not equality of work.
    assert [l for l in first_c if l.startswith('H3D_TABLE ')]==[l for l in first_r if l.startswith('H3D_TABLE ')]
    assert [l.split()[:1]+l.split()[2:] for l in first_c if ROW.match(l)]==[l.split()[:1]+l.split()[2:] for l in first_r if ROW.match(l)]
    oldscore=D/'candidate_path_delay_eltwise_dev_01/runs/eltwise_layer_D0'
    assert records(logs['G'])==records((oldscore/'stdout.log').read_text().splitlines())
    assert route_body(dirs['G']/'routed.route')==route_body(oldscore/'routed.route')
    assert pre_cost_records(logs['G'])==pre_cost_records(logs['E'])
    assert route_body(dirs['G']/'routed.route')==route_body(dirs['E']/'routed.route')
    assert sha(dirs['G']/'h3d_final_guides.csv')==sha(dirs['E']/'h3d_final_guides.csv')
    for a in ['F','G','E','N']:
        env=read(dirs[a]/'manifest.json')['environment'];assert env['VPR_H3D_CANDIDATE_PATH_SCORE']=='0' and env['VPR_H3D_CANDIDATE_PATH_DELAY']==('0.25' if a in ['F','N'] else '0') and env['VPR_H3D_SOURCE_EMPTY_REVERSE']=='0' and env['VPR_H3D_SOURCE_COVERAGE_SKIP']==('1' if a in ['E','N'] else '0')
    m=read(dirs['N']/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);gh=sha(graph);assert gh==m['shared_inputs'][str(graph.resolve())]['sha256']
    inputs=[Path(__file__),D/'analyze_candidate_path_score.py',D/'verify_candidate_paths.py',D/'verify_path_witnesses_v2.py',D/'compact_witness_unit_01/validation.json',D/'path_witness_unit_01/validation.json',b/'registration.json',b/'input_seal.json',b/'completion.json',graph]
    inputs += [p/n for p in dirs.values() for n in ['stdout.log','manifest.json','independent_audit.json','final_guide_audit.json']]
    inputs += [control/'stdout.log',control/'routed.route']
    bindings={str(p):sha(p) for p in inputs};data={};summaries={};delay={};queries={};cached={};paths=[];wanted=set();wanted_edges=set()
    for a in dirs:
        data[a],summaries[a]=parse(logs[a]);queries[a]=[fields(l) for l in logs[a] if l.startswith('H3D_CANDIDATE_PATH ')];cached[a]=[fields(l) for l in logs[a] if l.startswith('H3D_PATH_PRICE_CACHE_OBSERVATION ')];delay[a]={}
        for r in cached[a]:data[a][int(r['plan']),int(r['net'])]['obs'].append(r)
        for line in logs[a]:
            if line.startswith('H3D_PATH_DELAY_SCORE '):
                r=fields(line);delay[a][tuple(int(r[k]) for k in ['plan','net','pin','entry'])]=r
        for r in queries[a]+cached[a]:
            if r['path']=='-':continue
            path=nodes(r);assert path[0][0]==int(r['entry']) and path[-1][0]==int(r['sink']);assert len({x[0] for x in path})==len(path)
            paths.append((a,r,path,'physical_units' in r));wanted.update(x[0] for x in path);wanted_edges.update((u[0],v[0],u[1]) for u,v in zip(path,path[1:]))
        for v in data[a].values():
            for r in v['layout'].values():wanted.add(int(r['sink']))
            for r in v['score'].values():wanted.add(int(r['entry']))
    gate_rows={a:[fields(l) for l in logs[a] if l.startswith('H3D_SOURCE_COVERAGE_SKIP ')] for a in ['E','N']}
    gate_summary={a:fields(next(l for l in reversed(logs[a]) if l.startswith('H3D_SOURCE_COVERAGE_SKIP_SUMMARY '))) for a in ['E','N']}
    for arm,rs in gate_rows.items():
        summary=gate_summary[arm];assert int(summary['omitted'])==0 and int(summary['rows'])==int(summary['skips'])==len(rs)
        assert int(summary['checks'])>=len(rs)
        for r in rs:
            entries=[(int(x),int(y)) for x,y in (s.split(',') for s in r['entries'].split(';'))]
            assert len(entries)==int(r['ranked']) and len({x for x,y in entries})==len(entries)
            assert all(y in [0,1] for x,y in entries)
            assert int(r['need'])==min(16,len(entries)) and sum(y for x,y in entries)==int(r['available'])<int(r['need'])
    layers=[];adj=[];cross=[]
    metadata={};switches={};found=[];pairs={(u,v) for u,v,w in wanted_edges};length=count=0
    for section,e in graph_records(graph):
        a=e.attrib
        if section=='switches':
            t=e.find('timing');v={} if t is None else t.attrib;assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal']);switches[int(a['id'])]=f32(v.get('Tdel',0))
        elif section=='rr_nodes':
            node=int(a['id']);v=e.find('loc').attrib
            assert node==len(layers);layer=int(v.get('layer_low',v.get('layer',0)));assert layer==int(v.get('layer_high',v.get('layer',0)));layers.append(layer)
            t=e.find('timing');assert t is None or all(float(t.attrib.get(k,0))==0 for k in ['R','C'])
            if a['type'] in ['CHANX','CHANY'] and a.get('direction','NONE')!='NONE':count+=1;length+=1+int(v['xhigh'])-int(v['xlow'])+int(v['yhigh'])-int(v['ylow'])
            if node in wanted:
                t=e.find('timing');assert t is None or all(float(t.attrib.get(k,0))==0 for k in ['R','C'])
                layer=int(v.get('layer_low',v.get('layer',0)));assert layer==int(v.get('layer_high',v.get('layer',0)))
                metadata[node]=dict(x=int(v['xlow']),y=int(v['ylow']),kind=a['type'],capacity=int(a.get('capacity',1)),layer=layer)
        elif section=='rr_edges':
            u,v=int(a['src_node']),int(a['sink_node'])
            if not adj:adj=[[] for _ in layers];cross=[False for _ in layers]
            switch=int(a['switch_id'])
            if layers[u]==layers[v]:adj[u].append((v,switches[switch]))
            else:cross[u]=True
            if (u,v) in pairs:found.append((u,v,switch))
    assert set(metadata)==wanted and {(u,v,switches[s]) for u,v,s in found}&wanted_edges==wanted_edges;span=length/count
    budget=int(fields(next(l for l in logs['N'] if l.startswith('H3D_DELAY_INIT ')))['budget']);assert budget==4096
    virtual={node:len(layers)+i for i,node in enumerate(n for n,has in enumerate(cross) if has)}
    inverse={v:k for k,v in virtual.items()};source_oracles={};oracle_source_sets={}
    for source in sorted({int(r['source']) for rs in gate_rows.values() for r in rs}):
        best={source:0.};queue=[(0.,source)];settled=set();terminal_entries=set()
        while queue and len(settled)<budget:
            cost,node=heapq.heappop(queue)
            if node in settled or cost!=best[node]:continue
            settled.add(node)
            if node>=len(layers):terminal_entries.add(inverse[node]);continue
            neighbors=adj[node]
            if node in virtual:neighbors=neighbors+[(virtual[node],0.)]
            for next_node,weight in neighbors:
                candidate=cost+weight
                if candidate<best.get(next_node,math.inf):best[next_node]=candidate;heapq.heappush(queue,(candidate,next_node))
        oracle_source_sets[source]=terminal_entries
        source_oracles[source]=dict(settled=len(settled),measured_terminals=len(terminal_entries),queue_nonempty=bool(queue))
    availability_checks=0
    for rs in gate_rows.values():
        for r in rs:
            known=oracle_source_sets[int(r['source'])]
            for item in r['entries'].split(';'):
                entry,flag=map(int,item.split(','));assert bool(flag)==(entry in known);availability_checks+=1
    del adj,cross,layers,virtual,inverse
    near=lambda a,b:math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-24)
    physical_counts=collections.Counter()
    for a,r,path,iscache in paths:
        unit=float(r['unit_seconds']);physical=math.fsum(x[1] for x in path);toll=math.fsum(x[2] for x in path)
        assert path[-1][1]==path[-1][2]==0
        assert metadata[path[0][0]]['layer']!=metadata[path[1][0]]['layer'] and all(metadata[x[0]]['layer']==metadata[path[-1][0]]['layer'] for x in path[1:])
        for x in path:assert x[4]==metadata[x[0]]['capacity'] and x[3]>=0 and x[6] in [0,1] and not math.isnan(x[5])
        for u,v in zip(path,path[1:]):
            node,d,t,occ,cap,acc,owned=v;price=acc*(1+float(r['pres_fac'])*max(0,occ+1-cap));fraction=max(0,price-1)/max(1,price) if math.isfinite(price) else 1.
            expected=float(r['toll_weight'])*unit*fraction if metadata[node]['kind'] in ['CHANX','CHANY'] and not owned else 0.;assert near(expected,u[2])
        if iscache:
            assert near(physical/unit,float(r['physical_units'])) and near(toll/unit,float(r['toll_units'])) and bool(int(r['exact_proxy']))==(toll==0);physical_counts[a+'_cached']+=1
        else:
            upper=float(r['priced_upper_seconds']);lower=float(r['lower_priced_seconds'])
            assert near(physical,float(r['physical_path_seconds'])) and near(toll,float(r['toll_path_seconds'])) and near(physical+toll,upper)
            if math.isfinite(lower):assert lower<=upper+max(1e-24,abs(upper)*1e-10)
            if r['stop']=='exact_proxy':assert near(lower,upper)
            physical_counts[a+'_fresh']+=1
    work={}
    for a,qs in queries.items():
        by_plan=collections.defaultdict(list)
        for q in qs:by_plan[int(q['plan']),int(q['net'])].append(q)
        charged=calls=hits=valid=0
        for key,group in by_plan.items():
            remaining=256;memo={};assert len(group)<=4 and len({q['pin'] for q in group})<=2
            for i,q in enumerate(group):
                assert int(q['request'])==i+1 and int(q['requests'])==len(group)
                allowance=max(1,remaining//(len(group)-i)) if remaining else 0;assert int(q['allowance'])==allowance
                amount=int(q['charged']);hit=int(q['cache_hit']);attempt=int(q['attempted']);k=int(q['sink']),int(q['entry'])
                if hit:
                    assert k in memo and amount==0
                    assert all(q[k]==memo[int(q['sink']),int(q['entry'])][k] for k in ['path','stop','priced_upper_seconds','physical_path_seconds','toll_path_seconds','lower_priced_seconds'])
                elif attempt:assert allowance>0 and amount==int(q['search_expansions'])<=allowance;memo[k]=q
                else:assert allowance==amount==0
                remaining-=amount;assert int(q['remaining'])==remaining>=0
                assert int(q['labels'])<=16384 and int(q['peak_heap'])<=65536 and float(q['toll_weight'])==.25
                charged+=amount;calls+=attempt and not hit;hits+=hit;valid+=q['path']!='-'
        summary=fields(next(l for l in reversed(logs[a]) if l.startswith('H3D_CANDIDATE_PATH_SUMMARY ')))
        for k,n in [('records',len(qs)),('plans',len(by_plan)),('charged_expansions',charged),('calls',calls),('cache_hits',hits),('paths',valid)]:assert int(summary[k])==n
        work[a]=dict(requests=len(qs),plans=len(by_plan),charged=charged,valid=valid)
    totals={};dp=0;delays_checked=0;maximum=0.;minimum=0.;zero_source_observations=0
    for a in ['F','N']:
        price_observed=price_estimated=price_changed=0;physical_changed=0;physical_observed=physical_estimated=0;median_checks=0;scored_plans=0
        for key,v in data[a].items():
            if not v['score']:continue
            scored_plans+=1;unique={};observed={};byquery={(int(q['pin']),int(q['entry'])):q for q in v['queries']}
            for o in v['obs']:
                pin,entry=int(o['pin']),int(o['entry']);sink=int(v['layout'][pin]['sink']);iscache='path' in o
                if not iscache:
                    q=byquery[pin,entry];unit=float(q['unit_seconds']);assert near(float(o['physical_units']),float(q['physical_path_seconds'])/unit) and near(float(o['toll_units']),float(q['toll_path_seconds'])/unit)
                geometry=2+(abs(metadata[sink]['x']-metadata[entry]['x'])+abs(metadata[sink]['y']-metadata[entry]['y']))/span;assert close(geometry,float(o['geometry_units']))
                sample=sink,entry;assert int(o['calibration_sample'])==(sample not in unique);unique.setdefault(sample,o);assert (pin,entry) not in observed;observed[pin,entry]=o
            assert unique
            scale=sum(min(4,max(.25,float(o['physical_units'])/float(o['geometry_units']))) for o in unique.values())/len(unique)
            rate=sum(min(1,max(0,float(o['toll_units'])/max(1,float(o['physical_units'])))) for o in unique.values())/len(unique);rho=1 if all(int(o['exact_proxy']) for o in unique.values()) else .25
            physical_by_leaf=collections.defaultdict(dict)
            for (pin,entry),o in observed.items():
                if 'path' in o:physical_by_leaf[pin][entry]=o
            for (pin,entry),r in v['score'].items():
                known=(pin,entry) in observed;risk=float(observed[pin,entry]['toll_units']) if known else float(r['geometry_units'])*scale*rate
                assert int(r['observed'])==known and int(r['samples'])==len(unique)
                for name,value in [('scale',scale),('rate',rate),('reliability',rho),('risk_units',risk)]:assert close(float(r[name]),value)
                delta=float(r['weight'])*rho*float(r['criticality'])*min(2,max(0,risk));assert close(delta,float(r['delta_units'])) and close(float(r['base_branch'])+delta,float(r['new_branch']))
                assert float(r['weight'])==0
                price_observed+=known;price_estimated+=not known;price_changed+=float(r['new_branch'])!=float(r['base_branch'])
                z=delay[a].get(key+(pin,entry));physical=physical_by_leaf[pin]
                expected_delay=bool(physical);assert bool(z)==expected_delay
                if z:
                    ratios=[min(4,max(.25,float(o['physical_units'])/float(o['geometry_units']))) for o in physical.values()];fit=statistics.median(ratios)
                    assert int(z['leaf_samples'])==len(ratios) and close(float(z['scale']),fit)
                    measured=entry in physical;assert bool(int(z['physical_measured']))==measured
                    previous=float(physical[entry]['physical_units']) if int(z['legacy_timed']) else float(r['geometry_units'])
                    next_sink=float(physical[entry]['physical_units']) if measured else float(r['geometry_units'])*fit
                    assert close(previous,float(z['previous_sink_units'])) and close(next_sink,float(z['next_sink_units']))
                    crit=float(r['criticality']);correction=.25*(1+4*crit)*min(2,max(-2,next_sink-previous))
                    assert float(z['weight'])==.25 and float(z['sink_cap_units'])==2 and close(correction,float(z['delta_units']))
                    assert close(float(z['price_branch']),float(r['new_branch'])) and close(float(z['price_branch'])+correction,float(z['new_branch']))
                    # Independent old sink/source decomposition, without trusting
                    # the reported timed flag to choose an arbitrary baseline.
                    source=float(v['entries'][entry]['source_units' if int(z['legacy_timed']) else 'geometry_source_units'])
                    assert close(previous*(1+4*crit)+4*crit*source,float(r['base_branch']))
                    assert close(float(z['new_branch']),float(v['pairs'][pin][entry]['branch_units'])) and float(z['new_branch'])>=0
                    delays_checked+=1;physical_changed+=float(z['price_branch'])!=float(z['new_branch']);physical_observed+=measured;physical_estimated+=not measured;maximum=max(maximum,correction);minimum=min(minimum,correction)
                    zero_source_observations+=measured and v['entries'][entry]['source_known']=='0';median_checks+=1
                else:assert float(r['new_branch'])==float(v['pairs'][pin][entry]['branch_units'])
            leaves=[];base=[];proposed={};previous_assignment={}
            for pin,layout in v['layout'].items():
                sink=int(layout['sink']);assert (int(layout['x']),int(layout['y']))==(metadata[sink]['x'],metadata[sink]['y'])
                cost={entry:float(p['branch_units']) for entry,p in v['pairs'][pin].items()};original={entry:float(v['score'][pin,entry]['base_branch']) if (pin,entry) in v['score'] else value for entry,value in cost.items()}
                leaves.append(dict(pin=pin,x=int(layout['x']),y=int(layout['y']),cost=cost));base.append(dict(pin=pin,x=int(layout['x']),y=int(layout['y']),cost=original))
                for entry,p in v['pairs'][pin].items():
                    if p['proposed']=='1':assert pin not in proposed;proposed[pin]=entry
                    if p['prior']=='1':assert pin not in previous_assignment;previous_assignment[pin]=entry
            assert fingerprint(v['entries'],leaves)==v['scored_fp'] and fingerprint(v['entries'],base)==v['base_fp']
            opening={entry:float(r['opening_units']) for entry,r in v['entries'].items()};best,_=optimum(leaves,opening);assigned=assignment_cost(leaves,opening,proposed);before=assignment_cost(leaves,opening,previous_assignment)
            assert close(best,assigned) and close(best,float(v['decision']['new_cost'])) and close(before,float(v['decision']['old_cost']))
            expected=math.isfinite(best) and (not math.isfinite(before) or best<before*(1-struct.unpack('f',struct.pack('f',.05))[0]));assert bool(int(v['decision']['accepted']))==expected;dp+=1
        summary=summaries[a]
        for k,n in [('records',price_observed+price_estimated),('observed',price_observed),('estimated',price_estimated),('changed',price_changed),('plans',scored_plans)]:assert int(summary[k])==n
        totals[a]=dict(scored_plans=scored_plans,price_observed=price_observed,price_estimated=price_estimated,price_changed=price_changed,physical_observed=physical_observed,physical_estimated=physical_estimated,physical_changed=physical_changed,per_candidate_median_checks=median_checks)
    for arm in ['F','N']:
        ds=fields(next(l for l in reversed(logs[arm]) if l.startswith('H3D_PATH_DELAY_SUMMARY ')))
        assert int(ds['records'])==len(delay[arm]) and int(ds['changed'])==totals[arm]['physical_changed']
    assert delays_checked==sum(len(x) for x in delay.values())
    rows=[dict(observe(Path(p)),arm=a,reused=True) for a,p in read(b/'registration.json')['references'].items()];rows += [dict(observe(p),arm=a,reused=False) for a,p in dirs.items()]
    c=next(r for r in rows if r['arm']=='F');t=next(r for r in rows if r['arm']=='N');comparable=c['status']==t['status']=='legal'
    comparison=dict(comparable=comparable,cpd_improvement_pct=(1-t['legal_cpd_ns']/c['legal_cpd_ns'])*100 if comparable else None,reference_status=c['status'],new_status=t['status'])
    assert all(sha(Path(p))==h for p,h in bindings.items())
    result=dict(status='sealed_source_coverage_gate_audit',passed=True,source_sha256=bindings,observations=rows,comparison=comparison,work=work,physical_path_records_checked=dict(physical_counts),directed_weighted_edges_checked=len(wanted_edges),score=totals,dp_fingerprint_checks=dp,delay_records_checked=delays_checked,minimum_correction_units=minimum,maximum_correction_units=maximum,measured_sink_with_unknown_source_records=zero_source_observations,
        same_route=route_body(dirs['F']/'routed.route')==route_body(dirs['N']/'routed.route'),same_final_guides=sha(dirs['F']/'h3d_final_guides.csv')==sha(dirs['N']/'h3d_final_guides.csv'),
        qualification='One seen case; fresh independent actual RRG edge/path/toll and query work checks; no temporal-state replay or full native shortest-distance oracle. Exact cached physical distances rely on the independently tested settled-forest primitive; new priced query UBs excluded from physical calibration. Per-leaf median, signed bounded correction, baseline sink/source decomposition, both fingerprints, shared optimum and same-score hysteresis recomputed. Ordered development time not formal runtime.')
    result['source_coverage_gate']=dict(summary=gate_summary,independent_forward_oracles=source_oracles,query_budget=budget,candidate_availability_checks=availability_checks,old_score_complete_route_and_guides_equivalent=True,old_score_all_base_tables_and_decisions_equivalent=True)
    result['qualification']+=' Full independent 4096-settlement forward Dijkstra on actual same-layer RR edges/virtual terminals verifies every source-known flag on every skipped ranked candidate set. Source-coverage skip equivalence tested separately under old and new scores.'
    write(b/'source_coverage_analysis.json',result);print({k:result[k] for k in ['passed','comparison','work','score','dp_fingerprint_checks','delay_records_checked','minimum_correction_units','maximum_correction_units','measured_sink_with_unknown_source_records','same_route','same_final_guides']})

if __name__=='__main__':main()
