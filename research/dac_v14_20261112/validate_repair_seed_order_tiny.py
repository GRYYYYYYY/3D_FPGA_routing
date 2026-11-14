#!/usr/bin/env python3
"""Real serial native regression for seed policies, actual FULLSTA and error restoration."""
import collections
import math
import os
import signal
import subprocess
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from actual_route_tree_identity import tree_identity

b=D/'repair_seed_order_tiny_01'
b.mkdir(exist_ok=False)
started=time.monotonic()
fixture=D/'resource_domain_tiny_regression_02'
initial=fixture/'initial'
root=D.parents[1]
arch=root/'results/architecture_flow_20261027/model_fixtures/n25_w100/hybrid_o/import_only.xml'
graph=arch.with_name('rr_graph.xml')
circuit=D/'reservation_workspace_02/vtr_flow/tasks/regression_tests/vtr_reg_strong/strong_pending_multisink/fixture.blif'
guard=root/'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard'
binary=D/'repair_seed_order_stage_01/bin/vpr'
binding=read(D/'repair_seed_order_stage_01/binding.json')
assert sha(binary)==binding['binary_sha256']
files=[Path(__file__).resolve(),D/'repair_seed_order_stage_01/binding.json',D/'actual_route_tree_identity.py',
       fixture/'completion.json',fixture/'partial.txt',fixture/'whole.txt',fixture/'domain.txt',initial/'routed.route',
       D/'repair_seed_order_workspace_01/vtr_flow/tasks/regression_tests/vtr_reg_strong/strong_repair_seed_order/run.py']
bound={str(path):sha(path) for path in files}
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
    source_sha256=bound,question='Do explicit serial seed policies preserve seed membership/native costs, actual FULL/freshSTA and rollback, with a bit-exact native default and clear invalid-policy/path errors?',
    limits=dict(memory_bytes=2*1024**3,child_seconds=60,this_chain_native_VPR=1,combined_with_BNN_pool_maximum=3),
    qualification='Strong integration regression on sealed small two-layer fixture, no new pack/place/route. Each subprocess is standalone: no extra loaded VPR parent alongside the running BNN actor.'))
records={}
def run(name,policy=None,request=None,feedback=False,route=None,missing_output_dirs=False,expected_ok=True):
    out=b/name
    out.mkdir()
    route=initial/'routed.route' if route is None else Path(route)
    command=[str(binary),str(arch),str(circuit),'--analysis','--device','fixture','--route_chan_width','100',
        '--seed','11','--num_workers','1','--clock_modeling','ideal','--check_route','full',
        '--verify_file_digests','off','--verify_route_file_switch_id','on','--read_rr_graph',str(graph),
        '--net_file',str(initial/'packed.net'),'--place_file',str(initial/'placed.place'),'--route_file',str(route)]
    env={key:value for key,value in os.environ.items() if not key.startswith('VPR_') and key not in ['LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']}
    env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VPR_H3D_MODE='off',
        VPR_H3D_FINAL_STA_TRACE=str(out/'native_sta_frontier.jsonl'),VPR_H3D_FINAL_TIMING_ECHO='')
    if request:
        if not missing_output_dirs:
            (out/'candidate').mkdir();(out/'candidate_restored').mkdir()
        env.update(VPR_JOINT_NATIVE_REQUEST=str(request),VPR_JOINT_NATIVE_OBJECTIVE='weighted_soft',
            VPR_JOINT_NATIVE_OUTPUT=str(out/'joint_native.log'),VPR_JOINT_NATIVE_REUSE_CROSSINGS=str(fixture/'domain.txt'),
            VPR_JOINT_NATIVE_VERTICAL_DOMAIN_TRACE=str(out/'vertical_domain.log'),
            VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE='1' if feedback else '',
            VPR_JOINT_NATIVE_CANDIDATE_DIRECTORY=str(out/'candidate'),VPR_JOINT_NATIVE_SEARCH_TRACE=str(out/'search_cost.log'),
            VPR_JOINT_NATIVE_SEED_TRACE=str(out/'actual_seed.log'))
        if policy is not None:env['VPR_JOINT_NATIVE_SEED_ORDER']=policy
    t=time.monotonic()
    with (out/'stdout.log').open('w') as log:
        process=subprocess.Popen(['prlimit','--as='+str(2*1024**3),'--core=0:0','--',str(guard),*command],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:code=process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait();raise
    record=dict(directory=str(out),returncode=code,seconds=time.monotonic()-t,policy=policy,expected_success=expected_ok,
        actual_command=command,private_environment={key:value for key,value in env.items() if key.startswith('VPR_')})
    records[name]=record
    write(b/'progress.json',records)
    if expected_ok:assert code==0,(name,code)
    else:assert code!=0 and code!=-signal.SIGSEGV,(name,code)
    return out

def normalized(path):
    rows=[]
    for line in Path(path).read_text().splitlines():
        row=line.split()
        if row[0]=='QUERY':row=row[:-1]
        if row[0]=='COMPLETE':row=row[:4]+row[5:]
        rows.append(row)
    return rows

def check_transaction(directory,success):
    rows=(directory/'joint_native.log').read_text().splitlines()
    assert rows[-1].split()[1]==str(int(success)) and rows[-1].endswith('occupancy_restored')
    restored=directory/'candidate_restored'
    assert (restored/'native_state_gate.txt').read_text()=='restored_source FULL fresh_STA actual_installed_trees\n'
    for name in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:
        assert sha(directory/name)==sha(restored/name)
    if success:assert (directory/'candidate/native_state_gate.txt').read_text()=='candidate FULL fresh_STA actual_installed_trees\n'
    else:assert not(directory/'candidate/native_state_gate.txt').exists()
    for line in (directory/'search_cost.log').read_text().splitlines():
        row=line.split();assert row[0]=='COST' and len(row)==12
        if row[6]=='1':assert all(math.isfinite(float(row[i])) for i in [8,9])
        assert float(row[11])==0.,'These registered repair queries use native Dijkstra/NoOpLookahead, not A*'

variants={}
for policy in [None,'native','rr_id','delay_rr_id']:
    name='unset' if policy is None else policy
    variants[name]=run(name,policy,fixture/'partial.txt')
    check_transaction(variants[name],True)
old=D/'export_policy_tiny_01/pool/job_0003/native'
assert normalized(variants['unset']/'joint_native.log')==normalized(old/'joint_native.log')
assert normalized(variants['native']/'joint_native.log')==normalized(variants['unset']/'joint_native.log')
assert tree_identity(variants['unset']/'candidate/routed.route')==tree_identity(old/'candidate/routed.route')
seed_maps={}
for name,path in variants.items():
    groups=collections.defaultdict(list)
    for line in (path/'actual_seed.log').read_text().splitlines():
        row=line.split();assert row[0]=='SEED' and len(row)==9
        groups[(int(row[1]),int(row[2]),float(row[4]))].append((int(row[5]),float(row[6]),float(row[7]),float(row[8])))
    seed_maps[name]=groups
    if name in ['rr_id','delay_rr_id']:
        for values in groups.values():
            key=(lambda row:row[0]) if name=='rr_id' else (lambda row:(row[1],row[0]))
            assert values==sorted(values,key=key),name
for name in ['native','rr_id','delay_rr_id']:
    assert seed_maps[name].keys()==seed_maps['unset'].keys()
    assert all(sorted(seed_maps[name][key])==sorted(seed_maps['unset'][key]) for key in seed_maps['unset'])
for name in ['native','rr_id','delay_rr_id']:
    candidate=variants[name]/'candidate'
    independent=run(name+'_independent_candidate_LOAD',route=candidate/'routed.route')
    for suffix in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:
        assert sha(candidate/suffix)==sha(independent/suffix)
failed=run('infeasible','rr_id',fixture/'whole.txt')
check_transaction(failed,False)
feedback=run('feedback','rr_id',fixture/'whole.txt',feedback=True)
check_transaction(feedback,True)
bad=run('invalid_policy','invalid',fixture/'partial.txt',expected_ok=False)
assert 'Invalid repair seed order' in (bad/'stdout.log').read_text()
missing=run('missing_candidate_directory','native',fixture/'partial.txt',missing_output_dirs=True,expected_ok=False)
assert 'Actual candidate output directory must already exist' in (missing/'stdout.log').read_text()
assert (missing/'joint_native.log').read_text().splitlines()[-1].endswith('occupancy_restored')
following=run('following_default',None,fixture/'partial.txt')
check_transaction(following,True)
assert normalized(following/'joint_native.log')==normalized(variants['unset']/'joint_native.log')
assert all(sha(path)==digest for path,digest in bound.items())
write(b/'completion.json',dict(passed=True,default_native_transaction_and_actual_tree_exact=True,
    explicit_policy_actual_seed_sort_and_membership_valid=True,independent_candidate_LOAD_full_precision_exact=True,
    source_recovery_exact=True,infeasible_and_failure_release_valid=True,invalid_policy_rejected=True,
    missing_output_directory_clear_error_with_occupancy_restored=True,following_default_exact=True,
    native_processes=len(records),complete_regression_seconds=time.monotonic()-started,
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),b/'registration.json',b/'progress.json']},
    qualification='Real standalone strong regression only, not quality improvement or global serialization-invariance proof. Stable policies preserve seed content/primary seed labels and actual native FULL/STA. The isolated real eltwise old/native sources remain a separate mechanism test. Every native process and diagnostic failure is retained.'))
print(dict(passed=True,native_processes=len(records)),flush=True)
