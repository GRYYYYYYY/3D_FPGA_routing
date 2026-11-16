"""Snapshot original balanced-run proof and costs; never run routing or STA.

Run once after the registered serial owner has finished its own matching.
Missing or divergent results remain unavailable, rather than being repaired here.
"""
import csv
from datetime import datetime, timezone
from pathlib import Path

from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity


def main():
    root = D / 'BNN_interleaved_timing_03'
    out = D / 'BNN_timing03_balanced_receipt_01'
    assert not out.exists(), 'Existing snapshot must not be overwritten'
    terminal = read(root / 'queue/completion.json')
    assert terminal['passed'] and terminal['status'] == 'registered_interleaved_timing_terminal'
    result = read(root / 'comparison.json')
    order = ['native_0', 'domain_0', 'domain_1', 'native_1']
    assert result['passed'] and list(result['rows']) == order
    assert result['all_registered_attempts_retained'] and result['registered_attempts'] == 4
    assert result['independent_new_inputs'] == 0 and not result['research_complete']
    available = result['paired_cost_observation_available']
    expected_valid = all(
        r['complete_verified'] and r['same_role_exact'] and r['measurement_complete']
        and r['environment_signature_consistent'] for r in result['rows'].values()
    ) and all(p['matched_initial_state'] and p['endpoint_comparison_available'] for p in result['pairs'])
    assert available is bool(expected_valid)
    sources = [root / p for p in [
        'plan.json', 'admission.json', 'configs/native.json', 'configs/domain.json',
        'queue/registration.json', 'queue/results.json', 'queue/completion.json', 'comparison.json',
    ]]
    rows, phases = [], []
    for name in order:
        case = root / name
        row = result['rows'][name]
        measurement = read(case / 'measurement/completion.json')
        assert measurement['complete_command_wall_seconds'] == row['complete_seconds']
        assert not measurement['live_descendants_after_command_exit']
        live = []
        for pid, ticks in measurement['process_identities'].items():
            actual = process_identity(int(pid))
            if actual and actual['state'] != 'Z' and actual['start_ticks'] == str(ticks):
                live.append(actual)
        assert not live, (name, 'A measured process is still live', live)
        proof_path = case / 'completion.json'
        proof = read(proof_path) if proof_path.exists() else {}
        if row['complete_verified']:
            assert proof['passed'] and proof['complete_configuration_verified']
            assert proof['complete_wall_seconds'] == row['complete_seconds']
            assert proof['CPD_ns'] == row['quality']['CPD_ns']
            assert all(proof['resources'][k] == row['quality'][k] for k in proof['resources'])
        rows.append(dict(
            arm=name, complete_command_seconds=row['complete_seconds'],
            complete_verified=row['complete_verified'], same_role_exact=row['same_role_exact'],
            environment_signature_consistent=row['environment_signature_consistent'],
            CPD_ns=proof.get('CPD_ns'), **proof.get('resources', {}),
            sampled_tree_PSS_peak_kib=row['sampled_tree_PSS_peak_kib'],
            sampled_tree_RSS_peak_kib=row['sampled_tree_RSS_peak_kib'],
            missing_memory_observations=row['missing_memory_observations'],
            observer_CPU_seconds=row['observer_CPU_seconds'],
            measured_process_identities_rechecked=len(measurement['process_identities']),
            failure_stage=row.get('failure_stage'),
        ))
        for rel in ['completion.json', 'measurement/completion.json', 'flow/completion.json',
                    'config.json', 'metadata_consumers.json', 'environment_before.json',
                    'environment_after.json', 'same_role_equivalence.json',
                    'flow/stages.json', 'flow/resource_flow/stages.json']:
            path = case / rel
            if path.exists():
                sources.append(path)
        for scope, path in [('top_level_phase', case / 'flow/stages.json'),
                            ('nested_resource_phase', case / 'flow/resource_flow/stages.json')]:
            if path.exists():
                for phase in read(path):
                    phases.append(dict(arm=name, scope=scope, phase=phase['phase'],
                                       complete_process_seconds=phase['complete_process_seconds'],
                                       status=phase['status'],
                                       recorded_returncode=phase.get('returncode'),
                                       returncode_recorded='returncode' in phase))
    ratios = result['pair_domain_over_native_ratios']
    if available:
        assert len(ratios) == 2
        for i, ratio in enumerate(ratios):
            assert ratio == (result['rows'][f'domain_{i}']['complete_seconds'] /
                             result['rows'][f'native_{i}']['complete_seconds'])
    else:
        assert ratios is None
    paper_binding = D / 'sharing_prior_art_paper_binding_18.json'
    sources += [paper_binding, Path(__file__).resolve(), D / 'BNN_interleaved_timing_v1.py',
                D / 'complete_resource_timing_equivalence_v1.py']
    assert all(p.stat().st_size < 4 * 1024**2 for p in sources), 'Only small original proofs are copied'
    # Do not re-read graph bytes, route bodies or full endpoint vectors: the original
    # serial owner has just verified those and sealed the comparison's source hashes.
    out.mkdir()
    snapshots = out / 'receipt_snapshots'
    snapshots.mkdir()
    origins = []
    for i, source in enumerate(sources):
        target = snapshots / f'{i:02d}_{source.name}'
        target.write_bytes(source.read_bytes())
        digest = sha(target)
        assert digest == sha(source)
        origins.append(dict(original=str(source), snapshot=str(target), sha256=digest))
    for filename, data in [('whole_costs.csv', rows), ('phase_costs.csv', phases)]:
        with (out / filename).open('w', newline='') as f:
            fields = list(dict.fromkeys(k for row in data for k in row))
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
    payload = dict(
        passed=True, status='original_balanced_whole_measurement_and_matching_snapshotted',
        observed_at=datetime.now(timezone.utc).isoformat(), original_batch=str(root),
        original_comparison_sha256=sha(root / 'comparison.json'),
        original_queue_completion_sha256=sha(root / 'queue/completion.json'),
        registered_order=order, rows=rows, pairs=result['pairs'],
        paired_cost_observation_available=available, pair_domain_over_native_ratios=ratios,
        native_mean_seconds=result['native_mean_seconds'], domain_mean_seconds=result['domain_mean_seconds'],
        ratio_of_arm_means=(result['domain_mean_seconds'] / result['native_mean_seconds']) if available else None,
        mean_of_pair_ratios=sum(ratios) / len(ratios) if available else None,
        matched_graph_payload_files_per_arm=6,
        graph_bytes_and_full_endpoints_checked_by='original_registered_serial_owner',
        independent_verifier_rerun=False, native_or_STA_calls_by_snapshot=0,
        independent_new_inputs=0, statistical_speedup_established=False,
        nested_phase_times_must_not_be_added_to_whole=True,
        observer_CPU_must_not_be_subtracted_from_wall=True,
        original_historical_complete_overhead_percent_approximately=22.95,
        historical_result_overwritten=False, paper18_changed=False,
        research_complete=False, goal_status='active', receipt_origins=origins,
        source_sha256={r['snapshot']: r['sha256'] for r in origins},
        artifact_sha256={name: sha(out / name) for name in ['whole_costs.csv', 'phase_costs.csv']},
        qualification='Four whole-command observations of one existing BNN input, no new independent circuit, placement or architecture. Ratios are available only if original full trajectory/request/native-work, six graph payload byte, environment, fresh-root and full endpoint gates all passed. Matching graph construction and observers are included in both arms. Original complete wall intervals are used directly; nested stages and separate research verification are not stitched into a whole time. Shared host and OS caches remain uncontrolled; two observations per arm support descriptive overhead only. Sampling gaps and observer CPU remain explicit. Historical approximately22.95percent observation and paper18 prior-art/contribution boundaries are preserved. Queue completion does not complete the research goal.',
    )
    write(out / 'completion.json', payload)
    print({k: payload[k] for k in ['passed', 'paired_cost_observation_available',
                                 'pair_domain_over_native_ratios', 'ratio_of_arm_means', 'goal_status']})


if __name__ == '__main__':
    main()
