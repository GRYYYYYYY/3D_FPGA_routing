#!/usr/bin/env python3
"""Fresh directed-edge audit and independent calibrated/shared-objective replay."""
import argparse,collections,math,resource,signal,struct,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from candidate_path_cached_records import records
from analyze_candidate_path_score import parse,close,fingerprint,optimum,assignment_cost
from verify_path_witnesses_v2 import fields,graph_records,f32
from verify_candidate_paths import nodes
from analyze_native_reconvergence_v2 import observe
from run_candidate_path_score import prefix

def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);args=ap.parse_args();b=args.batch.resolve()
    resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));signal.alarm(1800)
    assert read(b/'input_seal.json')['passed'];assert read(b/'completion.json')['disabled_gate_passed'];assert not read(b/'completion.json')['missing_arms']
    rd={a:b/'runs'/('eltwise_layer_'+a) for a in ['K0','K1']};lines={a:(p/'stdout.log').read_text().splitlines() for a,p in rd.items()}
    old=D/'candidate_path_score_eltwise_dev_01/runs/eltwise_layer_S1'
    assert records(lines['K0'])==records((old/'stdout.log').read_text().splitlines())
    assert route_body(rd['K0']/'routed.route')==route_body(old/'routed.route')
    assert records(prefix(lines['K0'],1))==records(prefix(lines['K1'],1))
    graph=Path(read(rd['K1']/'manifest.json')['command'][read(rd['K1']/'manifest.json')['command'].index('--read_rr_graph')+1])
    inputs=[graph,b/'registration.json',b/'completion.json',b/'input_seal.json',Path(__file__),D/'analyze_candidate_path_score.py',D/'verify_candidate_paths.py',D/'verify_path_witnesses_v2.py',D/'candidate_path_cached_records.py']
    inputs += [p/n for p in rd.values() for n in ['stdout.log','manifest.json','independent_audit.json','final_guide_audit.json']]
    bindings={str(p):sha(p) for p in inputs};m=read(rd['K1']/'manifest.json');assert bindings[str(graph)]==m['shared_inputs'][str(graph.resolve())]['sha256']
    data={};summaries={};all_paths=[];wanted=set();wanted_edges=set();cache_counts={};queries={}
    for arm in rd:
        data[arm],summaries[arm]=parse(lines[arm]);queries[arm]=[fields(l) for l in lines[arm] if l.startswith('H3D_CANDIDATE_PATH ')]
        cached=[fields(l) for l in lines[arm] if l.startswith('H3D_PATH_PRICE_CACHE_OBSERVATION ')];cache_counts[arm]=len(cached)
        for r in cached:
            key=int(r['plan']),int(r['net']);data[arm][key]['obs'].append(r)
        for r in queries[arm]+cached:
            if r['path']=='-':continue
            path=nodes(r);assert path[0][0]==int(r['entry']) and path[-1][0]==int(r['sink']);assert len({v[0] for v in path})==len(path)
            wanted.update(x[0] for x in path);wanted_edges.update((u[0],v[0],u[1]) for u,v in zip(path,path[1:]));all_paths.append((r,path,'physical_units' in r))
        for v in data[arm].values():
            for pin,r in v['layout'].items():wanted.add(int(r['sink']))
            for r in v['score'].values():wanted.add(int(r['entry']))
    metadata={};switches={};found_edges=[];pairs={(u,v) for u,v,w in wanted_edges};length=count=0
    for section,e in graph_records(graph):
        a=e.attrib
        if section=='switches':
            timing=e.find('timing');v={} if timing is None else timing.attrib
            assert all(f32(v.get(k,0.))==0 for k in ['R','Cin','Cout','Cinternal']);switches[int(a['id'])]=f32(v.get('Tdel',0.))
        elif section=='rr_nodes':
            node=int(a['id']);v=e.find('loc').attrib
            if a['type'] in ['CHANX','CHANY'] and a.get('direction','NONE')!='NONE':count+=1;length+=1+int(v['xhigh'])-int(v['xlow'])+int(v['yhigh'])-int(v['ylow'])
            if node in wanted:
                timing=e.find('timing');assert timing is None or all(float(timing.attrib.get(k,0))==0 for k in ['R','C'])
                layer=int(v.get('layer_low',v.get('layer',0)));assert layer==int(v.get('layer_high',v.get('layer',0)))
                metadata[node]=dict(kind=a['type'],x=int(v['xlow']),y=int(v['ylow']),layer=layer,capacity=int(a.get('capacity',1)))
        elif section=='rr_edges':
            u,v=int(a['src_node']),int(a['sink_node'])
            if (u,v) in pairs:found_edges.append((u,v,int(a['switch_id'])))
    assert set(metadata)==wanted;assert {(u,v,switches[s]) for u,v,s in found_edges}&wanted_edges==wanted_edges
    span=length/count;cached_checked=fresh_checked=0
    near=lambda a,b:math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-24)
    for r,path,cached in all_paths:
        unit=float(r['unit_seconds']);physical=math.fsum(x[1] for x in path);toll=math.fsum(x[2] for x in path)
        assert path[-1][1]==path[-1][2]==0
        assert metadata[path[0][0]]['layer']!=metadata[path[1][0]]['layer']
        assert all(metadata[x[0]]['layer']==metadata[path[-1][0]]['layer'] for x in path[1:])
        for x in path:
            assert x[4]==metadata[x[0]]['capacity'] and x[3]>=0 and x[6] in [0,1] and not math.isnan(x[5])
        for u,v in zip(path,path[1:]):
            node,delay,unused,occ,cap,acc,owned=v;price=acc*(1+float(r['pres_fac'])*max(0,occ+1-cap))
            fraction=max(0,price-1)/max(1,price) if math.isfinite(price) else 1.
            expected=float(r['toll_weight'])*unit*fraction if metadata[node]['kind'] in ['CHANX','CHANY'] and not owned else 0.
            assert near(u[2],expected)
        if cached:
            assert near(physical/unit,float(r['physical_units'])) and near(toll/unit,float(r['toll_units']))
            assert bool(int(r['exact_proxy']))==(toll==0);cached_checked+=1
            key=int(r['plan']),int(r['net']);pair=data['K1'][key]['pairs'][int(r['pin'])][int(r['entry'])]
            assert int(pair['sink_known'])==1
        else:
            assert near(physical,float(r['physical_path_seconds'])) and near(toll,float(r['toll_path_seconds']))
            assert near(physical+toll,float(r['priced_upper_seconds']));fresh_checked+=1
    work={}
    for arm,qs in queries.items():
        by_plan=collections.defaultdict(list)
        for q in qs:by_plan[int(q['plan']),int(q['net'])].append(q)
        charged=calls=hits=valid=0
        for key,group in by_plan.items():
            remaining=256;memo={};assert len(group)<=4 and len({r['pin'] for r in group})<=2
            for i,q in enumerate(group):
                assert int(q['request'])==i+1 and int(q['requests'])==len(group)
                allowance=max(1,remaining//(len(group)-i)) if remaining else 0;assert int(q['allowance'])==allowance
                amount=int(q['charged']);hit=int(q['cache_hit']);attempt=int(q['attempted']);k=int(q['sink']),int(q['entry'])
                if hit:assert k in memo and amount==0
                elif attempt:assert 0<allowance and amount==int(q['search_expansions'])<=allowance;memo[k]=q
                else:assert allowance==amount==0
                remaining-=amount;assert int(q['remaining'])==remaining>=0;assert int(q['labels'])<=16384 and int(q['peak_heap'])<=65536
                assert float(q['toll_weight'])==.25
                gap=float(q['local_gap']);v=data[arm][key];pin=int(q['pin']);costs=[]
                for entry,p in v['pairs'][pin].items():
                    cost=float(v['entries'][entry]['opening_units'])+float(v['score'].get((pin,entry),{}).get('base_branch',p['branch_units']))
                    costs.append((cost,entry))
                if q['proposed']=='1':chosen_cost=dict((e,c) for c,e in costs)[int(q['entry'])]
                else:
                    # gap/priority are based on pre-score shared assignment, which
                    # may differ from the scored proposal; derive its cost from
                    # candidate cost pairs consistent with the recorded gap.
                    options=[c for c,e in costs if any(close(alt-c,gap) for alt,x in costs if x!=e)]
                    assert options;chosen_cost=options[0]
                expected=float(q['criticality'])*(.25+.75/(1+abs(gap)/max(1,abs(chosen_cost)))) if int(q['rank_alternatives']) else float(q['criticality'])*.25
                assert close(float(q['priority']),expected)
                charged+=amount;calls+=attempt and not hit;hits+=hit;valid+=q['path']!='-'
        summary=fields(next(l for l in reversed(lines[arm]) if l.startswith('H3D_CANDIDATE_PATH_SUMMARY ')))
        for k,value in [('records',len(qs)),('plans',len(by_plan)),('calls',calls),('cache_hits',hits),('charged_expansions',charged),('paths',valid)]:assert int(summary[k])==value
        work[arm]=dict(records=len(qs),plans=len(by_plan),charged=charged,valid=valid,calls=calls,hits=hits)
    totals={};changed_proposals=[]
    for arm,plans in data.items():
        obs_count=est_count=changed=checked=0;leaf_obs=collections.Counter();samples=collections.Counter();maximum_delta=0
        for key,v in plans.items():
            if not v['score']:continue
            unique={};observed={};by_query={(int(q['pin']),int(q['entry'])):q for q in v['queries']}
            for o in v['obs']:
                pin,entry=int(o['pin']),int(o['entry']);sink=int(v['layout'][pin]['sink']);cache='path' in o
                unit=float(o['unit_seconds']) if cache else float(by_query[pin,entry]['unit_seconds'])
                if not cache:
                    q=by_query[pin,entry];assert near(float(o['physical_units']),float(q['physical_path_seconds'])/unit) and near(float(o['toll_units']),float(q['toll_path_seconds'])/unit)
                    assert int(o['exact_proxy'])==(q['stop']=='exact_proxy')
                geometry=2+(abs(metadata[sink]['x']-metadata[entry]['x'])+abs(metadata[sink]['y']-metadata[entry]['y']))/span;assert close(geometry,float(o['geometry_units']))
                sample=(sink,entry);assert int(o['calibration_sample'])==(sample not in unique);unique.setdefault(sample,o)
                assert (pin,entry) not in observed;observed[pin,entry]=o
            assert unique
            scale=sum(min(4,max(.25,float(o['physical_units'])/float(o['geometry_units']))) for o in unique.values())/len(unique)
            rate=sum(min(1,max(0,float(o['toll_units'])/max(1,float(o['physical_units'])))) for o in unique.values())/len(unique)
            rho=1. if all(int(o['exact_proxy']) for o in unique.values()) else .25;samples[len(unique)]+=1
            selected={int(q['pin']) for q in v['queries']};assert {p for p,e in v['score']}==selected
            for pin in selected:leaf_obs[sum(p==pin for p,e in observed)]+=1
            for (pin,entry),r in v['score'].items():
                known=(pin,entry) in observed;geometry=float(r['geometry_units']);risk=float(observed[pin,entry]['toll_units']) if known else geometry*scale*rate
                assert int(r['observed'])==known and int(r['samples'])==len(unique)
                for name,value in [('scale',scale),('rate',rate),('reliability',rho),('risk_units',risk)]:assert close(float(r[name]),value),(arm,key,name)
                delta=float(r['weight'])*rho*float(r['criticality'])*min(2,max(0,risk));assert 0<=delta<=2
                assert close(delta,float(r['delta_units'])) and close(float(r['base_branch'])+delta,float(r['new_branch']))
                assert float(r['new_branch'])==float(v['pairs'][pin][entry]['branch_units'])
                obs_count+=known;est_count+=not known;changed+=float(r['new_branch'])!=float(r['base_branch']);maximum_delta=max(maximum_delta,delta)
            leaves=[];base=[];proposed={};prior={}
            for pin,layout in v['layout'].items():
                sink=int(layout['sink']);assert (int(layout['x']),int(layout['y']))==(metadata[sink]['x'],metadata[sink]['y'])
                cost={e:float(p['branch_units']) for e,p in v['pairs'][pin].items()};original={e:float(v['score'][pin,e]['base_branch']) if (pin,e) in v['score'] else c for e,c in cost.items()}
                leaves.append(dict(pin=pin,x=int(layout['x']),y=int(layout['y']),cost=cost));base.append(dict(pin=pin,x=int(layout['x']),y=int(layout['y']),cost=original))
                for e,p in v['pairs'][pin].items():
                    if int(p['proposed']):assert pin not in proposed;proposed[pin]=e
                    if int(p['prior']):assert pin not in prior;prior[pin]=e
            assert fingerprint(v['entries'],leaves)==v['scored_fp'] and fingerprint(v['entries'],base)==v['base_fp']
            opening={e:float(r['opening_units']) for e,r in v['entries'].items()};best,_=optimum(leaves,opening);assigned=assignment_cost(leaves,opening,proposed);previous=assignment_cost(leaves,opening,prior)
            assert close(best,assigned) and close(best,float(v['decision']['new_cost'])) and close(previous,float(v['decision']['old_cost']))
            accepted=math.isfinite(best) and (not math.isfinite(previous) or best<previous*(1-struct.unpack('f',struct.pack('f',.05))[0]));assert bool(int(v['decision']['accepted']))==accepted;checked+=1
            if arm=='K1':
                oldv=data['K0'][key];old_proposed={(p,e) for p,ps in oldv['pairs'].items() for e,r in ps.items() if r['proposed']=='1'}
                if old_proposed!=set(proposed.items()):changed_proposals.append(dict(plan=key[0],net=key[1],prior_cost=previous,new_cost=best,accepted=accepted,reference_accepted=oldv['decision']['accepted']=='1',fractional_gain=(previous-best)/previous if previous else 0,changed_pair_count=len(old_proposed.symmetric_difference(set(proposed.items())))))
        summary=summaries[arm]
        for k,n in [('records',obs_count+est_count),('observed',obs_count),('estimated',est_count),('changed',changed)]:assert int(summary[k])==n
        totals[arm]=dict(scored_plans=checked,observed=obs_count,estimated=est_count,changed=changed,maximum_delta_units=maximum_delta,leaf_observed_count_distribution=dict(leaf_obs),calibration_sample_counts=dict(samples),summary=summary)
    rows=[dict(observe(Path(p)),arm=a,reused=True) for a,p in read(b/'registration.json')['references'].items()]
    rows += [dict(observe(p),arm=a,reused=False) for a,p in rd.items()]
    assert all(sha(Path(p))==h for p,h in bindings.items())
    result=dict(status='sealed_cached_score_physics_and_objective_audit',passed=True,source_sha256=bindings,observations=rows,work=work,score=totals,physical_paths_checked=dict(cached=cached_checked,fresh=fresh_checked,directed_weighted_edges=len(wanted_edges)),changed_proposals=changed_proposals,
        acceptance_changes=sum(v['decision']['accepted']!=data['K0'][key]['decision']['accepted'] for key,v in data['K1'].items() if v['decision']),same_query_records=queries['K0']==queries['K1'],same_route=route_body(rd['K0']/'routed.route')==route_body(rd['K1']/'routed.route'),same_guides=sha(rd['K0']/'h3d_final_guides.csv')==sha(rd['K1']/'h3d_final_guides.csv'),
        qualification='One seen case, repeated plan/leaf events. Fresh actual RRG edges, bounded destination toll and work audited; no temporal ownership replay or all-query native shortest-distance oracle. Cached zero-toll priced exactness relies on settled physical-shortest forest primitive plus nonnegative toll; positive toll is upper bound only. Independently recomputed calibration, fingerprints, shared optimum and same-objective 5% hysteresis. Ordered development costs are not formal timing.')
    write(b/'cached_score_analysis.json',result);print({k:result[k] for k in ['passed','work','physical_paths_checked','changed_proposals','acceptance_changes','same_query_records','same_route','same_guides']})

if __name__=='__main__':main()
