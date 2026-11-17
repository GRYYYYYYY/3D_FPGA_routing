"""Small scope/AST checks only; no graph, raw vector or native execution."""
import ast
import copy
import inspect
import textwrap
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from lstm_failed_scope_audit_v1 import metadata_gate,TX,AUDIT,transform_frozen_tree,transformed_raw_transaction
from cp1r3_supplemental_verifier_v2 import transformed_verifier,FROZEN_SHA
import cp1r3_raw_admission_v1 as raw


def main():
    out=D/'LSTM_domain_whole_admission_03/metadata_validation_02.json'
    assert not out.exists()
    attempts=read(TX.parent.parent/'attempts.json')
    i=next(i for i,a in enumerate(attempts) if a['transaction']==str(TX))
    values=[str(TX),read(TX/'completion.json'),read(TX/'progress.json'),read(TX/'registration.json'),
            attempts[i],attempts[i+1],read(TX.parent.parent/'steps.json'),read(AUDIT)]
    assert metadata_gate(*values)
    rows=[]
    for name,change in [
        ('fallback_failure',lambda p:p['reuse_off'].update(status='FULL_STA_failed')),
        ('fallback_accepted',lambda p:p['reuse_off']['policies']['resources_under_timing'].update(accepted=True)),
        ('failed_role_adopted',lambda p:p['reuse_on'].update(accepted=True)),
        ('failed_role_relabelled',lambda p:p['reuse_on'].update(status='legal_evaluated'))]:
        mutated=copy.deepcopy(values);change(mutated[2])
        # Reseal all duplicate metadata views, so the test must reject the
        # unauthorized outcome, not merely a stale duplicate dictionary.
        mutated[1]['roles']=copy.deepcopy(mutated[2]);mutated[4]['roles']=copy.deepcopy(mutated[2])
        try:metadata_gate(*mutated)
        except (AssertionError,KeyError):rows.append(dict(name=name,duplicate_views_resealed=True,rejected=True))
        else:raise AssertionError(name)
    verifier=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1r3/runtime/verify_complete_unified_method_v1.py')
    assert sha(verifier)==FROZEN_SHA
    base,_=transformed_verifier(verifier.read_text())
    tree,shape,_=transform_frozen_tree(copy.deepcopy(base))
    class UndoFrozen(ast.NodeTransformer):
        def visit_Assert(self,node):
            if (isinstance(node.test,ast.BoolOp) and isinstance(node.test.op,ast.Or)
                and isinstance(node.test.values[-1],ast.Call)
                and isinstance(node.test.values[-1].func,ast.Name)
                and node.test.values[-1].func.id=='__audit_known_closed_scope'):
                node.test=node.test.values[0]
            return self.generic_visit(node)
        def visit_If(self,node):
            if isinstance(node.test,ast.Call) and isinstance(node.test.func,ast.Name) and node.test.func.id=='__audit_known_failed_role':return None
            return self.generic_visit(node)
    assert ast.dump(UndoFrozen().visit(copy.deepcopy(tree)))==ast.dump(base)
    captured=[];original_fix=ast.fix_missing_locations
    def capture(node):
        captured.append(copy.deepcopy(node));return original_fix(node)
    try:
        ast.fix_missing_locations=capture
        _,rawshape=transformed_raw_transaction(raw)
    finally:ast.fix_missing_locations=original_fix
    assert len(captured)==1
    class UndoRaw(ast.NodeTransformer):
        def visit_Assert(self,node):
            test=node.test
            if isinstance(test,ast.IfExp):node.test=test.orelse
            elif isinstance(test,ast.BoolOp) and isinstance(test.op,ast.Or):node.test=test.values[0]
            elif (isinstance(test,ast.BoolOp) and isinstance(test.op,ast.And)
                  and isinstance(test.values[0],ast.BoolOp) and isinstance(test.values[0].op,ast.Or)):
                test.values[0]=test.values[0].values[0]
            return self.generic_visit(node)
        def visit_Assign(self,node):
            if (len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
                and node.targets[0].id=='evaluated' and isinstance(node.value,ast.Call)
                and isinstance(node.value.args[0],ast.IfExp)):
                return ast.parse("evaluated=self.state(row['evaluation'],flow)").body[0]
            return self.generic_visit(node)
    untouched=ast.parse(textwrap.dedent(inspect.getsource(raw.Audit.transaction)))
    assert ast.dump(UndoRaw().visit(captured[0]))==ast.dump(untouched)
    for name in ['lstm_failed_scope_audit_v1.py','cp1r3_supplemental_verifier_v3.py','audit_lstm_domain_raw_03.py',
                 'match_lstm_admitted_pair_03.py','queue_lstm_domain_whole_admission_03.py']:
        compile((D/name).read_text(),str(D/name),'exec')
    write(out,dict(passed=True,actual_metadata_positive_case=True,negative_resealed_cases=rows,
                   original_frozen_AST_exact_reverse=True,original_raw_transaction_AST_exact_reverse=True,
                   normal_native_fallback_path_unmodified=True,frozen_shape=shape,raw_shape=rawshape,
                   actual_whole_verifier_executed=False,graph_or_raw_vector_reads=False,new_native_or_STA_calls=0,
                   source_sha256={str(D/n):sha(D/n) for n in ['validate_lstm_domain_whole_admission_03.py',
                       'lstm_failed_scope_audit_v1.py','cp1r3_supplemental_verifier_v3.py','audit_lstm_domain_raw_03.py',
                       'match_lstm_admitted_pair_03.py','queue_lstm_domain_whole_admission_03.py',
                       'cp1r3_supplemental_verifier_v2.py','cp1r3_raw_admission_v1.py']}))
    print(dict(passed=True,resealed_negative_cases=len(rows),frozen_and_raw_AST_exactly_reversible=True,
               original_frozen_assert_nodes=shape['original_assert_nodes_retained'],whole_verification=False))


if __name__=='__main__':
    main()
