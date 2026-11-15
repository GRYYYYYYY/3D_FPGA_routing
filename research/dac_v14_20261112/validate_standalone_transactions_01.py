"""Replay real owner transaction audits/materialization outside the historical project."""
import ast,json,os,shutil,subprocess,tempfile,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

package=D/'standalone_transactions_dev_01';report=D/'standalone_transactions_validation_01';report.mkdir(exist_ok=False)
for f in package.glob('*.py'):compile(f.read_text(),str(f),'exec')
write(package/'artifact_manifest.json',dict(format='standalone_transactions_development_v1',full_method_frozen=False,
    native_worker_interface_execution_validated=False,
    sha256={f.name:sha(f) for f in package.iterdir() if f.is_file()},
    qualification='Scientific audit and materialization closure plus explicit native transaction entry. Native adapter execution and complete controller confirmation pending.'))
work=Path(tempfile.mkdtemp(prefix='standalone-transactions-'));runtime=work/'runtime';fixture=work/'fixture';fixture.mkdir()
shutil.copytree(package,runtime,ignore=shutil.ignore_patterns('__pycache__'))
prior=Path(read(D/'standalone_selection_validation_01/completion.json')['relocated_directory'])
for name in ['numpy','numpy.libs','lxml','lxml.libs']:
    if (prior/'runtime'/name).exists():shutil.copytree(prior/'runtime'/name,runtime/name,ignore=shutil.ignore_patterns('__pycache__'))
origin=D/'R1_owner_release_joint_probe_01/transaction'
original_role=read(origin/'registration.json')['roles']['joint_native'];source=Path(original_role['source']);state=Path(original_role['state'])
source_new=fixture/'source';state_new=fixture/'state';source_new.mkdir();state_new.mkdir()
mapping={};sources={};relocations=[]
def register(old,new):mapping[str(Path(old).resolve())]=Path(new).resolve()
def destination(old):
    old=Path(old).resolve()
    if str(old) in mapping:return mapping[str(old)]
    if old.is_relative_to(D.parents[1]):return fixture/'opaque'/old.relative_to(D.parents[1])
    return old
def exact(old,new=None):
    old=Path(old).resolve();new=destination(old) if new is None else Path(new).resolve()
    register(old,new);h=sha(old);sources[str(old)]=h
    if old!=new:
        new.parent.mkdir(parents=True,exist_ok=True)
        if not new.exists():shutil.copy2(old,new)
        assert sha(new)==h
    return new
graph=Path(read(D/'rr_audit_cache_bnn_01/completion.json')['graph'])
register(graph,prior/'R1/rr_graph.xml');assert sha(destination(graph))==sha(graph)
for name in ['routed.route','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','independent_audit.json','packed.net','placed.place']:
    register(source/name,source_new/name)
    previous=prior/'R1'/name
    if previous.exists() and sha(previous)==sha(source/name):
        os.link(previous,source_new/name);sources[str(source/name)]=sha(previous)
    else:exact(source/name)
register(state,state_new);register(source,source_new)
register(state/'completion.json',state_new/'completion.json');register(state/'endpoint_vector.json',state_new/'endpoint_vector.json')
exact(state/'endpoint_vector.json')
register(source/'manifest.json',source_new/'manifest.json')
for role in ['joint_native','joint_target_CB_domain']:
    old=origin/role;new=fixture/role
    register(old,new);register(old/'runs/state',new/'runs/state')
    for suffix in ['candidate','candidate_restored']:
        register(old/'runs/state'/suffix,new/'runs/state'/suffix)
    for name in ['completion.json','registration.json','candidate_exports.json']:register(old/name,new/name)
    register(old/'runs/state/manifest.json',new/'runs/state/manifest.json')
def translate(value):
    if isinstance(value,str) and value.startswith('/'):
        return str(destination(value))
    if isinstance(value,list):return [translate(x) for x in value]
    if isinstance(value,dict):return {translate(k):translate(v) for k,v in value.items()}
    return value
def metadata(old):
    old=Path(old);original=read(old);new=translate(original)
    if 'source_sha256' in original:
        rebound={}
        for f,h in original['source_sha256'].items():
            assert sha(f)==h,(old,f)
            target=destination(f)
            if not target.exists():exact(f)
            rebound[str(target)]=sha(target)
        new['source_sha256']=rebound
    # Shared manifest records include digests of metadata that may be relocated.
    if 'shared_inputs' in original:
        shared={}
        for f,row in original['shared_inputs'].items():
            target=destination(f)
            if not target.exists():exact(f)
            shared[str(target)]=dict(row,sha256=sha(target))
        new['shared_inputs']=shared
    target=destination(old);target.parent.mkdir(parents=True,exist_ok=True)
    # Preserve original receipt bytes next to explicitly derived relocation.
    original_copy=target.with_name(target.name+'.origin');shutil.copy2(old,original_copy)
    new['receipt_relocation']=dict(original_sha256=sha(old),original_receipt=str(original_copy),new_native_execution=False,
        qualification='Path/digest rebasing of already executed evidence for dependency replay; original numerical/protocol outputs copied exactly.')
    write(target,new);sources[str(old.resolve())]=sha(old)
    relocations.append(dict(origin=str(old),derived=str(target),origin_sha256=sha(old),derived_sha256=sha(target)))

metadata(source/'manifest.json');metadata(state/'completion.json')
for role in ['joint_native','joint_target_CB_domain']:
    old=origin/role;new=fixture/role;run=old/'runs/state';nr=new/'runs/state'
    for name in ['routed.route','packed.net','placed.place','stdout.log','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','joint_native.log','vertical_domain.log']:
        if (run/name).exists():register(run/name,nr/name);exact(run/name)
    for kind in ['candidate','candidate_restored']:
        for f in (run/kind).iterdir():
            if f.is_file():register(f,nr/kind/f.name);exact(f)
    metadata(old/'registration.json');metadata(run/'manifest.json');metadata(old/'completion.json');metadata(old/'candidate_exports.json')
roles={}
for name,role in read(origin/'registration.json')['roles'].items():
    role=translate(role);role['source_sha256']={}
    for f,h in read(origin/'registration.json')['roles'][name]['source_sha256'].items():
        assert sha(f)==h
        dst=destination(f)
        if not dst.exists():exact(f)
        role['source_sha256'][str(dst)]=sha(dst)
    roles[name]=role
write(fixture/'registration.json',dict(roles=roles,receipt_relocation='Imported original transaction registration; no new native execution.'))
write(fixture/'relocation.json',dict(passed=True,receipts=relocations,native_calls_new=0,source_sha256=sources))
write(report/'registration.json',dict(relocated_directory=str(work),original_transaction=str(origin),native_calls_planned=0,
    source_sha256={str(package/'artifact_manifest.json'):sha(package/'artifact_manifest.json'),str(origin/'registration.json'):sha(origin/'registration.json')},
    qualification='Only actual existing receipts are rebased, with original bytes retained; never submitted as a new native run.'))
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']}
env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def execute(script,args,label,expected=0):
    cmd=['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/script),*map(str,args)]
    start=time.monotonic()
    with (report/(label+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    write(report/(label+'_execution.json'),dict(command=cmd,returncode=r.returncode,elapsed_seconds=time.monotonic()-start))
    assert (r.returncode==0)==(expected==0),label
for role in roles:
    execute('audit_native_feedback_objective_cached.py',['--batch',fixture,'--role',role,'--cache',prior/'R1/audit_cache','--output',fixture/(role+'_audit')],role+'_scope')
    before=read(origin/(role+'_audit/analysis.json'));after=read(fixture/(role+'_audit/analysis.json'))
    for key in ['passed','status','scope','queries','attempts','changed_delays','native_transaction_seconds']:assert before[key]==after[key],key
    assert Path(before['candidate_route']).read_bytes()==Path(after['candidate_route']).read_bytes()
    execute('audit_explicit_crossing_source_domain_v2.py' if role=='joint_target_CB_domain' else 'audit_retained_crossing_domain.py',
        ['--batch',fixture,'--role',role],role+'_domain')
    execute('materialize_crossing_source_candidate_v1.py',['--worker',fixture/role,'--output',fixture/(role+'_evaluation'),
        '--full-graph-cache',prior/'R1/full_cache','--audited-route',after['candidate_route']],role+'_materialize')
    assert read(fixture/(role+'_evaluation/endpoint_vector.json'))==read(origin/(role+'_evaluation/endpoint_vector.json'))
    actual=read(fixture/(role+'_evaluation/runs/state/independent_audit.json'));expected=read(origin/(role+'_evaluation/runs/state/independent_audit.json'))
    assert actual['physical_metrics']==expected['physical_metrics'] and actual['audit']==expected['audit']
    write(report/(role+'_result.json'),dict(passed=True,scope_queries_attempts_changes_exact=True,candidate_bytes_exact=True,
        full_endpoint_vector_exact=True,independent_physical_audit_exact=True,new_native_calls=0))
assert all(sha(f)==h for f,h in sources.items())
write(report/'completion.json',dict(passed=True,relocated_directory=str(work),roles=list(roles),native_calls_new=0,
    historical_project_Python_reads_forbidden=True,actual_scope_candidate_vector_physical_audit_exact=True,
    native_worker_execution_validated=False,transaction_orchestrator_execution_validated=False,full_method_frozen=False,
    artifact_manifest_sha256=sha(package/'artifact_manifest.json'),source_sha256=sources,
    qualification='Actual outside-project replay of existing two-arm R1 owner native protocols: scope reconstruction, domain checks and installed candidate materialization. Imported receipt path/digest rebasing explicit, originals retained. No new native execution or independent input; new worker/orchestrator still require execution validation.'))
print(dict(passed=True,roles=list(roles),native_calls_new=0,relocated_directory=str(work)),flush=True)
