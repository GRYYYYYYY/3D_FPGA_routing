"""Execute one predeclared portable owner transaction; never retry native work."""
import copy,os,subprocess,time,traceback
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
root=D/'standalone_transaction_native_check_01';plan=read(root/'plan.json');w=Path(plan['workspace']);execution=w/'execution';execution.mkdir(exist_ok=False);start=time.monotonic()
assert all(sha(f)==h for f,h in plan['input_sha256'].items())
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
transaction=execution/'transaction'
cmd=['/usr/bin/python3',str(w/'runtime/guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(w/'runtime/transact.py'),'--inputs',str(w/'inputs.json'),'--state',str(w/'state'),'--root-state',str(w/'state'),'--selection',str(w/'selection'),'--output',str(transaction),'--kind','owner','--domain-mode','unrestricted']
command=['/usr/bin/python3',str(D/'supervise_component_process_v1.py'),'--receipt',str(execution/'supervision.json'),'--seconds',str(plan['limits']['whole_component_seconds']),'--',*cmd]
def scientific_audit(value):
 v=copy.deepcopy(value['audit']);v.pop('audit_wall_seconds',None)
 for k in ['route','rr_graph']:v['inputs'].pop(k,None)
 return v
try:
 with (execution/'transaction.log').open('x') as log:
  child=subprocess.Popen(command,cwd=w,env=env,stdout=log,stderr=subprocess.STDOUT)
  ticks=Path('/proc',str(child.pid),'stat').read_text().rsplit(')',1)[1].split()[19]
  write(root/'active_supervisor.json',dict(pid=child.pid,start_ticks=ticks,command=command));code=child.wait()
 assert code==0 and read(execution/'supervision.json')['passed']
 c=read(transaction/'completion.json');assert c['passed'] and c['transaction_feasible'] and c['accepted']
 assert c['native_worker_calls']==2 and Path(c['selected_state'])==transaction/'evaluation'
 assert (transaction/'request.txt').read_bytes()==(w/'expected/request.txt').read_bytes()
 assert read(transaction/'evaluation/endpoint_vector.json')==read(w/'expected/endpoint_vector.json')
 assert route_body(transaction/'evaluation/runs/state/routed.route')==route_body(w/'expected/candidate.route')
 actual=read(transaction/'evaluation/runs/state/independent_audit.json');expected=read(w/'expected/independent_audit.json')
 assert actual['physical_metrics']==expected['physical_metrics'] and scientific_audit(actual)==scientific_audit(expected)
 for name in ['source_control','candidate']:
  assert read(transaction/name/'completion.json')['passed']
  assert read(transaction/name/'input_seal.json')['passed']
 assert all(sha(f)==h for f,h in plan['input_sha256'].items())
 sources=[root/'plan.json',execution/'supervision.json',transaction/'completion.json',transaction/'evaluation/completion.json',transaction/'candidate_audit/analysis.json',transaction/'candidate_domain_audit.json']
 write(root/'completion.json',dict(passed=True,native_calls_new=2,nonempty_transaction_calls_new=1,source_and_candidate_native_FULL_STA=True,restored_source_gates_passed=True,full_endpoint_vector_exact=True,route_body_exact=True,physical_scientific_audit_exact=True,request_exact=True,fixed_current_R1_root_acceptance=True,complete_component_seconds=time.monotonic()-start,workspace=str(w),new_independent_inputs=0,full_method_frozen=False,source_sha256={str(f):sha(f) for f in sources},qualification='Actual explicit-input owner transaction adapter execution outside project. Known R1 test input, not independent circuit evidence or complete-method cost. Fresh source audits in both workers included in this component time; original optimized resource backend not replaced.'))
 print(dict(passed=True,native_calls_new=2,new_independent_inputs=0),flush=True)
except Exception as exc:
 manifests=list(transaction.glob('*/runs/state/manifest.json')) if transaction.exists() else []
 calls=sum('process_group_id' in read(f) for f in manifests)
 write(root/'completion.json',dict(passed=False,status='component_validation_failed_preserved',error=repr(exc),workspace=str(w),native_calls_new=calls,new_independent_inputs=0,source_sha256={str(root/'plan.json'):sha(root/'plan.json')},qualification='Preserve actual native receipts; do not retry executed work. Resume unmet read-only comparisons separately where appropriate.'))
 traceback.print_exc();raise
