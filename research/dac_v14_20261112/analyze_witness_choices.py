#!/usr/bin/env python3
"""Exploratory within-leaf coverage and toll contrasts; never shared-DP dominance."""
import collections
import math
from pathlib import Path
import statistics
from retained_prefix_workflow import D, read, write, sha
from verify_path_witnesses_v2 import fields, path_nodes


def main():
    b=D/'path_witness_eltwise_dev_02';physics_path=D/'path_witness_physical_audit_02/analysis.json';physics=read(physics_path)
    assert physics['passed'] and physics['complete_measured_coverage'] and not int(physics['path_cache']['skipped_queries'])
    assert read(b/'input_seal.json')['passed'] and read(b/'completion.json')['gate_passed']
    destination=D/'path_witness_choice_diagnostic_01.json';assert not destination.exists()
    log=b/'runs/eltwise_layer_T/stdout.log';openings={};leaves=collections.defaultdict(dict);paths={};decisions={}
    with log.open() as stream:
        for line in stream:
            if not line.startswith(('H3D_PREFIX_ENTRY ','H3D_PREFIX_PAIR ','H3D_PATH_WITNESS ','H3D_PREFIX_DECISION ')):continue
            r=fields(line);plan,net=int(r['plan']),int(r['net'])
            if line.startswith('H3D_PREFIX_ENTRY '):openings[plan,net,int(r['entry'])]=float(r['opening_units'])
            elif line.startswith('H3D_PREFIX_DECISION '):decisions[plan,net]=int(r['accepted'])
            elif line.startswith('H3D_PREFIX_PAIR '):leaves[plan,net,int(r['pin'])][int(r['entry'])]=r
            else:
                assert r['status']=='measured';new_premium=[]
                for node,delay,occ,capacity,acc,owned,ordinary in path_nodes(r):
                    if ordinary and not owned:new_premium.append(max(0.,acc*(1+float(r['pres_fac'])*max(0,occ+1-capacity))-1))
                paths[plan,net,int(r['pin']),int(r['entry']),int(r['reverse'])]=dict(all_ordinary_premium=float(r['premium_sum']),
                    unowned_ordinary_premium=math.fsum(new_premium))
    coverage=collections.Counter();proposed=collections.Counter();comparisons=[];no_proposal=0
    for (plan,net,pin),candidates in leaves.items():
        selected=[entry for entry,r in candidates.items() if r['proposed']=='1']
        assert len(selected)<=1
        if not selected:no_proposal+=1
        known={}
        for entry,r in candidates.items():
            sides=tuple(side for side in [0,1] if (plan,net,pin,entry,side) in paths)
            label='both' if len(sides)==2 else 'source_only' if sides==(0,) else 'sink_only' if sides==(1,) else 'neither'
            coverage[label]+=1
            if selected and entry==selected[0]:proposed[('accepted' if decisions[plan,net] else 'rejected')+':'+label]+=1
            if len(sides)==2:
                known[entry]=dict(independent_charge=openings[plan,net,entry]+float(r['branch_units']),
                    observed_proxy_toll=math.fsum(paths[plan,net,pin,entry,side]['unowned_ordinary_premium'] for side in sides))
        if not selected or selected[0] not in known:continue
        chosen=known[selected[0]];alternatives=[(entry,value) for entry,value in known.items() if entry!=selected[0]]
        if not alternatives:continue
        best_entry,best=min(alternatives,key=lambda x:(x[1]['observed_proxy_toll'],x[0]))
        comparisons.append(dict(plan=plan,net=net,pin=pin,accepted=decisions[plan,net],proposed_entry=selected[0],
            proposed=chosen,best_known_toll_alternative_entry=best_entry,alternative=best,
            lower_observed_toll=best['observed_proxy_toll']<chosen['observed_proxy_toll'],
            independent_charge_difference=best['independent_charge']-chosen['independent_charge']))
    lower=[r for r in comparisons if r['lower_observed_toll']]
    result=dict(status='posthoc_coverage_and_local_proxy_diagnostic',candidate_leaf_events=sum(coverage.values()),
        coverage=dict(coverage),proposed_coverage=dict(proposed),leaves=len(leaves),leaves_without_proposal=no_proposal,
        proposed_both_known_with_known_alternative=len(comparisons),lower_toll_alternative_events=len(lower),
        accepted_lower_toll_alternative_events=sum(r['accepted'] for r in lower),
        lower_toll_and_lower_independent_charge_events=sum(r['independent_charge_difference']<=0 for r in lower),
        comparisons=comparisons,sources_sha256={str(p):sha(p) for p in [log,physics_path,b/'path_witness_analysis.json',Path(__file__),D/'verify_path_witnesses_v2.py']},
        qualification='Exploratory one-case repeated table/leaf events, not independent samples. Both-side known subset only; no zero-price imputation for unknowns. Independent opening+branch charge is not shared-DP marginal cost, and a lower local charge/toll does not establish global dominance or final QoR. Unowned ordinary-resource multipliers are a proxy, not actual native incremental cost. Single canonical shortest witness may miss cheaper equal-delay paths.')
    write(destination,result);print({k:v for k,v in result.items() if k not in ['comparisons','sources_sha256','qualification']})


if __name__=='__main__':main()
