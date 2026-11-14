#!/usr/bin/env python3
"""Current-STA native repair controller with immutable states and full child timing."""
import argparse,hashlib,json,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from current_sta_selector import select
from endpoint_timing_policy import decide

def run_dir(state):return Path(read(state/'completion.json')['run'])

def input_identity(run):
    manifest=read(run/'manifest.json')
    shared=sorted((Path(p).name,v['sha256']) for p,v in manifest['shared_inputs'].items())
    return [sha(run/'packed.net'),sha(run/'placed.place'),shared]

def state_key(state):
    run=run_dir(state);vector=read(state/'endpoint_vector.json')
    body=route_body(run/'routed.route');assert body==read(state/'completion.json')['route_body_sha256']
    return json.dumps([body,input_identity(run),vector['constraints_sha256']],sort_keys=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--initial-state',type=Path,required=True);parser.add_argument('--batch',type=Path,required=True)
    parser.add_argument('--policy',choices=['strict','endpoint_vector','both'],default='both');parser.add_argument('--scope',choices=['target_only','conflict'],default='conflict')
    parser.add_argument('--objective',choices=['weighted_soft','physical_capacity'],default='weighted_soft');parser.add_argument('--near-ns',type=float,default=0.)
    a=parser.parse_args();started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));assert shutil.disk_usage(D).free>=80*1024**3
    b=a.batch.resolve();b.mkdir(exist_ok=False);initial=a.initial_state.resolve();assert read(initial/'completion.json')['passed']
    policies=['strict','endpoint_vector'] if a.policy=='both' else [a.policy]
    scripts=['current_sta_selector.py','endpoint_timing_policy.py','run_current_endpoint_queries_v2.py','audit_current_sta_queries.py','run_current_relaxed_queries_v2.py','run_current_joint_search.py','prepare_native_scope_request.py','run_native_objective_state_analysis.py','audit_native_objective.py','run_endpoint_state_analysis.py']
    files=[Path(__file__),*[D/n for n in scripts],D/'native_objective_stage_01/binding.json',D/'native_current_sta_scope_policy_experiment_01.json',initial/'completion.json',initial/'endpoint_vector.json'];bindings={str(p):sha(p) for p in files}
    write(b/'registration.json',dict(status='registered_before_work',initial_state=str(initial),policies=policies,scope=a.scope,objective=a.objective,near_ns=a.near_ns,source_sha256=bindings,
      pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
      question='Can current-STA selection, automatic affected-branch scope and native free-path transactions advance each independent exact acceptance policy?',
      candidate_order='Single targets with audited capacity gain first; then joint targets with audited relaxed gain and compatible paths. Query paths identify scope only; native chooses all replacement paths.',
      timing='Every child fromPopen toterminal; controller monotonic total includes preparations, failures, validation, caching, decisions and rollback. Reused historical costs are separately identified.',
      limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),no_overall_step_or_date_cap=True))
    calls=[];decisions=[];attempts=[];outcomes={};receipts=[];queries={};joint={};native_cache={};evaluations={}
    histories=list((D/'native_endpoint_vector_dev_01').glob('*/completion.json'))+list((D/'joint_endpoint_diagnostics_01').glob('*/completion.json'))
    histories+=list(D.glob('current_sta_policy_*/evaluation_*/completion.json'))+list(D.glob('*/*_evaluation/completion.json'))+list(D.glob('plateau_successor_evaluation_01/*/completion.json'))
    histories+=list(D.glob('current_sta_policy_native_*/attempt_*/evaluation/completion.json'))
    for path in histories:
        complete=read(path)
        if complete.get('passed') and complete.get('full_precision_cpd_s') is not None and (path.parent/'endpoint_vector.json').exists():evaluations[state_key(path.parent)]=path.parent
    evaluations[state_key(initial)]=initial
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
        calls.append(dict(tag=tag,command=command,status=status,returncode=code,complete_process_seconds=time.monotonic()-t));write(b/'process_costs.json',calls)
        return status=='completed'
    def get_queries(current,key):
        if key in queries:return queries[key]
        source=run_dir(current);selection=select(source/'native_sta_frontier.jsonl',a.near_ns)
        for history in sorted(D.glob('current_sta_policy_*/queries_*/analysis.json')):
            old=history.parent
            if old.is_relative_to(b) or read(old/'selection.json')['targets']!=selection['targets']:continue
            prior=Path(read(old/'execution_registration.json')['input_run'])
            if route_body(prior/'routed.route')!=route_body(source/'routed.route') or input_identity(prior)!=input_identity(source):continue
            ex=read(old/'execution.json');an=read(history);assert an['passed'] and all(sha(p)==h for p,h in an['source_sha256'].items())
            assert all(sha(p)==h for p,h in ex['source_sha256'].items()) and all(sha(old/p)==h for p,h in ex['output_sha256'].items())
            receipts.append(dict(kind='capacity_queries',source=str(old),source_sha256=sha(history)));write(b/'reuse_receipts.json',receipts);queries[key]=old;return old
        q=b/f'queries_{len(queries):03d}'
        ok=invoke('run_current_endpoint_queries_v2.py',['--state',current,'--batch',q,'--near-ns',a.near_ns],q.name)
        if ok:ok=invoke('audit_current_sta_queries.py',['--batch',q],q.name+'_audit')
        queries[key]=q if ok else None;return queries[key]
    def get_joint(key,q):
        if key in joint:return joint[key]
        work=b/f'joint_{len(joint):03d}';work.mkdir();relaxed=work/'relaxed';search=work/'search'
        ok=invoke('run_current_relaxed_queries_v2.py',['--capacity-batch',q,'--batch',relaxed],work.name+'_relaxed')
        if ok:ok=invoke('audit_current_sta_queries.py',['--batch',relaxed],work.name+'_audit')
        if ok:ok=invoke('run_current_joint_search.py',['--queries',relaxed,'--batch',search],work.name+'_search')
        opportunity=search/'current/opportunity.json';joint[key]=opportunity if ok and opportunity.exists() and read(opportunity)['status']=='compatible' else None
        return joint[key]
    def candidate(current,key,single=None,opportunity=None):
        work=b/f'attempt_{len(attempts):03d}';tag=work.name;source=run_dir(current)
        record=dict(work=str(work),source_state=str(current),single=single,opportunity=None if opportunity is None else str(opportunity));attempts.append(record)
        args=['--state',current,'--batch',work,'--scope',a.scope,'--objective',a.objective,'--near-ns',a.near_ns]
        args+=['--single',*single] if single else ['--opportunity',opportunity]
        if not invoke('prepare_native_scope_request.py',args,tag+'_scope'):
            record['status']='scope_generation_failed';write(b/'attempts.json',attempts);return None,record
        request=work/'candidate.txt';reuse_key=(key,sha(request),a.objective)
        if reuse_key in native_cache:
            previous,origin=native_cache[reuse_key];record.update(status='reused_identical_native_attempt',reuse_source=origin);write(b/'attempts.json',attempts);return previous,record
        ok=invoke('run_native_objective_state_analysis.py',['--source',source,'--batch',work/'candidate','--native-cases',request,'--objective',a.objective],tag+'_native')
        if ok:ok=invoke('audit_native_objective.py',['--batch',work,'--role','candidate'],tag+'_audit')
        audit=read(work/'candidate_audit/analysis.json') if ok else {}
        if not audit.get('candidate_route'):
            record.update(status='transaction_failed_rolled_back' if ok else 'native_or_audit_failed');native_cache[reuse_key]=(None,str(work));write(b/'attempts.json',attempts);return None,record
        vector=read(current/'endpoint_vector.json');route=Path(audit['candidate_route']);evalkey=json.dumps([route_body(route),input_identity(source),vector['constraints_sha256']],sort_keys=True)
        state=evaluations.get(evalkey);reused=state is not None
        if reused:
            rd=run_dir(state);assert read(rd/'analysis_gate.json')['passed'] and read(rd/'independent_audit.json')['audit']['passed']
            assert route_body(rd/'routed.route')==route_body(route) and input_identity(rd)==input_identity(source)
            for path,value in read(source/'manifest.json')['shared_inputs'].items():assert sha(path)==value['sha256']
            assert sha(read(rd/'manifest.json')['command'][0])==read(D/'native_endpoint_vector_stage_01/binding.json')['binary_sha256']
            receipts.append(dict(kind='FULL_STA',source=str(state),completion_sha256=sha(state/'completion.json'),route_body_sha256=route_body(route)));write(b/'reuse_receipts.json',receipts)
        else:
            state=work/'evaluation';ok=invoke('run_endpoint_state_analysis.py',['--source',source,'--batch',state,'--candidate-route',route],tag+'_evaluation')
            if not ok:record['status']='evaluation_failed_original_retained';write(b/'attempts.json',attempts);return None,record
            assert read(state/'completion.json')['passed'];evaluations[evalkey]=state
        record.update(status='legal_candidate',evaluated_state=str(state),reused_evaluation=reused,native_attempts=len(audit['attempts']),native_queries=len(audit['queries']))
        native_cache[reuse_key]=(state,str(work));write(b/'attempts.json',attempts);return state,record
    for policy in policies:
        current=initial;visited={state_key(initial)};steps=0
        while True:
            key=state_key(current);rd=run_dir(current);selection=select(rd/'native_sta_frontier.jsonl',a.near_ns)
            write(b/f'{policy}_state_{steps:03d}.json',dict(state=str(current),state_identity=hashlib.sha256(key.encode()).hexdigest(),selection=selection))
            q=get_queries(current,key)
            if q is None:outcomes[policy]=dict(state=str(current),status='query_generation_failed',accepted_steps=steps);break
            rank={(r['net'],r['pin']):i for i,r in enumerate(selection['targets'])};rows=read(q/'analysis.json')['results']
            singles=[(r['net'],r['pin']) for r in sorted(rows,key=lambda r:rank[r['net'],r['pin']]) if r['improvement_ns']>1e-6]
            def candidates():
                for target in singles:yield candidate(current,key,single=target)
                op=get_joint(key,q)
                if op:yield candidate(current,key,opportunity=op)
            accepted=False
            for state,record in candidates():
                if state is None:
                    decisions.append(dict(policy=policy,step=steps,source_state=str(current),attempt=record,accepted=False,reason=record['status']));write(b/'decisions.json',decisions);continue
                candidatekey=state_key(state);result=decide(policy,read(current/'endpoint_vector.json'),read(state/'endpoint_vector.json'),True,candidatekey in visited)
                before=current;t=time.monotonic()
                if result['accepted']:current=state;visited.add(candidatekey);accepted=True
                rollback_seconds=0. if accepted else time.monotonic()-t
                decisions.append(dict(policy=policy,step=steps,source_state=str(before),evaluated_state=str(state),attempt=str(record['work']),decision=result,rollback_seconds=rollback_seconds));write(b/'decisions.json',decisions)
                write(b/(policy+'_current.json'),dict(state=str(current),cpd_s=read(current/'endpoint_vector.json')['cpd_s']))
                if accepted:print(dict(policy=policy,accepted_step=steps,cpd_ns=read(current/'endpoint_vector.json')['cpd_s']*1e9),flush=True);break
            if not accepted:
                outcomes[policy]=dict(state=str(current),status='current_operator_exhausted',accepted_steps=steps,cpd_s=read(current/'endpoint_vector.json')['cpd_s'],scope='This selector/objective/scope operator only; not an overall research stop.');break
            steps+=1
    assert all(sha(p)==h for p,h in bindings.items())
    write(b/'completion.json',dict(status='native_scope_policy_terminal',outcomes=outcomes,complete_orchestrator_seconds=time.monotonic()-started,complete_child_process_seconds=sum(r['complete_process_seconds'] for r in calls),
      source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'process_costs.json',b/'attempts.json',b/'decisions.json',b/'reuse_receipts.json'] if p.exists()},
      qualification='Complete measured controller with shared exact-history reuse. Not independent cold-start policy runtimes; reused work remains separately attributed. No overall research date/count cap.'))
    print(outcomes,flush=True)

if __name__=='__main__':main()
