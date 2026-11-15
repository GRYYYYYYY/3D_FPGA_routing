"""Keep completed replay outputs; compare audit content apart from paths and stopwatch."""
import copy,json,os,shutil,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
first=D/'standalone_transactions_validation_01';report=D/'standalone_transactions_validation_02';report.mkdir(exist_ok=False)
work=Path(read(first/'registration.json')['relocated_directory']);runtime=work/'runtime';fixture=work/'fixture'
prior=Path(read(D/'standalone_selection_validation_01/completion.json')['relocated_directory'])
original=D/'R1_owner_release_joint_probe_01/transaction'
package=D/'standalone_transactions_dev_01'
assert all(sha(package/n)==h==sha(runtime/n) for n,h in read(package/'artifact_manifest.json')['sha256'].items())
assert read(first/'joint_native_materialize_execution.json')['returncode']==0
assert read(fixture/'joint_native_evaluation/completion.json')['passed']
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']}
env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def execute(script,args,label):
    command=['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/script),*map(str,args)]
    begin=time.monotonic()
    with (report/(label+'.log')).open('x') as log:r=subprocess.run(command,cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    write(report/(label+'_execution.json'),dict(command=command,returncode=r.returncode,elapsed_seconds=time.monotonic()-begin))
    assert r.returncode==0,label
def canonical_audit(data):
    data=copy.deepcopy(data['audit']);data.pop('audit_wall_seconds')
    for field in ['rr_graph','route']:data['inputs'].pop(field)
    return data
results=[]
for role in ['joint_native','joint_target_CB_domain']:
    if not (fixture/(role+'_audit/analysis.json')).exists():
        execute('audit_native_feedback_objective_cached.py',['--batch',fixture,'--role',role,'--cache',prior/'R1/audit_cache','--output',fixture/(role+'_audit')],role+'_scope')
    if not (fixture/(role+'_domain_audit.json')).exists():
        execute('audit_explicit_crossing_source_domain_v2.py' if role=='joint_target_CB_domain' else 'audit_retained_crossing_domain.py',['--batch',fixture,'--role',role],role+'_domain')
    before=read(original/(role+'_audit/analysis.json'));after=read(fixture/(role+'_audit/analysis.json'))
    for key in ['passed','status','scope','queries','attempts','changed_delays','native_transaction_seconds']:assert before[key]==after[key],key
    assert Path(before['candidate_route']).read_bytes()==Path(after['candidate_route']).read_bytes()
    if not (fixture/(role+'_evaluation')).exists():
        execute('materialize_crossing_source_candidate_v1.py',['--worker',fixture/role,'--output',fixture/(role+'_evaluation'),'--full-graph-cache',prior/'R1/full_cache','--audited-route',after['candidate_route']],role+'_materialize')
    assert read(fixture/(role+'_evaluation/completion.json'))['passed']
    assert read(fixture/(role+'_evaluation/endpoint_vector.json'))==read(original/(role+'_evaluation/endpoint_vector.json'))
    actual=read(fixture/(role+'_evaluation/runs/state/independent_audit.json'));expected=read(original/(role+'_evaluation/runs/state/independent_audit.json'))
    assert actual['physical_metrics']==expected['physical_metrics'] and canonical_audit(actual)==canonical_audit(expected)
    results.append(dict(role=role,passed=True,scope_queries_attempts_changes_exact=True,candidate_bytes_exact=True,
        full_endpoint_vector_exact=True,physical_audit_all_nonpath_nontime_fields_exact=True))

# Admit the same copied current state and actually prepare a whole owner transaction.
source=fixture/'source';state=fixture/'state';m=read(source/'manifest.json');command=m['command']
binary=Path(read(fixture/'joint_native/runs/state/manifest.json')['command'][0])
paths=dict(binary=binary,architecture=Path(command[1]),circuit=Path(command[2]),graph=Path(command[command.index('--read_rr_graph')+1]),
    packed=source/'packed.net',placement=source/'placed.place',route=source/'routed.route')
arguments=command[3:]
if '--route' in arguments:arguments.remove('--route')
for option,key in [('--read_rr_graph','graph'),('--net_file','packed'),('--place_file','placement'),('--route_file','route')]:arguments[arguments.index(option)+1]='{'+key+'}'
for option,value in [('--timing_report_npaths','10'),('--verify_route_file_switch_id','on')]:
    if option in arguments:arguments[arguments.index(option)+1]=value
    else:arguments += [option,value]
descriptor=fixture/'explicit_inputs.json';write(descriptor,dict(format='standalone_native_observation_input_v1',files={k:dict(path=str(v),sha256=sha(v)) for k,v in paths.items()},analysis_arguments=arguments,
    full_graph_cache=dict(path=str(prior/'R1/full_cache'),completion_sha256=sha(prior/'R1/full_cache/completion.json'))))
selection=fixture/'selection';selection.mkdir(exist_ok=False)
for name in ['owner.json','crossing.json','sta.json']:shutil.copy2(prior/'R1/selection'/name,selection/name)
old=read(prior/'R1/selection/completion.json');old['source_sha256']=dict(old['source_sha256'])
for before,after in [(prior/'R1/routed.route',source/'routed.route'),(prior/'R1/native_sta_frontier.jsonl',source/'native_sta_frontier.jsonl'),
                     (prior/'R1/native_sta_frontier.jsonl.constraints.echo',source/'native_sta_frontier.jsonl.constraints.echo'),
                     (prior/'R1/endpoint_vector.json',state/'endpoint_vector.json'),(prior/'R1/independent_audit.json',source/'independent_audit.json')]:
    assert sha(before)==sha(after);old['source_sha256'][str(after)]=old['source_sha256'].pop(str(before))
old['receipt_relocation']='Byte-exact selected scope data; observation path bindings rebased to byte-exact copies, no new selection/native execution.'
write(selection/'completion.json',old)
execute('transact.py',['--inputs',descriptor,'--state',state,'--root-state',state,'--selection',selection,'--output',fixture/'prepared_owner',
    '--kind','owner','--domain-mode','unrestricted','--prepare-only'],'owner_prepare')
assert (fixture/'prepared_owner/request.txt').read_bytes()==Path(read(original/'registration.json')['roles']['joint_native']['request']).read_bytes()
reg=read(fixture/'prepared_owner/registration.json');assert len(reg['roles']['candidate']['queries'])==5
helper=D/'test_standalone_worker_preflight_01.py';shutil.copy2(helper,runtime/helper.name)
execute(helper.name,['--capture',fixture/'worker_preflight_capture.json','--inputs',descriptor,'--source',source,'--batch',fixture/'worker_preflight',
    '--seed-order','delay_rr_id','--candidate-full-sta','--native-cases',fixture/'prepared_owner/empty_request.txt'],'worker_preflight')
assert read(fixture/'worker_preflight_capture.json')['passed']
write(report/'completion.json',dict(passed=True,relocated_directory=str(work),results=results,native_calls_new=0,
    reused_completed_native_role_materialization=True,original_failure_scope='Audit paths and audit_wall_seconds differ by construction; scientific fields all exact.',
    whole_owner_request_preparation_exact=True,worker_preparation_current_binary_and_command_checked=True,
    native_worker_execution_validated=False,full_transaction_execution_validated=False,full_method_frozen=False,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),helper,package/'artifact_manifest.json',first/'registration.json',fixture/'relocation.json',fixture/'worker_preflight_capture.json']},
    qualification='Actual outside-project scope/domain/materialization replay, full vector and physical audit exact apart from declared paths/clock. Complete prepared owner request matches original5connections. Worker preflight stops at io.run boundary; no new native process, no whole-transaction execution proof or independent sample.'))
print(dict(passed=True,roles=2,owner_queries=5,native_calls_new=0,native_worker_execution_validated=False),flush=True)
