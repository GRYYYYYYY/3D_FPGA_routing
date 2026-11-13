#!/usr/bin/env python3
import collections,math,subprocess,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import fields
from analyze_retained_prefix import parse_trace
from test_outside_dp_core import serialize,parse
ROOT=D.parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from check_route import read_trace

def main():
    out=D/'outside_dp_table_replay_01';out.mkdir(exist_ok=False);b=D/'retained_outside_trace_eltwise_dev_01';audit=read(b/'outside_trace_analysis.json');assert audit['passed'];core=D/'outside_dp_core_01';assert read(core/'unit_validation.json')['passed'];rd=b/'runs/eltwise_layer_D';lines=(rd/'stdout.log').read_text().splitlines();parsed=parse_trace(lines);print(type(parsed),flush=True)
    # Parse original finite matrices directly; keep the observer's per-plan event association separate.
    event=None;prefix_event={};contexts={};leaflog={};entries=collections.defaultdict(dict);pairs=collections.defaultdict(dict);decisions={}
    for l in lines:
        if l.startswith('H3D_OUTSIDE_CONTEXT '):r=fields(l);event=int(r['event']);contexts[event]=r
        elif l.startswith('H3D_OUTSIDE_LEAF '):r=fields(l);leaflog[int(r['event']),int(r['pin'])]=r
        elif l.startswith('H3D_PREFIX_TABLE '):
            r=fields(l)
            if event is not None and contexts[event]['net']==r['net']:prefix_event[int(r['plan'])]=event
        elif l.startswith('H3D_PREFIX_ENTRY '):
            r=fields(l);p=int(r['plan'])
            if p in prefix_event:entries[p][int(r['entry'])]=float(r['opening_units'])
        elif l.startswith('H3D_PREFIX_PAIR '):
            r=fields(l);p=int(r['plan'])
            if p in prefix_event:pairs[p][int(r['pin']),int(r['entry'])]=r
        elif l.startswith('H3D_PREFIX_DECISION '):r=fields(l);decisions[int(r['plan'])]=r
    routes=read_trace(rd/'routed.route');locations={(net,n.pin):n.low[:2] for net,r in routes.items() for n in r['trace'] if n.kind=='SINK' and n.pin is not None}
    outside={}
    for w in audit['rows']:
        if w['reason']=='valid':outside[w['event'],w['pin']]=min(outside.get((w['event'],w['pin']),math.inf),w['raw'])
    cases=[];labels=[];metadata={}
    for plan,ev in sorted(prefix_event.items()):
        opening=list(entries[plan].values());channel={entry:i for i,entry in enumerate(entries[plan])};pins=sorted({pin for pin,e in pairs[plan]});prior={};leaves=[];proposed={}
        for pin in pins:
            rs=[r for (p,e),r in pairs[plan].items() if p==pin];cs={channel[int(r['entry'])]:float(r['branch_units']) for r in rs};old=[channel[int(r['entry'])] for r in rs if r['prior']=='1'];current=[channel[int(r['entry'])] for r in rs if r['proposed']=='1']
            if len(old)==1:prior[pin]=old[0]
            if len(current)==1:proposed[pin]=current[0]
            x,y=locations[int(contexts[ev]['net']),pin];leaves.append(dict(pin=pin,x=x,y=y,outside=math.inf,candidates=cs))
        base=dict(opening=opening,leaves=leaves,prior=prior);metadata[plan]=dict(event=ev,net=int(contexts[ev]['net']),decision=decisions[plan],proposed=proposed)
        for eta in [None,0.,.25]:
            ls=[]
            for leaf in leaves:
                standalone=min((opening[c]+v for c,v in leaf['candidates'].items()),default=math.inf);raw=outside.get((ev,leaf['pin']),math.inf);cost=math.inf if eta is None else max(raw,(1-eta)*standalone);ls.append(dict(leaf,outside=cost))
            cases.append(dict(base,leaves=ls));labels.append((plan,eta))
    assert cases;serialize(cases,out/'cases.txt');write(out/'cases.json',dict(labels=labels,cases=cases,metadata=metadata))
    write(out/'registration.json',dict(status='registered_before_cpp_replay',source_sha256={str(p):sha(p) for p in [__file__,D/'test_outside_dp_core.py',D/'analyze_retained_prefix.py',core/'driver',core/'unit_validation.json',b/'outside_trace_analysis.json',rd/'stdout.log',rd/'routed.route']},question='On exactly captured finite refresh matrices, does eta0 reproduce native shared decisions, and can verified no-new-cross options change bounded-benefit DP proposals or the existing5% same-objective refresh acceptance?',qualification='Offline counterfactual on fixed native contexts; accepted proposal changes do not prove reroute or finalSTA gains. Actual routing will change future contexts and must be tested separately.'))
    with (out/'results.log').open('w') as f,(out/'stderr.log').open('w') as err:subprocess.run([str(core/'driver')],stdin=(out/'cases.txt').open(),stdout=f,stderr=err,check=True,timeout=120)
    results=parse(out/'results.log');reports=[];by={}
    for i,label in enumerate(labels):by[label]=results[i,0]
    for plan in metadata:
        base=by[plan,None];z=by[plan,0.];r=by[plan,.25];m=metadata[plan];old=float(m['decision']['old_cost']);native=float(m['decision']['new_cost']);same=lambda a,b:a==b or math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
        assert same(base['cost'],native) and same(base['previous'],old) and base['assignment']==m['proposed'],(plan,base,m)
        assert z['cost']==base['cost'] and z['assignment']==base['assignment'] and z['outside']==0
        accept=lambda x:math.isfinite(x['cost']) and (not math.isfinite(x['previous']) or x['cost']<x['previous']*.95)
        assert accept(base)==bool(int(m['decision']['accepted']))
        reports.append(dict(plan=plan,event=m['event'],net=m['net'],baseline=base,eta0=z,eta25=r,proposal_changed=r['assignment']!=base['assignment'],baseline_accepted=accept(base),eta25_accepted=accept(r),accepted_changed=accept(base)!=accept(r),eta25_outside=r['outside']))
    summary=dict(plans=len(reports),eta0_all_exact=True,baseline_all_native_exact=True,eta25_changed_proposals=sum(r['proposal_changed'] for r in reports),eta25_changed_and_accepted=sum(r['proposal_changed'] and r['eta25_accepted'] for r in reports),acceptance_changes=sum(r['accepted_changed'] for r in reports),proposals_with_outside=sum(r['eta25_outside']>0 for r in reports),outside_leaf_proposals=sum(r['eta25_outside'] for r in reports))
    write(out/'analysis.json',dict(passed=True,status='sealed_captured_outside_DP_counterfactual',summary=summary,rows=reports,source_sha256={str(p):sha(p) for p in [out/'registration.json',out/'cases.txt',out/'cases.json',out/'results.log',core/'driver']},qualification='Baseline/eta0 shared solver reproduce original native proposal/current prior costs and assignments, including5% acceptance on captured tables. Extended shared and independent cores tested independently on random tables, but this report describes shared counterfactual only. Each outside witness was independently current-tree/graph/BB/price checked; raw surrogate and25% leaf-benefit bound are not native search costs or physical timing promises. No native quality pilot yet.'))
    print(summary)
if __name__=='__main__':main()
