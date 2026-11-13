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

def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);args=ap.parse_args();b=args.batch.resolve()
    resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));signal.alarm(1800)
    assert read(b/'input_seal.json')['passed'];done=read(b/'completion.json');assert done['disabled_gate_passed'] and not done['missing_arms']
    dirs={a:b/'runs'/('eltwise_layer_'+a) for a in ['P','D0','D1']};logs={a:(p/'stdout.log').read_text().splitlines() for a,p in dirs.items()}
    prior=D/'compact_witness_eltwise_dev_01/runs/eltwise_layer_C1';control=D/'candidate_path_queries_eltwise_dev_01/runs/eltwise_layer_Qp'
    assert records(logs['P'])==records((prior/'stdout.log').read_text().splitlines());assert route_body(dirs['P']/'routed.route')==route_body(prior/'routed.route')
    assert route_body(dirs['D0']/'routed.route')==route_body(control/'routed.route') and sha(dirs['D0']/'h3d_final_guides.csv')==sha(control/'h3d_final_guides.csv')
    pre=lambda ls:[l for l in ls if l.startswith('H3D_PREFIX_')]
    assert pre(logs['D0'])==pre((control/'stdout.log').read_text().splitlines())
    first_control=prefix(logs['D0'],1);first_treatment=prefix(logs['D1'],1)
    allowed={l.split()[0] for l in first_control if l.startswith('H3D_')}
    assert records(first_control,allowed)==records(first_treatment,allowed)
    for line in first_treatment:
        if line.startswith('H3D_PATH_DELAY_SUMMARY '):
            r=fields(line);assert r['records']==r['changed']=='0'
        if line.startswith('H3D_PATH_PRICE_SCORE_SUMMARY '):
            r=fields(line);assert all(r[k]=='0' for k in ['plans','records','observed','estimated','changed','extra_solves'])
    # Explicit native settings check: isolate delay, not a price+delay mixture.
    for a in ['D0','D1']:
        env=read(dirs[a]/'manifest.json')['environment'];assert env['VPR_H3D_CANDIDATE_PATH_SCORE']=='0' and env['VPR_H3D_CANDIDATE_PATH_DELAY']==('0.25' if a=='D1' else '0')
    m=read(dirs['D1']/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);gh=sha(graph);assert gh==m['shared_inputs'][str(graph.resolve())]['sha256']
    inputs=[Path(__file__),D/'analyze_candidate_path_score.py',D/'verify_candidate_paths.py',D/'verify_path_witnesses_v2.py',D/'compact_witness_unit_01/validation.json',D/'path_witness_unit_01/validation.json',b/'registration.json',b/'input_seal.json',b/'completion.json',graph]
    inputs += [p/n for p in dirs.values() for n in ['stdout.log','manifest.json','independent_audit.json','final_guide_audit.json']]
    inputs += [control/'stdout.log',control/'routed.route',prior/'stdout.log']
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
    metadata={};switches={};found=[];pairs={(u,v) for u,v,w in wanted_edges};length=count=0
    for section,e in graph_records(graph):
        a=e.attrib
        if section=='switches':
            t=e.find('timing');v={} if t is None else t.attrib;assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal']);switches[int(a['id'])]=f32(v.get('Tdel',0))
        elif section=='rr_nodes':
            node=int(a['id']);v=e.find('loc').attrib
            if a['type'] in ['CHANX','CHANY'] and a.get('direction','NONE')!='NONE':count+=1;length+=1+int(v['xhigh'])-int(v['xlow'])+int(v['yhigh'])-int(v['ylow'])
            if node in wanted:
                t=e.find('timing');assert t is None or all(float(t.attrib.get(k,0))==0 for k in ['R','C'])
                layer=int(v.get('layer_low',v.get('layer',0)));assert layer==int(v.get('layer_high',v.get('layer',0)))
                metadata[node]=dict(x=int(v['xlow']),y=int(v['ylow']),kind=a['type'],capacity=int(a.get('capacity',1)),layer=layer)
        elif section=='rr_edges':
            u,v=int(a['src_node']),int(a['sink_node'])
            if (u,v) in pairs:found.append((u,v,int(a['switch_id'])))
    assert set(metadata)==wanted and {(u,v,switches[s]) for u,v,s in found}&wanted_edges==wanted_edges;span=length/count
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
    for a in ['P','D1']:
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
                assert float(r['weight'])==(1 if a=='P' else 0)
                price_observed+=known;price_estimated+=not known;price_changed+=float(r['new_branch'])!=float(r['base_branch'])
                z=delay[a].get(key+(pin,entry));physical=physical_by_leaf[pin]
                expected_delay=a=='D1' and bool(physical);assert bool(z)==expected_delay
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
    ds=fields(next(l for l in reversed(logs['D1']) if l.startswith('H3D_PATH_DELAY_SUMMARY ')));assert int(ds['records'])==delays_checked==len(delay['D1']) and int(ds['changed'])==totals['D1']['physical_changed']
    rows=[dict(observe(Path(p)),arm=a,reused=True) for a,p in read(b/'registration.json')['references'].items()];rows += [dict(observe(p),arm=a,reused=False) for a,p in dirs.items()]
    c=next(r for r in rows if r['arm']=='D0');t=next(r for r in rows if r['arm']=='D1');comparable=c['status']==t['status']=='legal'
    comparison=dict(comparable=comparable,cpd_improvement_pct=(1-t['legal_cpd_ns']/c['legal_cpd_ns'])*100 if comparable else None,reference_status=c['status'],new_status=t['status'])
    assert all(sha(Path(p))==h for p,h in bindings.items())
    result=dict(status='sealed_physical_sink_delay_audit',passed=True,source_sha256=bindings,observations=rows,comparison=comparison,work=work,physical_path_records_checked=dict(physical_counts),directed_weighted_edges_checked=len(wanted_edges),score=totals,dp_fingerprint_checks=dp,delay_records_checked=delays_checked,minimum_correction_units=minimum,maximum_correction_units=maximum,measured_sink_with_unknown_source_records=zero_source_observations,
        same_route=route_body(dirs['D0']/'routed.route')==route_body(dirs['D1']/'routed.route'),same_final_guides=sha(dirs['D0']/'h3d_final_guides.csv')==sha(dirs['D1']/'h3d_final_guides.csv'),
        qualification='One seen case; fresh independent actual RRG edge/path/toll and query work checks; no temporal-state replay or full native shortest-distance oracle. Exact cached physical distances rely on the independently tested settled-forest primitive; new priced query UBs excluded from physical calibration. Per-leaf median, signed bounded correction, baseline sink/source decomposition, both fingerprints, shared optimum and same-score hysteresis recomputed. Ordered development time not formal runtime.')
    write(b/'physical_delay_analysis.json',result);print({k:result[k] for k in ['passed','comparison','work','score','dp_fingerprint_checks','delay_records_checked','minimum_correction_units','maximum_correction_units','measured_sink_with_unknown_source_records','same_route','same_final_guides']})

if __name__=='__main__':main()
