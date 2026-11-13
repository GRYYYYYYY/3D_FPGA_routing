#!/usr/bin/env python3
"""Post-hoc saved worst-path union with exact audited RR terminal identities."""
import csv,json,resource,signal,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
ROOT=D.parents[1];sys.path[:0]=[str(D/'critical_path_diagnostics'),str(ROOT/'scripts')]
from inspect_paths import inspect
from compare_connections import extract
from check_route import read_trace


def main():
    resource.setrlimit(resource.RLIMIT_AS,(16*1024**3,16*1024**3));signal.alarm(600)
    out=D/'bounded_range_path_diagnostic_01';out.mkdir(exist_ok=False)
    sources={str(Path(__file__)):sha(Path(__file__))};reports=[];private=[];cases=[]
    for group,batch,arms,count in [('first','bounded_critical_count1_eltwise_dev_01',['C'],1),('final','bounded_cap_eltwise_dev_01',['C'],2),('range','bounded_cap_range_eltwise_dev_02',['L1','H1'],1),('range','bounded_cap_range_eltwise_dev_02',['L2','H2'],2)]:
        b=D/batch;assert read(b/'input_seal.json')['passed']
        for a in arms:cases.append((f'{group}_{a}',b/'runs'/('eltwise_layer_'+a),count))
    for label,rd,count in cases:
        m=read(rd/'manifest.json');au=read(rd/'independent_audit.json');assert m['status']=='completed' and m['metrics']['native_full_check_passed'] and au['audit']['passed']
        private.append(tuple(sha(rd/n) for n in ['packed.net','placed.place']));r=inspect(rd);r['label']=label;r['max_convergences']=count;r['batch_sealed']=True;reports.append(r)
        for n in ['report_timing.setup.rpt','packed.net','placed.place','routed.route','manifest.json','independent_audit.json','h3d_final_guides.csv']:sources[str(rd/n)]=sha(rd/n)
        sources[str(rd.parent.parent/'input_seal.json')]=sha(rd.parent.parent/'input_seal.json')
    assert len(set(private))==1
    write(out/'reported_paths.json',reports)
    connections={}
    for r in reports:
        for c in r['connections']:
            if c['inter_cluster']:connections[c['net'],tuple(c['sink_location'])]=c
    rows=[];ambiguous=[]
    for label,rd,count in cases:
        audit=read(rd/'independent_audit.json');routes=read_trace(rd/'routed.route');by_name={v['name']:(n,v) for n,v in routes.items()}
        guides={(int(r['net']),int(r['pin'])):r for r in csv.DictReader((rd/'h3d_final_guides.csv').open())}
        on_net={n for n,p in guides}
        for (name,location),c in connections.items():
            net,info=by_name[name];paths=extract(info,location)
            if len(paths)!=1:ambiguous.append(dict(label=label,net=name,location=location,paths=len(paths)));continue
            p=paths[0];pins={n.pin for n in info['trace'] if n.inode==p['sink'] and n.pin is not None}
            if len(pins)!=1:ambiguous.append(dict(label=label,net=name,location=location,pins=sorted(pins)));continue
            pin=next(iter(pins));delay=audit['audit']['nets'][str(net)]['routed_sink_delay_ns'][str(pin)]
            rows.append(dict(label=label,max_convergences=count,net=name,cluster_net=net,pin=pin,source_rr=info['trace'][0].inode,sink_rr=p['sink'],sink_location=location,physical_connection_ns=delay,crossings=p['crossings'],direct_guide=guides.get((net,pin)),any_guide_on_net=net in on_net))
    by_key={}
    for r in rows:by_key.setdefault((r['net'],tuple(r['sink_location'])),[]).append(r)
    for group in by_key.values():assert len({(r['source_rr'],r['sink_rr'],r['cluster_net'],r['pin']) for r in group})==1
    differences=[]
    for key,rs in by_key.items():
        rmap={r['label']:r for r in rs}
        for c,t in [('first_C','range_L1'),('first_C','range_H1'),('final_C','range_L2'),('final_C','range_H2')]:
            if c not in rmap or t not in rmap:continue
            a,b=rmap[c],rmap[t]
            differences.append(dict(comparison=c+'->'+t,net=a['net'],pin=a['pin'],source_rr=a['source_rr'],sink_rr=a['sink_rr'],reference_ns=a['physical_connection_ns'],new_ns=b['physical_connection_ns'],delta_ns=b['physical_connection_ns']-a['physical_connection_ns'],reference_direct_guide=bool(a['direct_guide']),new_direct_guide=bool(b['direct_guide']),reference_any_net_guide=a['any_guide_on_net'],new_any_net_guide=b['any_guide_on_net']))
    for p in [D/'critical_path_diagnostics/inspect_paths.py',D/'critical_path_diagnostics/compare_connections.py',ROOT/'scripts/check_route.py']:sources[str(p)]=sha(p)
    assert all(sha(Path(p))==h for p,h in sources.items())
    result=dict(status='sealed_posthoc_worst_path_union',passed=True,native_route_calls=0,union_intercluster_connections=len(connections),exact_rows=len(rows),ambiguous=ambiguous,reports=[dict(label=r['label'],max_convergences=r['max_convergences'],cpd_ns=r['cpd_ns'],startpoint=r['startpoint'],endpoint=r['endpoint']) for r in reports],rows=rows,differences=differences,source_sha256=sources,
        qualification='Post-hoc one worst setup path per saved legal result; increments rounded0.001ns. Same packed/place and unique matched RR source/sink/net-pin identities across routes; exact RR connection delays reused from independent zero-RC route audits. Atom pin mapping is by reported driver-net and unique sink cluster/location, not a general exact atom-terminal certificate. Physical connection deltas are not complete atom STA deltas or a single event/cause. Final guide absence distinguishes direct/whole-net guide presence but does not prove no indirect routing influence. Ambiguous matches retained, excluded from exact comparisons.')
    write(out/'analysis.json',result)
    with (out/'differences.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(differences[0]) if differences else ['comparison']);w.writeheader();w.writerows(differences)
    print(dict(union_connections=len(connections),exact_rows=len(rows),ambiguous=len(ambiguous),largest_regressions=sorted(differences,key=lambda r:r['delta_ns'],reverse=True)[:6]))

if __name__=='__main__':main()
