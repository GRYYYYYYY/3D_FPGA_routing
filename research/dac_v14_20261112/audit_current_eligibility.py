#!/usr/bin/env python3
"""Audit each actual guide eligibility decision and matched native QoR."""
import collections, csv, re
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body,normalized_command
from verify_path_witnesses_v2 import fields,f32
from analyze_native_reconvergence_v2 import observe
b=D/'current_eligibility_eltwise_dev_02';reg=read(b/'registration.json');done=read(b/'completion.json')
assert read(b/'input_seal.json')['passed'] and done['gate_passed'] and not done['missing_arms']
source={str(p):sha(p) for p in [Path(__file__),b/'registration.json',b/'input_seal.json',b/'completion.json']}
result={};rows=[];logs={};dirs={a:b/'runs'/('eltwise_layer_'+a) for a in reg['arms']}
for a,rd in dirs.items():
    m=read(rd/'manifest.json');lines=(rd/'stdout.log').read_text().splitlines();logs[a]=lines
    row=dict(observe(rd),arm=a,count=1 if a=='E1' else 2,group='current_eligibility',reused=False);rows.append(row)
    for n in ['manifest.json','stdout.log','independent_audit.json','final_guide_audit.json','pair_check.json','time.txt']:
        if (rd/n).exists():source[str(rd/n)]=sha(rd/n)
    assert read(rd/'pair_check.json')['passed']
    refm=read(Path(reg['reference'])/'manifest.json');expected=dict(refm['environment'],VPR_H3D_TRACE_SEARCH_DOMAIN='1',VPR_H3D_BOX_GUIDE_ADMISSION='0',VPR_H3D_CURRENT_GUIDE_ELIGIBILITY='0' if a=='C2' else '1')
    assert m['environment']==expected
    cmd=list(m['command']);cmd[cmd.index('--router_max_convergence_count')+1]='2'
    assert normalized_command(cmd)==normalized_command(refm['command'])
    for n in ['packed.net','placed.place']:assert sha(rd/n)==sha(Path(reg['reference'])/n)
    assert read(rd/'diagnostic_recovery_reproduction.json')['passed']
    if a=='C2':
        assert read(rd/'disabled_reproduction.json')['passed']
        assert not any(l.startswith('H3D_CURRENT_ELIGIBILITY') for l in lines)
        continue
    # The domain observer runs on original parameters immediately before local gating.
    domain={};decisions={};active=None;edge_rows=0;prior={};reactivations=[]
    for l in lines:
        if l.startswith('H3D_SEARCH_DOMAIN '):
            r=fields(l);key=int(r['search']);assert key not in domain;domain[key]=r
        elif l.startswith('H3D_CURRENT_ELIGIBILITY '):
            r=fields(l);key=int(r['search']);assert key not in decisions;d=domain[key]
            for k in ['iter','attempt','search','net','pin','guide','criticality','rcv']:assert r[k]==d[k],(a,key,k)
            c=float(r['criticality']);t=float(r['threshold']);assert c==f32(c) and t==f32(float(m['environment']['VPR_H3D_MIN_CRITICALITY']))
            expected=int(r['guide'])==1 and int(r['rcv'])==0 and c<t
            assert bool(int(r['suppressed']))==expected
            decisions[key]=r;active=r
            if r['guide']=='1':
                k=(r['net'],r['pin']);prev=prior.get(k)
                if prev and prev['suppressed']=='1' and r['suppressed']=='0' and prev['preferred']==d['preferred']:
                    reactivations.append(dict(net=k[0],pin=k[1],from_search=prev['search'],to_search=r['search'],preferred=d['preferred']))
                prior[k]=dict(r,preferred=d['preferred'])
        elif l.startswith('H3D_GUIDE_INFLUENCE_EDGE '):
            r=fields(l);assert active is not None and active['suppressed']=='0'
            for k in ['iter','attempt','net','pin','criticality','rcv']:assert r[k]==active[k],(a,k)
            edge_rows+=1
    assert decisions.keys()=={k for k,v in domain.items() if v['guide']=='1'}
    last=lambda prefix:fields(next(l for l in reversed(lines) if l.startswith(prefix+' ')))
    summ=last('H3D_CURRENT_ELIGIBILITY_SUMMARY');ds=last('H3D_SEARCH_DOMAIN_SUMMARY');ins=last('H3D_GUIDE_INFLUENCE_SUMMARY')
    assert int(summ['checks'])==int(summ['rows'])==len(decisions) and int(summ['omitted'])==int(ds['omitted'])==0
    assert int(summ['guided'])==sum(int(x['guide']) for x in decisions.values())
    assert int(summ['suppressed'])==sum(int(x['suppressed']) for x in decisions.values())
    assert int(ins['rows'])==edge_rows
    probe=last('H3D_RESIDUAL_SUMMARY')
    result[a]=dict(searches=len(decisions),guided_searches=int(summ['guided']),suppressed=int(summ['suppressed']),edge_rows_audited=edge_rows,guided_crossing_evaluations=int(ins['events']),same_preference_reactivations=reactivations,threshold=float(summ['threshold']),residual_probe_seconds=float(probe['seconds']),residual_queries=int(probe['queries']),residual_work=int(probe['expansions']),native_status=row['status'])
prior_binding=read(D/'bounded_cap_range_eltwise_dev_02/recovery_binding_v2.json')['checks']
for count,rs in reg['references'].items():
    for a,p in rs.items():
        rd=Path(p)
        for n in ['manifest.json','independent_audit.json','stdout.log','routed.route','time.txt','final_guide_audit.json']:
            if (rd/n).exists():assert sha(rd/n)==prior_binding[str(rd/n)]['expected_sha256'];source[str(rd/n)]=sha(rd/n)
        rows.append(dict(observe(rd),arm=a,count=int(count),group='reference',reused=True))
comparisons={};C=next(r for r in rows if r['arm']=='C2')
for a in ['E2','E1']:
    r=next(r for r in rows if r['arm']==a)
    c=C if a=='E2' else next(x for x in rows if x['arm']=='Tf' and x['count']==1)
    comparisons[a]=dict(control_path=c['path'],both_legal=r['status']==c['status']=='legal',same_complete_route=route_body(dirs[a]/'routed.route')==route_body(Path(c['path'])/'routed.route') if r['status']==c['status']=='legal' else None,cpd_improvement_pct=(1-r['legal_cpd_ns']/c['legal_cpd_ns'])*100 if r['status']==c['status']=='legal' else None,iterations_delta=r['iterations']-c['iterations'])
    for name in ['A0','R1','A1']:
        cr=next(x for x in rows if x['arm']==name and x['count']==r['count']);comparisons[a][name+'_cpd_improvement_pct']=(1-r['legal_cpd_ns']/cr['legal_cpd_ns'])*100 if r['status']==cr['status']=='legal' else None
# This diagnostic preserves the first differing native counter row, without claiming
# an exact per-node trajectory or identifying the first causal path divergence.
first_divergence=None
ci=[l for l in logs['C2'] if l.startswith('H3D_ITER ')]
ei=[l for l in logs['E2'] if l.startswith('H3D_ITER ')]
for c,e in zip(ci,ei):
    if c!=e:
        first_divergence=dict(iteration=int(fields(c)['iter']),control=c,enabled=e);break
P=D/'paper/data/current_eligibility_v14.csv'
with P.open('w') as f:
    w=csv.writer(f);w.writerow(['group','arm','max_convergences','reused','status','CPD_ns','iterations','SB_net_occupancy','CB_source_net_occupancy','planning_seconds','router_seconds','complete_process_seconds'])
    for r in rows:
        pm=r.get('physical_metrics') or {};w.writerow([r['group'],r['arm'],r['count'],r['reused'],r['status'],r.get('legal_cpd_ns'),r.get('iterations'),pm.get('sb_pair_net_occupancy'),pm.get('cb_crossing_output_source_net_occupancy'),r.get('planning_seconds'),r.get('router_seconds'),r.get('process_seconds')])
source[str(P)]=sha(P)
write(b/'eligibility_analysis.json',dict(passed=True,observations=rows,mechanism=result,comparisons=comparisons,first_native_counter_divergence=first_divergence,source_sha256=source,firstlegal_prefix=read(dirs['E1']/'first_legal_prefix_reproduction.json'),quality_promoted=False,qualification='Actual search-local decisions checked against independent domain records and native float threshold; recorded influence edge rows never belong to suppressed searches. Raw edge trace is sampled, cumulative counts retained. No independent replay of every heap edge; no formal speedup from ordered instrumented development runs. One seen circuit with two stopping rules, not independent circuit samples.'))
print(dict(passed=True,mechanism={k:{n:v for n,v in r.items() if n!='same_preference_reactivations'} for k,r in result.items()},reactivations={k:len(r['same_preference_reactivations']) for k,r in result.items()},comparisons=comparisons,first_native_counter_divergence=first_divergence))
