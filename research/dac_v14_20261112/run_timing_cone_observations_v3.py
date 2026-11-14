#!/usr/bin/env python3
"""Collect necessary full-precision timing-cone data and observer regressions."""
import os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from native_timing_echo import read_echo

b=D/'timing_cone_spmv_dev_03';start=time.monotonic()
resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));assert shutil.disk_usage(D).free>=80*1024**3
stage=D/'timing_cone_stage_03';binding=read(stage/'binding.json');assert sha(stage/'bin/vpr')==binding['binary_sha256']
def configuration(path):
    values={}
    for line in path.read_text().splitlines():
        if line.startswith(('#','//')) or ':' not in line or '=' not in line:continue
        key,rest=line.split(':',1);kind,value=rest.split('=',1)
        if kind in ['BOOL','STRING','UNINITIALIZED']:values[key]=value
    return values
old=configuration(D/'src/build/CMakeCache.txt');new=configuration(stage/'CMakeCache.txt')
allowed_extra={'CAPNP_LITE','EXTERNAL_CAPNP','PKG_CONFIG_ARGN','WITH_FIBERS','WITH_OPENSSL','WITH_ZLIB'}
differences={k:[old.get(k),new.get(k)] for k in set(old)|set(new) if old.get(k)!=new.get(k)}
assert all(k in allowed_extra and k not in old for k in differences),differences
assert all(new[k]=='serial' for k in ['VPR_EXECUTION_ENGINE','TATUM_EXECUTION_ENGINE'])
b.mkdir(exist_ok=False)
write(b/'build_configuration_comparison.json',dict(passed=True,differences=differences,qualification='Every common BOOL/STRING/UNINITIALIZED cache option matches baseline. Only extra unused third-party discovery keys are permitted; serial engines and native runtime guard remain mandatory.'))
plateau=D/'current_sta_policy_native_spmv_A0_near_physical_01/attempt_000/evaluation';joint=D/'current_sta_policy_native_spmv_A0_near_physical_01/attempt_003/evaluation'
roles=[('plateau_off',plateau,False,False),('plateau_on',plateau,True,True),('joint_on',joint,True,True)]
files=[Path(__file__).resolve(),D/'run_timing_cone_state_analysis_v2.py',D/'native_timing_echo.py',D/'test_native_timing_echo.py',D/'spmv_timing_cone_sensitivity_experiment_01.json',stage/'binding.json',D/'full_route_graph_cache_validation_01/completion.json']
for state in [plateau,joint]:files += [state/'completion.json',state/'endpoint_vector.json']
bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(status='registered_before_work',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],source_sha256=bindings,roles=[dict(role=r,source_state=str(s),echo=e,fresh_cached_physical_audit=f) for r,s,e,f in roles],question='Which native timing-cone changes mask6997p1 endpoint benefit? Validate default-off/on exact observer neutrality and inspect new graph/arrival/required data without rerouting.',native_analysis_calls_planned=3,route_search_calls=0,limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3)))
calls=[];results={}
for role,state,echo,fresh in roles:
 source=Path(read(state/'completion.json')['run']);out=b/role
 cmd=[sys.executable,str(D/'run_timing_cone_state_analysis_v2.py'),'--source',str(source),'--batch',str(out),'--full-graph-cache',str(D/'full_route_graph_cache_e695_01')]
 if echo:cmd+=['--timing-echo']
 if fresh:cmd+=['--fresh-physical-audit']
 t=time.monotonic();status='completed'
 with (b/(role+'.log')).open('w') as f:
  process=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=process.wait(timeout=1800);status='completed' if code==0 else 'failed'
  except subprocess.TimeoutExpired:
   status='timeout';os.killpg(process.pid,signal.SIGTERM)
   try:code=process.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);code=process.wait()
 calls.append(dict(role=role,command=cmd,status=status,returncode=code,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',calls)
 assert status=='completed',(role,status)
 c=read(out/'completion.json');assert c['passed'];assert read(out/'endpoint_vector.json')==read(state/'endpoint_vector.json'),'Observer changed exact endpoint vector or original trace'
 run=Path(c['run']);assert route_body(source/'routed.route')==route_body(run/'routed.route')
 graph_counts=None
 if echo:
  graph=read_echo(run/'timing_graph.full_precision.echo');graph_counts=dict(nodes=len(graph['nodes']),edges=len(graph['edges']),tags=len(graph['tags']),constraints_sha256=graph['constraints_text_sha256']);del graph
 results[role]=dict(passed=True,state=str(out),exact_original_vector_equal=True,route_unchanged=True,cpd_s=c['full_precision_cpd_s'],timing=c['timing'],graph_counts=graph_counts,echo_sha256=c['timing_echo_sha256'],fresh_cached_physical_audit=fresh)
 bindings[str(out/'completion.json')]=sha(out/'completion.json');bindings[str(out/'endpoint_vector.json')]=sha(out/'endpoint_vector.json')
 if echo:bindings[str(run/'timing_graph.full_precision.echo')]=sha(run/'timing_graph.full_precision.echo')
 write(b/'progress.json',results);print(role,results[role]['cpd_s'],graph_counts,flush=True)
assert results['plateau_on']['graph_counts']==results['joint_on']['graph_counts']
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=True,status='timing_cone_observations_terminal',roles=results,source_sha256=bindings,complete_orchestrator_seconds=time.monotonic()-start,native_analysis_calls=3,route_search_calls=0,qualification='New necessary timing-cone observations plus explicit off/on regression. No quality experiment rerouted. Counts alone are not graph identity; paired graph/delay/tag analysis follows. Fresh physical audits use validated graph metadata while native FULL/STA remains intact.'))
