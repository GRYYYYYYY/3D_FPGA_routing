#!/usr/bin/env python3
"""Actual directed crossing costs, group sampling and exact native equivalence."""
import argparse,collections,math,resource,signal,statistics,struct
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from guide_influence_records import records
from verify_path_witnesses_v2 import fields,graph_records,f32
from analyze_native_reconvergence_v2 import observe
from routing_log_metrics import ROW

FOCUS={(4674,9):0,(4674,21):1,(4675,23):2}
def near(a,b):return a==b or math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-24)
def values(text):return [] if text=='-' else list(map(int,text.split(',')))
def bin_id(c):return 0 if c<.7 else 1 if c<.9 else 2 if c<.95 else 3

def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);args=ap.parse_args();b=args.batch.resolve()
    resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));signal.alarm(1800)
    assert read(b/'input_seal.json')['passed'];done=read(b/'completion.json');assert done['disabled_gate_passed'] and not done['missing_arms']
    dirs={a:b/'runs'/('eltwise_layer_'+a) for a in ['C','T']};logs={a:(p/'stdout.log').read_text().splitlines() for a,p in dirs.items()}
    prior=D/'source_coverage_gate_eltwise_dev_01/runs/eltwise_layer_F'
    assert records(logs['C'])==records((prior/'stdout.log').read_text().splitlines())
    assert records(logs['C'])==records(logs['T'])
    prefix=lambda ls:[l for l in ls if l.startswith('H3D_PREFIX_')]
    assert prefix(logs['C'])==prefix(logs['T'])
    native_rows=lambda ls:[l.split()[:1]+l.split()[2:] for l in ls if ROW.match(l)]
    assert native_rows(logs['C'])==native_rows(logs['T'])
    assert route_body(dirs['C']/'routed.route')==route_body(dirs['T']/'routed.route')
    assert sha(dirs['C']/'h3d_final_guides.csv')==sha(dirs['T']/'h3d_final_guides.csv')
    m=read(dirs['T']/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);assert sha(graph)==m['shared_inputs'][str(graph.resolve())]['sha256']
    inputs=[Path(__file__),D/'guide_influence_records.py',D/'guide_influence_native_settings_01.json',D/'guide_influence_implementation.json',D/'verify_path_witnesses_v2.py',b/'input_seal.json',b/'completion.json',b/'registration.json',graph]
    inputs += [p/n for p in dirs.values() for n in ['manifest.json','stdout.log','independent_audit.json','final_guide_audit.json']]
    bindings={str(p):sha(p) for p in inputs}
    edges=[fields(l) for l in logs['T'] if l.startswith('H3D_GUIDE_INFLUENCE_EDGE ')]
    contexts=[fields(l) for l in logs['T'] if l.startswith('H3D_GUIDE_INFLUENCE_CONTEXT ')]
    summaries=[fields(l) for l in logs['T'] if l.startswith('H3D_GUIDE_INFLUENCE_SUMMARY ')]
    buckets=[fields(l) for l in logs['T'] if l.startswith('H3D_GUIDE_INFLUENCE_BUCKET ')]
    assert summaries;summary=summaries[-1];final_iter=int(summary['iter']);last={}
    for r in buckets:
        if int(r['iter'])==final_iter:last[int(r['bin']),int(r['configurable']),int(r['preferred'])]=r
    assert len(last)==16
    wanted=set();wanted_pairs=set();wanted_edge_ids=set()
    for r in edges:
        u,v,sw=int(r['from']),int(r['to']),int(r['switch']);wanted.update([u,v]);wanted.update(values(r['preferred_ids']));wanted_pairs.add((u,v));wanted_edge_ids.add((u,v,sw))
    for r in contexts:
        wanted.add(int(r['sink']));wanted.update(values(r['preferred']))
        if r['edges']=='-':assert int(r['crossings'])==0;continue
        seen=set()
        for item in r['edges'].split(';'):
            u,v,ur,vr,ut,vt=item.split(',');u,v=int(u),int(v);assert (u,v) not in seen;seen.add((u,v));assert int(ur) in [0,1] and int(vr) in [0,1]
            wanted.update([u,v]);wanted_pairs.add((u,v))
        assert len(seen)==int(r['crossings'])
    metadata={};switches={};found=set();pair_switches=collections.defaultdict(set)
    for section,e in graph_records(graph):
        a=e.attrib
        if section=='switches':
            t=e.find('timing');v={} if t is None else t.attrib;assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal'])
            switches[int(a['id'])]=dict(delay=f32(v.get('Tdel',0)),configurable=a['type'].lower() not in ['short','buffer'],type=a['type'])
        elif section=='rr_nodes':
            node=int(a['id']);t=e.find('timing');assert t is None or all(float(t.attrib.get(k,0))==0 for k in ['R','C'])
            if node in wanted:
                v=e.find('loc').attrib;layer=int(v.get('layer_low',v.get('layer',0)));assert layer==int(v.get('layer_high',v.get('layer',0)))
                metadata[node]=dict(layer=layer,kind=a['type'],capacity=int(a.get('capacity',1)))
        elif section=='rr_edges':
            u,v,sw=int(a['src_node']),int(a['sink_node']),int(a['switch_id'])
            if (u,v) in wanted_pairs:found.add((u,v,sw));pair_switches[u,v].add(sw)
    assert set(metadata)==wanted and wanted_edge_ids<=found
    unit=sum(s['delay'] for s in switches.values() if s['delay']>0)/sum(s['delay']>0 for s in switches.values());assert near(unit,float(summary['unit_seconds']))
    groups=collections.Counter();row_buckets=collections.Counter();focus_rows=collections.defaultdict(list);previous_event=0
    for r in edges:
        event=int(r['event']);assert event>previous_event;previous_event=event
        net,pin=int(r['net']),int(r['pin']);crit=float(r['criticality']);assert 0<=crit<=1
        bucket=bin_id(crit);focus=FOCUS.get((net,pin));group=focus if focus is not None else 3+bucket
        assert int(r['group'])==group and int(r['bin'])==bucket
        groups[group]+=1;assert int(r['group_row'])==groups[group]<= (2000 if focus is not None else 1000)
        u,v,sw=int(r['from']),int(r['to']),int(r['switch']);s=switches[sw]
        assert metadata[u]['layer']!=metadata[v]['layer'] and bool(int(r['configurable']))==s['configurable']
        pref=u in values(r['preferred_ids']);assert bool(int(r['preferred']))==pref
        assert float(r['physical_seconds'])==s['delay']
        before,after,miss=float(r['before_congestion']),float(r['after_congestion']),float(r['miss_weight'])
        expected=f32(before*f32(1+miss)) if s['configurable'] and not pref else before
        assert after==expected
        analytic=(1-crit)*(after-before);physical=crit*s['delay'];timing=0 if int(r['rcv']) else crit*float(r['timing_penalty_seconds'])
        finite=all(math.isfinite(x) for x in [analytic,physical,timing]);assert bool(int(r['finite']))==finite
        if finite:
            assert near(analytic,float(r['analytic_extra'])) and near(physical,float(r['weighted_physical_seconds'])) and near(timing,float(r['weighted_timing_seconds']))
            assert analytic>=0 and float(r['timing_penalty_seconds'])==0
        row_buckets[bucket,int(r['configurable']),int(pref)]+=1
        if focus is not None:focus_rows[net,pin].append(r)
    assert len(edges)==int(summary['rows'])==sum(groups.values())<=10000
    assert int(summary['events'])==int(summary['rows'])+int(summary['omitted'])
    assert sum(int(r['count']) for r in last.values())==int(summary['events'])
    assert sum(int(r['rows']) for r in last.values())==len(edges)
    for key,r in last.items():
        assert int(r['rows'])==row_buckets[key] and 0<=int(r['positive'])<=int(r['finite'])<=int(r['count'])
        assert 0<=int(r['below_unit'])<=int(r['positive'])
    for a,z in zip(summaries,summaries[1:]):
        for k in ['events','rows','omitted','attempts','contexts','context_omitted']:assert int(a[k])<=int(z[k])
    assert int(summary['context_omitted'])==0 and int(summary['contexts'])==len(contexts)<=2000
    focus_contexts=collections.defaultdict(list);context_map={};previous_attempt=0
    for r in contexts:
        attempt=int(r['attempt']);assert attempt>previous_attempt;previous_attempt=attempt
        net,pin=int(r['net']),int(r['pin']);assert (net,pin) in FOCUS;context_map[attempt]=r;focus_contexts[net,pin].append(r)
        if not int(r['guide']):assert r['preferred']=='-'
        assert int(r['reexpand_sink_layer'])<=int(r['tree_nodes'])
        if r['edges']!='-':
            for item in r['edges'].split(';'):
                u,v,ur,vr,ut,vt=item.split(',');u,v=int(u),int(v);assert metadata[u]['layer']!=metadata[v]['layer']
                assert (u,v) in pair_switches
                expected={f32(float(ut)+switches[sw]['delay']) for sw in pair_switches[u,v]}
                assert float(vt) in expected or any(math.isclose(float(vt)-float(ut),switches[sw]['delay'],rel_tol=1e-5,abs_tol=2e-15) for sw in pair_switches[u,v])
    focus_stats={}
    for key in FOCUS:
        rs=focus_rows[key];cs=focus_contexts[key]
        for r in rs:
            c=context_map[int(r['attempt'])];assert (r['net'],r['pin'],r['iter'])==(c['net'],c['pin'],c['iter'])
            assert r['preferred_ids']==c['preferred'] and r['criticality']==c['criticality']
        positive=[float(r['analytic_extra'])/unit for r in rs if math.isfinite(float(r['analytic_extra'])) and float(r['analytic_extra'])>0]
        focus_stats[str(key)]=dict(contexts=len(cs),guided_contexts=sum(c['guide']=='1' for c in cs),contexts_existing_sink_layer_reexpand=sum(int(c['reexpand_sink_layer'])>0 for c in cs),contexts_with_existing_crossing=sum(int(c['crossings'])>0 for c in cs),sampled_crossing_evaluations=len(rs),sampled_positive_misses=len(positive),sampled_positive_extra_units_median=statistics.median(positive) if positive else None,sampled_positive_extra_units_max=max(positive) if positive else None,qualification='Seen focus cases and capped per-focus raw events; current tree re_expand is present state, not proof of actual queued seeds or single cause.')
    rows=[dict(observe(Path(p)),arm=a,reused=True) for a,p in read(b/'registration.json')['references'].items()]+[dict(observe(p),arm=a,reused=False) for a,p in dirs.items()]
    assert all(sha(Path(p))==h for p,h in bindings.items())
    result=dict(status='sealed_actual_guide_influence_audit',passed=True,observations=rows,source_sha256=bindings,same_all_non_time_records=True,same_all_prefix_records=True,same_all_native_iteration_rows=True,same_complete_route=True,same_final_guides=True,summary=summary,buckets=list(last.values()),groups=dict(groups),focus=focus_stats,directed_edges_checked=len(found),raw_edge_records_checked=len(edges),context_records_checked=len(contexts),unit_seconds=unit,
        qualification='One seen circuit. Independent actual RR edge/switch/configurability/Tdel, raw float guide multiplier and analytical criticality-weighted contribution checks on capped stratified rows; all cumulative bin counts retained with exact omissions. No full temporal replay or independent verification of unrecorded edge sums. Native route/guides/heap counters/queries/DP unchanged. Cumulative counts describe evaluations, not independent connections; edge cost contributions are not full path/STA effects or causal attribution; ordered trace timing not formal production overhead.')
    write(b/'guide_influence_analysis.json',result);print({k:result[k] for k in ['passed','summary','groups','focus','directed_edges_checked','raw_edge_records_checked','context_records_checked']})

if __name__=='__main__':main()
