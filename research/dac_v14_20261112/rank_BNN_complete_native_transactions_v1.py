"""Rank actual nested native work; do not infer speedup from component deletion."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from run_native_scope_policy_v4 import run_dir

out=D/'BNN_complete_transaction_cost_rank_01';out.mkdir(exist_ok=False)
rows=[];files=[Path(__file__).resolve()];checks={}
for role in ['bnn_native','bnn_domain']:
    case=D/'complete_resource_timing_full_flow_01'/role
    proof=read(case/'completion.json');assert proof['passed']
    cost=D/('complete_BNN_native_cost_analysis_01' if role=='bnn_native' else 'complete_BNN_domain_cost_analysis_01')
    summary=read(cost/'summary.json');assert summary['passed'] and summary['complete_wall_seconds']==proof['complete_wall_seconds']
    flow=case/'flow';transactions={}
    for attempt in read(flow/'resource_flow/repair/attempts.json'):
        transactions[str(Path(attempt['transaction']))]='resource'
    for path in (flow/'timing').glob('round_*/proposal_*/transaction/process_costs.json'):
        transactions[str(path.parent)]='timing'
    for directory,phase in transactions.items():
        tx=Path(directory);reg=read(tx/'registration.json');costs=read(tx/'process_costs.json')
        for cost_row in costs:
            tag=cost_row['tag']
            if not tag.endswith('_native'):continue
            name=tag[:-7];worker=tx/name;closed=read(worker/'completion.json');assert closed['passed']
            audit=read(tx/(name+'_audit/analysis.json'));assert audit['passed']
            protocol=run_dir(worker)/'joint_native.log';last=protocol.read_text().splitlines()[-1].split()
            assert last[0]=='COMPLETE' and last[-1]=='occupancy_restored'
            core=float(last[4]);assert core>=0
            if 'native_transaction_seconds' in audit:assert core==audit['native_transaction_seconds']
            request=reg['roles'][name];per_net={n:len(pins) for n,pins in request['removed_pins'].items()}
            rows.append(dict(role=role,phase=phase,transaction=str(tx),worker=name,
                actual_core_seconds=core,native_worker_wrapper_seconds=cost_row['complete_process_seconds'],
                actual_native_process_seconds=closed['timing']['native_process_seconds'],
                removed_nets=len(per_net),requested_connections=sum(per_net.values()),
                largest_single_net_removed_pins=max(per_net.values()),removed_pins_per_net=per_net,
                actual_native_queries=len(audit['queries']),actual_search_attempts=len(audit['attempts']),
                actual_heap_pushes=sum(q['pushes'] for q in audit['queries']),
                actual_heap_pops=sum(q['pops'] for q in audit['queries'])))
            files += [tx/'registration.json',tx/'process_costs.json',worker/'completion.json',
                      tx/(name+'_audit/analysis.json'),protocol]
    selected=[row for row in rows if row['role']==role]
    total=sum(row['actual_core_seconds'] for row in selected)
    expected=summary['nested_diagnostics_not_added_to_wall']['actual_native_search_core_seconds']
    assert abs(total-expected)<1e-8
    checks[role]=dict(actual_workers=len(selected),core_sum_seconds=total,
        core_fraction_of_actual_whole_wall=total/proof['complete_wall_seconds'],
        resource_core_seconds=sum(row['actual_core_seconds'] for row in selected if row['phase']=='resource'),
        timing_core_seconds=sum(row['actual_core_seconds'] for row in selected if row['phase']=='timing'),
        requested_connections=sum(row['requested_connections'] for row in selected),
        native_queries=sum(row['actual_native_queries'] for row in selected),
        native_attempts=sum(row['actual_search_attempts'] for row in selected))
    files += [case/'completion.json',cost/'summary.json',flow/'resource_flow/repair/attempts.json']
rows.sort(key=lambda row:-row['actual_core_seconds'])
write(out/'transactions.json',rows)
write(out/'completion.json',dict(passed=True,native_calls_new=0,actual_core_sums_match_closed_costs=True,
    actual_cases=checks,top_transactions=rows[:5],source_sha256={str(f):sha(f) for f in dict.fromkeys(files)},
    artifact_sha256={'transactions.json':sha(out/'transactions.json')},
    qualification='Ranked actual native transaction/search core intervals nested within worker wrappers, not additive whole-wall phases or predicted savings. Inputs, current scopes, repair opportunities and fallback differ across actual trajectories; high connection counts and expensive transactions are associated observations, not an isolated fanout-causality or speedup experiment. Existing fixed connection-budget and grouping controls must execute their actual versions before cost or quality benefit is claimed. No old quality/new-time splice, no native rerun.'))
print(dict(passed=True,actual_cases=checks,top=[{k:row[k] for k in ['role','phase','actual_core_seconds','requested_connections','largest_single_net_removed_pins']} for row in rows[:5]]),flush=True)
