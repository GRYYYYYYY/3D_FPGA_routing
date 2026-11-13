#!/usr/bin/env python3
"""Independent formula/hash/fixed-hierarchy objective checks on the score pilot."""
import argparse
import collections
import math
from pathlib import Path
import struct
from retained_prefix_workflow import D, read, write, sha, route_body
from candidate_path_records import records
from verify_path_witnesses_v2 import fields,graph_records
from analyze_native_reconvergence_v2 import observe
from run_candidate_path_score import prefix
from routing_log_metrics import ROW


def close(a,b):return a==b or math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)


def split(leaves):
    x=[l['x'] for l in leaves];y=[l['y'] for l in leaves];axis='x' if max(x)-min(x)>=max(y)-min(y) else 'y'
    ordered=sorted(leaves,key=lambda l:(l[axis],l['pin']));n=len(ordered)//2;return ordered[:n],ordered[n:]


def optimum(leaves,opening):
    if len(leaves)==1:
        common=dict(leaves[0]['cost']);best=min((opening[c]+b for c,b in common.items()),default=math.inf)
        return best,common
    a,b=split(leaves);ca,xa=optimum(a,opening);cb,xb=optimum(b,opening)
    common={c:xa[c]+xb[c] for c in xa.keys()&xb.keys()}
    return min(ca+cb,min((opening[c]+v for c,v in common.items()),default=math.inf)),common


def assignment_cost(leaves,opening,assignment):
    if any(l['pin'] not in assignment or assignment[l['pin']] not in l['cost'] for l in leaves):return math.inf
    chosen={assignment[l['pin']] for l in leaves}
    if len(chosen)==1:
        c=next(iter(chosen));return opening[c]+sum(l['cost'][c] for l in leaves)
    a,b=split(leaves);return assignment_cost(a,opening,assignment)+assignment_cost(b,opening,assignment)


def fingerprint(entries,leaves):
    value=14695981039346656037
    def mix(word):
        nonlocal value
        for byte in struct.pack('<Q',word):value=((value^byte)*1099511628211)&((1<<64)-1)
    def bits(number):return struct.unpack('<Q',struct.pack('<d',number))[0]
    mix(len(entries))
    for entry,r in entries.items():mix(entry);mix(bits(float(r['opening_units'])))
    indices={entry:i for i,entry in enumerate(entries)};mix(len(leaves))
    for leaf in leaves:
        for word in [leaf['pin'],leaf['x'],leaf['y'],len(leaf['cost'])]:mix(word)
        for entry,cost in leaf['cost'].items():mix(indices[entry]);mix(bits(cost))
    return value


def parse(lines):
    data=collections.defaultdict(lambda:dict(entries={},pairs=collections.defaultdict(dict),layout={},score={},obs=[],queries=[],base_fp=None,scored_fp=None,decision=None))
    recent={};summary=None
    for line in lines:
        if line.startswith('H3D_TABLE '):
            r=fields(line);recent[int(r['net'])]=int(r['fingerprint'],16);continue
        if line.startswith('H3D_PATH_PRICE_SCORE_SUMMARY '):summary=fields(line);continue
        if not line.startswith(('H3D_PREFIX_ENTRY ','H3D_PREFIX_PAIR ','H3D_PREFIX_DECISION ','H3D_PATH_PRICE_','H3D_CANDIDATE_PATH ')):continue
        r=fields(line)
        if 'plan' not in r:continue
        key=int(r['plan']),int(r['net']);v=data[key]
        if line.startswith('H3D_PREFIX_ENTRY '):v['entries'][int(r['entry'])]=r
        elif line.startswith('H3D_PREFIX_PAIR '):v['pairs'][int(r['pin'])][int(r['entry'])]=r
        elif line.startswith('H3D_PREFIX_DECISION '):v['decision']=r
        elif line.startswith('H3D_PATH_PRICE_LAYOUT '):v['layout'][int(r['pin'])]=r
        elif line.startswith('H3D_PATH_PRICE_TABLE '):v['scored_fp']=int(r['fingerprint'],16);v['base_fp']=recent[key[1]]
        elif line.startswith('H3D_PATH_PRICE_SCORE '):v['score'][int(r['pin']),int(r['entry'])]=r
        elif line.startswith('H3D_PATH_PRICE_OBSERVATION '):v['obs'].append(r)
        elif line.startswith('H3D_CANDIDATE_PATH '):v['queries'].append(r)
    return data,summary


def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);args=ap.parse_args();b=args.batch.resolve()
    assert read(b/'input_seal.json')['passed'];done=read(b/'completion.json');assert done['disabled_gate_passed'] and not done['missing_arms']
    c=b/'runs/eltwise_layer_S0';s=b/'runs/eltwise_layer_S1';baseline=D/'candidate_path_queries_eltwise_dev_01/runs/eltwise_layer_Qp'
    cm=read(c/'manifest.json');sm=read(s/'manifest.json');base=(baseline/'stdout.log').read_text().splitlines();control=(c/'stdout.log').read_text().splitlines();treatment=(s/'stdout.log').read_text().splitlines()
    assert records(control)==records(base) and route_body(c/'routed.route')==route_body(baseline/'routed.route')
    query=lambda lines:[l for l in lines if l.startswith('H3D_CANDIDATE_PATH ')]
    # Exact oracle-input reuse is conditional, never inferred from matching CPD.
    same_queries=query(base)==query(control)==query(treatment)
    assert same_queries,'New trajectories need a fresh actual-RRG query audit; do not reuse this one'
    physical=D/'candidate_path_queries_physical_audit_01/analysis.json';certificate=read(physical);assert certificate['passed'] and read(physical.parent/'input_seal.json')['passed']
    graph=Path(sm['command'][sm['command'].index('--read_rr_graph')+1]);assert sha(graph)==sm['shared_inputs'][str(graph.resolve())]['sha256']
    assert any(Path(p).resolve()==graph.resolve() and h==sha(graph) for p,h in certificate['source_sha256'].items())
    first_c=prefix(control,1);first_s=prefix(treatment,1);allowed={l.split()[0] for l in first_c if l.startswith('H3D_')}
    assert records(first_c,allowed)==records(first_s,allowed)
    assert [l.split()[:1]+l.split()[2:] for l in first_c if ROW.match(l)]==[l.split()[:1]+l.split()[2:] for l in first_s if ROW.match(l)]
    data,summary=parse(treatment);old,_=parse(control);assert summary
    wanted=set();score_records=[];unit_by_plan={};layouts={}
    for key,v in data.items():
        if not v['score']:continue
        assert v['obs'] and v['layout'] and v['scored_fp'] is not None
        for r in v['score'].values():wanted.add(int(r['entry']))
        for pin,r in v['layout'].items():wanted.add(int(r['sink']));layouts[key,pin]=r
        for q in v['queries']:unit_by_plan[key]=float(q['unit_seconds'])
    metadata={};length=count=0
    for section,e in graph_records(graph):
        if section=='rr_edges':break
        if section!='rr_nodes':continue
        a=e.attrib;l=e.find('loc').attrib;node=int(a['id'])
        if a['type'] in ['CHANX','CHANY'] and a.get('direction','NONE')!='NONE':
            count+=1;length+=1+int(l['xhigh'])-int(l['xlow'])+int(l['yhigh'])-int(l['ylow'])
        if node in wanted:metadata[node]=dict(x=int(l['xlow']),y=int(l['ylow']))
    assert set(metadata)==wanted and count>0;span=length/count
    observations=estimates=changed=dp_checks=0;sample_counts=collections.Counter();maximum_delta=0.;proposal_changes=decision_changes=0
    for key,v in data.items():
        if not v['score']:continue
        unique={};by_query={(int(q['pin']),int(q['entry'])):q for q in v['queries']}
        for o in v['obs']:
            pin,entry=int(o['pin']),int(o['entry']);q=by_query[pin,entry];sink=int(q['sink']);unit=float(q['unit_seconds'])
            assert math.isfinite(float(q['priced_upper_seconds'])) and close(float(o['physical_units']),float(q['physical_path_seconds'])/unit)
            assert close(float(o['toll_units']),float(q['toll_path_seconds'])/unit)
            geometry=2+(abs(metadata[sink]['x']-metadata[entry]['x'])+abs(metadata[sink]['y']-metadata[entry]['y']))/span
            assert close(geometry,float(o['geometry_units']))
            sample=(sink,entry);assert int(o['calibration_sample'])==(sample not in unique);unique[sample]=o
            assert int(o['exact_proxy'])==(q['stop']=='exact_proxy')
        scale=sum(min(4.,max(.25,float(o['physical_units'])/float(o['geometry_units']))) for o in unique.values())/len(unique)
        rate=sum(min(1.,max(0.,float(o['toll_units'])/max(1.,float(o['physical_units'])))) for o in unique.values())/len(unique)
        reliability=1. if all(int(o['exact_proxy']) for o in unique.values()) else .25
        sample_counts[len(unique)]+=1;observed={(int(o['pin']),int(o['entry'])):o for o in v['obs']}
        selected_pins={int(q['pin']) for q in v['queries']};assert {p for p,e in v['score']}==selected_pins
        for (pin,entry),r in v['score'].items():
            sink=int(v['layout'][pin]['sink']);geometry=2+(abs(metadata[sink]['x']-metadata[entry]['x'])+abs(metadata[sink]['y']-metadata[entry]['y']))/span
            known=(pin,entry) in observed;risk=float(observed[pin,entry]['toll_units']) if known else geometry*scale*rate
            assert int(r['observed'])==known and int(r['samples'])==len(unique)
            for label,value in [('scale',scale),('rate',rate),('reliability',reliability),('geometry_units',geometry),('risk_units',risk)]:assert close(float(r[label]),value),(key,label)
            delta=float(r['weight'])*reliability*float(r['criticality'])*min(2,max(0,risk));assert 0<=delta<=2
            assert close(delta,float(r['delta_units'])) and close(float(r['base_branch'])+delta,float(r['new_branch']))
            assert float(r['new_branch'])==float(v['pairs'][pin][entry]['branch_units'])
            observations+=known;estimates+=not known;changed+=float(r['new_branch'])!=float(r['base_branch']);maximum_delta=max(maximum_delta,delta)
        leaves=[];base_leaves=[];proposed={};prior={}
        for pin,layout in v['layout'].items():
            sink=int(layout['sink']);assert (int(layout['x']),int(layout['y']))==(metadata[sink]['x'],metadata[sink]['y'])
            costs={entry:float(r['branch_units']) for entry,r in v['pairs'][pin].items()}
            original={entry:float(v['score'][pin,entry]['base_branch']) if (pin,entry) in v['score'] else value for entry,value in costs.items()}
            leaves.append(dict(pin=pin,x=int(layout['x']),y=int(layout['y']),cost=costs));base_leaves.append(dict(pin=pin,x=int(layout['x']),y=int(layout['y']),cost=original))
            for entry,r in v['pairs'][pin].items():
                if int(r['proposed']):assert pin not in proposed;proposed[pin]=entry
                if int(r['prior']):assert pin not in prior;prior[pin]=entry
        assert fingerprint(v['entries'],leaves)==v['scored_fp'] and fingerprint(v['entries'],base_leaves)==v['base_fp']
        opening={entry:float(r['opening_units']) for entry,r in v['entries'].items()}
        best,_=optimum(leaves,opening);assigned=assignment_cost(leaves,opening,proposed);previous=assignment_cost(leaves,opening,prior)
        assert close(best,assigned) and close(best,float(v['decision']['new_cost'])) and close(previous,float(v['decision']['old_cost']))
        expected=math.isfinite(best) and (not math.isfinite(previous) or best<previous*(1-struct.unpack('f',struct.pack('f',.05))[0]))
        assert bool(int(v['decision']['accepted']))==expected;dp_checks+=1
        old_proposed={(pin,entry) for pin,p in old[key]['pairs'].items() for entry,r in p.items() if int(r['proposed'])}
        proposal_changes+=len(old_proposed.symmetric_difference(set(proposed.items())))
        decision_changes+=v['decision']['accepted']!=old[key]['decision']['accepted']
    assert int(summary['records'])==observations+estimates and int(summary['observed'])==observations and int(summary['estimated'])==estimates and int(summary['changed'])==changed
    rows=[]
    for arm,p in read(b/'registration.json')['references'].items():rows.append(dict(observe(Path(p)),arm=arm,reused=True))
    for arm,p in [('Qp',baseline),('S0',c),('S1',s)]:rows.append(dict(observe(p),arm=arm,reused=arm=='Qp'))
    result=dict(status='sealed_calibrated_price_score_analysis',passed=True,observations=rows,score_records=observations+estimates,observed_score_records=observations,estimated_score_records=estimates,
        changed_branch_records=changed,maximum_delta_units=maximum_delta,calibrated_plan_sample_counts=dict(sample_counts),independent_dp_fingerprint_checks=dp_checks,
        shared_dp_proposal_symmetric_difference=proposal_changes,acceptance_changes=decision_changes,same_query_records=same_queries,
        same_route=route_body(c/'routed.route')==route_body(s/'routed.route'),same_final_guides=sha(c/'h3d_final_guides.csv')==sha(s/'h3d_final_guides.csv'),
        physical_query_certificate_reuse=dict(passed=True,source=str(physical),sha256=sha(physical),criterion='Identical graph hash and every directed query path/node-price/work record; not inferred from final CPD.'),
        source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'completion.json',b/'input_seal.json',c/'manifest.json',s/'manifest.json',s/'stdout.log',physical,Path(__file__)]},
        qualification='One seen case, repeated plan/leaf records. Independently rebuilt calibration, bounded additions, base/scored fingerprints, fixed-hierarchy optimum and same-score prior hysteresis. Physical certificate reused only for exactly identical query records. No QoR or formal runtime claim from unchanged routes or altered proxy tables.')
    write(b/'price_score_analysis.json',result);print({k:v for k,v in result.items() if k not in ['observations','source_sha256','qualification','physical_query_certificate_reuse']})


if __name__=='__main__':main()
