#!/usr/bin/env python3
"""Matched single-transaction 2x2: reuse completed cells, execute missing cells."""
import copy,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from endpoint_timing_policy import decide
from run_native_scope_policy_v3 import input_identity,native_config,run_dir

b=D/'spmv_adoption_factorial_01';started=time.monotonic();b.mkdir(exist_ok=False)
resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));assert shutil.disk_usage(D).free>=80*1024**3
assert (D/'current_sta_policy_native_spmv_A0_near_physical_01/completion.json').exists(),'Do not overlap live native controller'
assert read(D/'full_route_graph_cache_validation_01/completion.json')['passed']
old={mode:D/name/'attempt_000' for mode,name in [('weighted_soft','current_sta_policy_native_spmv_A0_near_01'),('physical_capacity','current_sta_policy_native_spmv_A0_near_physical_01')]}
templates={mode:read(p/'registration.json')['roles']['candidate'] for mode,p in old.items()}
template=templates['weighted_soft'];state=Path(template['state']);source=Path(template['source']);other=templates['physical_capacity']
for key in ['state','source','targets','removed_pins','queries','fixed_target_paths']:assert template[key]==other[key],key
assert sha(template['request'])==sha(other['request'])
files=[Path(__file__).resolve(),D/'run_native_objective_state_analysis.py',D/'audit_native_objective_cached.py',D/'run_endpoint_state_analysis_cached.py',D/'full_route_graph_cache_validation_01/completion.json',D/'native_objective_stage_01/binding.json',D/'endpoint_timing_policy.py',state/'completion.json',state/'endpoint_vector.json']
for p in old.values():files += [p/'registration.json',p/'candidate_audit/analysis.json',p/'evaluation/completion.json',p/'evaluation/endpoint_vector.json']
roles={}
for mode in ['weighted_capacity','physical_soft']:
    r=copy.deepcopy(template);r['objective']=mode;roles[mode]=r
write(b/'registration.json',dict(status='registered_before_work',roles=roles,pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],question='At identical source6008p12/scope/request/criticality, is endpoint plateau adoption caused by physical objective, hard capacity or their interaction?',reused_roles={k:str(v) for k,v in old.items()},source_sha256={str(p):sha(p) for p in files},guards=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),qualification='Single-state factorial mechanism diagnostic, not four independent policy trajectories. Complete exact candidates may reuse certified FULL/STA; all incremental costs recorded.'))
costs=[];results={};references=[state]+[p/'evaluation' for p in old.values()]
def invoke(script,args,tag):
    assert shutil.disk_usage(D).free>=80*1024**3
    command=[sys.executable,str(D/script),*map(str,args)];t=time.monotonic();status='completed'
    with (b/(tag+'.log')).open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:code=process.wait(timeout=1800);status='completed' if code==0 else 'failed'
        except subprocess.TimeoutExpired:
            status='timeout';os.killpg(process.pid,signal.SIGTERM)
            try:code=process.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);code=process.wait()
    costs.append(dict(tag=tag,status=status,returncode=code,command=command,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',costs)
    return status=='completed'
def summarize(mode,audit,evaluation,reused):
    decisions={p:decide(p,read(state/'endpoint_vector.json'),read(evaluation/'endpoint_vector.json'),True) for p in ['strict','endpoint_vector']}
    write(b/(mode+'_decisions.json'),decisions)
    return dict(status='legal_candidate',evaluation=str(evaluation),reused_FULL_STA=reused,cpd_ns=read(evaluation/'endpoint_vector.json')['cpd_s']*1e9,physical_changes=audit['changed_delays'],native_queries=len(audit['queries']),native_search_attempts=len(audit['attempts']),native_core_seconds=audit['native_transaction_seconds'],decisions={p:dict(accepted=d['accepted'],setup_improved=d['comparison']['setup_improved'],setup_regressed=d['comparison']['setup_regressed']) for p,d in decisions.items()})
for mode,p in old.items():results[mode]=dict(summarize(mode,read(p/'candidate_audit/analysis.json'),p/'evaluation',True),reused_native_transaction=True)
write(b/'progress.json',results)
for mode,r in roles.items():
    ok=invoke('run_native_objective_state_analysis.py',['--source',source,'--batch',b/mode,'--native-cases',r['request'],'--objective',mode],mode+'_native')
    if ok:ok=invoke('audit_native_objective_cached.py',['--batch',b,'--role',mode,'--cache',D/'rr_audit_cache_e695_dev_01','--output',b/(mode+'_audit')],mode+'_audit')
    if not ok:
        results[mode]=dict(status='native_or_physical_audit_failed',accepted=False,rollback='Immutable original retained; see process stderr, no failed candidate evaluated.')
        write(b/'progress.json',results);continue
    audit=read(b/(mode+'_audit/analysis.json'))
    if not audit.get('candidate_route'):
        results[mode]=dict(status='transaction_failed_rolled_back');write(b/'progress.json',results);continue
    candidate=Path(audit['candidate_route']);evaluation=None
    for prior in references:
        run=run_dir(prior)
        if route_body(candidate)==route_body(run/'routed.route') and input_identity(source)==input_identity(run) and native_config(source)==native_config(run):
            assert read(prior/'completion.json')['passed']
            assert read(state/'endpoint_vector.json')['constraints_sha256']==read(prior/'endpoint_vector.json')['constraints_sha256']
            evaluation=prior;break
    reused=evaluation is not None
    if not reused:
        evaluation=b/(mode+'_evaluation')
        ok=invoke('run_endpoint_state_analysis_cached.py',['--source',source,'--batch',evaluation,'--candidate-route',candidate,'--full-graph-cache',D/'full_route_graph_cache_e695_01'],mode+'_evaluation')
        if not ok:results[mode]=dict(status='FULL_STA_or_physical_audit_failed');write(b/'progress.json',results);continue
    results[mode]=summarize(mode,audit,evaluation,reused);results[mode]['reused_native_transaction']=False
    write(b/'progress.json',results);print(mode,results[mode]['decisions'],flush=True)
paths=[b/'registration.json',b/'process_costs.json',b/'progress.json',*b.glob('*_decisions.json')]
write(b/'completion.json',dict(status='matched_factorial_terminal',passed=True,roles=results,complete_orchestrator_seconds=time.monotonic()-started,complete_child_process_seconds=sum(r['complete_process_seconds'] for r in costs),source_sha256={str(p):sha(p) for p in paths},qualification='Failed physical audits are explicit rejected outcomes, not successful repairs. Two completed cells reused; remaining cells run once from the identical immutable initial state. Reuse times are not independent full algorithm runtimes.'))
