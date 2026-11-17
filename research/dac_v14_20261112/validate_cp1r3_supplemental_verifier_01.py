"""Validate an isolated audit rule; never execute a frozen verifier or native job."""
import ast
import copy
import json
from pathlib import Path
from owner_registration_transition_v1 import verify_transition,digest
from cp1r3_supplemental_verifier_v1 import D,COHORT,FROZEN_SHA,SEAL,OUTPUT_COUNTS,read,write,sha,transformed_verifier


def main():
    out=D/'CP1r3_supplemental_verifier_validation_01';assert not (out/'validation.json').exists()
    release=Path(read(COHORT/'plan.json')['release']);verifier=release/'runtime/verify_complete_unified_method_v1.py'
    assert sha(verifier)==FROZEN_SHA;source=verifier.read_text();tree,shape=transformed_verifier(source)
    compile(tree,str(verifier),'exec')
    class Reverse(ast.NodeTransformer):
        def visit_Assert(self,node):
            if isinstance(node.test,ast.Call) and isinstance(node.test.func,ast.Name) and node.test.func.id=='__audit_owner_binding':
                node.test=ast.parse(SEAL,mode='eval').body;return node
            return self.generic_visit(node)
        def visit_Name(self,node):
            if node.id=='__audit_output':node.id='root'
            return node
    assert ast.dump(Reverse().visit(copy.deepcopy(tree)))==ast.dump(ast.parse(source))
    guards=0
    for changed in [source.replace("prep['registration_sha256']==sha(tx/'registration.json')",'True'),
                    source.replace("root/'queue/status.json'","root/'different_status.json'"),
                    source.replace("write(root/'queue/status.json',dict(status='terminal',passed=True));",'')]:
        rejected=False
        try:transformed_verifier(changed)
        except AssertionError:rejected=True
        assert rejected;guards+=1
    case=Path(read(COHORT/'plan.json')['inputs'][0]['workspace'])/'native'
    parent=read(case/'flow/resource_flow/repair/registration.json')
    runtime=case/'flow/resource_flow/phase_runtime.json';runtime_bytes=runtime.read_bytes();rows=[]
    for rank in range(3):
        tx=case/f'flow/resource_flow/repair/round_004/owner_{rank:02d}'
        data=(tx/'registration.json').read_bytes();actual=json.loads(data)
        prep=read(tx/'preparation.json');execution=read(tx/'execution_registration.json')
        row=verify_transition(data,prep,execution,parent,runtime,runtime_bytes)
        assert row['mode']=='exact_documented_pre_execution_runtime_binding';rows.append(row)
        mutations=[]
        m=copy.deepcopy(actual);m['roles']['joint_native']['queries'][0]['pin']+=1;mutations.append((m,prep,execution,parent,runtime_bytes))
        m=copy.deepcopy(actual);m['unregistered_extra_field']=True;mutations.append((m,prep,execution,parent,runtime_bytes))
        m=copy.deepcopy(actual);m['runtime_config']=str(runtime)+'.other';mutations.append((m,prep,execution,parent,runtime_bytes))
        m=copy.deepcopy(actual);m['source_sha256'][str(runtime)]='0'*64;mutations.append((m,prep,execution,parent,runtime_bytes))
        m=copy.deepcopy(prep);m['passed']=False;mutations.append((actual,m,execution,parent,runtime_bytes))
        m=copy.deepcopy(prep);m['transaction_registered']=False;mutations.append((actual,m,execution,parent,runtime_bytes))
        m=copy.deepcopy(parent);m['source_sha256'][str(runtime)]='0'*64;mutations.append((actual,prep,execution,m,runtime_bytes))
        mutations.append((actual,prep,execution,parent,runtime_bytes+b'\n'))
        for changed,pre,exe,par,runbytes in mutations:
            # Re-seal the changed execution bytes: these tests must catch an
            # unauthorized transition, not merely a stale execution digest.
            changed_bytes=(json.dumps(changed,indent=2)+'\n').encode()
            resealed=copy.deepcopy(exe);resealed['registration_sha256']=digest(changed_bytes)
            rejected=False
            try:verify_transition(changed_bytes,pre,resealed,par,runtime,runbytes)
            except (AssertionError,KeyError):rejected=True
            assert rejected;guards+=1
        bad=copy.deepcopy(execution);bad['registration_sha256']='0'*64
        rejected=False
        try:verify_transition(data,prep,bad,parent,runtime,runtime_bytes)
        except AssertionError:rejected=True
        assert rejected;guards+=1
        exact=copy.deepcopy(prep);exact['registration_sha256']=digest(data)
        assert verify_transition(data,exact,execution,parent,runtime,runtime_bytes)['mode']=='unchanged_preparation_and_execution_bytes'
    wrapper=(D/'cp1r3_supplemental_verifier_v1.py').read_text()
    assert wrapper.index("assert terminal.exists()")<wrapper.index('fcntl.flock(serial')<wrapper.index("audit.mkdir(parents=True)")<wrapper.index('exec(compile(tree')
    assert 'fcntl.LOCK_EX|fcntl.LOCK_NB' in wrapper
    out.mkdir(exist_ok=True)
    write(out/'validation.json',dict(passed=True,registered_observed_native_owner_rows=len(rows),
        negative_guards=guards,synthetic_in_memory_tests_not_experiments=True,
        exact_reversible_AST_transform=True,all_original_assertions_retained=shape['assertions_retained'],
        bytecode_compilation_passed=True,original_frozen_verifier_executed=False,
        actual_full_reverification_performed=False,new_native_or_STA_calls=0,new_queue_owner=False,
        current_cohort_and_downstream_owners_unchanged=True,
        source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'owner_registration_transition_v1.py',D/'cp1r3_supplemental_verifier_v1.py',verifier]},
        qualification='Small immutable owner metadata, reversible AST shape, compilation and adversarial in-memory guards only. This is not a whole-verifier replay, byte/STA audit, experiment completion, adapter admission or benefit evidence.'))
    print(dict(passed=True,actual_metadata_rows=len(rows),negative_guards=guards,
               all_original_assertions=shape['assertions_retained'],whole_reverification=False,native_or_STA_calls=0))


if __name__=='__main__':main()
