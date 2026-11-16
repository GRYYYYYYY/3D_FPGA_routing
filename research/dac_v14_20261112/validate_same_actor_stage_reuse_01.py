"""Exercise adoption side effects with tiny fixtures; never claims native evidence."""
import ast,copy,tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from same_actor_stage_reuse_v1 import StageReuse,audit_record_gate
from recovery_prefix_v1 import compatible_roles

guards=[];checks=[]
def reject(name,fn):
    try:fn()
    except (AssertionError,KeyError,ValueError):guards.append(name);return
    raise AssertionError('Guard did not reject '+name)

def fixture(base,sealed):
    old=base/'old';new=base/'new';oldtx=old/'round_000/candidate_00';newtx=new/'round_000/candidate_00'
    worker=oldtx/'reuse_on';run=worker/'runs/state';run.mkdir(parents=True);newtx.mkdir(parents=True)
    state=base/'source';state.mkdir();vector=dict(cpd_s=1e-8,setup=[1.],hold=[0.],endpoint_ids=[[1,2,3]],constraints_sha256='fixture')
    write(state/'endpoint_vector.json',vector)
    request=oldtx/'request.txt';request.write_text('1\n7 1 2\n0\n')
    domain=oldtx/'domain.txt';domain.write_text('fixture-domain\n')
    newrequest=newtx/'request.txt';newrequest.write_bytes(request.read_bytes())
    newdomain=newtx/'domain.txt';newdomain.write_bytes(domain.read_bytes())
    role=dict(state=str(state),source=str(state),request=str(request),crossing_domain=str(domain),
        objective='weighted_soft',original_budget=dict(CPD_s=1e-8,wirelength=10,SB_pairs=2,CB_sources=1),
        fixed_resource_limits=dict(wirelength=11,SB_pairs=2,CB_sources=1),crossing_reuse_enabled=True,
        domain_failure_release=True,seed_order='delay_rr_id',queries=[dict(net=7,pin=2)],
        removed_pins={'7':[2]},source_sha256={str(state/'endpoint_vector.json'):sha(state/'endpoint_vector.json'),str(request):sha(request),str(domain):sha(domain)})
    newrole=copy.deepcopy(role);newrole.update(request=str(newrequest),crossing_domain=str(newdomain))
    newrole['source_sha256']={str(state/'endpoint_vector.json'):sha(state/'endpoint_vector.json'),str(newrequest):sha(newrequest),str(newdomain):sha(newdomain)}
    write(oldtx/'registration.json',dict(roles={'reuse_on':role}))
    write(newtx/'registration.json',dict(roles={'reuse_on':newrole}))
    write(worker/'registration.json',dict(pid=999999999,start_ticks='0',source_sha256={}))
    for name in ['native_sta_frontier.jsonl','joint_native.log','stdout.log','time.txt']:(run/name).write_text('tiny adapter test fixture\n')
    write(run/'manifest.json',dict(status='completed' if sealed else 'running',returncode=0 if sealed else None,shared_inputs={},private_input_sha256={}))
    if sealed:
        write(worker/'completion.json',dict(passed=True));write(worker/'input_seal.json',dict(passed=True))
    audit=oldtx/'reuse_on_audit';audit.mkdir();candidate=audit/'candidate.route';candidate.write_text('fixture candidate\n')
    write(audit/'analysis.json',dict(passed=True,candidate_route=str(candidate),candidate_sha256=sha(candidate),source_sha256={str(run/'joint_native.log'):sha(run/'joint_native.log')}))
    write(oldtx/'reuse_on_domain_audit.json',dict(passed=True,source_sha256={str(domain):sha(domain)}))
    (oldtx/'reuse_on_evaluation').mkdir()
    case=dict(passed=True,pair='fixture',arm='domain',source_state=str(state),fixed_original_budget=role['original_budget'],
        full_method_complete=False,adoption_implemented=False,stages=dict(native_source_control=dict(
            verified_existing_execution=True,query_count=1,exact_observation=dict(passed=True,checks={'fixture_exact':True}),
            receipt_kind='sealed_worker' if sealed else 'raw_success_unsealed_manifest',original_manifest_unchanged=True,new_native_calls=0),
            candidate_physical_audit=dict(existing_passed_receipt=True),domain_audit=dict(existing_passed_receipt=True),
            candidate_STA=dict(completed=False,persisted_payload_present=False)))
    casepath=base/'case.json';write(casepath,case)
    # Test proof is explicitly synthetic; the real adapter's caller must seal
    # the actual serial audit outputs before execution in a real experiment.
    mapping={str(p.resolve()):sha(p) for p in [*old.rglob('*'),state/'endpoint_vector.json'] if p.is_file()}
    summary=dict(passed=True,rows=[case],source_sha256=mapping)
    summarypath=base/'summary.json';write(summarypath,summary)
    plan=dict(pair='fixture',arm='domain',recovery_actor=str(new),original_actor=str(old),original_transaction=str(oldtx),original_role='reuse_on',
        stage_audit_summary=str(summarypath),stage_audit_summary_sha256=sha(summarypath),stage_audit=str(casepath),stage_audit_sha256=sha(casepath))
    planpath=base/'plan.json';write(planpath,plan)
    return planpath,oldtx,newtx,role,newrole,case,summary

with tempfile.TemporaryDirectory(prefix='same-actor-reuse-test-') as folder:
    folder=Path(folder)
    for sealed in [False,True]:
        b=folder/('sealed' if sealed else 'unsealed');b.mkdir()
        planpath,oldtx,newtx,role,newrole,case,summary=fixture(b,sealed)
        before={str(p):p.read_bytes() for p in oldtx.rglob('*') if p.is_file()}
        reuse=StageReuse(planpath,newtx)
        assert reuse.consume('run_serial_seed_resource_state_analysis_stream_v1.py',['--batch',newtx/'reuse_on'],'reuse_on_native')
        assert read(newtx/'reuse_on/endpoint_vector.json')==read(Path(role['state'])/'endpoint_vector.json')
        assert reuse.consume('audit_native_feedback_objective_cached.py',['--output',newtx/'reuse_on_audit'],'reuse_on_audit')
        assert (newtx/'reuse_on_audit').is_symlink()
        assert reuse.consume('audit_failure_release_domain.py',[],'reuse_on_domain_audit')
        assert (newtx/'reuse_on_domain_audit.json').is_symlink()
        assert reuse.consume('run_serial_census_state_analysis_stream_v1.py',[],'reuse_on_FULL_STA') is False
        reuse.finish();assert read(newtx/'stage_reuse_seal.json')['passed']
        assert all(Path(p).read_bytes()==data for p,data in before.items())
        assert {str(p) for p in oldtx.rglob('*') if p.is_file()}==set(before)
        assert len(read(newtx/'stage_reuse_index.json')['records'])==3
        assert read(newtx/'reuse_on/completion.json')['native_analysis_calls_new']==0
        checks.append('sealed_stage_chain' if sealed else 'unsealed_raw_stage_chain_without_manifest_rewrite')
        payload=oldtx/'reuse_on_evaluation/partial.trace';payload.write_text('must never replay\n')
        reject('partial_STA_'+str(sealed),lambda:reuse.consume('run_serial_census_state_analysis_stream_v1.py',[],'reuse_on_FULL_STA'))
        payload.unlink()
        for key,value in [('seed_order','native'),('domain_failure_release',False),('original_budget',{}),('queries',[dict(net=7,pin=3)]),('removed_pins',{})]:
            changed=copy.deepcopy(newrole);changed[key]=value
            reject('actual_role_field_'+key+'_'+str(sealed),lambda c=changed:compatible_roles(role,c))
        for key,value in [('passed',False),('pair','other'),('source_state','wrong')]:
            bad=copy.deepcopy(case);bad[key]=value;badsummary=dict(summary,rows=[bad])
            if key=='source_state':
                # role() separately binds source_state to the audited state.
                continue
            reject('wrong_case_'+key+'_'+str(sealed),lambda c=bad,s=badsummary:audit_record_gate(read(planpath),s,c,oldtx))
        bad=copy.deepcopy(case);bad['stages']['native_source_control']['exact_observation']['checks']['fixture_exact']=False
        reject('inexact_observation_'+str(sealed),lambda:audit_record_gate(read(planpath),dict(summary,rows=[bad]),bad,oldtx))
        (oldtx/'reuse_on/runs/state/joint_native.log').write_text('changed after serial audit\n')
        changed=StageReuse(planpath,newtx)
        reject('changed_old_native_bytes_'+str(sealed),lambda:changed.consume('run_serial_seed_resource_state_analysis_stream_v1.py',['--batch',newtx/'another_worker'],'reuse_on_native'))
        # No old transaction exists at a newly reached round: hook explicitly
        # returns False so the original native body can execute that new work.
        fresh=newtx.parents[1]/'round_001/candidate_00';fresh.mkdir(parents=True)
        assert StageReuse(planpath,fresh).consume('run_serial_seed_resource_state_analysis_stream_v1.py',[],'reuse_on_native') is False
        checks.append('new_round_not_suppressed_'+str(sealed))
    # An old registered but never executed optional native role must also remain
    # executable. This is required after a domain candidate is rejected.
    b=folder/'optional';b.mkdir();planpath,oldtx,newtx,*_=fixture(b,False)
    for tx in [oldtx,newtx]:
        r=read(tx/'registration.json');r['roles']['reuse_off']=dict(r['roles']['reuse_on']);write(tx/'registration.json',r)
    hook=StageReuse(planpath,newtx)
    assert hook.consume('run_serial_seed_resource_state_analysis_stream_v1.py',[],'reuse_off_native') is False
    assert hook.consume('run_serial_census_state_analysis_stream_v1.py',[],'reuse_off_FULL_STA') is False
    checks.append('unexecuted_optional_native_and_STA_remain_executable')

root=D/'interrupted_stage_adapter_01';revision=read(root/'revision.json')
for name,row in revision['revisions'].items():
    text=(root/'runtime_extension'/name).read_text();ast.parse(text)
    assert sha(root/'runtime_extension'/name)==row['source_sha256']
    assert text.startswith(revision['bootstrap']);restored=text[len(revision['bootstrap']):]
    for old,new in reversed(row['replacements']):assert restored.count(new)==1;restored=restored.replace(new,old)
    assert restored==Path(row['parent']).read_text() and sha(row['parent'])==row['parent_sha256']
for name in ['same_actor_stage_reuse_v1.py','recovery_prefix_v1.py']:
    assert (root/'runtime_extension'/name).read_bytes()==(D/name).read_bytes()
write(root/'validation.json',dict(passed=True,integration_checks=checks,negative_guards=guards,
    source_transform_reverses_to_exact_frozen_parent=True,original_fixture_receipts_unchanged=True,
    test_native_calls=0,real_native_calls=0,actual_serial_stage_audit_pending=True,
    real_recovery_execution_verified=False,full_flow_dispatch_implemented=False,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'same_actor_stage_reuse_v1.py',root/'revision.json',*sorted((root/'runtime_extension').glob('*.py'))]},
    qualification='Tiny synthetic integration fixtures validate adoption side effects and replay guards only. They are not circuit evidence, a completed serial audit, native behavior equivalence, full-method execution or cold-cost measurement.'))
print(dict(passed=True,integration_checks=len(checks),negative_guards=len(guards),native_calls=0))
