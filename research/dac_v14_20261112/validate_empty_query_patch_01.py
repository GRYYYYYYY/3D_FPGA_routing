"""Actual completed empty/nonempty input replay, without rerunning query/native work."""
import difflib
import os
import subprocess
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

root=D/'empty_query_patch_validation_01';plan=read(root/'plan.json')
runtime=Path(plan['runtime']);patch=D/'empty_query_patch_01'
for name in ['query_current_protected_critical.py','query_critical_owner_exchange.py']:
    before=(runtime/name).read_text().splitlines(True);after=(patch/name).read_text().splitlines(True)
    assert all(tag in ['equal','insert'] for tag,*_ in difflib.SequenceMatcher(None,before,after).get_opcodes()),name
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')}
env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',H3D_EXPLICIT_RUNTIME_CONFIG=plan['runtime_config'])
results=[]
for item in plan['fixtures']:
    feedback=Path(item['feedback']);owners=read(feedback/'owners/completion.json')
    assert bool(owners['rows'])==(item['mode']=='nonempty')
    for kind,script in [('protected','query_current_protected_critical.py'),('exchange','query_critical_owner_exchange.py')]:
        case=root/(item['id']+'_'+kind);case.mkdir(exist_ok=False)
        output=case/'worker';receipt=case/'replay.json'
        args=['--output',str(output),'--audit-cache',item['audit_cache'],'--query-graph',item['query_graph']]
        if kind=='protected':args+=['--capacity-batch',str(feedback/'capacity'),'--opportunities',str(feedback/'owners/completion.json')]
        else:args+=['--feedback',str(feedback)]
        cmd=['/usr/bin/python3','-I',str(D/'replay_empty_query_worker_01.py'),'--runtime',str(runtime),'--script',str(patch/script),'--mode',item['mode'],'--result',str(receipt),'--',*args]
        with (case/'replay.log').open('x') as log:
            code=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
        assert code==0,(case,'replay failed')
        r=read(receipt);assert r['passed']
        if item['mode']=='empty':
            actual=read(output/'completion.json');expected=read(feedback/('protected/completion.json' if kind=='protected' else '../exchange_query/completion.json'))
            assert actual['rows']==expected['rows']==[]
            assert actual['query_subprocess_executed'] is False and actual['graph_mapping_executed'] is False
            assert all(sha(f)==h for f,h in actual['source_sha256'].items())
            if kind=='protected':
                assert actual['protected_nets']==expected['protected_nets']
                assert actual['query_process_seconds'] is None
            r['actual_empty_rows_and_metadata_preserved']=True
        else:
            assert not (output/'completion.json').exists()
            r['scope']='Dispatch only; no nonempty query result recomputed or inferred.'
        results.append(dict(fixture=item['id'],kind=kind,**r))
write(root/'completion.json',dict(passed=True,checks=results,
    original_nonempty_bodies_retained_byte_exact=True,new_native_routes=0,new_query_processes=0,
    full_method_equivalence_verified=False,whole_time_saving_established=False,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),D/'replay_empty_query_worker_01.py',root/'plan.json',patch/'preparation.json',patch/'query_current_protected_critical.py',patch/'query_critical_owner_exchange.py']},
    qualification='Real completed conv_hls empty data and BNN nonempty data used. Empty workers execute original upstream digest/state checks and new argument/driver guards with mapping/process launches forbidden. Nonempty paths stop at the original graph-map boundary. Not independent new routing evidence, full nonempty replay, candidate/proposal equivalence or complete speedup. Future package and symmetric complete controls required.'))
print(dict(passed=True,checks=len(results),native_calls_new=0,query_processes_new=0))
