"""Reject altered installed-state gates and wrong complete candidate trees."""
import json,os,shutil,subprocess
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
proof=read(D/'standalone_transactions_validation_03/completion.json');assert proof['passed']
work=Path(proof['relocated_directory']);runtime=work/'runtime_v2';fixture=work/'fixture'
report=D/'standalone_transaction_guards_01';report.mkdir(exist_ok=False)
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']}
env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
bad=fixture/'invalid_gate_worker';bad.mkdir()
for name in ['completion.json','registration.json']:shutil.copy2(fixture/'joint_native'/name,bad/name)
candidate=bad/'candidate';candidate.mkdir();(candidate/'native_state_gate.txt').write_text('candidate not_checked\n')
exports=read(fixture/'joint_native/candidate_exports.json');exports['candidate']=str(candidate);write(bad/'candidate_exports.json',exports)
cache=Path(read(fixture/'explicit_inputs.json')['full_graph_cache']['path'])
audit=Path(read(fixture/'joint_native_audit/analysis.json')['candidate_route'])
tests=[('altered_actual_gate',bad,audit,None),('different_complete_tree',fixture/'joint_native',fixture/'source/routed.route','Actual installed candidate differs from independent scope reconstruction')]
results=[]
for label,worker,route,reason in tests:
    output=fixture/(label+'_output');assert not output.exists()
    command=['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/'materialize_crossing_source_candidate_v1.py'),
        '--worker',str(worker),'--output',str(output),'--full-graph-cache',str(cache),'--audited-route',str(route)]
    r=subprocess.run(command,cwd=runtime,env=env,capture_output=True,text=True,timeout=300)
    write(report/(label+'.json'),dict(command=command,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
    assert r.returncode!=0 and 'AssertionError' in r.stderr and not output.exists(),label
    if reason:assert reason in r.stderr
    else:assert "candidate FULL fresh_STA actual_installed_trees" in r.stderr
    results.append(dict(case=label,rejected_before_output=True))
write(report/'completion.json',dict(passed=True,tests=results,native_calls_new=0,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),D/'standalone_transactions_validation_03/completion.json',runtime/'materialize_crossing_source_candidate_v1.py']},
    qualification='Negative actual-receipt tests of materialization admission; altered gate and wrong entire candidate tree rejected without output/native execution. Positive original candidates remain unchanged.'))
print(dict(passed=True,rejected=len(results),native_calls_new=0))
