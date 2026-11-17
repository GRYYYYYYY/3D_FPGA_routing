"""Exercise actual lifecycle helpers against the unchanged frozen seal assertion."""
import ast
import copy
import importlib.util
import json
import tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

out=D/'owner_registration_development_fix_02'
target=out/'validation.json';assert not target.exists()
patch=read(out/'source_patch.json')
assert all(sha(p)==h for p,h in patch['source_sha256'].items())
assert all(sha(p)==h for p,h in patch['development_source_sha256'].items())
module=out/'runtime/owner_runtime_registration_v2.py'
spec=importlib.util.spec_from_file_location('prospective_owner_runtime',module)
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
plan=read(D/'cp1r3_distinct_input_cohort_01/plan.json')
verifier=Path(plan['release'])/'runtime/verify_complete_unified_method_v1.py'
matches=[n for n in ast.walk(ast.parse(verifier.read_text())) if isinstance(n,ast.Assert)
         and "prep['registration_sha256']" in ast.unparse(n.test)]
assert len(matches)==1
frozen_check=compile(ast.Expression(matches[0].test),str(verifier),'eval')
work=Path(tempfile.mkdtemp(prefix='owner-runtime-lifecycle-'));runtime=work/'runtime.json'
write(runtime,dict(version='fixture',phase='owner'));checks=[]
shared={'fixture_source':'123'}
original=dict(roles={'joint_native':dict(queries=[dict(net=1,pin=2,raw_criticality=.25)],
    source_sha256=shared)},source_sha256=shared)

def fixture(name,bound=True,sealed=True):
    tx=work/name;tx.mkdir()
    reg=helper.bind_runtime(original,runtime) if bound else copy.deepcopy(original)
    write(tx/'registration.json',reg)
    if sealed:write(tx/'preparation.json',dict(passed=True,transaction_registered=True,
        registration_sha256=sha(tx/'registration.json')))
    return tx

def rejects(name,change):
    tx=fixture(name);change(tx)
    before={p.name:p.read_bytes() for p in tx.iterdir()}
    try:helper.bind_for_execution(tx,runtime)
    except (AssertionError,FileNotFoundError):pass
    else:raise AssertionError('Expected rejection: '+name)
    assert before=={p.name:p.read_bytes() for p in tx.iterdir()}
    checks.append(dict(name=name,passed=True,failed_before_mutation=True))

tx=fixture('valid_owner');before=(tx/'registration.json').read_bytes()
helper.bind_for_execution(tx,runtime)
assert (tx/'registration.json').read_bytes()==before
assert eval(frozen_check,dict(prep=read(tx/'preparation.json'),tx=tx,sha=sha))
checks.append(dict(name='valid_owner_passes_unchanged_frozen_assertion_without_write',passed=True))
assert 'runtime_config' not in original and str(runtime) not in shared
assert read(tx/'registration.json')['roles']==original['roles']
checks.append(dict(name='request_and_role_bindings_unchanged_despite_shared_input_dictionary',passed=True))
tx=fixture('ordinary',False,False);helper.bind_for_execution(tx,runtime)
assert read(tx/'registration.json')==helper.bind_runtime(original,runtime)
before=(tx/'registration.json').read_bytes();helper.bind_for_execution(tx,runtime)
assert (tx/'registration.json').read_bytes()==before
checks.append(dict(name='ordinary_first_bind_then_idempotent_before_execution',passed=True))

def alter_reg(tx,key,value):
    reg=read(tx/'registration.json');reg[key]=value;write(tx/'registration.json',reg)
rejects('changed_registration',lambda tx:alter_reg(tx,'extra',True))
rejects('different_runtime_path',lambda tx:alter_reg(tx,'runtime_config',str(work/'other.json')))
rejects('previous_execution',lambda tx:write(tx/'execution_registration.json',dict(status='started')))
rejects('failed_preparation',lambda tx:write(tx/'preparation.json',dict(passed=False,transaction_registered=True,registration_sha256=sha(tx/'registration.json'))))
rejects('unregistered_preparation',lambda tx:write(tx/'preparation.json',dict(passed=True,transaction_registered=False,registration_sha256=sha(tx/'registration.json'))))
def legacy(tx):
    write(tx/'registration.json',original)
    write(tx/'preparation.json',dict(passed=True,transaction_registered=True,registration_sha256=sha(tx/'registration.json')))
rejects('legacy_unbound_owner_not_silently_repaired',legacy)
saved=runtime.read_bytes()
def drift(tx):runtime.write_text('{"changed":true}\n')
rejects('runtime_bytes_drift',drift);runtime.write_bytes(saved)
def partial(tx):
    reg=read(tx/'registration.json');del reg['runtime_config'];write(tx/'registration.json',reg)
rejects('partial_binding',partial)

# Check placement in the prospective source, not only the helper in isolation.
owner=(out/'runtime/current_owner_transaction_v1.py').read_text()
assert owner.index('registration=bind_runtime(')<owner.index("write(output/'registration.json',registration)")<owner.index("registration_sha256=sha(output/'registration.json')")
controller=(out/'runtime/run_unified_resource_repair_v1.py').read_text()
invoke=next(n for n in ast.parse(controller).body if isinstance(n,ast.FunctionDef) and n.name=='invoke')
assert 'bind_for_execution' in ast.unparse(invoke.body[1])
assert ast.unparse(invoke).index('bind_for_execution')<ast.unparse(invoke).index('run_phase')
checks.append(dict(name='prospective_prepare_and_invoke_order_before_seal_and_launch',passed=True))
assert all(sha(p)==h for p,h in patch['source_sha256'].items())
write(target,dict(passed=True,checks=checks,count=len(checks),fixture_directory=str(work),
    unchanged_frozen_assertion=ast.unparse(matches[0]),frozen_verifier_sha256=sha(verifier),
    new_native_or_STA_calls=0,installed_in_release=False,complete_native_validation=False,
    qualification='Actual lifecycle helper and integration placement checks using tiny fixtures. The unchanged original preparation-seal assertion passes after prospective binding. Negative cases reject before writes or launch. This does not execute a full owner selector, worker, native query, physical audit or complete release. Historical failed records stay unchanged; queued supplemental/raw admission still operates on the original frozen code.'))
print(dict(passed=True,checks=len(checks),native_calls=0,installed=False))
