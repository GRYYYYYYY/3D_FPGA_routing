"""Copy completed original prefix receipts, with no replay or cohort admission."""
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

out = D / 'CP1r3_lstm_native_progress_01'
assert not out.exists()
cohort = D / 'cp1r3_distinct_input_cohort_01'
q = cohort / 'queue_priority_02'
registration = read(q / 'registration.json')
owner = process_identity(registration['pid'])
assert owner and owner['state'] != 'Z' and owner['start_ticks'] == registration['start_ticks']
phase = read(q / 'status.json')
assert phase['status'] == 'running_confirmation_arm' and phase['input'] == 'lstm' and phase['arm'] == 'native'
case = Path(phase['case'])
initial = case / 'flow/resource_flow/initial'
root = read(initial / 'completion.json')
assert root['passed'] and not root['initial_route_imported']
repair = case / 'flow/resource_flow/repair'
steps = read(repair / 'steps.json')
assert len(steps) >= 2
sources = [cohort / 'plan.json', cohort / 'preflight.json', q / 'registration.json',
           initial / 'completion.json', initial / 'physical_audit.json']
rows = []
for step in steps[:2]:
    assert step['accepted_role'] == 'reuse_off'
    tx = Path(step['transaction'])
    complete = read(tx / 'completion.json')
    evaluation = Path(step['committed_evaluation'])
    result = read(evaluation / 'completion.json')
    decisions = read(tx / 'reuse_off_decisions.json')
    assert complete['passed'] and result['passed'] and all(result['checks'].values())
    assert decisions['resources_under_timing']['accepted']
    comparison = {k: v for k, v in decisions['strict']['comparison'].items() if k != 'changes'}
    assert comparison['compatible'] and comparison['cpd_after_s'] == result['full_precision_cpd_s']
    rows.append(dict(round=step['round'], accepted_role=step['accepted_role'],
        CPD_ns=result['full_precision_cpd_s'] * 1e9,
        resources=step['roles']['reuse_off']['resources'], endpoint_comparison=comparison,
        complete_transaction_seconds=complete['complete_orchestrator_seconds'],
        native_core_seconds=step['roles']['reuse_off']['native_core_seconds'],
        strict_CPD_policy_accepted=decisions['strict']['accepted'],
        resource_policy_accepted=decisions['resources_under_timing']['accepted']))
    sources += [tx / 'completion.json', tx / 'reuse_off_decisions.json',
                tx / 'registration.json', tx / 'process_costs.json', evaluation / 'completion.json']
sources.append(Path(__file__).resolve())
assert all(p.stat().st_size < 4 * 1024**2 for p in sources)
out.mkdir()
snapshots = out / 'receipt_snapshots'
snapshots.mkdir()
origins = []
for i, path in enumerate(sources):
    target = snapshots / f'{i:02d}_{path.name}'
    target.write_bytes(path.read_bytes())
    origins.append(dict(original=str(path), snapshot=str(target), sha256=sha(target)))
write(out / 'completion.json', dict(
    passed=True, observed_at=datetime.now(timezone.utc).isoformat(),
    status='two_completed_original_native_resource_transactions_snapshotted',
    case=str(case), original_queue_owner=owner, observed_accepted_steps=len(steps),
    summarized_prefix_steps=2, rows=rows, release='current_sta_cp1r3',
    native_or_STA_calls_by_snapshot=0, large_graph_or_endpoint_vector_reparsed=False,
    whole_algorithm_cost=None, complete_confirmation_passed=False, paired_domain_comparison_available=False,
    new_independent_complete_paired_outcomes=0, paper_result_added=False,
    source_sha256={r['snapshot']: r['sha256'] for r in origins}, receipt_origins=origins,
    qualification='Intermediate original unrestricted-native prefix on one registered LSTM input. FULL/STA/physical checks and resource acceptance belong to the copied original transactions. No domain or release attribution, terminal algorithm benefit, matched six-role confirmation or complete wall cost. Nested transaction/core times are separate and not assembled into a whole. Original live single owner continues the next stage; historical files are not rewritten.'))
print(dict(passed=True, prefix_transactions=len(rows), whole_confirmation=False,
           new_native_or_STA_calls=0, latest_resources=rows[-1]['resources']))
