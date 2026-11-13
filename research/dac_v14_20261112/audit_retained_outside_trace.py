#!/usr/bin/env python3
import collections,math,resource,signal,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import fields,graph_records,f32
from audit_residual_query_offline import near
from analyze_search_domain_v2 import inside
from analyze_native_reconvergence_v2 import observe
ROOT=D.parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from check_route import read_trace

def main():
    resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
    b=D/'retained_outside_trace_eltwise_dev_01';assert read(b/'input_seal.json')['passed'];done=read(b/'completion.json');assert done['gate_passed'] and not done['missing_arms'];rd=b/'runs/eltwise_layer_D';c=b/'runs/eltwise_layer_C';m=read(rd/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);assert sha(graph)==m['shared_inputs'][str(graph)]['sha256']
    reg=read(b/'registration.json');ref=Path(reg['reference']);assert read(ref.parent.parent/'residual_native_analysis.json')['passed']
    bindings={str(p):sha(p) for p in [Path(__file__),Path(near.__code__.co_filename),Path(inside.__code__.co_filename),graph,b/'registration.json',b/'completion.json',b/'input_seal.json',ref.parent.parent/'residual_native_analysis.json',D/'retained_outside_experiment_01.json',D/'retained_outside_trace_experiment_01.json']}
    for directory in [c,rd]:
        assert read(directory/'trace_reproduction.json')['passed'] and read(directory/'independent_audit.json')['audit']['passed'] and read(directory/'final_guide_audit.json')['passed']
        for n in ['manifest.json','stdout.log','routed.route','independent_audit.json','final_guide_audit.json','trace_reproduction.json']:bindings[str(directory/n)]=sha(directory/n)
    assert not any(l.startswith('H3D_OUTSIDE_') for l in (c/'stdout.log').read_text().splitlines())
    contexts={};trees=collections.defaultdict(list);leaves={};witness={};paths=collections.defaultdict(list);cache={};fresh_q=None;fresh_path=[];event=None;prefix_event={};physical_open=collections.defaultdict(dict);physical_branch=collections.defaultdict(list);cache_matches=0
    def flush():
        nonlocal fresh_q,fresh_path
        if fresh_q is None:return
        assert len(fresh_path)==int(fresh_q['edge_rows'])==int(fresh_q['path_edges'])
        if fresh_q['hit']=='0' and fresh_q['has_path']=='1':
            sink=int(fresh_q['sink']);search=int(fresh_q['search'])
            for count in range(len(fresh_path)):
                source=fresh_path[count-1][1] if count else sink;path=tuple(fresh_path[:count]);variants=cache.setdefault((sink,source),[])
                if any(p==path for origin,p in variants):continue
                assert len(variants)<16 # verified no cache stops on this frozen trajectory
                variants.append((search,path))
        fresh_q=None;fresh_path=[]
    for line in (rd/'stdout.log').read_text().splitlines():
        if line.startswith('H3D_RESIDUAL_QUERY '):flush();fresh_q=fields(line)
        elif line.startswith('H3D_RESIDUAL_EDGE '):
            r=fields(line);assert fresh_q is not None and r['search']==fresh_q['search'];fresh_path.append((int(r['from']),int(r['to']),float(r['physical_seconds']),float(r['toll_seconds'])))
        elif line.startswith('H3D_OUTSIDE_CONTEXT '):
            flush();r=fields(line);event=int(r['event']);assert event not in contexts;contexts[event]=r
            # Snapshot only the indexed static suffixes relevant to this plan, before any later query.
            contexts[event]['cache_snapshot']={s:sorted([(a,o,p) for (t,a),vs in cache.items() if t==s for o,p in vs],key=lambda v:(v[0],v[1])) for s in {k[0] for k in cache}}
        elif line.startswith('H3D_OUTSIDE_TREE '):
            r=fields(line);assert int(r['seq'])==len(trees[int(r['event'])]);trees[int(r['event'])].append(r)
        elif line.startswith('H3D_OUTSIDE_LEAF '):
            r=fields(line);key=(int(r['event']),int(r['pin']));assert key not in leaves;leaves[key]=r
        elif line.startswith('H3D_OUTSIDE_EDGE '):
            r=fields(line);key=(int(r['event']),int(r['pin']),int(r['witness']));assert int(r['index'])==len(paths[key]);paths[key].append(r)
        elif line.startswith('H3D_OUTSIDE_WITNESS '):
            r=fields(line);key=(int(r['event']),int(r['pin']),int(r['witness']));assert key not in witness;witness[key]=r
        elif line.startswith('H3D_PREFIX_TABLE ') and event is not None:
            r=fields(line)
            if r['net']==contexts[event]['net']:prefix_event[int(r['plan'])]=event
        elif line.startswith('H3D_PREFIX_ENTRY '):
            r=fields(line);p=int(r['plan'])
            if p in prefix_event:physical_open[prefix_event[p]][int(r['entry'])]=float(r['opening_units'])
        elif line.startswith('H3D_PREFIX_PAIR '):
            r=fields(line);p=int(r['plan'])
            if p in prefix_event:physical_branch[prefix_event[p],int(r['pin'])].append((int(r['entry']),float(r['branch_units'])))
    flush()
    wanted_nodes={int(t['node']) for rs in trees.values() for t in rs};wanted_nodes.update(int(r['sink']) for r in leaves.values());wanted_edges={(int(t['parent']),int(t['node']),int(t['switch'])) for rs in trees.values() for t in rs if int(t['parent'])>=0};wanted_pairs={(u,v) for u,v,s in wanted_edges}
    wanted_real={(int(e['to']),int(e['from']),float(e['delay'])) for ps in paths.values() for e in ps};wanted_pairs.update((u,v) for u,v,w in wanted_real);wanted_nodes.update(n for ps in paths.values() for e in ps for n in [int(e['from']),int(e['to'])])
    nodes={};switch={};found_edges=set();found_weights=set();layer_count=0
    for section,e in graph_records(graph):
        at=e.attrib
        if section=='switches':
            t=e.find('timing');v={} if t is None else t.attrib;assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal']);switch[int(at['id'])]=f32(v.get('Tdel',0))
        elif section=='rr_nodes':
            n=int(at['id']);v=e.find('loc').attrib;layer=int(v.get('layer_low',v.get('layer',0)));layer_count=max(layer_count,layer+1)
            if n in wanted_nodes:
                t=e.find('timing');assert t is None or all(float(t.attrib.get(k,0))==0 for k in ['R','C']);assert layer==int(v.get('layer_high',v.get('layer',0)));nodes[n]=dict(kind=at['type'],capacity=int(at['capacity']),layer=layer,direction=at.get('direction','NONE'),**{k:int(v[k]) for k in ['xlow','xhigh','ylow','yhigh']})
        elif section=='rr_edges':
            u,v,s=int(at['src_node']),int(at['sink_node']),int(at['switch_id'])
            if (u,v) in wanted_pairs:found_edges.add((u,v,s));found_weights.add((u,v,switch[s]))
    assert wanted_edges<=found_edges and wanted_real<=found_weights
    unit=sum(x for x in switch.values() if x>0)/sum(x>0 for x in switch.values());routes=read_trace(rd/'routed.route');terminal={}
    for net,data in routes.items():
        for t in data['trace']:
            if t.kind=='SINK' and t.pin is not None:terminal[net,t.pin]=t.inode
    tree_checks=0;prefix_checks=0;snapshot_checks=0;legacy_checks=0;out=[];reasons=collections.Counter();valid_leaf=collections.defaultdict(list);price_snapshot={}
    for ev,ctx in contexts.items():
        rows=trees[ev];assert len([x for (event,pin),x in leaves.items() if event==ev])==int(ctx['leaves']);assert near(float(ctx['unit']),unit)
        assert int(ctx['guard'])==0 # this input has complete, unguarded witness observations
        if int(ctx['witnesses']):assert len(rows)==int(ctx['tree_nodes'])
        else:assert not rows
        bynode={int(t['node']):t for t in rows};root=[]
        for t in rows:
            n,p,s=int(t['node']),int(t['parent']),int(t['switch']);d=float(t['delay']);tree_checks+=1
            if p<0:root.append(n);assert s==-1 and d==0.;continue
            assert p in bynode and (p,n,s) in found_edges;pd=float(bynode[p]['delay']);assert f32(f32(pd)+f32(switch[s]))==d;prefix_checks+=1
        if rows:assert len(root)==1 and root[0]==routes[int(ctx['net'])]['trace'][0].inode
        for (event,pin),leaf in leaves.items():
            if event!=ev:continue
            sink=int(leaf['sink']);assert sink==terminal[int(ctx['net']),pin];assert leaf['net']==ctx['net']
            cached=ctx['cache_snapshot'].get(sink,[]);assert len(cached)==int(leaf['witnesses'])
            # Cache variants are emitted in anchor order, then insertion order. Check origin and path independently, tolerating no duplicates.
            observed={}
            for key,w in witness.items():
                if key[:2]!=(ev,pin):continue
                ps=paths[key];a=int(w['anchor']);o=int(w['origin']);physical_path=tuple((int(e['from']),int(e['to']),float(e['delay']),0.) for e in ps);identity=(a,o,physical_path);assert identity not in observed;observed[identity]=key
                assert (a,o,physical_path) in cached;cache_matches+=1
                assert int(w['edges'])==len(ps);reason='valid'
                if a not in bynode:reason='anchor_absent'
                elif not int(bynode[a]['expand']):reason='anchor_inactive'
                elif nodes[a]['layer']!=nodes[sink]['layer']:reason='wrong_layer'
                sequence=[sink]+[int(e['to']) for e in ps];simple=(all(int(e['from'])==sequence[i] for i,e in enumerate(ps)) and sequence[-1]==a and len(sequence)==len(set(sequence)))
                bb=all(inside(nodes[n],ctx,layer_count) for n in sequence);hit=any(n in bynode for n in sequence[:-1])
                if reason=='valid':reason='not_simple' if not simple else 'outside_bb' if not bb else 'tree_intersection' if hit else 'valid'
                assert reason==w['reason'];assert all(nodes[n]['layer']==nodes[sink]['layer'] for n in sequence)
                physical=0.;premium=0.
                for e in ps:
                    u,v=int(e['from']),int(e['to']);delay=float(e['delay']);assert (v,u,delay) in found_weights
                    info=nodes[u];assert int(e['capacity'])==info['capacity'];ordinary=info['kind'] in ['CHANX','CHANY'] and info['direction']!='NONE';assert bool(int(e['ordinary']))==ordinary
                    snap=(int(e['occ']),float(e['acc']),int(e['capacity']));key_snap=(ev,u);assert key_snap not in price_snapshot or price_snapshot[key_snap]==snap;price_snapshot[key_snap]=snap
                    price=float(e['acc'])*(1+float(ctx['pres'])*max(0,int(e['occ'])+1-int(e['capacity'])));toll=max(0.,price-1.)/max(1.,price) if ordinary else 0.;assert near(price,float(e['price'])) and near(toll,float(e['premium']));physical+=delay;premium+=toll;snapshot_checks+=1
                prefix=float(bynode[a]['delay']) if a in bynode else 0.;raw=(1+4*float(leaf['criticality']))*(prefix+physical)/unit+float(ctx['opening'])*premium
                assert near(prefix,float(w['prefix'])) and near(physical,float(w['physical'])) and near(premium,float(w['premium'])) and near(raw,float(w['raw']));reasons[reason]+=1
                record=dict(event=ev,net=int(ctx['net']),pin=pin,refresh=bool(int(ctx['refresh'])),anchor=a,origin=o,reason=reason,prefix_seconds=prefix,physical_seconds=physical,premium=premium,raw=raw,standalone=float(leaf['standalone']),criticality=float(leaf['criticality']),raw_improves=raw<float(leaf['standalone']));out.append(record)
                if reason=='valid':valid_leaf[ev,pin].append(record)
            assert len(observed)==len(cached)
            branches=physical_branch[ev,pin]
            if int(ctx['refresh']) and branches:
                standalone=min(physical_open[ev][entry]+cost for entry,cost in branches);assert near(standalone,float(leaf['standalone']));legacy_checks+=1
    stats=dict(contexts=len(contexts),refresh_contexts=sum(int(x['refresh']) for x in contexts.values()),contexts_with_cached_witnesses=sum(int(x['witnesses'])>0 for x in contexts.values()),leaf_events=len(leaves),cached_witnesses=len(witness),reasons=dict(reasons),valid_leaf_events=len(valid_leaf),valid_improving_leaf_events=sum(min(r['raw'] for r in rs)<rs[0]['standalone'] for rs in valid_leaf.values()),tree_rows_checked=tree_checks,tree_prefix_float_checks=prefix_checks,price_edge_snapshots_checked=snapshot_checks,causal_witness_matches=cache_matches,independent_refresh_standalone_checks=legacy_checks,real_tree_edge_switches=len(wanted_edges),real_suffix_edge_delays=len(wanted_real))
    assert sum(reasons.values())==len(witness)
    observations=[dict(observe(p),arm=a,count=2,reused=False) for a,p in [('C',c),('D',rd)]]
    assert all(sha(p)==h for p,h in bindings.items());write(b/'outside_trace_analysis.json',dict(passed=True,status='sealed_current_pruned_tree_suffix_observer',source_sha256=bindings,statistics=stats,rows=out,observations=observations,qualification='Complete captured current pruned-tree RR edges/switches/prefix float sums rooted at paired net source, sink pin RR identity, all cached physical suffixes with causal origin and no-future cache membership, BB/layer/simplicity and other-tree-node intersection checked. Current price formulas/capacity and within-plan snapshot consistency independently checked; no independent temporal replay of all-net occupancy/accumulated cost. Local tree extension is graph/tree consistency, not joint capacity feasibility or final STA optimization. No new query, changed DP/guide or full native behavior; independent route/full native/finalguide/input audits and non-time residual trace reproduction. Standalone costs independently reconstructed for refresh finite-table leaves with old prefix table; initial standalone values are observed only.'))
    print(stats)
if __name__=='__main__':main()
