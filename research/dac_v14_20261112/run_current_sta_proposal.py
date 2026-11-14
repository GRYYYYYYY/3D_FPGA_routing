#!/usr/bin/env python3
"""Native FULL/STA evaluation of one ranked current-state repair proposal.

The accepted state is a pointer to an immutable run; rejection leaves it pointing
to the input. Completed native processes are never retried by this runner.
"""
import argparse
import collections
import fcntl
import math
import os
from pathlib import Path
import shutil
import sys
from retained_prefix_workflow import D, read, write, sha, require_formal_terminal
ROOT=D.parents[1]
OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from check_route import read_trace
from verify_path_witnesses_v2 import graph_records, f32


def compare_physical(source, proposal, net, pin, graph):
    switches={}
    for section,e in graph_records(graph):
        if section!='switches':break
        t=e.find('timing');switches[int(e.attrib['id'])]=0. if t is None else f32(t.attrib.get('Tdel',0))
    assert switches
    original=read_trace(source);repaired=read_trace(proposal)
    assert original.keys()==repaired.keys()
    assert all(original[n]==repaired[n] for n in original if n!=net)
    def sink_delays(traces):
        result={}
        for n,info in traces.items():
            trace=info['trace'];children=collections.defaultdict(dict)
            for a,b in zip(trace,trace[1:]):
                if a.switch!=-1:children[a.inode][b.inode]=a.switch
            values={trace[0].inode:0.};stack=[trace[0].inode]
            while stack:
                u=stack.pop()
                for v,s in children[u].items():
                    assert v not in values;values[v]=values[u]+switches[s];stack.append(v)
            for node in trace:
                if node.kind=='SINK':result[n,node.inode,node.pin]=values[node.inode]
        return result
    before,after=sink_delays(original),sink_delays(repaired)
    assert before.keys()==after.keys()
    changed=[dict(net=k[0],sink=k[1],pin=k[2],before_ns=before[k]*1e9,after_ns=after[k]*1e9)
        for k in before if not math.isclose(before[k],after[k],abs_tol=1e-24,rel_tol=1e-12)]
    assert len(changed)==1 and changed[0]['net']==net and changed[0]['pin']==pin
    assert changed[0]['after_ns']<changed[0]['before_ns']
    return dict(passed=True,sink_connections=len(before),changed=changed,other_net_traces_exact=True,
        scope='All sink delays are independently accumulated from actual route switch IDs on the previously verified zero-RC graph. Final timing is separately recomputed by native STA.')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--queries',type=Path,required=True)
    parser.add_argument('--batch',type=Path,required=True)
    parser.add_argument('--proposal-index',type=int,default=0)
    args=parser.parse_args();require_formal_terminal()
    lock=(D/'critical_scope_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    q=args.queries.resolve();a=read(q/'analysis.json');assert a['passed']
    assert all(sha(p)==h for p,h in a['source_sha256'].items())
    ex=read(q/'execution.json');assert all(sha(p)==h for p,h in ex['source_sha256'].items())
    assert all(sha(q/p)==h for p,h in ex['output_sha256'].items())
    proposals=sorted([r for r in a['results'] if 'candidate_route' in r],key=lambda r:(-r['improvement_ns'],r['net'],r['pin']))
    assert 0<=args.proposal_index<len(proposals)
    selected=proposals[args.proposal_index];candidate=Path(selected['candidate_route'])
    assert sha(candidate)==selected['candidate_route_sha256']
    source=Path(read(q/'execution_registration.json')['input_run']);pm=read(source/'manifest.json')
    assert pm['status']=='completed' and pm['metrics']['native_full_check_passed']
    assert read(source/'independent_audit.json')['audit']['passed']
    graph=Path(pm['command'][pm['command'].index('--read_rr_graph')+1])
    assert sha(graph)==pm['shared_inputs'][str(graph)]['sha256']
    b=args.batch.resolve();b.mkdir(exist_ok=False);(b/'bin').mkdir()
    shutil.copy2(pm['command'][0],b/'bin/vpr')
    shutil.copy2(OLD/'runtime_dependency_binding.json',b/'runtime_dependency_binding.json')
    files=[Path(__file__),D/'current_sta_repair_experiment_01.json',q/'analysis.json',q/'execution.json',q/'execution_registration.json',
        candidate,source/'manifest.json',source/'routed.route',source/'independent_audit.json',source/'packed.net',source/'placed.place',graph,b/'bin/vpr']
    bindings={str(p):sha(p) for p in files}
    reg=dict(status='registered_before_native_analysis',input_run=str(source),query_batch=str(q),
        ranked_candidates=[dict(net=r['net'],pin=r['pin'],improvement_ns=r['improvement_ns']) for r in proposals],
        selected_index=args.proposal_index,selected=selected,source_sha256=bindings,pid=os.getpid(),
        start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
        limits=dict(timeout_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
        native_analysis_calls_planned=1,route_search_calls=0,
        acceptance='Native FULL, independent physical/capacity audit, only selected sink delay changes, strictly lower native reported CPD.',
        control_reuse='Reuse completed input state STA/route at exact immutable hashes. This is a quality intervention, not a paired formal timing run.')
    write(b/'registration.json',reg);io.BASE=b;io.ADDRESS_SPACE_BYTES=reg['limits']['memory_bytes']
    for p,h in bindings.items():io.frozen_hash(p,h)
    assert shutil.disk_usage(D).free>=reg['limits']['disk_reserve_bytes']
    rd=b/'runs/eltwise_layer_R';rd.mkdir(parents=True)
    for name in ['packed.net','placed.place']:shutil.copy2(source/name,rd/name)
    shutil.copy2(candidate,rd/'routed.route')
    before={name:sha(rd/name) for name in ['packed.net','placed.place','routed.route']}
    write(rd/'pair_check.json',dict(passed=True,checks={name:sha(rd/name)==sha(source/name) for name in ['packed.net','placed.place']},
        scope='Same packing/placement and graph; registered isolated target route change.'))
    physical=compare_physical(source/'routed.route',rd/'routed.route',selected['net'],selected['pin'],graph)
    write(b/'physical_change_audit.json',physical)
    cmd=list(pm['command']);cmd[0]=str(b/'bin/vpr')
    if '--route' in cmd:cmd.remove('--route')
    assert '--analysis' in cmd
    cmd[cmd.index('--timing_report_npaths')+1]='10'
    if '--verify_route_file_switch_id' not in cmd:cmd.extend(['--verify_route_file_switch_id','on'])
    else:cmd[cmd.index('--verify_route_file_switch_id')+1]='on'
    for opt,name in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/name)
    result=io.run(rd.name,cmd,environment={'VPR_H3D_MODE':'off'},timeout=1800,
        frozen=[cmd[0],cmd[1],cmd[2],graph,b/'registration.json'],private_inputs=[rd/name for name in before],
        tags=dict(circuit='eltwise_layer',arm='R',phase='current_STA_repair_native_analysis',route_search_calls=0,target_net=selected['net'],target_pin=selected['pin']))
    gate=dict(process_completed=result['status']=='completed',native_FULL=result['metrics'].get('native_full_check_passed',False),
        route_load_observed='Finished loading route file' in (rd/'stdout.log').read_text(),
        inputs_unchanged=all(sha(rd/name)==h for name,h in before.items()),cpd_present=result['metrics'].get('critical_path_ns') is not None)
    write(rd/'analysis_gate.json',dict(passed=all(gate.values()),checks=gate))
    # Bind the graph actually consumed, never the older fixture's graph path.
    study.BASE=b;audit=study.audit_batch({'fixture':{'original_graph':str(graph)}},[result],b/'independent_native_analysis_audit.json')
    io.seal_inputs(b/'input_seal.json')
    valid=all(gate.values()) and audit['passed']
    cpd=result['metrics'].get('critical_path_ns');old=pm['metrics']['critical_path_ns']
    accepted=valid and cpd<old
    write(b/'completion.json',dict(status='native_analysis_terminal',passed=valid,accepted=accepted,
        accepted_run=str(rd if accepted else source),input_run=str(source),candidate_run=str(rd),
        selected=dict(net=selected['net'],pin=selected['pin']),before_cpd_ns=old,after_cpd_ns=cpd,
        process_status=result['status'],native_analysis_calls=1,route_search_calls=0,
        process_seconds=result['wall_seconds'],gate=gate,physical_change=physical,
        interpretation='Strict CPD acceptance for this proposal only; no robust cross-circuit method promotion or formal runtime comparison.'))
    print(dict(valid=valid,accepted=accepted,cpd_before=old,cpd_after=cpd,net=selected['net'],pin=selected['pin']),flush=True)


if __name__=='__main__':main()
