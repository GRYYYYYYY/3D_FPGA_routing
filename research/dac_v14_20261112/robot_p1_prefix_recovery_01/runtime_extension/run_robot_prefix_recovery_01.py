"""Finish one interrupted development flow with its original root and archive."""
import argparse,os,resource,shutil,sys,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    import json
    plan=json.loads(args.plan.read_text());release=Path(plan['release']);runtime=release/'runtime'
    ext=Path(__file__).resolve().parent
    sys.path[:0]=[str(runtime),str(ext)]
    from retained_prefix_workflow import D,read,write,sha,route_body
    from controller_runtime import package_files,worker_descriptor
    from timing_runtime import activate
    from phase_supervision import run_phase
    from run_native_scope_policy_v4 import run_dir
    from state_resource_assurance import require_publication_proof
    from endpoint_timing_policy_streaming_v2 import compare
    started=time.monotonic();b=args.output.resolve();b.mkdir(exist_ok=False)
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));assert shutil.disk_usage(b).free>=80*1024**3
    manifest=read(release/'release_manifest.json');assert manifest['release_id']=='current_sta_cp1r3'
    assert manifest['parent_release_manifest_sha256']==plan['parent_release_manifest_sha256']
    assert all(sha(release/n)==h for n,h in manifest['files_sha256'].items())
    assert all(sha(f)==h for f,h in plan['source_sha256'].items())
    assert all(sha(f)==h for f,h in plan['prefix_sha256'].items())
    assert read(plan['validation'])['passed']
    for name,h in plan['unchanged_algorithm_files'].items():assert sha(runtime/name)==h
    old=Path(plan['original_actor']);old_flow=old.parent;phase=Path(plan['phase_runtime_config'])
    config=read(plan['original_config']);spec,physical,binaries,files=activate(phase)
    assert config['timing_fraction']==.9 and config['terminal_resource_policy']=='endpoint_wire_before_timing'
    assert config['final_state_policy']=='strict_timing_terminal_after_endpoint_wire_handoff'
    for k in list(os.environ):
        if k.startswith('VPR_') or k in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']:os.environ.pop(k)
    os.environ.update(H3D_RECOVERY_RUNTIME=str(runtime),PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    activate(phase);write(b/'registration.json',dict(plan=str(args.plan.resolve()),plan_sha256=sha(args.plan),
        release_manifest_sha256=sha(release/'release_manifest.json'),original_flow=str(old_flow.parent),
        recovered_prefix=True,cost_scope='recovery_suffix_only',fresh_complete_algorithm_seconds=None,
        source_sha256={str(f):sha(f) for f in [*package_files(),phase,*files]}))
    stages=[]
    def invoke(tag,command,timeout=1800):
        begin=time.monotonic();_,code,status=run_phase(command,b,tag,timeout)
        stages.append(dict(phase=tag,status=status,returncode=code,complete_process_seconds=time.monotonic()-begin));write(b/'stages.json',stages)
        assert code==0,(tag,status,code)
    resource_flow=b/'resource_flow';resource_flow.mkdir()
    for name in ['initial','joint_graph_indexes','graph_audit_cache','full_graph_cache']:
        source=old_flow/name;assert source.exists();(resource_flow/name).symlink_to(source.resolve(),target_is_directory=True)
    original_reg=read(old/'registration.json');initial=Path(original_reg['initial_state'])
    actor=resource_flow/'repair';command=[sys.executable,str(ext/'resume_resource_controller.py'),'--resume-plan',str(args.plan.resolve()),
        '--runtime-config',str(phase),'--initial-state',str(initial),'--batch',str(actor),
        '--full-graph-cache',str((old_flow/'full_graph_cache').resolve()),'--bundle-size',str(original_reg['bundle_size']),
        '--domain-mode',original_reg['domain_mode'],'--seed-order',original_reg['seed_order'],'--owner-rank-windows',str(original_reg['owner_rank_windows'])]
    if original_reg['domain_feedback']:command.append('--domain-feedback')
    if not original_reg['owner_escalation']:command.append('--disable-owner-escalation')
    invoke('continue_resource_from_original_checkpoint',command,timeout=None)
    closed=read(actor/'completion.json');assert closed['passed'] and read(actor/'prefix_consumption_seal.json')['passed']
    resource_final=Path(closed['final_state']);selection=b/'terminal_wire_selection'
    invoke('terminal_resource_wire_selection',[sys.executable,str(D/'select_terminal_resource_alternative_v2.py'),'--actor',str(actor),'--output',str(selection),'--mode','endpoint'])
    selected=read(selection/'completion.json');assert selected['passed'] and selected['mode']=='endpoint'
    assert Path(selected['state']).resolve()==resource_final.resolve()
    target=resource_final if selected['selected'] is None else Path(selected['selected']['state']).resolve()
    # Same recovered execution archive, including the original completed prefix.
    allowed={str(initial.resolve()),str(resource_final.resolve())}
    for row in read(actor/'attempts.json'):
        for result in row.get('roles',{}).values():
            if result.get('status')=='legal_evaluated':allowed.add(str(Path(result['evaluation']).resolve()))
    assert str(target.resolve()) in allowed,'Terminal candidate outside actual recovered trajectory'
    r0=require_publication_proof(resource_final)['resource_axes'];r1=require_publication_proof(target)['resource_axes']
    if target.resolve()!=resource_final.resolve():
        cp=compare(read(resource_final/'endpoint_vector.json'),read(target/'endpoint_vector.json'))
        assert cp['compatible'] and cp['cpd_nonworse'] and cp['setup_regressed']==cp['hold_violation_regressions']==0
        assert r1['wirelength']<r0['wirelength'] and all(r1[k]==r0[k] for k in ['SB_pairs','CB_sources'])
    root_vector=read(initial/'endpoint_vector.json');root_axes=require_publication_proof(initial)['resource_axes']
    limits=dict(wirelength=(root_axes['wirelength']*1001+999)//1000,SB_pairs=r1['SB_pairs'],CB_sources=r1['CB_sources'])
    assert read(target/'endpoint_vector.json')['cpd_s']<=root_vector['cpd_s'] and all(r1[k]<=limits[k] for k in limits)
    write(b/'absolute_timing_limits.json',limits)
    write(b/'terminal_resource_handoff.json',dict(passed=True,selected_resource_state=str(target),original_root=str(initial),
        original_actor=str(old),recovery_actor=str(actor),actual_trajectory_archive=sorted(allowed),
        terminal_wire_commits=int(target.resolve()!=resource_final.resolve()),fresh_complete_cost_available=False))
    query=(old_flow/'joint_graph_indexes/query_graph').resolve();assert read(query/'completion.json')['passed']
    handoff=b/'timing_initial';descriptor=worker_descriptor(phase,run_dir(target),old_flow/'full_graph_cache','resource',b/'timing_handoff_inputs.json')
    invoke('resource_final_handoff_FULL_STA',[sys.executable,str(D/'run_serial_census_state_analysis_stream_v1.py'),'--inputs',str(descriptor),
        '--source',str(run_dir(target)),'--batch',str(handoff),'--full-graph-cache',str(old_flow/'full_graph_cache'),'--timing-echo','--fresh-physical-audit'])
    assert read(handoff/'completion.json')['passed']
    x,y=[read(s/'endpoint_vector.json') for s in [target,handoff]]
    assert all(x[k]==y[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
    assert route_body(run_dir(target)/'routed.route')==route_body(run_dir(handoff)/'routed.route')
    timing=b/'timing'
    invoke('complete_current_STA_timing',[sys.executable,str(D/'run_complete_flow_critical_portfolio_stream_v1.py'),'--runtime-config',str(phase),
        '--initial-state',str(handoff),'--batch',str(timing),'--query-graph',str(query),'--audit-cache',str(old_flow/'graph_audit_cache'),
        '--full-graph-cache',str(old_flow/'full_graph_cache'),'--policy','timing_under_resources','--budget-mode','explicit_absolute',
        '--fixed-limits',str(b/'absolute_timing_limits.json'),'--fraction',str(config['timing_fraction'])],timeout=None)
    terminal=read(timing/'completion.json');assert terminal['passed'] and terminal['operator_stop']=='no_admissible_candidate_in_current_portfolio'
    final=Path(terminal['final_state']);quality=require_publication_proof(final)['resource_axes'];v=read(final/'endpoint_vector.json')
    assert all(sha(f)==h for f,h in plan['prefix_sha256'].items())
    write(b/'completion.json',dict(passed=True,status='recovered_full_method_terminal',initial_state=str(initial),final_state=str(final),
        final_CPD_ns=v['cpd_s']*1e9,final_resources=quality,own_root_endpoint_summary={k:z for k,z in compare(root_vector,v).items() if k!='changes'},
        prefix_steps=len(read(old/'steps.json')),resource_accepted_steps=closed['accepted_steps'],owner_commits=closed['owner_commits'],
        timing_accepted_steps=terminal['accepted_steps'],absolute_timing_limits=limits,complete_recovery_driver_seconds=time.monotonic()-started,
        cost_scope='recovery_suffix_only',fresh_complete_algorithm_seconds=None,new_independent_physical_inputs=0,frozen_confirmation=False,
        source_sha256={str(f):sha(f) for f in [args.plan.resolve(),actor/'completion.json',actor/'prefix_consumption_seal.json',selection/'completion.json',
            b/'terminal_resource_handoff.json',handoff/'completion.json',timing/'completion.json',b/'absolute_timing_limits.json']},
        qualification='Completes the interrupted development input using its exact original root, fixed envelopes, actual prefix/archive and verified completed native requests. Current measured cost is the new suffix only; historical failed attempt remains separate. No fresh whole-flow speedup, new independent input or CP1r3 confirmation claim.'))
    print(dict(passed=True,final_CPD_ns=v['cpd_s']*1e9,resources=quality,cost_scope='recovery_suffix_only'))

if __name__=='__main__':main()
