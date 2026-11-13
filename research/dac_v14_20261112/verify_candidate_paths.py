#!/usr/bin/env python3
"""Actual-RRG path/proxy checks and fixed-work accounting for query-only controls."""
import argparse
import collections
import math
import os
from pathlib import Path
import resource
import shutil
import signal
import time
from retained_prefix_workflow import D, read, write, sha, route_body
from verify_path_witnesses_v2 import fields, graph_records, f32

ARMS={'Q0':1,'Qh':2,'Qp':3}


def nodes(r):
    if r['path']=='-':return []
    return [(int(a),float(b),float(c),int(d),int(e),float(f),int(g))
            for a,b,c,d,e,f,g in (x.split(',') for x in r['path'].split(';'))]


def close(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-24)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);ap.add_argument('--out',required=True);args=ap.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));signal.alarm(1800)
    assert shutil.disk_usage(D).free>=80*1024**3
    b=args.batch.resolve();assert read(b/'input_seal.json')['passed'] and read(b/'completion.json')['gate_passed']
    c=b/'runs/eltwise_layer_C';cm=read(c/'manifest.json');graph=Path(cm['command'][cm['command'].index('--read_rr_graph')+1])
    graph_hash=sha(graph);assert graph_hash==cm['shared_inputs'][str(graph.resolve())]['sha256']
    old=D/'path_witness_eltwise_dev_02';physics_path=D/'path_witness_physical_audit_02/analysis.json';physics=read(physics_path)
    assert physics['passed'] and physics['complete_measured_coverage'] and not int(physics['path_cache']['skipped_queries'])
    assert read(old/'input_seal.json')['passed']
    oldlog=old/'runs/eltwise_layer_T/stdout.log';known=set()
    assert sha(oldlog)==physics['sources_sha256'][str(oldlog)]
    assert [h for p,h in physics['sources_sha256'].items() if Path(p).resolve()==graph.resolve()]==[graph_hash]
    with oldlog.open() as stream:
        for line in stream:
            if line.startswith('H3D_PATH_WITNESS '):
                r=fields(line)
                if r['reverse']=='1':known.add(tuple(int(r[k]) for k in ['plan','net','pin','entry']))
    def prefix(path):return [x for x in path.read_text().splitlines() if x.startswith('H3D_PREFIX_')]
    assert prefix(c/'stdout.log')==prefix(oldlog)
    out=D/args.out;out.mkdir(exist_ok=False);shutil.copy2(__file__,out/'runner.py');started=time.monotonic()
    inputs=[graph,b/'registration.json',b/'completion.json',b/'input_seal.json',oldlog,old/'input_seal.json',physics_path,Path(__file__),D/'verify_path_witnesses_v2.py']
    rows={};summaries={};wanted_nodes=set();wanted_edges=set();pairs={};openings={};tables={};source_known={}
    with (c/'stdout.log').open() as stream:
        for line in stream:
            if line.startswith('H3D_PREFIX_ENTRY '):
                r=fields(line);key=int(r['plan']),int(r['net']),int(r['entry'])
                openings[key]=float(r['opening_units']);source_known[key]=bool(int(r['source_known']))
            elif line.startswith('H3D_PREFIX_PAIR '):
                r=fields(line);key=tuple(int(r[k]) for k in ['plan','net','pin','entry']);pairs[key]=r
            elif line.startswith('H3D_PREFIX_TABLE '):
                r=fields(line);tables[int(r['plan']),int(r['net'])]=float(r['unit_seconds'])
    leaf_costs=collections.defaultdict(list)
    for key,r in pairs.items():
        charge=openings[key[0],key[1],key[3]]+float(r['branch_units'])
        if math.isfinite(charge):leaf_costs[key[:3]].append((charge,key[3],r['proposed']=='1'))
    for arm in ARMS:
        rd=b/'runs'/f'eltwise_layer_{arm}';m=read(rd/'manifest.json')
        assert read(rd/'query_equivalence.json')['passed'] and m['status']=='completed' and m['metrics']['native_full_check_passed']
        assert read(rd/'independent_audit.json')['audit']['passed'] and read(rd/'final_guide_audit.json')['passed']
        assert route_body(rd/'routed.route')==route_body(c/'routed.route') and sha(rd/'h3d_final_guides.csv')==sha(c/'h3d_final_guides.csv')
        assert prefix(rd/'stdout.log')==prefix(c/'stdout.log')
        assert sha(rd/'stdout.log')==m['outputs']['stdout.log']['sha256']
        inputs.extend(rd/n for n in ['stdout.log','manifest.json','query_equivalence.json','independent_audit.json','final_guide_audit.json'])
        records=[]
        with (rd/'stdout.log').open() as stream:
            for line in stream:
                if line.startswith('H3D_CANDIDATE_PATH '):records.append(fields(line))
                elif line.startswith('H3D_CANDIDATE_PATH_SUMMARY '):summaries[arm]=fields(line)
        rows[arm]=records
        for r in records:
            key=tuple(int(r[k]) for k in ['plan','net','pin','entry']);assert key in pairs and key not in known
            assert r['proposed']==pairs[key]['proposed'] and int(r['mode'])==ARMS[arm] and r['native_target']=='1'
            assert 0.<=float(r['priority'])<=float(r['criticality'])<=1.
            costs=leaf_costs[key[:3]];selected=[cost for cost,entry,proposed in costs if proposed];assert len(selected)==1
            alternatives=[cost for cost,entry,proposed in costs if not proposed]
            gap=min(alternatives)-selected[0] if alternatives else 0.
            uncertainty=1/(1+abs(gap)/max(1,abs(selected[0]))) if alternatives else 0.
            assert close(gap,float(r['local_gap'])) and int(r['rank_alternatives'])==len(alternatives)
            assert close(float(r['priority']),float(r['criticality'])*(.25+.75*uncertainty))
            assert close(float(r['unit_seconds']),tables[key[0],key[1]])
            wanted_nodes.update([int(r['entry']),int(r['sink'])]);path=nodes(r)
            if path:
                assert math.isfinite(float(r['priced_upper_seconds'])) and path[0][0]==int(r['entry']) and path[-1][0]==int(r['sink'])
                assert len({x[0] for x in path})==len(path)
                wanted_nodes.update(x[0] for x in path)
                wanted_edges.update((u[0],v[0],u[1]) for u,v in zip(path,path[1:]))
            else:assert math.isnan(float(r['priced_upper_seconds']))
    request_fields=['plan','net','pin','entry','request','requests','proposed','criticality','local_gap','rank_alternatives','priority']
    request_lists={arm:[[r[k] for k in request_fields] for r in data] for arm,data in rows.items()}
    assert request_lists['Q0']==request_lists['Qh']==request_lists['Qp']
    bindings={str(p):sha(p) for p in inputs}
    write(out/'registration.json',dict(question='Validate directed candidate paths, physical/priced sums and per-plan new work; compare only identical query request lists and unchanged native routes.',
        pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
        source_sha256=bindings,memory_bytes=32*1024**3,timeout_seconds=1800,native_route_calls=0,
        scope='Independent actual RR edges/weights and captured proxy-formula/work audit. No independent replay of temporal ownership/criticality or full native optimum oracle.'))
    metadata={};switches={};edge_ids=[];wanted_pairs={(u,v) for u,v,w in wanted_edges};counts=collections.Counter()
    for section,e in graph_records(graph):
        counts[section]+=1;a=e.attrib
        if section=='switches':
            timing=e.find('timing');v={} if timing is None else timing.attrib
            assert all(f32(v.get(k,0.))==0. for k in ['R','Cin','Cout','Cinternal'])
            switches[int(a['id'])]=f32(v.get('Tdel',0.))
        elif section=='rr_nodes':
            node=int(a['id'])
            if node in wanted_nodes:
                v=e.find('loc').attrib;layer=int(v.get('layer_low',v.get('layer',0)))
                assert layer==int(v.get('layer_high',v.get('layer',0)))
                metadata[node]=dict(kind=a['type'],layer=layer,capacity=int(a.get('capacity',1)),x=int(v['xlow']),y=int(v['ylow']))
        elif section=='rr_edges':
            u,v=int(a['src_node']),int(a['sink_node'])
            if (u,v) in wanted_pairs:edge_ids.append((u,v,int(a['switch_id'])))
    assert set(metadata)==wanted_nodes
    found={(u,v,switches[sw]) for u,v,sw in edge_ids if (u,v,switches[sw]) in wanted_edges};assert found==wanted_edges
    results={}
    for arm,records in rows.items():
        by_plan=collections.defaultdict(list);stops=collections.Counter();valid=exact=charged=calls=hits=proposed_valid=0;new_bilateral_bounds=new_bilateral_exact=0
        for r in records:by_plan[int(r['plan']),int(r['net'])].append(r)
        for plan,group in by_plan.items():
            assert len(group)<=4 and len({r['pin'] for r in group})<=2
            assert [int(r['request']) for r in group]==list(range(1,len(group)+1)) and all(int(r['requests'])==len(group) for r in group)
            remaining=256;memo={}
            for r in group:
                allowance=max(1,remaining//(len(group)-int(r['request'])+1)) if remaining else 0
                assert int(r['allowance'])==allowance
                amount=int(r['charged']);hit=int(r['cache_hit']);attempt=int(r['attempted']);key=int(r['sink']),int(r['entry'])
                if hit:
                    assert key in memo and amount==0
                    assert all(r[k]==memo[key][k] for k in ['path','stop','priced_upper_seconds','physical_path_seconds','toll_path_seconds','lower_priced_seconds'])
                elif attempt:
                    assert allowance>0 and amount==int(r['search_expansions'])<=allowance;memo[key]=r
                else:assert amount==0 and allowance==0
                assert int(r['labels'])<=16384 and int(r['peak_heap'])<=65536
                remaining-=amount;assert int(r['remaining'])==remaining and remaining>=0
                charged+=amount;calls+=attempt and not hit;hits+=hit;stops[r['stop']]+=1
                upper=float(r['priced_upper_seconds']);lower=float(r['lower_priced_seconds']);weight=float(r['toll_weight'])
                assert weight==(.25 if arm=='Qp' else 0.)
                if r['stop']=='memory_limit':assert math.isnan(lower)
                if math.isfinite(upper):
                    valid+=1;proposed_valid+=r['proposed']=='1';path=nodes(r)
                    for node,delay,toll,occ,capacity,acc,owned in path:
                        assert capacity==metadata[node]['capacity'] and occ>=0 and owned in [0,1] and not math.isnan(acc)
                    assert metadata[path[0][0]]['layer']!=metadata[path[1][0]]['layer']
                    assert all(metadata[x[0]]['layer']==metadata[path[-1][0]]['layer'] for x in path[1:])
                    assert path[-1][1]==path[-1][2]==0.
                    assert close(math.fsum(x[1] for x in path),float(r['physical_path_seconds']))
                    assert close(math.fsum(x[2] for x in path),float(r['toll_path_seconds'])) and close(math.fsum(x[1]+x[2] for x in path),upper)
                    if math.isfinite(lower):assert lower<=upper+max(1e-24,abs(upper)*1e-10)
                    if r['stop']=='exact_proxy':assert close(lower,upper);exact+=1
                    for u,v in zip(path,path[1:]):
                        node,delay,toll,occ,capacity,acc,owned=v
                        assert capacity==metadata[node]['capacity'] and owned in [0,1] and occ>=0
                        price=acc*(1+float(r['pres_fac'])*max(0,occ+1-capacity))
                        fraction=max(0.,price-1)/max(1.,price) if math.isfinite(price) else 1.
                        expected=weight*float(r['unit_seconds'])*fraction if metadata[node]['kind'] in ['CHANX','CHANY'] and not owned else 0.
                        assert close(u[2],expected)
                    # Source availability is taken from the unchanged table,
                    # not imputed from a newly found sink-side upper bound.
                    source_entry=(plan[0],plan[1],int(r['entry']))
                    # opening metadata alone is not a measurement certificate;
                    # the exact source_known field is read below.
                    if source_known.get(source_entry,False):
                        new_bilateral_bounds+=1
                        new_bilateral_exact+=weight==0. and r['stop']=='exact_proxy'
                else:assert not nodes(r)
        summary=summaries[arm]
        assert int(summary['records'])==len(records) and int(summary['plans'])==len(by_plan)
        assert int(summary['charged_expansions'])==charged and int(summary['calls'])==calls and int(summary['cache_hits'])==hits
        assert int(summary['paths'])==valid and int(summary['exact_proxy'])==exact
        results[arm]=dict(requests=len(records),new_calls=calls,cache_hits=hits,charged_expansions=charged,valid_paths=valid,exact_priced_proxy=exact,
            valid_proposal_paths=proposed_valid,known_source_and_new_valid_sink_bound=new_bilateral_bounds,
            known_source_and_new_exact_physical_sink=new_bilateral_exact,stops=dict(stops),query_seconds=float(summary['seconds']))
    checks={p:sha(p)==h for p,h in bindings.items()};assert all(checks.values())
    write(out/'input_seal.json',dict(passed=True,checks=checks))
    write(out/'analysis.json',dict(passed=True,results=results,identical_mode_request_lists=True,all_reverse_requests_previously_unmeasured=True,
        inspected_graph_records=dict(counts),weighted_edges_checked=len(wanted_edges),source_sha256=bindings,
        qualification='Query-only information/extra-work comparison. Valid priced paths are upper bounds; exact priced proxy is not shortest physical delay when toll>0. No new query result enters old physical caches, no routing/QoR or speedup claim, no independent temporal-state replay or full native optimum oracle.'))
    write(out/'completion.json',dict(status='candidate_path_physical_work_audit_complete',wall_seconds=time.monotonic()-started,native_route_calls=0));print(results)


if __name__=='__main__':main()
