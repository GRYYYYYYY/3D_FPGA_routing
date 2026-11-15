"""Run the newly registered portable native interface once, then compare actual outputs."""
import copy,os,subprocess,sys,time,traceback
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
root=D/'standalone_native_observation_equivalence_01';plan=read(root/'plan.json');workspace=Path(plan['workspace']);package=workspace/'runtime'
execution=workspace/'execution';execution.mkdir(exist_ok=False);started=time.monotonic()
bound=plan['input_sha256'];assert all(sha(f)==h for f,h in bound.items())
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')}
env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def invoke(name,script,args):
    cmd=['/usr/bin/python3',str(package/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(package/script),*map(str,args)]
    t=time.monotonic()
    with (execution/(name+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=workspace,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1900)
    write(execution/(name+'_execution.json'),dict(command=cmd,returncode=r.returncode,process_seconds=time.monotonic()-t));assert r.returncode==0,(name,r.returncode)
def normalized(audit):
    result=copy.deepcopy(audit);result.pop('audit_wall_seconds',None)
    for key in ['rr_graph','route']:result['inputs'].pop(key,None)
    return result
try:
    template=read(workspace/'input_template.json')
    invoke('joint_indexes','build_joint_graph_indexes_v1.py',['--graph',workspace/template['files']['graph']['path'],'--output',execution/'indexes'])
    config=copy.deepcopy(template)
    for row in config['files'].values():row['path']=os.path.relpath(workspace/row['path'],execution)
    config['full_graph_cache']=dict(path='indexes/full_cache',completion_sha256=sha(execution/'indexes/full_cache/completion.json'))
    write(execution/'inputs.json',config)
    invoke('native_observation','observe.py',['--inputs',execution/'inputs.json','--output',execution/'observation','--timing-echo'])
    observed=execution/'observation';complete=read(observed/'completion.json');assert complete['passed'] and complete['accepted'] is None
    assert complete['native_analysis_calls']==1 and complete['route_search_calls']==0
    actual=read(observed/'endpoint_vector.json');expected=read(workspace/'expected/endpoint_vector.json')
    assert actual==expected,'Full serialized native vector/metrics/constraint/trace identity differs'
    audit=read(observed/'runs/state/independent_audit.json');original=read(workspace/'expected/independent_audit.json')
    assert normalized(audit['audit'])==normalized(original['audit'])
    assert audit['physical_metrics']==original['physical_metrics']
    for name in ['packed.net','placed.place','routed.route']:assert sha(observed/'runs/state'/name)==sha(workspace/'inputs'/name)
    assert sha(observed/'runs/state/native_sta_frontier.jsonl')==sha(workspace/'expected/native_sta_frontier.jsonl')
    assert all(sha(f)==h for f,h in bound.items())
    files=[Path(__file__).resolve(),root/'plan.json',execution/'inputs.json',execution/'indexes/completion.json',observed/'completion.json',observed/'endpoint_vector.json',observed/'runs/state/independent_audit.json',observed/'input_seal.json']
    write(root/'completion.json',dict(passed=True,workspace=str(workspace),native_calls_new=1,route_search_calls=0,
        full_serialized_endpoint_vector_exact=True,raw_native_trace_exact=True,cached_physical_audit_exact=True,inputs_unchanged=True,
        current_native_FULL_STA_and_timing_echo_passed=True,validation_component_process_seconds=time.monotonic()-started,
        source_sha256={str(f):sha(f) for f in files},independent_circuit_results_new=0,full_method_frozen=False,
        qualification='One new native interface validation on an existing tiny input, executing outside the historical project with local Python dependencies and explicit inputs. Complete original numerical/trace/audit identity required. This is component execution equivalence, not an independent circuit benefit, routing search, complete algorithm cost or full-method confirmation.'))
    print(dict(passed=True,native_calls_new=1,full_vector_and_audit_exact=True),flush=True)
except Exception as exc:
    manifest=execution/'observation/runs/state/manifest.json'
    write(root/'completion.json',dict(passed=False,status='component_validation_failed_preserved',error=repr(exc),workspace=str(workspace),
        native_execution_manifest_exists=manifest.exists(),native_calls_new=1 if manifest.exists() and 'process_group_id' in read(manifest) else 0,
        route_search_calls=0,source_sha256={str(root/'plan.json'):sha(root/'plan.json')},qualification='Do not repeat a completed native call; inspect actual phase/output and resume only unmet read-only validation.'))
    traceback.print_exc();raise
