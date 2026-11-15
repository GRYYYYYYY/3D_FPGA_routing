"""Three-way combine two actual route branches; always require new native STA.

The terminal wire alternative and completed timing branch share one actual
resource source. Only compatible RR-parent/switch changes are merged. Final
occupancy is checked globally; every changed tree keeps its fixed terminals.
No search, native acceptance or whole cost is inferred from composition.
"""
import argparse
import collections
import hashlib
import os
from pathlib import Path
import re
import resource
import time
import numpy as np

from retained_prefix_workflow import D, read, write, sha
from run_native_scope_policy_v4 import run_dir
from actual_route_tree_identity import tree_identity
from resource_opportunity_census import stream_trace, wire_units
from coordinated_repair_tree import from_trace, nodes, prefixes, serialize
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS
from state_resource_assurance import require_publication_proof
from native_zero_rc_tree_delay_v1 import sink_delays


def merge_edges(base, alternative, target):
    assert base['root']==alternative['root']==target['root']
    assert base['sinks']==alternative['sinks']==target['sinks']
    missing=object()
    side={node for node in set(base['edges'])|set(alternative['edges'])
          if base['edges'].get(node,missing)!=alternative['edges'].get(node,missing)}
    main={node for node in set(base['edges'])|set(target['edges'])
          if base['edges'].get(node,missing)!=target['edges'].get(node,missing)}
    conflicts=[node for node in sorted(side&main)
               if alternative['edges'].get(node,missing)!=target['edges'].get(node,missing)]
    if conflicts:
        return None,dict(compatible=False,conflicting_parent_or_switch_nodes=conflicts,
                         side_changed_nodes=len(side),timing_changed_nodes=len(main))
    result=dict(root=target['root'],sinks=dict(target['sinks']),edges=dict(target['edges']))
    for node in side:
        if node in alternative['edges']:result['edges'][node]=alternative['edges'][node]
        else:result['edges'].pop(node,None)
    # prefixes() rejects detached/cyclic trees and missing parents.
    delays=prefixes(result)
    assert set(delays)==nodes(result)
    assert set(result['sinks'].values())<=nodes(result)
    reached={result['root']}
    for sink in result['sinks'].values():
        node=sink;steps=0
        while node!=result['root']:
            assert node in result['edges']
            reached.add(node);node=result['edges'][node][0];steps+=1
            assert steps<=len(result['edges'])
    assert reached==nodes(result),'Merged tree has a dangling nonterminal branch'
    return result,dict(compatible=True,side_changed_nodes=len(side),
                       timing_changed_nodes=len(main),same_changed_node_entries=len(side&main))


def build(selection, target_state, cache_directory, output):
    started=time.monotonic()
    selection,target_state,output=[Path(p).resolve() for p in [selection,target_state,output]]
    output.mkdir(exist_ok=False)
    resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
    write(output/'registration.json',dict(pid=os.getpid(),
        start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
        selection=str(selection),target_state=str(target_state),native_calls=0,
        source_sha256={str(Path(__file__).resolve()):sha(__file__)}))
    selected=read(selection/'completion.json')
    assert selected['passed'] and selected['selected'] is not None
    assert all(sha(p)==h for p,h in selected['source_sha256'].items())
    base_state=Path(selected['state']);side_state=Path(selected['selected']['state'])
    states=dict(base=base_state,side=side_state,timing=target_state)
    runs={label:run_dir(state) for label,state in states.items()}
    axes={label:require_publication_proof(state)['resource_axes'] for label,state in states.items()}
    vectors={label:read(state/'endpoint_vector.json') for label,state in states.items()}
    source_inputs={}
    for label,run in runs.items():
        manifest=read(run/'manifest.json');command=manifest['command']
        assert manifest['metrics']['native_full_check_passed']
        graph=Path(command[command.index('--read_rr_graph')+1])
        source_inputs[label]=[manifest['shared_inputs'][str(graph)]['sha256'],
                             sha(command[1]),sha(command[2]),sha(run/'packed.net'),sha(run/'placed.place'),
                             vectors[label]['constraints_sha256']]
    assert source_inputs['base']==source_inputs['side']==source_inputs['timing']
    cache=FullRouteGraphCache(graph,cache_directory);g=cache.g
    assert g.receipt['graph_sha256']==source_inputs['base'][0]
    identities={}
    for label,run in runs.items():
        identities[label]=tree_identity(run/'routed.route')
        write(output/(label+'_tree_ids.json'),identities[label])
        print(dict(stage='tree_identity',branch=label,nets=len(identities[label])),flush=True)
    assert identities['base'].keys()==identities['side'].keys()==identities['timing'].keys()
    side_changed={n for n in identities['base'] if identities['base'][n]!=identities['side'][n]}
    timing_changed={n for n in identities['base'] if identities['base'][n]!=identities['timing'][n]}
    assert side_changed,'Selected wire alternative has no changed physical trees'
    trees={label:{} for label in runs};occupancy=np.zeros(g.n,dtype=np.int32)
    for label,run in runs.items():
        for record in stream_trace(run/'routed.route'):
            if label=='timing' and record['trace']:
                occupancy[np.array(sorted({n.inode for n in record['trace']}),dtype=np.int64)]+=1
            if record['net'] in side_changed:
                trees[label][record['net']]=from_trace(record['trace'],g.switches)
        assert set(trees[label])==side_changed
    assert np.all(occupancy<=g.capacities)
    merged={};merges=[]
    for net in sorted(side_changed):
        try:
            result,receipt=merge_edges(trees['base'][net],trees['side'][net],trees['timing'][net])
        except (AssertionError,KeyError,RecursionError) as error:
            result=None;receipt=dict(compatible=False,error_type=type(error).__name__,error=str(error))
        merges.append(dict(net=net,**receipt))
        if result is not None:merged[net]=result
    write(output/'merge_checks.json',merges)
    write(output/'branches.json',dict(side_changed_nets=sorted(side_changed),timing_changed_nets=sorted(timing_changed),
                                     overlapping_nets=sorted(side_changed&timing_changed)))
    if len(merged)!=len(side_changed):
        write(output/'completion.json',dict(passed=True,status='incompatible_tree_changes_no_candidate',
            native_calls_new=0,actual_merge_checks=str(output/'merge_checks.json'),
            native_FULL_STA_completed=False,committed_to_original_actor=False))
        return
    def metadata(node):
        a=g.nodes[node]
        return dict(kind=KINDS[int(a[1])],low=tuple(map(int,a[2:5])),high=tuple(map(int,a[5:8])),
                    ptc=int(a[8]),direction=cache.meta['directions'][int(cache.extra[node,0])])
    def physical(tree):
        sb,cb=set(),set()
        for child,(parent,_,_) in tree['edges'].items():
            if int(g.nodes[parent,4])!=int(g.nodes[child,4]):
                if metadata(parent)['kind']=='OPIN':cb.add(parent)
                else:sb.add(tuple(sorted([parent,child])))
        return dict(wirelength=sum(wire_units(metadata(node)) for node in nodes(tree)),
                    SB_pairs=len(sb),CB_sources=len(cb))
    predictions=[];before_metrics={};after_metrics={}
    for net,tree in merged.items():
        old=trees['timing'][net]
        occupancy[np.array(sorted(nodes(old)),dtype=np.int64)]-=1
        occupancy[np.array(sorted(nodes(tree)),dtype=np.int64)]+=1
        g.require_edges([(parent,child,switch) for child,(parent,switch,_) in tree['edges'].items()])
        before_metrics[net]=physical(old);after_metrics[net]=physical(tree)
        before,after=[sink_delays(t,audited_zero_rc=True) for t in [old,tree]]
        for pin,delay in after.items():
            predictions.append(dict(net=net,pin=pin,sink=tree['sinks'][pin],before_s=before[pin],after_s=delay,
                                    delta_s=delay-before[pin]))
    conflicts=np.flatnonzero(occupancy>g.capacities)
    write(output/'capacity_check.json',dict(passed=not len(conflicts),nodes=g.n,
          conflicted_nodes=[dict(node=int(n),occupancy=int(occupancy[n]),capacity=int(g.capacities[n])) for n in conflicts[:128]],
          total_conflicted_nodes=len(conflicts)))
    if len(conflicts):
        write(output/'completion.json',dict(passed=True,status='combined_capacity_conflict_no_candidate',native_calls_new=0,
              native_FULL_STA_completed=False,committed_to_original_actor=False))
        return
    delta={k:sum(after_metrics[n][k]-before_metrics[n][k] for n in merged) for k in axes['timing']}
    structural={k:axes['timing'][k]+delta[k] for k in delta}
    allmeta={node:metadata(node) for tree in merged.values() for node in nodes(tree)}
    replacement={net:serialize(tree,allmeta) for net,tree in merged.items()}
    header=re.compile(r'^Net\s+(\d+)\s+\(')
    candidate=output/'candidate.route'
    with (runs['timing']/'routed.route').open(newline='') as incoming,candidate.open('w',newline='') as outgoing:
        skip=False
        for line in incoming:
            match=header.match(line)
            if match:
                net=int(match[1]);skip=net in replacement
                if skip:outgoing.write(line+'\n'+replacement[net]+'\n')
            if not skip:outgoing.write(line)
    def untouched(path):
        digest=hashlib.sha256();skip=False
        for line in Path(path).open(newline=''):
            match=header.match(line)
            if match:skip=int(match[1]) in replacement
            if not skip:digest.update(line.encode())
        return digest.hexdigest()
    untouched_digest=untouched(runs['timing']/'routed.route')
    assert untouched(candidate)==untouched_digest
    recount=np.zeros(g.n,dtype=np.int32);seen=set()
    for record in stream_trace(candidate):
        if not record['trace']:continue
        recount[np.array(sorted({n.inode for n in record['trace']}),dtype=np.int64)]+=1
        if record['net'] in merged:
            assert from_trace(record['trace'],g.switches)==merged[record['net']]
            seen.add(record['net'])
    assert seen==set(merged) and np.array_equal(occupancy,recount)
    write(output/'transaction_trees.json',merged)
    write(output/'physical_sink_predictions.json',predictions)
    write(output/'cache_identity.json',cache.receipt)
    files=[Path(__file__).resolve(),D/'actual_route_tree_identity.py',D/'native_zero_rc_tree_delay_v1.py',
           D/'coordinated_repair_tree.py',selection/'completion.json',output/'registration.json',cache.directory/'completion.json']
    for label,state in states.items():
        files += [state/'completion.json',state/'endpoint_vector.json',runs[label]/'manifest.json',
                  runs[label]/'independent_audit.json',runs[label]/'routed.route']
    artifacts=['candidate.route','transaction_trees.json','physical_sink_predictions.json','cache_identity.json',
               'merge_checks.json','branches.json','capacity_check.json','base_tree_ids.json','side_tree_ids.json','timing_tree_ids.json']
    write(output/'completion.json',dict(passed=True,status='complete_structural_candidate_pending_native_FULL_STA',
        native_calls_new=0,state=str(target_state),base_state=str(base_state),side_state=str(side_state),
        affected_nets=sorted(merged),side_changed_nets=len(side_changed),timing_changed_nets=len(timing_changed),
        overlapping_nets=len(side_changed&timing_changed),candidate_route=str(candidate),candidate_sha256=sha(candidate),
        original_resources=axes['timing'],structural_resource_delta=delta,structural_full_route_resources=structural,
        predicted_sink_connections=len(predictions),predicted_changed_sink_connections=sum(r['delta_s']!=0 for r in predictions),
        all_fixed_terminals_preserved=True,all_changed_edges_actual=True,all_actual_RR_node_capacities_satisfied=True,
        all_other_net_bytes_exact=True,untouched_route_bytes_sha256=untouched_digest,
        native_FULL_STA_completed=False,committed_to_original_actor=False,
        complete_construction_seconds=time.monotonic()-started,
        source_sha256={str(f):sha(f) for f in dict.fromkeys(files)},
        artifact_sha256={n:sha(output/n) for n in artifacts},
        qualification='Development composition of one deterministic terminal-wire alternative and a completed actual timing branch from the same physical resource source. Compatible RR-parent/switch deltas are merged; conflicting changes, disconnected/dangling trees or capacity violations fail closed. Unchanged net bytes and fixed terminals remain exact; changed edge/switch and whole-node capacity checks pass. Structural resource counts and binary32 sink predictions are not new native legal/STA results or complete cost. Fresh native FULL/STA, independent full physical audit, actual terminal/scope/constraint identities, fixed original envelopes and predicted-delay validation remain required. Original actors untouched; no native search or creation cost borrowed.'))
    print(dict(status='candidate_pending_native',resources=structural,delta=delta,
               overlap_nets=len(side_changed&timing_changed),seconds=time.monotonic()-started),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['selection','target-state','full-graph-cache','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();build(a.selection,a.target_state,a.full_graph_cache,a.output)
