"""Bound completed prefix receipts and conditional scheduling, never whole QoR."""
import math,time
from pathlib import Path
from datetime import datetime,timezone
from retained_prefix_workflow import D,read,write,sha

out=D/'LSTM_budget_cost_progress_01';assert not out.exists()
plan=read(D/'cp1r3_distinct_input_cohort_01/plan.json');item=next(x for x in plan['inputs'] if x['id']=='lstm')
base=Path(item['workspace']);repair=base/'domain/flow/resource_flow/repair'
current_bytes=(repair/'current_state.json').read_bytes();current=__import__('json').loads(current_bytes)
steps=read(repair/'steps.json');count=current['accepted_steps'];assert count==len(steps) and count>=7
rows=[];sources=[]
for step in steps:
    tx=Path(step['transaction']);closed=read(tx/'completion.json');name=step['accepted_role'];row=closed['roles'][name]
    decisions=read(tx/(name+'_decisions.json'));assert closed['passed'] and decisions['resources_under_timing']['accepted']
    assert row['status']=='legal_evaluated' and step['committed_evaluation']==row['evaluation']
    assert row['cpd_s']==current['anchor']['CPD_s']
    comparison=decisions['strict']['comparison']
    rows.append(dict(round=step['round'],transaction=str(tx),resources=row['resources'],CPD_ns=row['cpd_s']*1e9,
        own_previous_to_candidate_resource_delta=decisions['resources_under_timing']['resource_delta'],
        endpoint_delta_summary={k:v for k,v in comparison.items() if k!='changes'},
        complete_transaction_seconds=closed['complete_orchestrator_seconds'],nested_native_core_seconds=row['native_core_seconds'],
        fixed_policy_accepted=True,not_whole_role_admission=True))
    sources += [tx/'completion.json',tx/(name+'_decisions.json')]
last=rows[-1];limits=current['resource_limits'];remaining={k:limits[k]-last['resources'][k] for k in limits}
assert all(x>=0 for x in remaining.values())
ordinary=max(r['complete_transaction_seconds'] for r in rows)
owners=[]
for p in sorted((base/'native/flow/resource_flow/repair').glob('round_*/owner_*/completion.json')):
    record=read(p);assert record['passed'];owners.append(record['complete_orchestrator_seconds']);sources.append(p)
assert len(owners)==3
native_result=read(D/'cp1r3_distinct_input_cohort_01/lstm_results.json')['native']
assert native_result['quality'] is None and native_result['status']=='execution_or_verification_failed'
resource_receipt=base/'native/flow/resource_flow/completion.json';r=read(resource_receipt)
# The historical resource envelope elapsed time is for planning only. Read
# its actual complete field instead of summing child or nested CPU measures.
resource_seconds=r['complete_driver_seconds']
tail=native_result['complete_seconds']-resource_seconds;assert 0<tail<1800
sources += [resource_receipt]
scenarios=[]
for extra_accepts in [0,3,6]:
    # Three ordinary probes and three owners describe the observed native
    # closing menu. One/two ordinary passes per domain probe are assumptions.
    lower=extra_accepts*ordinary+3*ordinary+sum(owners)+tail
    upper=extra_accepts*ordinary+6*ordinary+sum(owners)+tail
    scenarios.append(dict(hypothetical_further_accepts=extra_accepts,domain_remaining_minutes=[lower/60,upper/60],
        remaining_confirmation_and_original_replay_hours=[lower/3600+2+10/60,upper/3600+8+40/60]))
assert current_bytes==(repair/'current_state.json').read_bytes(),'Prefix advanced; take a new explicit snapshot'
assert all(p.stat().st_size<4*1024**2 for p in sources)
out.mkdir();(out/'receipts').mkdir();origins=[]
for i,p in enumerate(sources):
    target=out/'receipts'/f'{i:03d}_{p.name}';target.write_bytes(p.read_bytes());assert sha(target)==sha(p)
    origins.append(dict(original=str(p),snapshot=str(target),sha256=sha(target)))
(out/'original_current_state_snapshot.json').write_bytes(current_bytes)
write(out/'prefix.json',rows)
write(out/'completion.json',dict(passed=True,observed_at=datetime.now(timezone.utc).isoformat(),
    accepted_prefix_steps=count,declared_current_resources=last['resources'],declared_root=current['anchor'],
    fixed_resource_limits=limits,remaining_resource_budget=remaining,
    ordinary_transaction_observed_range_seconds=[min(r['complete_transaction_seconds'] for r in rows),ordinary],
    native_owner_observed_complete_transaction_seconds=owners,
    native_original_complete_command_seconds=native_result['complete_seconds'],native_resource_elapsed_seconds=resource_seconds,
    native_post_resource_difference_seconds_for_planning_only=tail,
    conditional_scheduling_scenarios=scenarios,additional_raw_admission_ETA=None,
    source_sha256={r['snapshot']:r['sha256'] for r in origins},receipt_origins=origins,
    new_native_or_STA_calls=0,raw_graph_route_or_full_STA_reverified=False,whole_domain_quality_admitted=False,
    complete_domain_seconds=None,paired_cost_ratio=None,paper_benefit_claims_authorized=False,
    original_native_failure_preserved=True,method_or_confirmation_rules_changed=False,
    qualification='Bounded completed-prefix metadata only. Counterfactual scheduling workload counts are sensitivity cases, not execution caps, forecasts or stopping rules. Domain closing probes may require fallback, zero-cut termination may be faster, owner costs may differ, and more successful scopes may extend beyond every scenario. Remaining four roles assume2–8h with uncalibrated DLA; original-check replay10–40min remains provisional. Additional raw admission has no calibrated time. Component costs are not assembled into a reported complete algorithm time. The native whole-verifier failure and domain unfinished status prevent a new complete paired QoR claim.'))
print(dict(passed=True,accepted_steps=count,remaining_wire=remaining['wirelength'],scenario_minutes=[s['domain_remaining_minutes'] for s in scenarios],full_role_result=False))
