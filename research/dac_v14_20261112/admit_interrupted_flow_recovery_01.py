"""Seal a per-arm development recovery plan only after its real stage audit."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

ROOT=D/'interrupted_flow_recovery_01'
def admit(spec):
    protocol=read(ROOT/'protocol.json');assert all(sha(p)==h for p,h in protocol['source_sha256'].items())
    summary_path=D/'interrupted_stage_reconciliation_01/completion.json';summary=read(summary_path)
    audit_path=D/'interrupted_stage_reconciliation_01'/(spec['pair']+'_'+spec['arm']+'_audit.json');audit=read(audit_path)
    assert audit['passed'] and audit in summary['rows'],'This arm lacks a successful actual stage audit'
    release=Path(protocol['release']);manifest=read(release/'release_manifest.json')
    assert manifest['release_id']=='current_sta_cp1r3' and manifest['parent_release_manifest_sha256']==protocol['parent_release_manifest_sha256']
    package=read(D/'confirmation_release_cp1r3_01/completion.json');assert package['passed']
    assert read(ROOT/'validation.json')['passed']
    case=ROOT/'arms'/(spec['pair']+'_'+spec['arm']);case.mkdir(exist_ok=False)
    original_flow=Path(spec['original_flow']);original_resource=original_flow/'resource_flow/repair'
    mode=spec['recovery_mode'];actor=original_flow/'timing' if mode=='timing_only_after_closed_resource' else original_resource
    target_actor=case/'flow/timing' if mode=='timing_only_after_closed_resource' else case/'flow/resource_flow/repair'
    config=original_flow.parent/'config.json';phase=original_flow/'resource_flow/phase_runtime.json'
    failed=original_flow.parent/'measurement/completion.json'
    metadata=[config,phase,failed,audit_path,summary_path,original_flow/'registration.json']
    for actor_path in [original_resource,actor]:
        metadata += [actor_path/n for n in ['registration.json','current_state.json','steps.json','attempts.json','process_costs.json','completion.json'] if (actor_path/n).exists()]
    if mode=='timing_only_after_closed_resource':
        metadata += [original_flow/n for n in ['terminal_wire_selection/completion.json','terminal_resource_handoff.json','absolute_timing_limits.json','timing_initial/completion.json','stages.json']]
    prefix=read(D/'interrupted_stage_reconciliation_01/inventory.json')['source_sha256'].copy()
    assert all(sha(p)==h for p,h in prefix.items())
    prefix.update({str(p):sha(p) for p in metadata})
    baseline=Path(protocol['parent_release'])/'runtime'
    unchanged={n:sha(baseline/n) for n in protocol['unchanged_algorithm_files']}
    assert all(sha(release/'runtime'/n)==h for n,h in unchanged.items())
    plan=dict(pair=spec['pair'],arm=spec['arm'],release=str(release),parent_release_manifest_sha256=protocol['parent_release_manifest_sha256'],
        recovery_mode=mode,original_flow=str(original_flow),original_actor=str(actor),original_resource_actor=str(original_resource),
        original_transaction=spec['original_transaction'],original_role=spec['original_role'],recovery_actor=str(target_actor),recovery_flow=str(case/'flow'),
        original_config=str(config),phase_runtime_config=str(phase),historical_failed_measurement=str(failed),
        original_timing_portfolio=(str(original_flow/'timing/round_000/portfolio/portfolio.json') if mode=='timing_only_after_closed_resource' else None),
        stage_audit=str(audit_path),stage_audit_sha256=sha(audit_path),stage_audit_summary=str(summary_path),stage_audit_summary_sha256=sha(summary_path),
        validation=str(ROOT/'validation.json'),unchanged_algorithm_files=unchanged,prefix_sha256=prefix,
        source_sha256={**protocol['source_sha256'],str(release/'release_manifest.json'):sha(release/'release_manifest.json'),str(audit_path):sha(audit_path),str(summary_path):sha(summary_path)},
        cost_scope='new_recovery_suffix_only',fresh_complete_algorithm_seconds=None,frozen_confirmation=False,new_independent_inputs=0,
        qualification='Actual audited same-prefix admission before this arm executes. No root/budget/portfolio reset, completed native replay, old receipt mutation or historical cost borrowing. Existing failures and rejected legal candidates remain.')
    write(case/'plan.json',plan)
    return case
