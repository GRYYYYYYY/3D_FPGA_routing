"""Finish an interrupted development flow from its actual stage cut point."""
import argparse,os,resource,shutil,sys,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    import json
    plan=json.loads(a.plan.read_text());release=Path(plan['release']);runtime=release/'runtime';ext=Path(__file__).resolve().parent
    sys.path[:0]=[str(runtime),str(ext)]
    from retained_prefix_workflow import D,read,write,sha,route_body
    from controller_runtime import worker_descriptor
    from timing_runtime import activate
    from phase_supervision import run_phase
    from run_native_scope_policy_v4 import run_dir
    from endpoint_timing_policy_streaming_v2 import compare
    from state_resource_assurance import require_publication_proof
    from recovery_prefix_v1 import Evidence
    from resource_policy_scheduling_v1 import SKIPPED
    start=time.monotonic();b=a.output.resolve();assert b==Path(plan['recovery_flow']).resolve();b.mkdir(exist_ok=False)
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));assert shutil.disk_usage(b).free>=80*1024**3
    manifest=read(release/'release_manifest.json');assert manifest['release_id']=='current_sta_cp1r3'
    assert manifest['parent_release_manifest_sha256']==plan['parent_release_manifest_sha256']
    assert all(sha(release/n)==h for n,h in manifest['files_sha256'].items())
    assert all(sha(f)==h for f,h in plan['source_sha256'].items())
    assert all(sha(f)==h for f,h in plan['prefix_sha256'].items())
    assert read(plan['validation'])['passed']
    assert all(sha(runtime/n)==h for n,h in plan['unchanged_algorithm_files'].items())
    for key in list(os.environ):
        if key.startswith('VPR_') or key in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']:os.environ.pop(key)
    os.environ.update(H3D_RECOVERY_RUNTIME=str(runtime),PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    phase=Path(plan['phase_runtime_config']);activate(phase)
    original_flow=Path(plan['original_flow']);old_resource=original_flow/'resource_flow';old_actor=old_resource/'repair'
    original_reg=read(old_actor/'registration.json');initial=Path(original_reg['initial_state']).resolve()
    config=read(plan['original_config'])
    assert config['timing_fraction']==.9 and config['terminal_resource_policy']=='endpoint_wire_before_timing'
    assert config['final_state_policy']=='strict_timing_terminal_after_endpoint_wire_handoff'
    mode=plan['recovery_mode'];assert mode in ['resource_then_timing','timing_only_after_closed_resource']
    write(b/'registration.json',dict(plan=str(a.plan.resolve()),plan_sha256=sha(a.plan),original_flow=str(original_flow),
        release_manifest_sha256=sha(release/'release_manifest.json'),recovery_mode=mode,cost_scope='new_recovery_suffix_only',
        fresh_complete_algorithm_seconds=None,new_independent_inputs=0,frozen_confirmation=False,source_sha256=plan['source_sha256']))
    stages=[]
    def invoke(tag,command,timeout=1800):
        begin=time.monotonic();_,code,status=run_phase(command,b,tag,timeout)
        stages.append(dict(phase=tag,status=status,returncode=code,complete_process_seconds=time.monotonic()-begin));write(b/'stages.json',stages)
        assert code==0,(tag,status,code)
    if mode=='resource_then_timing':
        resource_flow=b/'resource_flow';resource_flow.mkdir()
        for name in ['initial','joint_graph_indexes','graph_audit_cache','full_graph_cache']:
            source=old_resource/name;assert source.exists();(resource_flow/name).symlink_to(source.resolve(),target_is_directory=True)
        actor=resource_flow/'repair'
        command=[sys.executable,str(ext/'resume_resource_controller.py'),'--resume-plan',str(a.plan.resolve()),'--runtime-config',str(phase),
            '--initial-state',str(initial),'--batch',str(actor),'--full-graph-cache',str((old_resource/'full_graph_cache').resolve()),
            '--bundle-size',str(original_reg['bundle_size']),'--domain-mode',original_reg['domain_mode'],'--seed-order',original_reg['seed_order'],
            '--owner-rank-windows',str(original_reg['owner_rank_windows'])]
        if original_reg['domain_feedback']:command.append('--domain-feedback')
        if not original_reg['owner_escalation']:command.append('--disable-owner-escalation')
        invoke('continue_resource_from_original_checkpoint',command,None)
        closed=read(actor/'completion.json');assert closed['passed'] and read(actor/'prefix_consumption_seal.json')['passed']
    else:
        # This input already completed resource/terminal/handoff. Verify their
        # actual archive rather than repeating those stages.
        (b/'resource_flow').symlink_to(old_resource,target_is_directory=True);actor=old_actor
        closed=read(actor/'completion.json');assert closed['passed']
        proof=Evidence();proof.verify(original_reg['source_sha256']);allowed={str(initial)};expected=initial
        def require_state(state):
            state=Path(state).resolve();require_publication_proof(state)
            proof.bind(state/'completion.json');proof.bind(state/'endpoint_vector.json')
            rd=run_dir(state);m=read(rd/'manifest.json');assert m['status']=='completed' and m['metrics']['native_full_check_passed']
            proof.bind(rd/'manifest.json');proof.bind(rd/'independent_audit.json')
            for n in ['packed.net','placed.place','routed.route']:proof.bind(rd/n,m['outputs'][n]['sha256'])
            allowed.add(str(state))
        require_state(initial)
        for i,row in enumerate(read(actor/'steps.json')):
            assert row['round']==i and Path(row['current_state']).resolve()==expected
            tx=Path(row['transaction']);role=row['accepted_role'];proof.bind(tx/'registration.json');proof.bind(tx/'completion.json')
            assert read(tx/'completion.json')['passed'];proof.verify(read(tx/'registration.json')['source_sha256'])
            recorded_role=read(tx/'registration.json')['roles'][role]
            assert recorded_role['original_budget']==original_reg['anchor']
            assert recorded_role['fixed_resource_limits']==original_reg['resource_limits']
            decision=tx/(role+'_decisions.json');proof.bind(decision);assert read(decision)['resources_under_timing']['accepted']
            expected=Path(row['committed_evaluation']).resolve();require_state(expected)
        assert expected==Path(closed['final_state']).resolve()==Path(read(actor/'current_state.json')['state']).resolve()
        assert closed['accepted_steps']==len(read(actor/'steps.json'))
        for attempt in read(actor/'attempts.json'):
            tx=Path(attempt['transaction']);progress=tx/'progress.json'
            if progress.exists():
                proof.bind(progress)
                for row in read(progress).values():
                    if row.get('status')=='legal_evaluated':require_state(row['evaluation'])
        proof.unchanged();write(b/'closed_resource_consumption_seal.json',dict(passed=True,source_sha256=proof.bound,
            actual_legal_archive=sorted(allowed),original_receipts_changed=False,new_native_calls=0))
    resource_final=Path(closed['final_state']).resolve();selection=b/'terminal_wire_selection'
    if mode=='timing_only_after_closed_resource':selection.symlink_to(original_flow/'terminal_wire_selection',target_is_directory=True)
    else:invoke('terminal_resource_wire_selection',[sys.executable,str(D/'select_terminal_resource_alternative_v2.py'),'--actor',str(actor),'--output',str(selection),'--mode','endpoint'])
    selected=read(selection/'completion.json');assert selected['passed'] and selected['mode']=='endpoint'
    assert Path(selected['state']).resolve()==resource_final
    target=resource_final if selected['selected'] is None else Path(selected['selected']['state']).resolve()
    allowed={str(initial),str(resource_final)}
    for row in read(actor/'attempts.json'):
        for result in row.get('roles',{}).values():
            if result.get('status')=='legal_evaluated':allowed.add(str(Path(result['evaluation']).resolve()))
    assert str(target) in allowed
    r0=require_publication_proof(resource_final)['resource_axes'];r1=require_publication_proof(target)['resource_axes']
    if target!=resource_final:
        comparison=compare(read(resource_final/'endpoint_vector.json'),read(target/'endpoint_vector.json'))
        assert comparison['compatible'] and comparison['cpd_nonworse'] and comparison['setup_regressed']==comparison['hold_violation_regressions']==0
        assert r1['wirelength']<r0['wirelength'] and all(r1[k]==r0[k] for k in ['SB_pairs','CB_sources'])
    root_vector=read(initial/'endpoint_vector.json');root_axes=require_publication_proof(initial)['resource_axes']
    limits=dict(wirelength=(root_axes['wirelength']*1001+999)//1000,SB_pairs=r1['SB_pairs'],CB_sources=r1['CB_sources'])
    assert read(target/'endpoint_vector.json')['cpd_s']<=root_vector['cpd_s'] and all(r1[k]<=limits[k] for k in limits)
    write(b/'absolute_timing_limits.json',limits)
    write(b/'terminal_resource_handoff.json',dict(passed=True,selected_resource_state=str(target),original_root=str(initial),
        original_actor=str(old_actor),recovery_actor=str(actor),actual_trajectory_archive=sorted(allowed),
        terminal_wire_commits=int(target!=resource_final),fresh_complete_cost_available=False))
    handoff=b/'timing_initial'
    if mode=='timing_only_after_closed_resource':
        old_handoff=read(original_flow/'terminal_resource_handoff.json')
        assert Path(old_handoff['selected_resource_state']).resolve()==target
        assert read(original_flow/'absolute_timing_limits.json')==limits
        assert sha(original_flow/'terminal_wire_selection/completion.json')==old_handoff['selection_sha256']
        handoff.symlink_to(original_flow/'timing_initial',target_is_directory=True)
    else:
        descriptor=worker_descriptor(phase,run_dir(target),old_resource/'full_graph_cache','resource',b/'timing_handoff_inputs.json')
        invoke('resource_final_handoff_FULL_STA',[sys.executable,str(D/'run_serial_census_state_analysis_stream_v1.py'),'--inputs',str(descriptor),
            '--source',str(run_dir(target)),'--batch',str(handoff),'--full-graph-cache',str(old_resource/'full_graph_cache'),'--timing-echo','--fresh-physical-audit'])
    assert read(handoff/'completion.json')['passed']
    x,y=[read(s/'endpoint_vector.json') for s in [target,handoff]]
    assert all(x[k]==y[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
    assert route_body(run_dir(target)/'routed.route')==route_body(run_dir(handoff)/'routed.route')
    query=(old_resource/'joint_graph_indexes/query_graph').resolve();assert read(query/'completion.json')['passed']
    timing=b/'timing';script=D/'run_complete_flow_critical_portfolio_stream_v1.py';extra=[]
    if mode=='timing_only_after_closed_resource':
        script=ext/'resume_timing_controller.py';extra=['--resume-plan',str(a.plan.resolve()),'--reuse-portfolio',plan['original_timing_portfolio']]
    invoke('complete_current_STA_timing',[sys.executable,str(script),*extra,'--runtime-config',str(phase),
        '--initial-state',str(handoff),'--batch',str(timing),'--query-graph',str(query),'--audit-cache',str(old_resource/'graph_audit_cache'),
        '--full-graph-cache',str(old_resource/'full_graph_cache'),'--policy','timing_under_resources','--budget-mode','explicit_absolute',
        '--fixed-limits',str(b/'absolute_timing_limits.json'),'--fraction',str(config['timing_fraction'])],None)
    terminal=read(timing/'completion.json');assert terminal['passed'] and terminal['operator_stop']=='no_admissible_candidate_in_current_portfolio'
    if mode=='timing_only_after_closed_resource':assert read(timing/'timing_prefix_consumption_seal.json')['passed']
    # Preserve the frozen controller's behavior, but do not promote a stopped
    # or audited-failed transaction to a scientifically complete recovery just
    # because the enclosing timing loop treated it as a failed proposal.
    verified_transactions=[]
    for path in b.rglob('progress.json'):
        tx=path.parent;registration=tx/'registration.json'
        if not registration.exists() or 'roles' not in read(registration):continue
        assert (tx/'completion.json').exists() and read(tx/'completion.json')['passed'],('Incomplete transaction',str(tx))
        assert all(row['status'] in ['legal_evaluated','transaction_failed_rolled_back',SKIPPED] for row in read(path).values()),('Infrastructure or audit failure',str(tx))
        verified_transactions.append(str(tx))
    final=Path(terminal['final_state']);quality=require_publication_proof(final)['resource_axes'];v=read(final/'endpoint_vector.json')
    assert all(sha(f)==h for f,h in plan['prefix_sha256'].items()) and all(sha(f)==h for f,h in plan['source_sha256'].items())
    files=[a.plan.resolve(),actor/'completion.json',selection/'completion.json',b/'terminal_resource_handoff.json',handoff/'completion.json',
        timing/'completion.json',b/'absolute_timing_limits.json',*b.rglob('*consumption_seal.json'),*b.rglob('stage_reuse_seal.json')]
    write(b/'completion.json',dict(passed=True,status='recovered_full_method_terminal',initial_state=str(initial),final_state=str(final),
        final_CPD_ns=v['cpd_s']*1e9,final_resources=quality,own_root_endpoint_summary={k:z for k,z in compare(root_vector,v).items() if k!='changes'},
        resource_accepted_steps=closed['accepted_steps'],owner_commits=closed['owner_commits'],timing_accepted_steps=terminal['accepted_steps'],
        absolute_timing_limits=limits,complete_recovery_driver_seconds=time.monotonic()-start,cost_scope='new_recovery_suffix_only',
        verified_new_transactions=verified_transactions,
        fresh_complete_algorithm_seconds=None,new_independent_physical_inputs=0,frozen_confirmation=False,
        source_sha256={str(f):sha(f) for f in files},
        qualification='Completes an interrupted development trajectory with its original root, archive and rules. Already closed resource/terminal/handoff/timing-query stages are retained as appropriate; actual same-actor native/audits are consumed only after serial proof. New suffix time remains separate from old failure cost; no cold complete cost, independent sample or frozen confirmation.'))
    print(dict(passed=True,resources=quality,CPD_ns=v['cpd_s']*1e9,cost_scope='new_recovery_suffix_only'))

if __name__=='__main__':main()
