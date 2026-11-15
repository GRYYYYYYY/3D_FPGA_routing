"""Bind actual BNN budget64 candidates and component cost without promoting a trajectory."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
root=D/'connection_budget_scope_probe_01';q=root/'queue';assert read(q/'completion.json')['passed']
proof=read(root/'completion.json');assert proof['passed'] and proof['committed_to_any_actor'] is False
plan=read(root/'plan.json');reg=read(q/'registration.json');assert all(sha(p)==h for p,h in reg['source_sha256'].items())
measure=read(root/'measurement/completion.json');assert measure['passed'] and not measure['live_descendants_after_command_exit']
tx=Path(plan['transaction']);roles=read(tx/'registration.json')['roles'];progress=read(tx/'progress.json')
assert plan['new_planned_connections']==54 and plan['old_planned_connections']==462
files=[Path(__file__).resolve(),q/'completion.json',q/'registration.json',root/'completion.json',root/'plan.json',root/'measurement/completion.json',tx/'registration.json',tx/'completion.json',tx/'progress.json']
summary={}
for name,role in roles.items():
    worker=tx/name;wc=read(worker/'completion.json');assert wc['passed']
    before=read(Path(role['state'])/'endpoint_vector.json');observed=read(worker/'endpoint_vector.json')
    assert all(before[k]==observed[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
    m=read(run_dir(worker)/'manifest.json');assert m['environment']['VPR_JOINT_NATIVE_SEED_ORDER']=='delay_rr_id'
    assert m['environment']['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE']==('1' if name=='reuse_on' else '0')
    assert sha(run_dir(worker)/'routed.route')==sha(Path(role['source'])/'routed.route')
    audit=read(tx/(name+'_audit/analysis.json'));assert audit['passed']
    domain=read(tx/(name+'_domain_audit.json'));assert domain['passed']
    row=progress[name]
    if row['status']=='legal_evaluated':
        assert len(audit['queries'])==54
        state=Path(row['evaluation']);sc=read(state/'completion.json');assert sc['passed']
        rd=run_dir(state);sm=read(rd/'manifest.json');assert sm['metrics']['native_full_check_passed']
        assert route_body(rd/'routed.route')==route_body(Path(audit['candidate_route']))
        assert read(rd/'independent_audit.json')['audit']['passed']
        assert read(state/'endpoint_vector.json')['constraints_sha256']==before['constraints_sha256']
        decision=read(tx/(name+'_decisions.json'))['resources_under_timing']
        summary[name]=dict(status=row['status'],CPD_ns=row['cpd_s']*1e9,resources=row['resources'],admissible_from_recorded_current_state=decision['accepted'],evaluation=str(state))
        files += [state/'completion.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'independent_audit.json',tx/(name+'_decisions.json')]
    else:
        assert row['status']=='transaction_failed_rolled_back';summary[name]=dict(status=row['status'],admissible_from_recorded_current_state=False)
    summary[name].update(actual_queries=len(audit['queries']),actual_search_attempts=len(audit['attempts']),query_core_seconds=sum(r['seconds'] for r in audit['queries']))
    files += [worker/'completion.json',worker/'endpoint_vector.json',run_dir(worker)/'manifest.json',tx/(name+'_audit/analysis.json'),tx/(name+'_domain_audit.json')]
write(root/'verification.json',dict(passed=True,roles=summary,source_original_route_and_full_vector_exact=True,
    complete_imported_scope_seconds=measure['complete_command_wall_seconds'],
    source_sha256={str(p):sha(p) for p in files},
    qualification='Actual same-current-source whole-cut budget54-query versus historical462-query workload. Every reported candidate has independent physical/capacity/scope/domain/native FULL/fresh STA and unchanged source vector/file. These candidates are not committed to any original actor and are not new completed repair trajectories. Imported scope wall counts its real OFF/ON execution and validation only; selection preparation and initial routing excluded. Core-time observations do not establish same-backend full-flow speedup or independent circuit confirmation.'))
print(dict(passed=True,roles=summary),flush=True)
