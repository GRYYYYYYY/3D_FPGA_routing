#!/usr/bin/env python3
"""Build an isolated coordinated repair using current capacities and real paths."""
import argparse
import array
import collections
import math
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,nodes,prefixes,prune_sinks,attach,downstream_pins,serialize
from verify_path_witnesses_v2 import graph_records,f32
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

parser=argparse.ArgumentParser();parser.add_argument('--opportunity',type=Path,required=True);parser.add_argument('--batch',type=Path,required=True);parser.add_argument('--order',choices=['ascending','descending'],default='ascending')
args=parser.parse_args();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
assert shutil.disk_usage(D).free>=80*1024**3
reg=read(D/'native_frontier_joint_policy_experiment_01.json');assert all(sha(p)==h for p,h in reg['source_sha256'].items())
op=read(args.opportunity.resolve());assert op['status']=='compatible'
seal=read(args.opportunity.resolve().parent/'candidate_binding.json');assert seal['passed'] and all(sha(p)==h for p,h in seal['source_sha256'].items())
source=Path(op['input_run']);m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
assert sha(graph)==m['shared_inputs'][str(graph)]['sha256']
targets=op['targets'];target=targets[0]
net,pin=target['net'],target['pin'];driver=D/'current_sta_queries_01/critical_capacity_driver';ex=read(D/'current_sta_queries_01/execution.json')
assert sha(driver)==ex['output_sha256']['critical_capacity_driver']
binary=D/'residual_query_offline_01/graph.bin';assert sha(binary)==read(binary.with_name('graph_binding.json'))['binary_graph_sha256']
b=args.batch.resolve();b.mkdir(exist_ok=False)
inputs=[Path(__file__),D/'coordinated_repair_tree.py',D/'test_coordinated_repair_tree.py',D/'native_frontier_joint_policy_experiment_01.json',
    args.opportunity.resolve(),args.opportunity.resolve().parent/'candidate_binding.json',source/'manifest.json',source/'routed.route',source/'independent_audit.json',graph,driver,binary]
bindings={str(p):sha(p) for p in inputs}
write(b/'registration.json',dict(status='registered_before_query',input_run=str(source),targets=[dict(net=t['net'],pin=t['pin']) for t in targets],order=args.order,
    sink_order='Ascending original net_pin_index; net order is the only selectable factor.',source_sha256=bindings,
    pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
    limits=dict(timeout_seconds=1800,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3),native_calls=0,
    qualification='External full-device zero-RC coordinated prototype. Exact per-attachment physical search does not optimize multi-terminal tree/whole-design timing. Native FULL/STA required after all sinks restored.'))
start=time.monotonic()
unit_source=D/'joint_coordinated_repair_01/unit_validation.json'
unit=read(unit_source);assert unit['passed'] and all(sha(p)==h for p,h in unit['source_sha256'].items())
write(b/'unit_validation.json',dict(passed=True,reused=True,source=str(unit_source),source_sha256=sha(unit_source),scope='Unchanged tree helper: prior1000randomized preservation/reattachment cases reused.'))
caps=array.array('I');kinds=[];switches={}
for section,e in graph_records(graph):
    a=e.attrib
    if section=='switches':
        t=e.find('timing');v={} if t is None else t.attrib
        assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal']);switches[int(a['id'])]=f32(v.get('Tdel',0))
    elif section=='rr_nodes':
        assert int(a['id'])==len(caps);caps.append(int(a['capacity']));kinds.append(a['type'])
        t=e.find('timing');v={} if t is None else t.attrib;assert all(f32(v.get(k,0))==0 for k in ['R','C'])
    elif section=='rr_edges':break
nreal=len(caps);traces=read_trace(source/'routed.route');owners=collections.defaultdict(set)
for n,info in traces.items():
    for node in {x.inode for x in info['trace']}:owners[node].add(n)
affected=collections.defaultdict(set)
for node_s,conflict in op['current_other_net_conflicts'].items():
    for owner in conflict['other_nets']:affected[owner].add(int(node_s))
blockers=sorted(affected,reverse=args.order=='descending')
original={n:from_trace(traces[n]['trace'],switches) for n in [*[t['net'] for t in targets],*blockers]};trees=dict(original)
def replace(n,new):
    for node in nodes(trees[n])-nodes(new):owners[node].remove(n)
    for node in nodes(new)-nodes(trees[n]):owners[node].add(n)
    trees[n]=new
pending={};pruning=[]
for n in blockers:
    pins=sorted({p for node in affected[n] for p in downstream_pins(original[n],node)})
    assert pins
    pending[n]=[(p,original[n]['sinks'][p]) for p in pins]
    kept=prune_sinks(original[n],pins);assert not nodes(kept)&affected[n]
    pruning.append(dict(net=n,conflicting_resources=sorted(affected[n]),removed_pins=pins,
        removed_nodes=sorted(nodes(original[n])-nodes(kept)),retained_nodes=sorted(nodes(kept))))
    replace(n,kept)
for t in targets:
    n,p=t['net'],t['pin'];kept_target=prune_sinks(original[n],[p]);forward=t['suffix_nodes'];weights=t['suffix_weights']
    new_target=attach(kept_target,p,original[n]['sinks'][p],forward,[None]*len(weights),weights);replace(n,new_target)
    assert math.isclose(prefixes(new_target)[original[n]['sinks'][p]],t['physical_seconds'],rel_tol=1e-12,abs_tol=1e-24)
assert all(len(ns)<=caps[node] for node,ns in owners.items())
write(b/'initial_transaction.json',dict(target_reserved_nodes={str(t['net']):t['suffix_nodes'] for t in targets},blockers=blockers,pruning=pruning,
    pending={str(n):v for n,v in pending.items()},partial_state_capacity_feasible=True))
rows=[];failure=None
for n in blockers:
    for p,sink in pending[n]:
        directory=b/f'query_{len(rows):02d}_net{n}_pin{p}';directory.mkdir()
        tree=trees[n];retained=nodes(tree);prefix=prefixes(tree)
        anchors={node:prefix[node] for node in retained if kinds[node] not in ['SINK','IPIN']}
        blocked={node for node,ns in owners.items() if len(ns)-int(n in ns)>=caps[node]}
        blocked|={node for node,capacity in enumerate(caps) if capacity==0}
        assert not retained&blocked
        write(directory/'state.json',dict(net=n,pin=p,sink=sink,tree=tree,anchors=anchors,blocked=sorted(blocked),
            pending_this_net=[x for x in pending[n] if x[0] not in tree['sinks']]))
        with (directory/'cases.txt').open('w') as f:
            f.write('1\n'+' '.join(map(str,[n,p,sink,len(retained),len(anchors),len(blocked)]))+'\n')
            f.write(' '.join(map(str,sorted(retained)))+'\n')
            for node,delay in sorted(anchors.items()):f.write(f'{node} {delay:.17g}\n')
            f.write(' '.join(map(str,sorted(blocked)))+'\n')
        begin=time.monotonic()
        with (directory/'stdout.log').open('w') as out,(directory/'stderr.log').open('w') as err:
            subprocess.run([str(driver),str(binary),str(directory/'cases.txt'),'capacity'],stdout=out,stderr=err,check=True,timeout=120)
        elapsed=time.monotonic()-begin;result=None;edges=[]
        for line in (directory/'stdout.log').read_text().splitlines():
            v=line.split();assert tuple(map(int,v[1:4]))==(n,p,1)
            if v[0]=='RESULT':
                assert result is None
                result=dict(net=n,pin=p,stop=int(v[4]),expansions=int(v[5]),labels=int(v[6]),peak_heap=int(v[7]),
                    physical_seconds=float(v[8]),lower_seconds=float(v[9]),core_seconds=float(v[10]),edge_count=int(v[11]),process_seconds=elapsed)
            else:
                assert v[0]=='EDGE' and int(v[4])==len(edges);edges.append((int(v[5]),int(v[6]),float(v[7])))
        assert result is not None
        result['edges']=edges;result['directory']=str(directory);rows.append(result)
        if result['stop']!=0:
            failure=dict(net=n,pin=p,stop=result['stop'],reason='No exact complete path under current sequential transaction; rollback required.')
            write(directory/'result.json',result);break
        assert result['physical_seconds']==result['lower_seconds']
        assert len(edges)==result['edge_count'] and edges[0][0]==sink and edges[-1][1]==nreal
        assert all(a[1]==z[0] for a,z in zip(edges,edges[1:]))
        assert edges[-1][0] in anchors and edges[-1][2]==anchors[edges[-1][0]]
        assert not {u for u,v,w in edges[:-1]}&retained
        assert not {u for u,v,w in edges}&blocked
        assert math.isclose(sum(w for u,v,w in edges),result['physical_seconds'],rel_tol=1e-12,abs_tol=1e-24)
        forward=[edges[-1][0]]+[u for u,v,w in reversed(edges[:-1])];weights=[w for u,v,w in reversed(edges[:-1])]
        updated=attach(tree,p,sink,forward,[None]*len(weights),weights);replace(n,updated)
        assert all(len(ns)<=caps[node] for node,ns in owners.items())
        result['partial_state_capacity_feasible']=True;write(directory/'result.json',result)
        print(dict(net=n,pin=p,new_physical_ns=result['physical_seconds']*1e9,restored=len(rows)),flush=True)
    if failure:break

# Resolve actual switch IDs independently against the original RRG, even for
# already restored partial branches when a later attachment fails.
wanted={(u,v,w) for tree in trees.values() for v,(u,sw,w) in tree['edges'].items() if sw is None}
needed=set().union(*(nodes(tree) for tree in trees.values()));metadata={};edge_switches=collections.defaultdict(list)
for section,e in graph_records(graph):
    a=e.attrib
    if section=='rr_nodes':
        node=int(a['id'])
        if node in needed:
            v=e.find('loc').attrib;z=int(v.get('layer_low',v.get('layer',0)))
            metadata[node]=dict(kind=a['type'],low=(int(v['xlow']),int(v['ylow']),z),high=(int(v['xhigh']),int(v['yhigh']),int(v.get('layer_high',z))),ptc=int(v['ptc']))
    elif section=='rr_edges':
        switch=int(a['switch_id']);edge=(int(a['src_node']),int(a['sink_node']),switches[switch])
        if edge in wanted:edge_switches[edge].append(switch)
assert wanted==edge_switches.keys()
for tree in trees.values():
    tree['edges']={v:(u,min(edge_switches[u,v,w]) if sw is None else sw,w) for v,(u,sw,w) in tree['edges'].items()}
write(b/'final_transaction_trees.json',{str(n):tree for n,tree in trees.items()})
candidate=None;changes=[]
if failure is None:
    for n,tree in trees.items():
        assert tree['sinks']==original[n]['sinks']
        before,after=prefixes(original[n]),prefixes(tree)
        for p,sink in tree['sinks'].items():
            if not math.isclose(before[sink],after[sink],rel_tol=1e-12,abs_tol=1e-24):
                changes.append(dict(net=n,pin=p,sink=sink,before_ns=before[sink]*1e9,after_ns=after[sink]*1e9))
    route_text=(source/'routed.route').read_text()
    for n,tree in sorted(trees.items()):
        match=re.search(r'^Net '+str(n)+r' \(.*?\)\n.*?(?=^Net |\Z)',route_text,re.M|re.S);assert match
        replacement=match.group(0).splitlines()[0]+'\n\n'+serialize(tree,metadata)+'\n'
        route_text=route_text[:match.start()]+replacement+route_text[match.end():]
    candidate=b/'candidate.route';candidate.write_text(route_text);parsed=read_trace(candidate)
    assert parsed.keys()==traces.keys()
    assert all(parsed[n]==traces[n] for n in traces if n not in trees)
    for n,tree in trees.items():assert from_trace(parsed[n]['trace'],switches)==tree
    recount=collections.Counter(node for info in parsed.values() for node in {x.inode for x in info['trace']})
    assert all(count<=caps[node] for node,count in recount.items())
assert all(sha(p)==h for p,h in bindings.items())
write(b/'analysis.json',dict(passed=True,status='complete_candidate_pending_native_FULL_STA' if candidate else 'transaction_failed_no_candidate',
    input_run=str(source),source_sha256=bindings,targets=[dict(net=t['net'],pin=t['pin']) for t in targets],blockers=blockers,affected_nets=sorted(trees),
    required_blocker_sink_count=sum(map(len,pending.values())),queries=rows,failure=failure,
    candidate_route=str(candidate) if candidate else None,candidate_sha256=sha(candidate) if candidate else None,
    changed_physical_sink_delays=changes,real_new_edges_checked=len(wanted),all_sinks_restored=failure is None,
    build_process_seconds=time.monotonic()-start,native_calls=0,
    qualification='Sequential physical shortest extensions with fixed other capacity. Complete candidate remains unaccepted until nativeFULL and fullSTA; failed transaction never changes accepted input route.'))
print(dict(status='candidate_ready' if candidate else 'rolled_back',failure=failure,changed_sink_delays=len(changes)),flush=True)
