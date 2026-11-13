#!/usr/bin/env python3
"""Independently stream actual native RR edges and validate read-only path traces."""
import argparse
import collections
import math
from pathlib import Path
import resource
import shutil
import signal
import statistics
import struct
import time
from lxml import etree
from retained_prefix_workflow import D, read, write, sha
from routing_log_metrics import ROW


def fields(line):
    return dict(x.split('=',1) for x in line.split()[1:])


def path_nodes(record):
    if record['path']=='-':return []
    result=[]
    for text in record['path'].split(';'):
        node,delay,occ,capacity,acc,owned,ordinary=text.split(',')
        result.append((int(node),float(delay),int(occ),int(capacity),float(acc),int(owned),int(ordinary)))
    return result


def logs(path):
    completed=0;pair=None
    with path.open() as stream:
        for line in stream:
            match=ROW.match(line)
            if match:completed=int(match[1])
            if line.startswith('H3D_PREFIX_PAIR '):pair=fields(line)
            if line.startswith('H3D_PATH_WITNESS '):
                r=fields(line)
                assert pair is not None and all(r[k]==pair[k] for k in ['plan','net','pin','entry','prior','proposed'])
                yield 'witness',r,completed+1
            elif line.startswith(('H3D_PREFIX_DECISION ','H3D_PATH_CACHE ','H3D_PATH_TRACE ','H3D_PREFIX_PAIR ','H3D_DELAY ')):
                yield line.split()[0],fields(line),completed+1


def graph_records(path):
    # Independent of the C++ RR reader and existing route-audit adapters.
    with path.open('rb') as stream:
        for _,element in etree.iterparse(stream,events=('end',),huge_tree=True):
            parent=element.getparent()
            if parent is not None and parent.tag in ['rr_nodes','rr_edges','switches']:
                yield parent.tag,element
                element.clear()
                while element.getprevious() is not None:del parent[0]


def f32(value):return struct.unpack('f',struct.pack('f',float(value)))[0]


def close(a,b):return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-24)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);ap.add_argument('--out',required=True);args=ap.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));signal.alarm(1800)
    assert shutil.disk_usage(D).free>=80*1024**3
    b=args.batch.resolve();assert read(b/'input_seal.json')['passed'] and read(b/'completion.json')['gate_passed']
    t=b/'runs/eltwise_layer_T';m=read(t/'manifest.json');assert m['status']=='completed' and m['metrics']['native_full_check_passed']
    assert read(t/'trace_equivalence.json')['passed'] and read(t/'independent_audit.json')['audit']['passed'] and read(t/'final_guide_audit.json')['passed']
    graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);assert sha(graph)==m['shared_inputs'][str(graph.resolve())]['sha256']
    log=t/'stdout.log';assert sha(log)==m['outputs']['stdout.log']['sha256']
    out=D/args.out;out.mkdir(exist_ok=False);shutil.copy2(__file__,out/'runner.py')
    inputs=[graph,log,t/'manifest.json',t/'trace_equivalence.json',t/'independent_audit.json',t/'final_guide_audit.json',b/'registration.json',b/'completion.json',b/'input_seal.json',Path(__file__),D/'routing_log_metrics.py']
    bindings={str(p):sha(p) for p in inputs};started=time.monotonic()
    write(out/'registration.json',dict(question='Do recorded paths exist with their reported directed switch-delay sums, and do reported planar price summaries match the captured node snapshot?',
        sources_sha256=bindings,timeout_seconds=1800,memory_bytes=32*1024**3,disk_reserve_bytes=80*1024**3,native_route_calls=0,
        scope='Physical edge/weight and reported proxy-formula audit. No independent temporal replay of occupancy/ownership, no all-endpoint shortest-path oracle, no final STA or causal search certificate.'))
    wanted_nodes=set();wanted_edges=set();decisions={};records=0;pair_count=0;cache=None;trace=None;delay=None
    for tag,r,iteration in logs(log):
        if tag=='witness':
            records+=1;nodes=path_nodes(r)
            if r['status']=='measured':
                assert nodes and len({n[0] for n in nodes})==len(nodes)
                wanted_nodes.update(n[0] for n in nodes)
                wanted_edges.update((a[0],z[0],a[1]) for a,z in zip(nodes,nodes[1:]))
            else:assert r['status'] in ['unmeasured','cache_limit'] and not nodes and math.isnan(float(r['delay_seconds']))
        elif tag=='H3D_PREFIX_DECISION':decisions[int(r['plan']),int(r['net'])]=int(r['accepted'])
        elif tag=='H3D_PREFIX_PAIR':pair_count+=1
        elif tag=='H3D_PATH_CACHE':cache=r
        elif tag=='H3D_PATH_TRACE':trace=r
        elif tag=='H3D_DELAY':delay=r
    assert cache and trace and records==int(trace['records'])<=50000
    assert records+int(trace['omitted'])==2*pair_count and int(trace['limit'])==50000
    assert int(cache['records'])<=int(cache['record_limit'])==2000000
    assert delay and int(cache['records'])<=int(delay['settled'])
    if int(cache['skipped_queries'])==0:assert int(cache['records'])==int(delay['settled'])
    metadata={};switches={};found_edges=set();wanted_pairs={(u,v) for u,v,w in wanted_edges};pending_edges=[]
    counts=collections.Counter()
    for section,e in graph_records(graph):
        counts[section]+=1;a=e.attrib
        if section=='switches':
            timing=e.find('timing');v={} if timing is None else timing.attrib
            assert all(f32(v.get(k,0.))==0. for k in ['R','Cin','Cout','Cinternal'])
            delay=f32(v.get('Tdel',0.));assert math.isfinite(delay) and delay>=0.;switches[int(a['id'])]=delay
        elif section=='rr_nodes':
            timing=e.find('timing');v={} if timing is None else timing.attrib
            assert f32(v.get('R',0.))==f32(v.get('C',0.))==0.
            node=int(a['id'])
            if node in wanted_nodes:
                loc=e.find('loc').attrib;lo=int(loc.get('layer_low',loc.get('layer',0)));hi=int(loc.get('layer_high',loc.get('layer',0)))
                assert lo==hi
                metadata[node]=dict(kind=a['type'],layer=lo,capacity=int(a.get('capacity',1)))
        elif section=='rr_edges':
            u,v=int(a['src_node']),int(a['sink_node'])
            if (u,v) in wanted_pairs:pending_edges.append((u,v,int(a['switch_id'])))
    assert set(metadata)==wanted_nodes
    for u,v,sw in pending_edges:
        edge=u,v,switches[sw]
        if edge in wanted_edges:found_edges.add(edge)
    assert found_edges==wanted_edges,('missing_directed_weighted_edges',len(wanted_edges-found_edges))
    first=read(b/'registration.json')['first_legal_iteration'];groups=collections.defaultdict(list);statuses=collections.Counter();unique_paths=set();snapshots={};measured=0
    for tag,r,iteration in logs(log):
        if tag!='witness':continue
        status=r['status'];statuses[('reverse' if int(r['reverse']) else 'forward')+':'+status]+=1
        if status!='measured':continue
        measured+=1;nodes=path_nodes(r);entry=int(r['entry']);endpoint=int(r['endpoint']);reverse=int(r['reverse'])
        assert (nodes[0][0],nodes[-1][0])==((entry,endpoint) if reverse else (endpoint,entry))
        assert nodes[-1][1]==0. and close(math.fsum(n[1] for n in nodes[:-1]),float(r['delay_seconds']))
        layers=[metadata[n[0]]['layer'] for n in nodes]
        crossings=sum(x!=y for x,y in zip(layers,layers[1:]))
        assert crossings==reverse and (not reverse or layers[0]!=layers[1])
        premium=[];maximum=1.;ordinary=overused=projected=0
        for i,(node,delay,occ,capacity,acc,owned,is_ordinary) in enumerate(nodes):
            assert capacity==metadata[node]['capacity'] and occ>=0 and owned in [0,1] and is_ordinary in [0,1]
            adjacent=(i>0 and layers[i-1]!=layers[i]) or (i+1<len(nodes) and layers[i]!=layers[i+1])
            planar=metadata[node]['kind'] in ['CHANX','CHANY'] and node!=entry and not adjacent
            assert is_ordinary==planar
            if not planar:continue
            ordinary+=1;demand=occ+(not owned);overused+=occ>capacity;projected+=demand>capacity
            price=acc*(1+float(r['pres_fac'])*max(0,demand-capacity));assert math.isfinite(price)
            premium.append(max(0.,price-1));maximum=max(maximum,price)
        assert int(r['finite_price'])==1 and ordinary==int(r['ordinary']) and overused==int(r['overused']) and projected==int(r['projected_overused'])
        assert math.isclose(math.fsum(premium),float(r['premium_sum']),rel_tol=1e-10,abs_tol=1e-9)
        assert math.isclose(maximum,float(r['max_price']),rel_tol=1e-12,abs_tol=1e-12)
        key=(int(r['plan']),int(r['net']),reverse,endpoint,entry)
        snapshot=(r['path'],r['premium_sum'],r['max_price'],r['pres_fac'])
        if key in snapshots:assert snapshots[key]==snapshot
        else:snapshots[key]=snapshot
        unique_paths.add((reverse,endpoint,entry))
        accepted=decisions[int(r['plan']),int(r['net'])]
        group=f"{'post' if iteration>first else 'pre'}_legal/side{reverse}/accepted{accepted}/prior{r['prior']}/proposed{r['proposed']}"
        groups[group].append(dict(premium=float(r['premium_sum']),overused=overused,projected=projected))
    summary={k:dict(repeated_leaf_side_events=len(v),positive_premium_events=sum(x['premium']>0 for x in v),
        observed_overuse_events=sum(x['overused']>0 for x in v),projected_overuse_events=sum(x['projected']>0 for x in v),
        median_premium=statistics.median(x['premium'] for x in v),maximum_premium=max(x['premium'] for x in v)) for k,v in groups.items()}
    checks={p:sha(p)==h for p,h in bindings.items()};write(out/'input_seal.json',dict(passed=all(checks.values()),checks=checks));assert all(checks.values())
    write(out/'analysis.json',dict(passed=True,records=records,measured_leaf_side_events=measured,status_counts=dict(statuses),
        unique_static_endpoint_entry_paths=len(unique_paths),unique_plan_side_entry_snapshots=len(snapshots),groups=summary,
        graph_records_inspected=dict(counts),requested_weighted_edges=len(wanted_edges),path_cache=cache,trace_limit=trace,sources_sha256=bindings,
        qualification='Canonical settled shortest witnesses, not minimum-congestion alternatives among equal-delay paths. Prices are ownership-aware negotiated multipliers, not summed native search costs. Repeated leaf events and temporal snapshots are not independent samples. Actual temporal state is read from diagnostic snapshots, not independently replayed. No QoR or causal adoption inference.'))
    write(out/'completion.json',dict(status='witness_physical_proxy_audit_complete',wall_seconds=time.monotonic()-started,native_route_calls=0))
    print(dict(records=records,measured=measured,unique_static_paths=len(unique_paths),groups=summary))


if __name__=='__main__':main()
