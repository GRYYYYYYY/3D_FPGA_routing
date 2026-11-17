"""Cost hierarchy of completed transactions; not complete paired timing/QoR."""
import csv,math,statistics
from pathlib import Path
from datetime import datetime,timezone
from retained_prefix_workflow import D,read,write,sha

out=D/'LSTM_transaction_costs_01';assert not out.exists()
plan=read(D/'cp1r3_distinct_input_cohort_01/plan.json');base=Path(next(x for x in plan['inputs'] if x['id']=='lstm')['workspace'])
rows=[];origins=[]
for arm in ['native','domain']:
    repair=base/arm/'flow/resource_flow/repair'
    # Only actor-acknowledged complete attempts; running scope is excluded.
    attempts=read(repair/'attempts.json')
    for item in attempts:
        tx=Path(item['transaction']);path=tx/'completion.json';closed=read(path)
        assert closed['passed'] and item['native_transaction_complete']
        costs_path=tx/'process_costs.json';costs=read(costs_path)
        assert all(c['status']=='completed' and c['returncode']==0 for c in costs)
        seconds=[c['complete_process_seconds'] for c in costs]
        assert math.isclose(sum(seconds),closed['complete_child_process_seconds'],rel_tol=1e-14,abs_tol=1e-9)
        whole=closed['complete_orchestrator_seconds'];assert whole>=sum(seconds)>0
        roles={name:r for name,r in closed['roles'].items() if r['status']!='not_executed_domain_candidate_accepted'}
        assert all(r['native_calls_new']==1 and r['native_core_seconds_new']==r['native_core_seconds'] for r in roles.values())
        timer=sum(r['native_core_seconds_new'] for r in roles.values())
        assert 0<=timer<=whole
        owner=item.get('mechanism')=='capacity_certified_owner_coordination'
        reused=all(r['reused_FULL_STA'] for r in roles.values())
        group=('owner' if owner else 'ordinary_reused_FULL_STA' if reused else 'ordinary_fresh_FULL_STA')
        parts={c['tag']:c['complete_process_seconds'] for c in costs};assert len(parts)==len(costs)
        residual=whole-sum(parts.values())
        rows.append(dict(arm=arm,group=group,transaction=str(tx),whole_transaction_seconds=whole,
            child_process_seconds=parts,outer_nonchild_seconds=residual,
            registered_role_native_transaction_timer_seconds=timer,
            registered_role_timer_percent_of_transaction=100*timer/whole,
            scope_count=len(roles),accepted_role=item.get('accepted_role'),
            callback_inclusion_not_treated_as_pure_maze_search=True,
            owner_source_serialization_control_in_whole_but_not_role_timer=owner))
        origins.extend([path,costs_path])
groups=[]
for arm,group in sorted({(x['arm'],x['group']) for x in rows}):
    selected=[x for x in rows if (x['arm'],x['group'])==(arm,group)]
    groups.append(dict(arm=arm,group=group,completed_transactions=len(selected),
        observed_transaction_range_seconds=[min(x['whole_transaction_seconds'] for x in selected),max(x['whole_transaction_seconds'] for x in selected)],
        mean_transaction_seconds=statistics.mean(x['whole_transaction_seconds'] for x in selected),
        observed_registered_role_timer_percent_range=[min(x['registered_role_timer_percent_of_transaction'] for x in selected),max(x['registered_role_timer_percent_of_transaction'] for x in selected)],
        mean_outer_nonchild_seconds=statistics.mean(x['outer_nonchild_seconds'] for x in selected)))
assert all(p.stat().st_size<4*1024**2 for p in origins)
out.mkdir();(out/'receipts').mkdir();snapshots=[]
for i,p in enumerate(origins):
    target=out/'receipts'/f'{i:03d}_{p.name}';target.write_bytes(p.read_bytes());assert sha(target)==sha(p)
    snapshots.append(dict(original=str(p),snapshot=str(target),sha256=sha(target)))
write(out/'transactions.json',rows);write(out/'groups.json',groups)
with (out/'overview.csv').open('w',newline='') as stream:
    writer=csv.writer(stream);writer.writerow(['arm','group','transactions','mean_transaction_s','min_role_timer_percent','max_role_timer_percent'])
    for r in groups:writer.writerow([r['arm'],r['group'],r['completed_transactions'],r['mean_transaction_seconds'],*r['observed_registered_role_timer_percent_range']])
write(out/'completion.json',dict(passed=True,observed_at=datetime.now(timezone.utc).isoformat(),
    completed_transactions=len(rows),groups=groups,original_native_whole_status=read(D/'cp1r3_distinct_input_cohort_01/lstm_results.json')['native']['status'],
    domain_whole_complete=(base/'domain/flow/completion.json').exists(),
    complete_domain_algorithm_seconds=None,formal_pair_cost_ratio=None,new_native_or_STA_calls=0,
    whole_pair_quality_admitted=False,paper_benefit_claims_authorized=False,
    source_sha256={r['snapshot']:r['sha256'] for r in snapshots},receipt_origins=snapshots,
    engineering_direction='Prioritize measured source/candidate observation, audit and data-handling costs; do not infer that maze-search optimization alone removes the observed complete workflow overhead. Any implementation optimization must preserve evidence gates and be applied to both arms before fresh whole-command timing.',
    qualification='Existing small cost receipts only. Child stages partition each individual transaction; nested native timers are not added to them. Role native timer includes its actual backend semantics and may include callbacks, not just search. Owner source serialization control is charged in whole transaction but outside the joint-role timer. These are differing adaptive scopes, not matched cross-arm speedup samples. Parent residual is uninstrumented controller/preparation/accounting work, not attributed entirely to hashing or Python. No sum of component costs is reported as a complete algorithm time; native original verifier failure and unfinished domain remain explicit.'))
print(dict(passed=True,transactions=len(rows),groups=groups,new_native_calls=0))
