"""Exact posthoc checks for one independently audited, never-adopted scope.

Historical completion/role values are never replaced. Normal roles retain their
original checks, including the legal native fallback in the same transaction.
This module does not run native routing/STA or write any historical result.
"""
import ast
import copy
import inspect
import textwrap
from pathlib import Path
from retained_prefix_workflow import D, read, route_body
from recovery_prefix_v1 import Evidence

FLOW=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/cp1r3_distinct_input_cohort_01/lstm/domain/flow')
TX=FLOW/'resource_flow/repair/round_013/candidate_00'
EVALUATION=TX/'reuse_on_evaluation'
AUDIT=D/'LSTM_necessary_readonly_02/domain_failed_evaluation/audit.json'


def metadata_gate(tx,closed,progress,registration,attempt,following,steps,audit):
    """Small-data gate; actual source closure is required separately below."""
    assert Path(tx).resolve()==TX
    assert closed['passed'] is False and closed['roles']==progress
    assert set(progress)==set(registration['roles'])=={'reuse_on','reuse_off'}
    bad,off=progress['reuse_on'],progress['reuse_off']
    assert bad['status']=='FULL_STA_failed' and bad['accepted'] is False
    assert off['status']=='legal_evaluated'
    assert off['policies']['resources_under_timing']['accepted'] is False
    assert attempt['transaction']==str(TX) and attempt['native_transaction_complete']
    assert attempt['roles']==progress
    assert not any(Path(s['transaction']).resolve()==TX for s in steps)
    assert following['current_state']==attempt['current_state']
    assert all(r['state']==attempt['current_state'] for r in registration['roles'].values())
    assert audit['passed'] and audit['kind']=='independent_raw_evidence_of_historically_failed_evaluation'
    assert audit['historical_status']=='FULL_STA_failed'
    assert audit['historical_completion_created'] is False
    assert audit['candidate_admitted_to_controller'] is False
    assert audit['whole_role_admitted'] is False and audit['clean_full_method_cost_admitted'] is False
    assert audit['new_native_or_STA_calls']==0
    q=audit['request']
    assert q['success'] and q['ordered_prefix_or_full_match']
    assert q['requested']==q['observed_queries']==q['successful_queries']==len(registration['roles']['reuse_on']['queries'])
    limits=registration['roles']['reuse_on']['fixed_resource_limits']
    assert limits==registration['roles']['reuse_off']['fixed_resource_limits']==audit['fixed_resource_limits']
    # This is an independent sufficient budget-rejection check, not a claim
    # that the original controller reached this policy after its seal failure.
    assert audit['resources']['wirelength']>limits['wirelength']
    assert audit['endpoints']['compatible'] and audit['endpoints']['hold_violation_regressions']==0
    return True


class KnownFailedScope:
    def __init__(self,audit_sha256,evidence=None):
        self.expected=audit_sha256
        self.e=Evidence() if evidence is None else evidence
        self.loaded=False
        self.events=[]

    def load(self):
        if self.loaded:return
        self.e.bind(AUDIT,self.expected)
        self.audit=read(AUDIT)
        assert self.audit['passed']
        self.e.verify(self.audit['source_sha256'])
        def doc(p):
            self.e.bind(p)
            return read(p)
        self.closed=doc(TX/'completion.json')
        self.progress=doc(TX/'progress.json')
        self.registration=doc(TX/'registration.json')
        attempts=doc(TX.parent.parent/'attempts.json')
        steps=doc(TX.parent.parent/'steps.json')
        i=next(i for i,a in enumerate(attempts) if a['transaction']==str(TX))
        self.attempt=attempts[i]
        metadata_gate(TX,self.closed,self.progress,self.registration,self.attempt,attempts[i+1],steps,self.audit)
        self.actor=doc(TX.parent.parent/'registration.json')
        assert self.actor['resource_limits']==self.audit['fixed_resource_limits']
        done=doc(FLOW/'completion.json')
        assert done['passed']
        for key in ['initial_state','resource_final_state','resource_policy_final_state','timing_initial_state','final_state']:
            assert Path(done[key]).resolve()!=EVALUATION
        assert not (EVALUATION/'completion.json').exists()
        assert not (EVALUATION/'runs/state/analysis_gate.json').exists()
        self.e.unchanged()
        self.loaded=True

    def closed_scope(self,tx,closed,attempt=None,repair=None):
        if Path(tx).resolve()!=TX:return False
        self.load()
        assert closed==self.closed
        if attempt is not None:assert attempt==self.attempt
        if repair is not None:assert Path(repair).resolve()==TX.parent.parent
        self.events.append(dict(kind='independent_failed_scope_gate',transaction=str(TX),historical_passed=False))
        return True

    def failed_role(self,tx,name,row,role,source=None,worker=None,limits=None):
        if row['status']!='FULL_STA_failed':return False
        assert Path(tx).resolve()==TX and name=='reuse_on'
        self.load()
        assert row==self.progress[name] and role==self.registration['roles'][name]
        if source is not None:
            source_path=source['state'] if isinstance(source,dict) else source
            assert Path(source_path).resolve()==Path(role['state']).resolve()
        if worker is not None:assert Path(worker).resolve()==TX/name
        if limits is not None:assert limits==self.audit['fixed_resource_limits']
        self.events.append(dict(kind='independent_rejected_failed_role',transaction=str(TX),role=name,
                           historical_status=row['status'],historical_evaluation_completion_created=False,
                           failed_candidate_never_adopted=True,wire_excess=self.audit['resources']['wirelength']-self.audit['fixed_resource_limits']['wirelength'],
                           native_fallback_must_still_follow_original_checks=True))
        return True

    def failed_values(self,tx,name,row,evaluated):
        assert self.failed_role(tx,name,row,self.registration['roles'][name])
        assert evaluated['rejected_failed_evaluation_only'] is True
        assert evaluated['resources']==self.audit['resources'] and evaluated['CPD_ns']==self.audit['CPD_ns']
        return True

    def rejected_state(self,state,flow):
        """Use the actual independent raw proof, never invent completion.json."""
        assert Path(state).resolve()==EVALUATION and Path(flow).resolve()==FLOW
        self.load()
        from cp1r3_raw_admission_v1 import vector_digest
        run=EVALUATION/'runs/state'
        self.e.bind(EVALUATION/'endpoint_vector.json')
        vector=read(EVALUATION/'endpoint_vector.json')
        self.e.bind(run/'manifest.json')
        manifest=read(run/'manifest.json')
        assert manifest['status']=='completed' and manifest['returncode']==0
        assert manifest['metrics']['native_full_check_passed']
        digest=self.e.bind(run/'native_sta_frontier.jsonl',vector['trace_sha256'])
        self.e.bind(str(run/'native_sta_frontier.jsonl')+'.constraints.echo',vector['constraints_sha256'])
        body=route_body(run/'routed.route')
        assert body==self.audit['route_body_sha256']
        assert vector['cpd_s']*1e9==self.audit['CPD_ns']
        assert not (EVALUATION/'completion.json').exists()
        return dict(state=str(EVALUATION),run=str(run),route_body_sha256=body,
                    packed_sha256=self.e.bind(run/'packed.net'),placed_sha256=self.e.bind(run/'placed.place'),
                    vector_semantic_sha256=vector_digest(vector),CPD_ns=self.audit['CPD_ns'],
                    constraints_sha256=vector['constraints_sha256'],raw_STA_sha256=digest,
                    resources=self.audit['resources'],actual_FULL_raw_STA_and_original_physical_proof_bound=True,
                    rejected_failed_evaluation_only=True,historical_completion_created=False,
                    historical_status='FULL_STA_failed',independent_raw_proof_revalidated=True)


def transform_frozen_tree(tree):
    """Two tracked changes; retain normal roles and all original assert nodes."""
    original=copy.deepcopy(tree)
    count=sum(isinstance(x,ast.Assert) for x in ast.walk(tree))
    closed_test=ast.dump(ast.parse("closed['passed']",mode='eval').body)
    rollback_test=ast.dump(ast.parse("row['status']=='transaction_failed_rolled_back'",mode='eval').body)
    class Change(ast.NodeTransformer):
        def __init__(self):self.closed=0;self.roles=0
        def visit_Assert(self,node):
            if ast.dump(node.test)==closed_test:
                self.closed+=1
                node.test=ast.BoolOp(op=ast.Or(),values=[node.test,ast.parse('__audit_known_closed_scope(tx,closed,attempt,repair)',mode='eval').body])
            return self.generic_visit(node)
        def visit_If(self,node):
            node=self.generic_visit(node)
            if ast.dump(node.test)==rollback_test:
                self.roles+=1
                extra=ast.parse("if __audit_known_failed_role(tx,name,row,role,source,worker,rreg['resource_limits']):\n resource_counts['rolled_back_candidates']+=1\n continue").body[0]
                return [extra,node]
            return node
    change=Change();result=change.visit(tree)
    assert change.closed==change.roles==1
    assert sum(isinstance(x,ast.Assert) for x in ast.walk(result))==count
    ast.fix_missing_locations(result)
    return result,dict(original_assert_nodes_retained=count,failed_scope_alternative_gates=1,
                       exact_failed_role_branches=1,normal_native_fallback_path_unchanged=True),original


def transformed_raw_transaction(base):
    """Keep original raw parsing/worker/fallback/domain checks at every role."""
    source=textwrap.dedent(inspect.getsource(base.Audit.transaction))
    tree=ast.parse(source);count=sum(isinstance(x,ast.Assert) for x in ast.walk(tree))
    patterns={k:ast.dump(ast.parse(v,mode='eval').body) for k,v in dict(
        closed="closed['passed']",status="row['status']=='legal_evaluated' and audit['candidate_route']",
        values="row['resources']==evaluated['resources'] and row['cpd_s']*1e9==evaluated['CPD_ns']").items()}
    class Change(ast.NodeTransformer):
        def __init__(self):self.n=dict(closed=0,status=0,values=0,evaluation=0)
        def visit_Assert(self,node):
            key=next((k for k,v in patterns.items() if ast.dump(node.test)==v),None)
            if key:
                self.n[key]+=1
                if key=='closed':node.test=ast.BoolOp(op=ast.Or(),values=[node.test,ast.parse('self.failed_scope.closed_scope(tx,closed)',mode='eval').body])
                elif key=='status':node.test=ast.parse("(row['status']=='legal_evaluated' or self.failed_scope.failed_role(tx,name,row,role,source,worker)) and audit['candidate_route']",mode='eval').body
                else:node.test=ast.IfExp(test=ast.parse("row['status']=='FULL_STA_failed'",mode='eval').body,
                    body=ast.parse('self.failed_scope.failed_values(tx,name,row,evaluated)',mode='eval').body,orelse=node.test)
            return self.generic_visit(node)
        def visit_Assign(self,node):
            if ast.dump(node)==ast.dump(ast.parse("evaluated = self.state(row['evaluation'],flow)").body[0]):
                self.n['evaluation']+=1
                return ast.parse("evaluated=self.state(EVALUATION if row['status']=='FULL_STA_failed' else row['evaluation'],flow)").body[0]
            return self.generic_visit(node)
    change=Change();result=change.visit(tree)
    assert change.n==dict(closed=1,status=1,values=1,evaluation=1),change.n
    assert sum(isinstance(x,ast.Assert) for x in ast.walk(result))==count
    ast.fix_missing_locations(result)
    namespace={**base.__dict__,'EVALUATION':EVALUATION}
    exec(compile(result,'<independent_exact_failed_scope_raw_transaction>','exec'),namespace)
    return namespace['transaction'],dict(original_raw_assert_nodes_retained=count,tracked_transformations=change.n,
                                        all_other_raw_methods_inherited=True,normal_native_fallback_checks_unchanged=True)
