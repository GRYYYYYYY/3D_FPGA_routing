"""Validate dispatch transforms and actual old envelope/role metadata, no native."""
import ast,copy,shutil,tempfile
from pathlib import Path
from types import SimpleNamespace
from retained_prefix_workflow import D,read,write,sha
from same_actor_timing_prefix_v1 import timing_envelope_gate
from recovery_prefix_v1 import compatible_roles,original_envelope

root=D/'interrupted_flow_recovery_01';ext=root/'runtime_extension'
assert not (root/'protocol.json').exists()
shutil.copy2(D/'run_interrupted_full_flow_recovery_v1.py',ext/'run_interrupted_full_flow_recovery_v1.py')
revision=read(root/'dispatch_revision.json');guards=[];actual=[]
def reject(name,fn):
    try:fn()
    except AssertionError:guards.append(name);return
    raise AssertionError('Guard did not reject '+name)
for name,row in revision['revisions'].items():
    text=(ext/name).read_text();ast.parse(text);assert sha(ext/name)==row['source_sha256']
    prefix=row['bootstrap'];assert text.startswith(prefix);restored=text[len(prefix):]
    for old,new in reversed(row['replacements']):assert restored.count(new)==1;restored=restored.replace(new,old)
    assert restored==Path(row['parent']).read_text() and sha(row['parent'])==row['parent_sha256']
for name in ['same_actor_stage_reuse_v1.py','recovery_prefix_v1.py','same_actor_timing_prefix_v1.py','run_interrupted_full_flow_recovery_v1.py']:
    assert (ext/name).read_bytes()==(D/name).read_bytes()
inventory=read(D/'interrupted_stage_reconciliation_01/inventory.json')
assert all(sha(p)==h for p,h in inventory['source_sha256'].items())
with tempfile.TemporaryDirectory(prefix='same-actor-real-roles-') as folder:
    folder=Path(folder)
    for i,row in enumerate(inventory['rows']):
        tx=Path(row['transaction']);role=read(tx/'registration.json')['roles'][row['role']]
        changed=copy.deepcopy(role);request=folder/(str(i)+'_request');request.write_bytes(Path(role['request']).read_bytes());changed['request']=str(request)
        if 'crossing_domain' in role:
            domain=folder/(str(i)+'_domain');domain.write_bytes(Path(role['crossing_domain']).read_bytes());changed['crossing_domain']=str(domain)
        compatible_roles(role,changed)
        bad=copy.deepcopy(changed);bad['original_budget']['CPD_s']+=1e-19
        reject(row['pair']+row['arm']+'_original_CPD',lambda b=bad:compatible_roles(role,b))
        bad=copy.deepcopy(changed);bad['queries']=list(reversed(bad['queries']));assert bad['queries']!=role['queries']
        reject(row['pair']+row['arm']+'_query_order',lambda b=bad:compatible_roles(role,b))
        request.write_bytes(request.read_bytes()+b'\n')
        reject(row['pair']+row['arm']+'_request_bytes',lambda c=changed:compatible_roles(role,c))
        flow=Path(row['flow']);actor=flow/'resource_flow/repair';reg=read(actor/'registration.json');checkpoint=read(actor/'current_state.json')
        args=SimpleNamespace(**{k:reg[k] for k in ['bundle_size','domain_mode','seed_order','domain_feedback','owner_rank_windows']},disable_owner_escalation=not reg['owner_escalation'])
        original_envelope(reg,checkpoint,reg['initial_state'],reg['anchor'],reg['resource_limits'],args)
        for key in ['wirelength','SB_pairs','CB_sources']:
            limits=dict(reg['resource_limits']);limits[key]+=1
            reject(row['pair']+row['arm']+'_resource_limit_'+key,lambda lim=limits:original_envelope(reg,checkpoint,reg['initial_state'],reg['anchor'],lim,args))
        actual.append(dict(pair=row['pair'],arm=row['arm'],accepted_resource_steps=row['accepted_resource_steps'],actual_role_and_original_envelope_metadata_match=True))
        if row['pair']=='clstm_input_contract_pair_02' and row['arm']=='native':
            old=read(flow/'timing/registration.json');portfolio=flow/'timing/round_000/portfolio/portfolio.json'
            plan=dict(recovery_mode='timing_only_after_closed_resource',original_timing_portfolio=str(portfolio))
            args=SimpleNamespace(**{k:old[k] for k in ['policy','budget_mode','fraction','native_mode']},resume_from=None,reuse_plan=[],reuse_portfolio=[portfolio],reuse_native_batch=[],reuse_query_batch=[],reuse_exchange=[])
            timing_envelope_gate(plan,old,old['initial_state'],old['anchor'],old['fixed_absolute_limits'],args)
            for key,value in [('fraction',.8),('policy','strict'),('budget_mode','zero_headroom'),('native_mode','reuse_only'),('reuse_plan',[portfolio]),('reuse_portfolio',[])]:
                bad=copy.deepcopy(args);setattr(bad,key,value)
                reject('timing_'+key,lambda b=bad:timing_envelope_gate(plan,old,old['initial_state'],old['anchor'],old['fixed_absolute_limits'],b))
            limits=dict(old['fixed_absolute_limits']);limits['SB_pairs']+=1
            reject('timing_fixed_SB_cap',lambda:timing_envelope_gate(plan,old,old['initial_state'],old['anchor'],limits,args))
            assert read(flow/'absolute_timing_limits.json')==old['fixed_absolute_limits']
            assert read(flow/'resource_flow/repair/completion.json')['passed']
            terminal=read(flow/'terminal_resource_handoff.json');assert terminal['passed']
            assert Path(terminal['selected_resource_state']).resolve()==Path(read(flow/'terminal_wire_selection/completion.json')['state']).resolve()
            assert not (flow/'timing/resume_state.json').exists()
            for name in ['steps.json','attempts.json']:
                assert not (flow/'timing'/name).exists() or read(flow/'timing'/name)==[]
for p in [*ext.glob('*.py'),D/'admit_interrupted_flow_recovery_01.py',D/'queue_interrupted_full_flow_recovery_01.py',D/'preregister_interrupted_full_flow_recovery_01.py']:
    ast.parse(p.read_text())
files=[Path(__file__).resolve(),root/'dispatch_revision.json',D/'interrupted_stage_adapter_01/validation.json',D/'interrupted_stage_reconciliation_01/inventory.json',*ext.glob('*.py')]
write(root/'validation.json',dict(passed=True,actual_case_metadata=actual,negative_guards=guards,
    source_transforms_reversible=True,synthetic_stage_integration='interrupted_stage_adapter_01/validation.json',
    actual_CLSTM_native_closed_resource_and_original_timing_envelope_metadata_match=True,
    new_native_calls=0,actual_serial_byte_STA_audit_complete=False,actual_recovery_execution_verified=False,
    source_sha256={str(p):sha(p) for p in files},
    qualification='Actual role/envelope/cut-point metadata and exact source transforms plus earlier tiny replay-side-effect fixtures. No heavy graph/STA parsing, actual native equivalence, completed method result or cold-cost proof. Per-case actual serial audit and sealed plan remain mandatory.'))
print(dict(passed=True,actual_cases=len(actual),negative_guards=len(guards),new_native_calls=0))
