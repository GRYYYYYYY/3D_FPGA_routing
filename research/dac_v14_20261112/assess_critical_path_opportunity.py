#!/usr/bin/env python3
"""Assess existing-route alternatives for the current final worst-path connections.

This is a retrospective local diagnostic, not an executable online selection
policy or a native legality/STA result. No native route calls are made.
"""
import collections
import csv
import json
from pathlib import Path
import resource
import signal
import sys
from retained_prefix_workflow import D, read, write, sha
sys.path.insert(0,str(D/'critical_path_diagnostics'))
from inspect_paths import inspect
from compare_connections import extract
from check_route import read_trace
from verify_path_witnesses_v2 import graph_records, f32

resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
out=D/'critical_path_opportunity_01';out.mkdir(exist_ok=False)
current=D/'actual_search_tree_eltwise_dev_01/runs/eltwise_layer_T2'
refs={r['arm']:Path(r['path']) for r in read(D/'native_reconvergence_circuit_summary.json')['observations']
      if r['circuit']=='eltwise_layer' and r['count']==2 and r['arm'] in ['A0','R1','A1']}
files=[Path(__file__),D/'tree_aware_candidate_offline_01/analysis.json',D/'native_reconvergence_circuit_summary.json']
for directory in [current,*refs.values()]:
    files.extend(directory/name for name in ['manifest.json','routed.route','packed.net','placed.place','report_timing.setup.rpt','independent_audit.json'])
bindings={str(p):sha(p) for p in files}
write(out/'registration.json',dict(status='registered_before_analysis',native_route_calls=0,
    question='Do already realized strong-native routes offer shorter physically attachable alternatives for current Tf final critical connections, and do current query contexts cover those connections?',
    inputs=bindings,scope='One seen eltwise, matched graph/packing/placement, count2; final worst-path selection is retrospective. Remove only the selected terminal exclusive chain, preserve every other branch; splice an existing baseline path at its last intersection with the retained tree. Count per-net RR occupancy and explicit physical edges; reserved OPIN/nonconfig/bus-mux closure and full STA remain unproven.'))
report=inspect(current);write(out/'current_worst_path.json',report)
connections=[c for c in report['connections'] if c['inter_cluster']]
current_traces=read_trace(current/'routed.route')
occupancy=collections.Counter(node for info in current_traces.values() for node in {n.inode for n in info['trace']})
audit=read(current/'independent_audit.json');assert audit['audit']['passed']
manifest=read(current/'manifest.json')
graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
assert sha(graph)==manifest['shared_inputs'][str(graph)]['sha256']
reference_traces={}
for label,directory in refs.items():
    m=read(directory/'manifest.json');assert m['metrics']['native_full_check_passed'] and read(directory/'independent_audit.json')['audit']['passed']
    assert all(sha(directory/name)==sha(current/name) for name in ['packed.net','placed.place'])
    g=Path(m['command'][m['command'].index('--read_rr_graph')+1]);assert sha(g)==sha(graph)
    reference_traces[label]={v['name']:(k,v) for k,v in read_trace(directory/'routed.route').items()}
guides={(int(r['net']),int(r['pin'])) for r in csv.DictReader((current/'h3d_final_guides.csv').open())}
query=read(D/'tree_aware_candidate_offline_01/analysis.json')
query_connections={(r['net'],r['pin']) for r in query['rows'] if r['mode']==3}
query_nets={net for net,pin in query_connections}
needed=set();proposals=[];connection_rows=[]
for c in connections:
    net=c['cluster_net'];info=current_traces[net];trace=info['trace']
    assert c['sink_location_matches']==1
    endpoint=c['sink_paths'][0];assert len(endpoint['route_pins'])==1
    sink=endpoint['sink'];pin=endpoint['route_pins'][0]
    parents={};switches={};children=collections.defaultdict(set);node_map={n.inode:n for n in trace}
    for a,z in zip(trace,trace[1:]):
        if a.switch==-1:continue
        assert z.inode not in parents or parents[z.inode]==a.inode
        parents[z.inode]=a.inode;switches[a.inode,z.inode]=a.switch;children[a.inode].add(z.inode)
    # Prune the target's exclusive chain until a branching node or source.
    assert not children[sink]
    removed=set();node=sink
    while node in parents:
        if children[node]-removed:break
        if node!=sink and node_map[node].kind=='SINK':break
        removed.add(node);node=parents[node]
    retained=set(node_map)-removed
    prefix={trace[0].inode:0.}
    connection_rows.append(dict(net=net,name=c['net'],pin=pin,sink=sink,source=trace[0].inode,
        current_physical_ns=audit['audit']['nets'][str(net)]['routed_sink_delay_ns'][str(pin)],
        direct_final_guide=(net,pin) in guides,any_final_guide_on_net=any(n==net for n,p in guides),
        in_guided_query_contexts=(net,pin) in query_connections,net_in_guided_query_contexts=net in query_nets,
        retained_nodes=len(retained),removed_nodes=len(removed)))
    for label,by_name in reference_traces.items():
        rn,other=by_name[c['net']];assert rn==net
        paths=extract(other,c['sink_location']);assert len(paths)==1
        path=paths[0];assert path['sink']==sink and path['nodes'][-1]==trace[0].inode
        forward=list(reversed(path['nodes']));sw=list(reversed(path['switches']))
        at=max(i for i,n in enumerate(forward) if n in retained)
        suffix=forward[at:];suffix_sw=sw[at:];anchor=suffix[0]
        assert not (set(suffix[1:])&retained)
        ancestry=[anchor];asw=[];node=anchor
        while node in parents:
            parent=parents[node];asw.append(switches[parent,node]);ancestry.append(parent);node=parent
        ancestry.reverse();asw.reverse()
        new_path=ancestry+suffix[1:];new_switches=asw+suffix_sw
        assert len(set(new_path))==len(new_path)
        new_nodes=retained|set(suffix)
        assert all(n in retained or n in suffix for n in new_path)
        changes={n:occupancy[n]-int(n in node_map)+int(n in new_nodes) for n in set(node_map)|new_nodes}
        needed.update(changes)
        proposals.append(dict(net=net,pin=pin,name=c['net'],reference=label,anchor=anchor,
            retained_prefix_nodes=ancestry,retained_prefix_switches=asw,suffix_nodes=suffix,suffix_switches=suffix_sw,
            new_path=new_path,new_switches=new_switches,current_physical_ns=connection_rows[-1]['current_physical_ns'],
            occupancy_after=changes,removed_nodes=sorted(removed),added_nodes=sorted(new_nodes-set(node_map))))
capacities={};delays={};edges=set();wanted={(u,v,s) for p in proposals for u,v,s in zip(p['new_path'],p['new_path'][1:],p['new_switches'])}
for section,e in graph_records(graph):
    a=e.attrib
    if section=='switches':
        t=e.find('timing');v={} if t is None else t.attrib
        assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal'])
        delays[int(a['id'])]=f32(v.get('Tdel',0))
    elif section=='rr_nodes' and int(a['id']) in needed:
        t=e.find('timing');v={} if t is None else t.attrib;assert all(f32(v.get(k,0))==0 for k in ['R','C'])
        capacities[int(a['id'])]=int(a['capacity'])
    elif section=='rr_edges':
        key=(int(a['src_node']),int(a['sink_node']),int(a['switch_id']))
        if key in wanted:edges.add(key)
assert needed<=capacities.keys() and wanted==edges
for p in proposals:
    cost=sum(delays[s] for s in p['new_switches'])*1e9
    conflicts={str(n):dict(after=occ,capacity=capacities[n],before=occupancy[n]) for n,occ in p.pop('occupancy_after').items() if occ>capacities[n]}
    p.update(new_physical_ns=cost,improvement_ns=p['current_physical_ns']-cost,
        rr_capacity_feasible=not conflicts,capacity_conflicts=conflicts,
        final_sta_evaluated=False,native_full_check=False)
assert all(sha(p)==h for p,h in bindings.items())
write(out/'analysis.json',dict(passed=True,native_route_calls=0,source_sha256=bindings,
    graph_sha256=sha(graph),current_CPD_ns=report['cpd_ns'],connections=connection_rows,proposals=proposals,
    qualification='Retrospective current-worst-path diagnostic; unique RR sink location and route pin identity, not independently certified atom-pin mapping. Alternative suffixes come from already legal same-input baseline routes and are spliced into current retained prefixes. Per-net RR capacity plus edge/path continuity is necessary, not native FULL legality/nonconfig/reserved-OPIN/bus-mux or full STA proof. Different final worst paths mean a shorter connection does not guarantee reduced CPD. No native route file changed.'))
print(json.dumps(dict(connections=connection_rows,proposals=[{k:v for k,v in p.items() if k in ['net','pin','reference','new_physical_ns','improvement_ns','rr_capacity_feasible','capacity_conflicts']} for p in proposals]),indent=2),flush=True)
