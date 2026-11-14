#!/usr/bin/env python3
"""Query generic current-STA targets with the validated fixed-tree capacity adapter."""
import argparse
from select_current_critical_targets import select
import array
import collections
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha,require_formal_terminal
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace
from verify_path_witnesses_v2 import graph_records,f32

require_formal_terminal();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);parser.add_argument('--batch',type=Path,required=True)
args=parser.parse_args();current=args.run.resolve();b=args.batch.resolve();b.mkdir(exist_ok=False);(b/'src').mkdir()
reg=read(D/'current_sta_repair_experiment_01.json')
assert all(sha(p)==h for p,h in reg['source_sha256'].items())
assert shutil.disk_usage(D).free>=80*1024**3
op=select(current);assert not op['unresolved']
current_targets=op['targets'];fixed=read(D/'critical_capacity_potential_01/cases.json')
op['targets']=[{k:c[k] for k in ['net','pin','sink']} for c in fixed]
op['current_path_targets_not_used']=current_targets
op['selection_scope']='Frozen initial worst-path identities from prior currentTf diagnostic; query current state with identical capacity/tree model.'
op['frozen_target_source_sha256']=sha(D/'critical_capacity_potential_01/cases.json')
write(b/'selection.json',op)
prior=read(D/'critical_capacity_potential_01/execution.json')
assert read(D/'critical_capacity_potential_01/unit_validation.json')['passed']
for rel in ['critical_capacity_driver']:
    assert sha(D/'critical_capacity_potential_01'/rel)==prior['output_sha256'][rel]
manifest=read(current/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
assert sha(graph)==manifest['shared_inputs'][str(graph)]['sha256']
binary=D/'residual_query_offline_01/graph.bin';gb=read(binary.with_name('graph_binding.json'));assert sha(binary)==gb['binary_graph_sha256']
for name in ['critical_capacity_adapter.h','critical_capacity_driver.cpp','test_critical_capacity.cpp']:
    shutil.copy2(D/name,b/'src'/name)
shutil.copy2(D/'tree_aware_candidate_offline_01/src/h3d_candidate_path.h',b/'src/h3d_candidate_path.h')
inputs=[Path(__file__),D/'current_sta_repair_experiment_01.json',D/'select_current_critical_targets.py',D/'critical_capacity_potential_01/cases.json',b/'selection.json',D/'critical_capacity_potential_01/unit_validation.json',
        current/'manifest.json',current/'routed.route',current/'independent_audit.json',binary,graph,*sorted((b/'src').glob('*'))]
bindings={str(p):sha(p) for p in inputs}
write(b/'execution_registration.json',dict(status='registered_before_input_preparation',pid=os.getpid(),
    start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],source_sha256=bindings,
    native_route_calls=0,limits=reg['per_process_limits'],input_run=str(current),query_modes=[1],previous_goal_turn='progress'))
started=time.monotonic()
# Reuse adapter correctness evidence by exact source identity. The small driver
# interface adds explicit capacity-only selection; it does not alter the solver.
for name in ['critical_capacity_adapter.h','h3d_candidate_path.h']:
    assert sha(b/'src'/name)==sha(D/'critical_capacity_potential_01/src'/name)
driver=b/'src/critical_capacity_driver.cpp'
t=driver.read_text().replace('assert(argc==3);','assert(argc==3 || (argc==4 && std::string(argv[3])=="capacity"));')
t=t.replace('for(int mode=0;mode<2;++mode)', 'for(int mode=(argc==4?1:0);mode<2;++mode)');driver.write_text(t)
# Bind the actual compiled driver after this declared CLI-only transformation.
bindings[str(driver)]=sha(driver)
registration=read(b/'execution_registration.json');registration['source_sha256']=bindings
write(b/'execution_registration.json',registration)
with (b/'critical_capacity_driver_compile.log').open('w') as out:
    subprocess.run(['g++','-std=c++20','-O2','-Wall','-Wextra','-D_GLIBCXX_ASSERTIONS','-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(b/'src'),str(driver),'-o',str(b/'critical_capacity_driver')],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=120)
write(b/'unit_validation.json',dict(passed=True,reused=True,source_validation=str(D/'critical_capacity_potential_01/unit_validation.json'),source_validation_sha256=sha(D/'critical_capacity_potential_01/unit_validation.json'),scope='Unchanged adapter/core; original2000 independent Floyd checks reused. Driver changes only optional capacity-only mode.'))
capacities=array.array('I');kinds=[];delays={}
assert sys.byteorder=='little' and capacities.itemsize==4
for section,e in graph_records(graph):
    a=e.attrib
    if section=='switches':
        timing=e.find('timing');v={} if timing is None else timing.attrib
        assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal'])
        delays[int(a['id'])]=f32(v.get('Tdel',0))
    elif section=='rr_nodes':
        assert int(a['id'])==len(capacities)
        capacities.append(int(a['capacity']));kinds.append(a['type'])
        timing=e.find('timing');v={} if timing is None else timing.attrib
        assert all(f32(v.get(k,0))==0 for k in ['R','C'])
    elif section=='rr_edges':break
assert len(capacities)==gb['nodes']
with (b/'capacities.bin').open('wb') as f:capacities.tofile(f)
traces=read_trace(current/'routed.route');owners=collections.defaultdict(list)
for net,info in traces.items():
    for node in {n.inode for n in info['trace']}:owners[node].append(net)
write(b/'occupancy_owners.json',{str(k):v for k,v in owners.items()})
cases=[]
for connection in op['targets']:
    net,pin,sink=connection['net'],connection['pin'],connection['sink'];trace=traces[net]['trace']
    nodes={n.inode:n for n in trace};parents={};switches={};children=collections.defaultdict(set)
    for a,z in zip(trace,trace[1:]):
        if a.switch==-1:continue
        assert z.inode not in parents or parents[z.inode]==a.inode
        parents[z.inode]=a.inode;switches[a.inode,z.inode]=a.switch;children[a.inode].add(z.inode)
    removed=set();node=sink
    assert not children[sink]
    while node in parents:
        if children[node]-removed:break
        if node!=sink and kinds[node]=='SINK':break
        removed.add(node);node=parents[node]
    retained=set(nodes)-removed;root=trace[0].inode
    prefixes={root:0.};stack=[root]
    while stack:
        parent=stack.pop()
        for child in children[parent]:
            assert child not in prefixes
            prefixes[child]=prefixes[parent]+delays[switches[parent,child]];stack.append(child)
    assert prefixes.keys()==nodes.keys()
    assert any(n.inode==sink and n.pin==pin and n.kind=='SINK' for n in trace)
    anchors={node:prefixes[node] for node in retained if kinds[node] not in ['SINK','IPIN']}
    blocked={node for node,capacity in enumerate(capacities) if len(owners.get(node,[]))-int(node in nodes)>=capacity}
    assert not (retained&blocked)
    original=[];node=sink
    while node in parents:original.append(node);node=parents[node]
    original.append(node);original.reverse()
    at=max(i for i,node in enumerate(original) if node in retained)
    assert original[at] in anchors and not set(original[at:])&blocked
    other_sinks={n.inode for n in trace if n.kind=='SINK' and n.pin is not None and n.pin!=pin}
    assert other_sinks<=retained and sink not in other_sinks
    cases.append(dict(net=net,pin=pin,sink=sink,root=root,original_nodes=sorted(nodes),retained=sorted(retained),
        removed=sorted(removed),anchors={str(k):v for k,v in anchors.items()},blocked=sorted(blocked),
        current_physical_seconds=prefixes[sink],original_path=original,other_sinks=sorted(other_sinks),
        tree_edges=[[u,v,sw,delays[sw]] for (u,v),sw in switches.items()],
        anchor_eligibility='Retained SOURCE/OPIN/channel graph branch points; excludes IPIN/SINK. Not historical native re_expand or actual queued-seed identity.',
        domain='Full-device graph; no single-cross restriction.'))
write(b/'cases.json',cases)
with (b/'cases.txt').open('w') as f:
    f.write(str(len(cases))+'\n')
    for c in cases:
        f.write(' '.join(map(str,[c['net'],c['pin'],c['sink'],len(c['retained']),len(c['anchors']),len(c['blocked'])]))+'\n')
        f.write(' '.join(map(str,c['retained']))+'\n')
        for node,delay in c['anchors'].items():f.write(f'{node} {delay:.17g}\n')
        f.write(' '.join(map(str,c['blocked']))+'\n')
begin=time.monotonic()
with (b/'query_stdout.log').open('w') as out,(b/'query_stderr.log').open('w') as err:
    subprocess.run([str(b/'critical_capacity_driver'),str(binary),str(b/'cases.txt'),'capacity'],stdout=out,stderr=err,check=True,timeout=900)
elapsed=time.monotonic()-begin
assert all(sha(p)==h for p,h in bindings.items())
write(b/'execution.json',dict(status='offline_terminal_pending_physical_audit',source_sha256=bindings,
    output_sha256={name:sha(b/name) for name in ['capacities.bin','occupancy_owners.json','cases.json','cases.txt',
        'unit_validation.json','query_stdout.log','query_stderr.log','critical_capacity_driver']},
    native_route_calls=0,elapsed_seconds=time.monotonic()-started,query_process_seconds=elapsed))
print(dict(targets=len(cases),query_process_seconds=elapsed,status='capacity_queries_terminal_physical_audit_pending'),flush=True)
