#!/usr/bin/env python3
"""Branch-local current-STA repair with immutable transactions and exact gates.

A pass exhausted under one selector/operator is a local terminal result, never
an overall research stop. Precomputed automatic joint transactions are consumed
only at their exact source state. Changed states always get fresh selection.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import os
import signal
import sys
import time
from retained_prefix_workflow import D,read,write,sha,route_body
from current_sta_selector import select
from endpoint_timing_policy import decide


def state_identity(state):
    done=read(state/'completion.json');assert done['passed']
    rd=Path(done['run']);v=read(state/'endpoint_vector.json')
    return hashlib.sha256(json.dumps([route_body(rd/'routed.route'),sha(rd/'packed.net'),sha(rd/'placed.place'),
        v['constraints_sha256'],sha(D/'native_endpoint_vector_stage_01/binding.json')]).encode()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--initial-state',type=Path,required=True);p.add_argument('--batch',type=Path,required=True)
    p.add_argument('--single-only',action='store_true');p.add_argument('--near-ns',type=float,default=0.);p.add_argument('--joint-native',type=Path);p.add_argument('--joint-state',type=Path)
    a=p.parse_args();started=time.monotonic();b=a.batch.resolve();b.mkdir(exist_ok=False)
    initial=a.initial_state.resolve();initial_id=state_identity(initial)
    assert bool(a.joint_native)==bool(a.joint_state)
    joint=None
    if a.joint_native:
        native=read(a.joint_native/'completion.json');assert native['passed']
        transaction=read(a.joint_native/'registration.json')
        assert route_body(Path(native['input_run'])/'routed.route')==route_body(Path(read(initial/'completion.json')['run'])/'routed.route')
        assert route_body(Path(read(a.joint_state/'completion.json')['run'])/'routed.route')==route_body(Path(native['candidate_run'])/'routed.route')
        joint=dict(state=str(a.joint_state.resolve()),targets=native['targets'],source_identity=initial_id,
                   origin=str(a.joint_native.resolve()),provenance='Previously automatically STA-selected and CBS-generated joint transaction, exact original route match.')
    files=[Path(__file__),D/'run_current_endpoint_queries_v2.py',D/'current_sta_selector.py',D/'endpoint_timing_policy.py',
           D/'run_endpoint_state_analysis.py',D/'audit_current_sta_queries.py',D/'run_current_relaxed_queries.py',D/'run_current_joint_search.py',D/'run_current_sta_transaction.py',initial/'completion.json',initial/'endpoint_vector.json']
    if joint:files += [a.joint_native/'completion.json',a.joint_native/'registration.json',a.joint_state/'completion.json',a.joint_state/'endpoint_vector.json']
    bindings={str(p):sha(p) for p in files}
    write(b/'registration.json',dict(status='registered_before_queries',initial_state=str(initial),initial_identity=initial_id,
        policies=['strict','endpoint_vector'],near_ns=a.near_ns,single_only=a.single_only,source_sha256=bindings,joint_reuse=joint,
        question='Can exact CPD and fixed-endpoint Pareto branches advance autonomously with fresh STA selection after each acceptance?',
        controls='Same initial state, selector, capacity search, tree scope and available candidate opportunities. This is not yet the native-router control.',
        acceptance='Exact full-precision native CPD and endpoint/domain values, fixed applied constraints, no increasing hold violation; zero tolerance.',
        limits='Per-process 1800 seconds, existing memory/disk guards; no total research count/date limit.',
        duplicate_rule='Exact current state plus candidate route body; duplicates skipped. Shared cached evaluations do not couple acceptance policies.'))
    calls=[];query_cache={};eval_cache={};joint_cache={};decisions=[];outcomes={};reuse_receipts=[]
    # Reuse previous observations only when the route, inputs and analyzer agree.
    known=list((D/'native_endpoint_vector_dev_01').glob('*/completion.json'))+list((D/'joint_endpoint_diagnostics_01').glob('*/completion.json'))
    known+=list(D.glob('current_sta_policy_*/evaluation_*/completion.json'))+list(D.glob('current_sta_*_joint_evaluation_*/completion.json'))
    for path in known:
        state=path.parent;done=read(path)
        if not done.get('passed') or done.get('full_precision_cpd_s') is None:continue
        rd=Path(done['run']);v=read(state/'endpoint_vector.json')
        key=(route_body(rd/'routed.route'),sha(rd/'packed.net'),sha(rd/'placed.place'),v['constraints_sha256'])
        # Completion-sealed data; FULL and unchanged physical input checks required.
        assert read(rd/'analysis_gate.json')['passed']
        eval_cache[key]=state
    def invoke(command,tag):
        t=time.monotonic()
        with (b/(tag+'.log')).open('w') as log:
            try:
                proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                code=proc.wait(timeout=1800)
                status='completed' if code==0 else 'failed'
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGTERM)
                try:code=proc.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
                status='timeout'
        calls.append(dict(tag=tag,command=command,status=status,returncode=code,complete_process_seconds=time.monotonic()-t))
        write(b/'process_costs.json',calls)
        return status=='completed'
    def produce_joint(current,current_id,q):
        if current_id in joint_cache:return joint_cache[current_id]
        source=Path(read(current/'completion.json')['run'])
        # Reuse an automatically generated transaction only for exactly the same
        # current route/packing/placement. Manual repaired starts are not imported.
        histories=list(D.glob('native_frontier_transaction_*_01'))+list(D.glob('current_sta_*_transaction_*'))
        target_pool={(r['net'],r['pin']) for r in select(source/'native_sta_frontier.jsonl',a.near_ns)['targets']}
        for old in histories:
            if not (old/'analysis.json').exists():continue
            old_result=read(old/'analysis.json')
            if not old_result.get('passed') or not old_result.get('candidate_route'):continue
            old_source=Path(old_result['input_run'])
            if route_body(source/'routed.route')!=route_body(old_source/'routed.route'):continue
            if any(sha(source/n)!=sha(old_source/n) for n in ['packed.net','placed.place']):continue
            targets=old_result.get('targets',[])
            if not targets or not {(t['net'],t['pin']) for t in targets}<=target_pool:continue
            assert sha(old_result['candidate_route'])==old_result['candidate_sha256']
            assert all(sha(p)==h for p,h in old_result['source_sha256'].items())
            candidate=dict(route=old_result['candidate_route'],targets=targets,kind='automatic_joint_transaction_reuse',transaction=str(old))
            joint_cache[current_id]=candidate
            reuse_receipts.append(dict(kind='joint_transaction',current_identity=current_id,source=str(old),analysis_sha256=sha(old/'analysis.json')))
            write(b/'reuse_receipts.json',reuse_receipts)
            return candidate
        work=b/f'joint_{len(joint_cache):03d}';work.mkdir()
        relaxed=work/'relaxed'
        ok=invoke([sys.executable,str(D/'run_current_relaxed_queries.py'),'--capacity-batch',str(q),'--batch',str(relaxed)],work.name+'_relaxed')
        if ok:ok=invoke([sys.executable,str(D/'audit_current_sta_queries.py'),'--batch',str(relaxed)],work.name+'_relaxed_audit')
        search=work/'search'
        if ok:ok=invoke([sys.executable,str(D/'run_current_joint_search.py'),'--queries',str(relaxed),'--batch',str(search)],work.name+'_search')
        opportunity=search/'current/opportunity.json'
        if not ok or not opportunity.exists() or read(opportunity)['status']!='compatible':
            joint_cache[current_id]=None;return None
        transaction=work/'transaction'
        ok=invoke([sys.executable,str(D/'run_current_sta_transaction.py'),'--opportunity',str(opportunity),'--batch',str(transaction)],work.name+'_transaction')
        result=read(transaction/'analysis.json') if ok else {}
        candidate=None
        if result.get('candidate_route'):
            candidate=dict(route=result['candidate_route'],targets=result['targets'],kind='current_STA_joint_transaction',transaction=str(transaction))
        joint_cache[current_id]=candidate
        return candidate
    for policy in ['strict','endpoint_vector']:
        current=initial;current_id=initial_id;seen=set();visited={current_id};steps=0
        while True:
            rd=Path(read(current/'completion.json')['run']);vector=read(current/'endpoint_vector.json')
            selection=select(rd/'native_sta_frontier.jsonl',a.near_ns)
            event=dict(policy=policy,step=steps,state=str(current),state_identity=current_id,selection=selection)
            write(b/f'{policy}_state_{steps:03d}.json',event)
            if current_id not in query_cache:
                for history in sorted(D.glob('current_sta_policy_*/queries_*/analysis.json')):
                    old=history.parent
                    if old.is_relative_to(b):continue
                    old_source=Path(read(old/'execution_registration.json')['input_run'])
                    if read(old/'selection.json')['targets']!=selection['targets']:continue
                    if route_body(old_source/'routed.route')!=route_body(rd/'routed.route'):continue
                    if any(sha(old_source/n)!=sha(rd/n) for n in ['packed.net','placed.place']):continue
                    ex=read(old/'execution.json');an=read(history)
                    assert an['passed'] and all(sha(p)==h for p,h in an['source_sha256'].items())
                    assert all(sha(p)==h for p,h in ex['source_sha256'].items())
                    assert all(sha(old/p)==h for p,h in ex['output_sha256'].items())
                    query_cache[current_id]=(old,True)
                    reuse_receipts.append(dict(kind='capacity_queries',current_identity=current_id,source=str(old),analysis_sha256=sha(history)))
                    write(b/'reuse_receipts.json',reuse_receipts)
                    break
            if current_id not in query_cache:
                q=b/f'queries_{len(query_cache):03d}'
                ok=invoke([sys.executable,str(D/'run_current_endpoint_queries_v2.py'),'--state',str(current),'--batch',str(q),'--near-ns',str(a.near_ns)],q.name)
                if ok:ok=invoke([sys.executable,str(D/'audit_current_sta_queries.py'),'--batch',str(q)],q.name+'_audit')
                query_cache[current_id]=(q,ok)
            q,ok=query_cache[current_id]
            if not ok:
                outcomes[policy]=dict(state=str(current),status='candidate_generation_failed',scope='This branch pass only');break
            rows=read(q/'analysis.json')['results'];rank={(r['net'],r['pin']):i for i,r in enumerate(selection['targets'])}
            candidates=[dict(route=r['candidate_route'],targets=[dict(net=r['net'],pin=r['pin'])],kind='single_capacity') for r in sorted(rows,key=lambda r:rank[r['net'],r['pin']]) if r.get('candidate_route')]
            if joint and current_id==joint['source_identity']:
                candidates.append(dict(state=joint['state'],route=str(Path(read(Path(joint['state'])/'completion.json')['run'])/'routed.route'),targets=joint['targets'],kind='automatic_joint_reuse'))
            accepted=False
            def ordered_candidates():
                yield from candidates
                if not a.single_only and not (joint and current_id==joint['source_identity']):
                    extra=produce_joint(current,current_id,q)
                    if extra:yield extra
            for candidate in ordered_candidates():
                body=route_body(candidate['route']);key=(current_id,body)
                if key in seen:continue
                seen.add(key);begin=time.monotonic();reuse=False
                eval_key=(body,sha(rd/'packed.net'),sha(rd/'placed.place'),vector['constraints_sha256'])
                state=eval_cache.get(eval_key)
                if state:reuse=True
                else:
                    state=b/f'evaluation_{len(calls):03d}'
                    ok=invoke([sys.executable,str(D/'run_endpoint_state_analysis.py'),'--source',str(rd),'--batch',str(state),'--candidate-route',candidate['route']],state.name)
                    if not ok:
                        decisions.append(dict(policy=policy,source_identity=current_id,candidate=candidate,accepted=False,reason='Failed/timeout evaluation; current immutable state retained',cost_seconds=time.monotonic()-begin))
                        write(b/'decisions.json',decisions);continue
                    eval_cache[eval_key]=state
                candidate_id=state_identity(state)
                result=decide(policy,vector,read(state/'endpoint_vector.json'),read(state/'completion.json')['passed'],candidate_id in visited)
                rollback_start=time.monotonic()
                if result['accepted']:
                    current=state;current_id=candidate_id;visited.add(current_id);accepted=True
                # Rollback is retaining the previous immutable state pointer.
                rollback_seconds=0. if accepted else time.monotonic()-rollback_start
                decisions.append(dict(policy=policy,step=steps,source_state=event['state'],source_identity=event['state_identity'],
                    candidate=candidate,evaluated_state=str(state),reused_evaluation=reuse,decision=result,
                    rollback_seconds=rollback_seconds,decision_complete_seconds=time.monotonic()-begin))
                write(b/'decisions.json',decisions)
                write(b/(policy+'_current.json'),dict(state=str(current),identity=current_id,cpd_s=read(current/'endpoint_vector.json')['cpd_s']))
                if accepted:break  # Mandatory fresh selection on the accepted state's STA.
            if not accepted:
                outcomes[policy]=dict(state=str(current),identity=current_id,status='current_operator_exhausted',
                    cpd_s=vector['cpd_s'],accepted_steps=steps,scope='This selector window and available operators only; continue research by changing mechanism/scope.')
                break
            steps+=1
    assert all(sha(p)==h for p,h in bindings.items())
    write(b/'completion.json',dict(status='policy_pass_terminal',outcomes=outcomes,process_calls=len(calls),
        complete_process_seconds=sum(r['complete_process_seconds'] for r in calls),complete_orchestrator_seconds=time.monotonic()-started,
        qualification='Includes new query/audit/native evaluation/failures. Reused historical work charged separately through provenance, never treated as a zero-cost end-to-end algorithm measurement.',
        source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'process_costs.json',b/'decisions.json',b/'reuse_receipts.json'] if p.exists()}))
    print(outcomes,flush=True)

if __name__=='__main__':main()
