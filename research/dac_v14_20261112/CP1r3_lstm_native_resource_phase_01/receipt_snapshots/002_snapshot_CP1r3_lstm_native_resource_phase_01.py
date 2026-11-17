"""Snapshot a closed original resource phase; no native, graph or STA replay."""
import ast
import csv
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

case=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/cp1r3_distinct_input_cohort_01/lstm/native')
flow=case/'flow';resource=flow/'resource_flow';repair=resource/'repair'
out=D/'CP1r3_lstm_native_resource_phase_01';assert not out.exists()
closed=read(resource/'completion.json');actor=read(repair/'completion.json')
terminal=read(flow/'terminal_wire_selection/completion.json');handoff=read(flow/'terminal_resource_handoff.json')
timing_initial=read(flow/'timing_initial/completion.json')
assert closed['passed'] and actor['passed'] and terminal['passed'] and handoff['passed']
assert timing_initial['passed'] and all(timing_initial['checks'].values())
assert actor['accepted_steps']==4 and actor['attempted_scopes']==12 and actor['owner_commits']==0
assert not handoff['changed'] and terminal['mode']=='endpoint' and terminal['eligible_candidates']==0
assert Path(closed['final_state'])==Path(handoff['selected_resource_state'])
reader=D/'refresh_current_status_20261114.py'
node=next(n for n in ast.parse(reader.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='evaluation_receipt_evidence')
namespace=dict(Path=Path,read=read,sha=sha)
exec(compile(ast.Module(body=[node],type_ignores=[]),str(reader),'exec'),namespace)
evidence_for=namespace['evaluation_receipt_evidence']
sources=[resource/'completion.json',repair/'completion.json',repair/'registration.json',repair/'steps.json',repair/'attempts.json',
    flow/'terminal_wire_selection/completion.json',flow/'terminal_resource_handoff.json',flow/'absolute_timing_limits.json',
    flow/'timing_initial/completion.json',flow/'stages.json',resource/'stages.json',resource/'initial/completion.json',
    resource/'initial/physical_audit.json',resource/'joint_graph_indexes/completion.json',case/'config.json',
    D/'cp1r3_distinct_input_cohort_01/plan.json',D/'cp1r3_distinct_input_cohort_01/preflight.json',Path(__file__).resolve()]
rows=[];attempts=read(repair/'attempts.json')
for attempt in attempts:
    tx=Path(attempt['transaction']);done=read(tx/'completion.json');registration=read(tx/'registration.json')
    assert done['passed']
    sources += [tx/'completion.json',tx/'registration.json',tx/'process_costs.json']
    for role,r in done['roles'].items():
        assert r['status']=='legal_evaluated'
        evaluation=Path(r['evaluation']);evidence=evidence_for(evaluation);assert evidence['passed']
        decisions=tx/(role+'_decisions.json');decision=read(decisions);sources.append(decisions)
        sources += list(map(Path,evidence['source_receipt_sha256']))
        request=Path(registration['roles'][role]['request']);sources.append(request)
        comparison={k:v for k,v in decision['strict']['comparison'].items() if k!='changes'}
        rows.append(dict(round=attempt['round'],rank=attempt['candidate_rank'],
            mechanism=attempt.get('mechanism','current_resource_rank_window'),role=role,
            accepted=attempt.get('accepted_role')==role,CPD_ns=r['cpd_s']*1e9,**r['resources'],
            complete_transaction_seconds=done['complete_orchestrator_seconds'],
            recorded_native_calls_new=r.get('native_calls_new'),native_core_seconds=r['native_core_seconds'],
            reused_FULL_STA=r['reused_FULL_STA'],evaluation_schema=evidence['schema'],
            request_sha256=sha(request),registered_queries=len(registration['roles'][role]['queries']),
            resource_reason=decision['resources_under_timing']['reason'],endpoint_comparison=comparison))
assert len(attempts)==12 and len(rows)==12 and sum(x['accepted'] for x in rows)==4
# Compose exact original change lists, including cancellation of changes across
# accepted states. This does not re-parse large vectors or add per-step counts.
changes={};state=Path(closed['initial_state']);steps=read(repair/'steps.json')
for step in steps:
    assert Path(step['current_state'])==state
    comparison=read(Path(step['transaction'])/(step['accepted_role']+'_decisions.json'))['strict']['comparison']
    assert comparison['compatible']
    for change in comparison['changes']:
        key=(change['kind'],change['endpoint_domain']);old,new=change['before_s'],change['after_s']
        if key in changes:assert changes[key][1]==old
        else:changes[key]=[old,old]
        changes[key][1]=new
    state=Path(step['committed_evaluation'])
assert state==Path(closed['final_state'])
endpoint_delta=dict(setup_improved=sum(k[0]=='setup' and v[1]>v[0] for k,v in changes.items()),
    setup_regressed=sum(k[0]=='setup' and v[1]<v[0] for k,v in changes.items()),
    hold_violation_regressions=sum(k[0]=='hold' and min(v[1],0)<min(v[0],0) for k,v in changes.items()),
    derived_from='Exact original compatible full-vector transition change lists along the accepted source chain; cancellations retained.',
    independently_reparsed_full_vectors=False)
assert all(p.stat().st_size<4*1024**2 for p in sources)
out.mkdir();snapshots=out/'receipt_snapshots';snapshots.mkdir();origins=[]
for i,source in enumerate(sorted(set(sources))):
    target=snapshots/f'{i:03d}_{source.name}';target.write_bytes(source.read_bytes())
    origins.append(dict(original=str(source),snapshot=str(target),sha256=sha(target)))
(out/'status_reader_function.py').write_text(ast.get_source_segment(reader.read_text(),node)+'\n')
write(out/'scope_outcomes.json',rows);write(out/'resource_phase_endpoint_delta.json',endpoint_delta)
with (out/'phase_costs.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['scope','phase','status','complete_process_seconds']);writer.writeheader()
    for scope,path in [('whole_method_top_level',flow/'stages.json'),('nested_resource_phase',resource/'stages.json')]:
        for row in read(path):writer.writerow(dict(scope=scope,**{k:row[k] for k in ['phase','status','complete_process_seconds']}))
write(out/'completion.json',dict(passed=True,observed_at=datetime.now(timezone.utc).isoformat(),case=str(case),
    status='original_resource_phase_and_terminal_handoff_receipts_snapshotted',release='current_sta_cp1r3',
    accepted_resource_steps=4,attempted_scopes=12,ordinary_scopes=9,owner_scopes=3,owner_commits=0,
    resource_final_CPD_ns=closed['final_CPD_s']*1e9,resource_final_resources=closed['final_resources'],
    resource_complete_driver_seconds=closed['complete_driver_seconds'],
    nested_repair_seconds=actor['complete_imported_state_workflow_seconds'],operator_stop=actor['operator_stop'],
    initial_to_resource_endpoint_delta=endpoint_delta,terminal_mode=terminal['mode'],
    terminal_same_source_candidates=terminal['actual_same_source_candidates'],terminal_eligible_candidates=0,
    terminal_changed=False,timing_handoff_passed=True,timing_handoff_original_checks=timing_initial['checks'],
    absolute_timing_limits=read(flow/'absolute_timing_limits.json'),
    whole_method_cost=None,complete_confirmation_passed=False,paired_domain_comparison_available=False,
    new_independent_complete_paired_outcomes=0,new_native_or_STA_calls_by_snapshot=0,
    source_sha256={x['snapshot']:x['sha256'] for x in origins},receipt_origins=origins,
    artifact_sha256={n:sha(out/n) for n in ['scope_outcomes.json','resource_phase_endpoint_delta.json','phase_costs.csv','status_reader_function.py']},
    qualification='Closed resource subflow, not the complete resource-plus-timing algorithm or matched N/D result. Ordinary and coordinated owner outcomes, all refusals and exact endpoint comparisons are retained. Source and installed-candidate observation schemas are distinct. Terminal endpoint policy preserves the accepted resource state; the lower-wire owner has a setup regression. Original phase/transaction times are nested and must not be summed into full algorithm time. No graph/STA/native query replay, frozen-rule change or independent-input benefit is created.'))
print(dict(passed=True,resource_driver_seconds=closed['complete_driver_seconds'],endpoint_delta=endpoint_delta,
    receipts=len(origins),timing_handoff_passed=True,whole_method_cost=None))
