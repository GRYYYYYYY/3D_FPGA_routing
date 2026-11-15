"""Actual relocated timing feedback and worker boundary checks, without native reruns."""
import ast,copy,os,shutil,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
report=D/'standalone_unified_method_validation_01';report.mkdir(exist_ok=False)
w=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/unified_method_01');w.mkdir(exist_ok=False)
package=D/'standalone_unified_method_dev_02';runtime=w/'runtime';shutil.copytree(package,runtime,ignore=shutil.ignore_patterns('__pycache__'))
previous=w.parent/'resource_controller_01/runtime_v3'
for name in ['numpy','numpy.libs','lxml','lxml.libs']:
    if (previous/name).exists():shutil.copytree(previous/name,runtime/name,ignore=shutil.ignore_patterns('__pycache__'))
mapping={};originals={}
def exact(old,new):
    old=Path(old).resolve();new.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old,new);h=sha(old);assert sha(new)==h;mapping[str(old)]=str(new);originals[str(old)]=h
def relocate(v):
    if isinstance(v,str):return mapping.get(v,v)
    if isinstance(v,list):return [relocate(x) for x in v]
    if isinstance(v,dict):return {relocate(k):relocate(x) for k,x in v.items()}
    return v
origin=D/'serial_seed_standalone_validation_01/candidate_evaluation';source=Path(read(origin/'completion.json')['run']);m=read(source/'manifest.json');command=m['command']
paths=dict(architecture=Path(command[1]),circuit=Path(command[2]),graph=Path(command[command.index('--read_rr_graph')+1]),packed=source/'packed.net',placement=source/'placed.place')
for key,old in paths.items():exact(old,w/'inputs'/(key+old.suffix));paths[key]=Path(mapping[str(old)])
phases={}
for key,stage in [('resource','native_resource_census_stage_01'),('owner','crossing_source_stage_01'),('timing_repair','resource_domain_stage_01'),('timing_observer','timing_cone_stage_03')]:
    f=w/'inputs'/('binary_'+key);exact(D/stage/'bin/vpr',f);phases[key]=dict(path=str(f),sha256=sha(f))
engines={}
for key,stage in [('capacity','current_sta_queries_01'),('relaxed','current_sta_relaxed_01')]:
    f=w/'inputs'/key/'critical_capacity_driver';exact(D/stage/'critical_capacity_driver',f);engines[key]=dict(path=str(f),sha256=sha(f))
unit=w/'inputs/query_unit_validation.json';exact(D/'current_sta_queries_01/unit_validation.json',unit)
newsource=w/'source';newsource.mkdir();newstate=w/'state';newstate.mkdir()
for name in ['routed.route','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','timing_graph.full_precision.echo','independent_audit.json','packed.net','placed.place']:exact(source/name,newsource/name)
exact(origin/'endpoint_vector.json',newstate/'endpoint_vector.json')
for old,new,changes in [(source/'manifest.json',newsource/'manifest.json',{}),(origin/'completion.json',newstate/'completion.json',dict(run=str(newsource)))]:
    exact(old,new.with_name(new.name+'.origin'));value=relocate(read(old));value.update(changes);value['receipt_relocation']=dict(original_sha256=sha(old),new_native_run=False);write(new,value)
full=D/'full_route_graph_cache_e695_01';parent=Path(read(full/'completion.json')['parent_cache'])
for old,new in [(parent,w/'audit_cache'),(full,w/'full_cache')]:
    c=read(old/'completion.json')
    for name in c['payload_sha256']:exact(old/name,new/name)
    exact(old/'completion.json',new/'origin_completion.json')
    if new.name=='audit_cache':c['graph']=str(paths['graph'])
    else:c.update(parent_cache=str(w/'audit_cache'),parent_completion_sha256=sha(w/'audit_cache/completion.json'))
    c['relocation']=dict(original_sha256=sha(old/'completion.json'),new_build=False);write(new/'completion.json',c)
query=w/'query_graph'
for name in ['graph.bin','graph_binding.json']:exact(D/'residual_query_offline_01'/name,query/name)
config=w/'runtime_config.json';write(config,dict(format='explicit_unified_phase_runtime_v1',physical_files={k:dict(path=str(p),sha256=sha(p)) for k,p in paths.items()},phase_binaries=phases,query_engines=engines,query_validations=dict(capacity=dict(path=str(unit),sha256=sha(unit))),full_graph_cache_completion_sha256=sha(w/'full_cache/completion.json')))
write(report/'registration.json',dict(workspace=str(w),original_state=str(origin),original_sha256=originals,package_manifest_sha256=sha(package/'artifact_manifest.json'),native_calls_planned=0,new_independent_inputs=0,qualification='Exact existing eltwise observation and graph payloads relocated; new code/feedback checks only. Query engines actually run; no VPR routing/analysis is launched.'))
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',H3D_EXPLICIT_RUNTIME_CONFIG=str(config))
def execute(script,args,label):
    cmd=['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/script),*map(str,args)];start=time.monotonic()
    with (report/(label+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    write(report/(label+'_execution.json'),dict(command=cmd,returncode=r.returncode,elapsed_seconds=time.monotonic()-start));assert r.returncode==0,label
    print(label,'passed',flush=True)
try:
    for name in ['run_complete_unified_method_v1.py','run_complete_flow_critical_portfolio_stream_v1.py','run_registered_independent_stream_transactions_v1.py','run_independent_resource_state_analysis_stream_v1.py','run_independent_timing_cone_analysis_stream_v1.py']:
        execute(name,['--help'],name.removesuffix('.py')+'_CLI')
    # Actual complete timing state machine until its first uncached native
    # proposal. Reuse-only is an explicit diagnostic mode, not a terminal result.
    limits=read(newsource/'independent_audit.json')['physical_metrics'];write(w/'limits.json',dict(wirelength=(limits['planar_wirelength_excluding_sb_half_nodes']*1001+999)//1000,SB_pairs=limits['sb_pairs_used'],CB_sources=limits['cb_crossing_output_sources_used']))
    actor=w/'timing'
    execute('run_complete_flow_critical_portfolio_stream_v1.py',['--runtime-config',config,'--initial-state',newstate,'--batch',actor,'--query-graph',query,'--audit-cache',w/'audit_cache','--full-graph-cache',w/'full_cache','--policy','timing_under_resources','--budget-mode','explicit_absolute','--fixed-limits',w/'limits.json','--native-mode','reuse_only'],'actual_timing_preflight')
    done=read(actor/'completion.json');assert done['passed'] and done['native_transaction_coordinators_started']==0
    feedback=actor/'round_000/feedback'
    assert read(feedback/'cone.json')['passed'] and read(feedback/'capacity/analysis.json')['passed'] and read(feedback/'relaxed/analysis.json')['passed']
    # Explicit same-actor query reuse must remain operational after relocation.
    rerun=actor/'diagnostic_same_state/feedback';rerun.mkdir(parents=True)
    execute('current_sta_arrival_cone_compact.py',['--state',newstate,'--output',rerun/'cone.json'],'same_state_selection')
    execute('run_current_cone_capacity_queries_cold_v1.py',['--reuse-root',actor,'--state',newstate,'--batch',rerun/'capacity','--reuse-batch',feedback/'capacity','--query-graph',query,'--audit-cache',w/'audit_cache','--cone',rerun/'cone.json'],'capacity_reuse')
    execute('audit_current_cone_queries.py',['--batch',rerun/'capacity','--query-graph',query,'--audit-cache',w/'audit_cache'],'capacity_reuse_audit')
    execute('run_current_graph_relaxed_queries_cold_v1.py',['--reuse-root',actor,'--capacity-batch',rerun/'capacity','--batch',rerun/'relaxed','--reuse-batch',feedback/'relaxed','--query-graph',query],'relaxed_reuse')
    execute('audit_current_cone_queries.py',['--batch',rerun/'relaxed','--query-graph',query,'--audit-cache',w/'audit_cache'],'relaxed_reuse_audit')
    reuse={}
    for key in ['capacity','relaxed']:
        ex=read(rerun/key/'execution.json');assert ex['new_queries']==0 and ex['reused_queries']>0
        assert (rerun/key/'query_stdout.log').read_bytes()==(feedback/key/'query_stdout.log').read_bytes();reuse[key]=dict(new=ex['new_queries'],reused=ex['reused_queries'])
    assert all(sha(runtime/n)==h for n,h in read(package/'artifact_manifest.json')['sha256'].items())
    write(report/'completion.json',dict(passed=True,workspace=str(w),runtime=str(runtime),actual_timing_state_machine_reached=done['operator_stop'],native_calls_new=0,new_independent_inputs=0,query_reuse=reuse,full_method_frozen=False,actual_native_backend_execution_tested=False,source_sha256={str(package/'artifact_manifest.json'):sha(package/'artifact_manifest.json'),str(actor/'completion.json'):sha(actor/'completion.json'),str(report/'registration.json'):sha(report/'registration.json'),str(Path(__file__).resolve()):sha(__file__)},qualification='Actual relocated feedback/portfolio and same-actor capacity/relaxed reuse. Native proposals explicitly held; no complete-method QoR/runtime or independent input result.'))
except BaseException as error:
    write(report/'completion.json',dict(passed=False,error=repr(error),workspace=str(w),native_calls_new=0,full_method_frozen=False,qualification='Preserve completed component steps; diagnose and resume only unexecuted checks in a new receipt.'))
    raise
