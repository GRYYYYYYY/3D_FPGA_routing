#!/usr/bin/env python3
"""Reuse two successful observations; parse actual format and collect only joint echo."""
import os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from native_timing_echo_v2 import read_echo

b=D/'timing_cone_spmv_dev_04';b.mkdir(exist_ok=False);start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));assert shutil.disk_usage(D).free>=80*1024**3
old=D/'timing_cone_spmv_dev_03';assert read(old/'build_configuration_comparison.json')['passed']
stage=D/'timing_cone_stage_03';assert sha(stage/'bin/vpr')==read(stage/'binding.json')['binary_sha256']
plateau=D/'current_sta_policy_native_spmv_A0_near_physical_01/attempt_000/evaluation';joint=D/'current_sta_policy_native_spmv_A0_near_physical_01/attempt_003/evaluation'
paths=[Path(__file__).resolve(),D/'native_timing_echo_v2.py',D/'test_native_timing_echo_v2.py',D/'run_timing_cone_state_analysis_v2.py',stage/'binding.json',old/'parser_failure_diagnosis.json',old/'build_configuration_comparison.json',old/'plateau_off/completion.json',old/'plateau_on/completion.json',plateau/'endpoint_vector.json',joint/'endpoint_vector.json']
bindings={str(p):sha(p) for p in paths}
write(b/'registration.json',dict(status='registered_before_recovery',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],source_sha256=bindings,question='Recover actual echo parsing without repeating successful default-off/on observations; collect missing joint candidate echo.',new_native_analysis_calls_planned=1,reused_native_observations=2,route_search_calls=0,limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3)))
results={};costs=[]
for role,state,echo in [('plateau_off',plateau,False),('plateau_on',plateau,True),('joint_on',joint,True)]:
    source=Path(read(state/'completion.json')['run']);reused=role!='joint_on';out=old/role if reused else b/role
    if not reused:
        cmd=[sys.executable,str(D/'run_timing_cone_state_analysis_v2.py'),'--source',str(source),'--batch',str(out),'--full-graph-cache',str(D/'full_route_graph_cache_e695_01'),'--timing-echo','--fresh-physical-audit'];t=time.monotonic();status='completed'
        with (b/(role+'.log')).open('w') as f:
            process=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            try:code=process.wait(timeout=1800);status='completed' if code==0 else 'failed'
            except subprocess.TimeoutExpired:
                status='timeout';os.killpg(process.pid,signal.SIGTERM)
                try:code=process.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);code=process.wait()
        costs.append(dict(role=role,command=cmd,status=status,returncode=code,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs);assert status=='completed'
    c=read(out/'completion.json');assert c['passed'];assert read(out/'endpoint_vector.json')==read(state/'endpoint_vector.json')
    run=Path(c['run']);assert route_body(run/'routed.route')==route_body(source/'routed.route')
    count=None;parse_seconds=0
    if echo:
        t=time.monotonic();g=read_echo(run/'timing_graph.full_precision.echo');parse_seconds=time.monotonic()-t
        count=dict(nodes=len(g['nodes']),edges=len(g['edges']),tags=len(g['tags']),constraints_sha256=g['constraints_text_sha256']);del g
        bindings[str(run/'timing_graph.full_precision.echo')]=sha(run/'timing_graph.full_precision.echo')
    results[role]=dict(passed=True,state=str(out),reused_native_observation=reused,exact_original_vector_equal=True,route_unchanged=True,cpd_s=c['full_precision_cpd_s'],timing=c['timing'],graph_counts=count,parse_seconds=parse_seconds,echo_sha256=c['timing_echo_sha256'])
    for p in [out/'completion.json',out/'endpoint_vector.json',run/'native_sta_frontier.jsonl']:bindings[str(p)]=sha(p)
    write(b/'progress.json',results);print(role, count,flush=True)
assert results['plateau_on']['graph_counts']==results['joint_on']['graph_counts']
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=True,status='timing_cone_observations_terminal',roles=results,source_sha256=bindings,complete_orchestrator_seconds=time.monotonic()-start,new_native_analysis_calls=1,reused_native_observations=2,total_successful_native_observations=3,prior_failed_native_observations=1,route_search_calls=0,qualification='Three successful new necessary observations across the recovery chain; successful off/on native calls never repeated. One earlier parallel-build observation terminated by threadguard and is excluded from equivalence. Existing original repair states remain immutable.'))
