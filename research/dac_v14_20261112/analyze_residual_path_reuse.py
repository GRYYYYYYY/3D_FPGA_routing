#!/usr/bin/env python3
"""Chronological reuse of static physical suffixes, never saved dynamic seed costs."""
import collections,math
from retained_prefix_workflow import D,read,write,sha
from audit_residual_query_offline import parse,near

def main():
    b=D/'residual_query_offline_01';a=read(b/'analysis.json');assert a['passed'];assert read(D/'residual_query_adapter_unit_01/validation.json')['passed'];out=D/'residual_path_reuse_offline_01';out.mkdir(exist_ok=False)
    write(out/'registration.json',dict(status='registered_before_reuse_analysis',native_route_calls=0,question='Can chronological reuse of validated physical suffixes improve residual multi-source coverage without increasing the fixed per-query budget or storing dynamic seedTdel?',arms=['P:always run same Qh, pool old and current valid suffixes','S:skip Qh only when a prior valid suffix is already available to a current seed; record lost opportunities'],source=str(b),cache='Immutable physical suffix paths keyed by(sink,RRsource); up to16 unique alternative witnesses/key and16384witnesses total. Explicit cap counts. No future records, no saved seedTdel/occupancy/prices. BB/layer admission and current prefix recomputed on each lookup.',qualification='Offline deterministic counterfactual on fixed saved contexts, not native rerouting or timing claim; previous native contexts are not allowed to change. Cached suffixes remain graph-walk UBs, not exact distances or legal tree extensions.'))
    rows,paths=parse(b/'query_stdout.log');cases={int(c['domain']['search']):c for c in read(b/'cases.json')};nreal=read(b/'graph_binding.json')['nodes'];P={};S={};observations=[];caps={'P':0,'S':0};inserts={'P':0,'S':0}
    # Node positions are re-read from the already bound exported graph for admission; path graph validity was independently audited from original RRG.
    import struct
    with (b/'graph.bin').open('rb') as f:
        f.seek(36);node_data=f.read(nreal*20)
    nodes=[struct.unpack_from('<iiiii',node_data,i*20) for i in range(nreal)]
    def admitted(n,c):
        _,_,x,y,z=nodes[n];r=c['domain'];return int(r['xmin'])<=x<=int(r['xmax']) and int(r['ymin'])<=y<=int(r['ymax']) and int(r['layer_min'])<=z<=int(r['layer_max']) and z==int(r['sink_layer'])
    def lookup(cache,c):
        best=None;sink=int(c['domain']['sink']);search=int(c['domain']['search'])
        for s in c['seeds']:
            if s['layer']!=int(c['domain']['sink_layer']):continue
            for origin,path in cache.get((sink,s['node']),[]):
                assert origin<=search
                if any(not admitted(n,c) for e in path for n in e[:2]):continue
                value=s['delay']+sum(e[2] for e in path)
                if best is None or value<best['seconds']:best=dict(seconds=value,seed=s['node'],origin_search=origin,path=path,current_prefix_seconds=s['delay'])
        return best
    def add(cache,c,tag):
        search=int(c['domain']['search']);sink=int(c['domain']['sink']);path=paths[search,1]
        if not path:return
        assert path[-1][1]==nreal;real=path[:-1]
        for i in range(len(real)+1):
            source=real[i-1][1] if i else sink;suffix=[(v,u,w) for u,v,w,t in reversed(real[:i])];assert not suffix or suffix[0][0]==source and suffix[-1][1]==sink
            key=(sink,source);old=cache.setdefault(key,[])
            if any(p==suffix for o,p in old):continue
            if len(old)>=16 or inserts[tag]>=16384:caps[tag]+=1;continue
            old.append((search,suffix));inserts[tag]+=1
    for search,c in sorted(cases.items()):
        query=rows[search,1];p_prior=lookup(P,c);s_prior=lookup(S,c);add(P,c,'P');p=lookup(P,c)
        if s_prior is None:add(S,c,'S')
        s=lookup(S,c);opt=c['oracle']['no_cross_BB_seconds']
        for result in [p,s]:
            if result:assert opt is not None and result['seconds']+1e-24>=opt and near(result['seconds'],result['current_prefix_seconds']+sum(e[2] for e in result['path']))
        observations.append(dict(search=search,guide=c['oracle']['guide'],oracle_seconds=opt,Qh_seconds=query['upper_seconds'],P=p,P_prior=p_prior,S=s,S_prior=s_prior,S_query_run=s_prior is None,S_query_expansions=query['expansions'] if s_prior is None else 0,Qh_query_expansions=query['expansions']))
    summaries={}
    for tag in ['P','S']:
        summaries[tag]=dict(requests=len(observations),paths=sum(r[tag] is not None for r in observations),guided_paths=sum(r['guide'] and r[tag] is not None for r in observations),query_requests=len(observations) if tag=='P' else sum(r['S_query_run'] for r in observations),expansions=sum(r['Qh_query_expansions' if tag=='P' else 'S_query_expansions'] for r in observations),prior_hits=sum(r[tag+'_prior'] is not None for r in observations),cache_witnesses=inserts[tag],cache_stops=caps[tag],max_gap=max((r[tag]['seconds']/r['oracle_seconds']-1 for r in observations if r[tag] and r['oracle_seconds']),default=None))
    sources={str(p):sha(p) for p in [__file__,b/'analysis.json',b/'cases.json',b/'query_stdout.log',b/'graph.bin',D/'residual_query_adapter_unit_01/validation.json']};write(out/'analysis.json',dict(passed=True,status='sealed_chronological_residual_suffix_reuse',source_sha256=sources,summaries=summaries,rows=observations,native_route_calls=0,qualification='Past query paths only; ordinary suffixes independently graph-audited in source experiment. Dynamic prefixes recomputed from current actual saved seed set, each path checked in current box/layer. P/S counterfactual evaluated on fixed contexts; no native route/QoR/runtime assertion. SourceTdel virtual edges are stripped from cache. Per-key capacity retains previous alternatives without replacement; stops explicit.'))
    print(summaries)
if __name__=='__main__':main()
