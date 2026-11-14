#!/usr/bin/env python3
"""Sequential tiny forced-path plus native-restoration transaction after the live seed test."""
import collections
import os
import signal
import subprocess
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from export_policy_analysis_pool import process_identity
from resource_opportunity_census import stream_trace
from coordinated_repair_tree import from_trace
from actual_route_tree_identity import tree_identity

b=D/'fused_preset_tiny_01'
b.mkdir(exist_ok=False)
prior=D/'repair_seed_order_eltwise_01'
owner=read(prior/'registration.json')
fixture=D/'resource_domain_tiny_regression_02'
initial=fixture/'initial'
reference=D/'export_policy_tiny_01/pool/job_0007/native/candidate/routed.route'
reference_tree=next(from_trace(record['trace'],collections.defaultdict(float)) for record in stream_trace(reference) if record['net']==4)
path=[reference_tree['sinks'][2]]
while path[-1]!=reference_tree['root']:path.append(reference_tree['edges'][path[-1]][0])
path.reverse()
edges=[(u,v,reference_tree['edges'][v][1]) for u,v in zip(path,path[1:])]
request=b/'preset_pin2_then_query_pin1.txt'
request.write_text('1\n4 2 1 2\n1\n4 2 '+str(len(edges))+'\n'+''.join(f'{u} {v} {sw}\n' for u,v,sw in edges)+'1\n4 1 1\n')
files=[Path(__file__).resolve(),prior/'registration.json',D/'repair_seed_order_tiny_01/completion.json',reference,request,
       D/'export_policy_stage_01/binding.json',D/'repair_seed_order_stage_01/binding.json',initial/'routed.route']
bound={str(path):sha(path) for path in files}
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bound,prior_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),
    question='After pruning both sinks, does a forced legal pin2 path plus a subsequent native pin1 search preserve the forced branch, increment occupancy, pass actual candidate FULL/freshSTA, and recover the original state?',
    limits=dict(this_chain_native_processes=1,combined_VPR_maximum=3,child_seconds=60,memory_bytes=2*1024**3),
    qualification='Independent tiny fixed-path operator coverage after the seed-policy experiment has really ended. Uses old export backend and new native/RR-ID policies; no new full route, no large preset-timing quality claim.'))
write(b/'status.json',dict(status='waiting_for_seed_source_experiment_to_end'))
while True:
    actual=process_identity(owner['pid'])
    if not actual or actual['state']=='Z' or actual['start_ticks']!=owner['start_ticks']:break
    time.sleep(15)
assert (prior/'completion.json').exists() and read(prior/'completion.json')['passed']
assert all(sha(path)==digest for path,digest in bound.items())
started=time.monotonic()
root=D.parents[1]
arch=root/'results/architecture_flow_20261027/model_fixtures/n25_w100/hybrid_o/import_only.xml'
graph=arch.with_name('rr_graph.xml')
circuit=D/'reservation_workspace_02/vtr_flow/tasks/regression_tests/vtr_reg_strong/strong_pending_multisink/fixture.blif'
guard=root/'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard'
records=[]
def run(name,binary,policy,route,repair):
    directory=b/name;directory.mkdir()
    command=[str(binary),str(arch),str(circuit),'--analysis','--device','fixture','--route_chan_width','100',
        '--seed','11','--num_workers','1','--clock_modeling','ideal','--check_route','full','--verify_file_digests','off',
        '--verify_route_file_switch_id','on','--read_rr_graph',str(graph),'--net_file',str(initial/'packed.net'),
        '--place_file',str(initial/'placed.place'),'--route_file',str(route)]
    env={key:value for key,value in os.environ.items() if not key.startswith('VPR_') and key not in ['LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']}
    env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VPR_H3D_MODE='off',
        VPR_H3D_FINAL_STA_TRACE=str(directory/'native_sta_frontier.jsonl'),VPR_H3D_FINAL_TIMING_ECHO='')
    if repair:
        (directory/'candidate').mkdir();(directory/'candidate_restored').mkdir()
        env.update(VPR_JOINT_NATIVE_REQUEST=str(request),VPR_JOINT_NATIVE_OBJECTIVE='weighted_soft',
            VPR_JOINT_NATIVE_OUTPUT=str(directory/'joint_native.log'),VPR_JOINT_NATIVE_CANDIDATE_DIRECTORY=str(directory/'candidate'),
            VPR_JOINT_NATIVE_SEED_ORDER=policy)
    t=time.monotonic()
    with (directory/'stdout.log').open('w') as log:
        process=subprocess.Popen(['prlimit','--as='+str(2*1024**3),'--core=0:0','--',str(guard),*command],cwd=directory,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write(b/'status.json',dict(status='running',case=name,pid=process.pid,start_ticks=process_identity(process.pid)['start_ticks']))
        try:code=process.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait();raise
    records.append(dict(case=name,returncode=code,seconds=time.monotonic()-t,binary_sha256=sha(binary),actual_command=command,
        environment={key:value for key,value in env.items() if key.startswith('VPR_')}))
    write(b/'processes.json',records)
    assert code==0,(name,code)
    return directory

original=tree_identity(initial/'routed.route')
for name,stage,policy in [('export_default','export_policy_stage_01','native'),
    ('seed_native','repair_seed_order_stage_01','native'),('seed_rr_id','repair_seed_order_stage_01','rr_id')]:
    binary=D/stage/'bin/vpr'
    actual=run(name,binary,policy,initial/'routed.route',True)
    assert (actual/'joint_native.log').read_text().splitlines()[-1].startswith('COMPLETE 1 1 1 ')
    assert (actual/'joint_native.log').read_text().splitlines()[-1].endswith('occupancy_restored')
    candidate=actual/'candidate'
    assert (candidate/'native_state_gate.txt').read_text()=='candidate FULL fresh_STA actual_installed_trees\n'
    trees=tree_identity(candidate/'routed.route')
    assert trees.keys()==original.keys() and all(trees[net]==original[net] for net in trees if net!=4)
    tree=next(from_trace(record['trace'],collections.defaultdict(float)) for record in stream_trace(candidate/'routed.route') if record['net']==4)
    assert tree['sinks'].keys()=={1,2}
    for u,v,sw in edges:assert tree['edges'][v][:2]==(u,sw),'Forced path modified by subsequent native search'
    for suffix in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:
        assert sha(actual/suffix)==sha(actual/'candidate_restored'/suffix)
    independent=run(name+'_independent_LOAD',binary,policy,candidate/'routed.route',False)
    for suffix in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:
        assert sha(candidate/suffix)==sha(independent/suffix)
assert all(sha(path)==digest for path,digest in bound.items())
write(b/'completion.json',dict(passed=True,forced_pin2_path_preserved_after_native_pin1_restoration=True,
    all_other_nets_physically_unchanged=True,native_FULL_fresh_STA_and_source_recovery_exact=True,
    same_binary_independent_candidate_LOAD_exports_exact=True,old_export_and_new_seed_policy_backends=True,
    native_processes=len(records),complete_regression_seconds=time.monotonic()-started,
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),b/'registration.json',b/'processes.json']},
    qualification='Tiny actual preset plus subsequent native-query operator validation only. Original source, forced branch, other branches/nets, actual FULL/STA, per-transaction occupancy restoration and independent candidate LOAD pass. No large CPD-changing forced-path quality or whole-configuration performance claim.'))
print(dict(passed=True,native_processes=len(records)),flush=True)
