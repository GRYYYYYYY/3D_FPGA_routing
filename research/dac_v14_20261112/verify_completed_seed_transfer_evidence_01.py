"""Read-only checks of sealed resource evidence; never launch a native process."""
from pathlib import Path
from retained_prefix_workflow import D, read, sha


def verify_evidence():
    def bindings(receipt, base=None):
        for p, h in receipt.get('source_sha256', {}).items():
            assert sha(p) == h, p
        for p, h in receipt.get('artifact_sha256', {}).items():
            assert sha(base / p) == h, p

    for name, count in [('multiobjective_completed_feedback_01', 336),
                        ('multiobjective_R1_seed_resource_01', 354),
                        ('multiobjective_completed_seed_transfer_01', 388)]:
        base = D / name
        receipt = read(base / 'completion.json')
        assert receipt['passed'] and receipt['records'] == count
        bindings(receipt, base)
    summary = read(D / 'completed_seed_transfer_summary_01.json')
    bindings(summary)
    assert summary['passed'] and (summary['completed_roles'], summary['registered_roles']) == (5, 8)
    comparisons = summary['previous_native_order_wire_comparison']
    for case in summary['paired_A0_cases']:
        circuit = case['circuit']
        for role in ['native', 'paired']:
            result = case['pair'][role]
            actor = Path(result['actor'])
            receipt = read(actor / 'completion.json')
            assert receipt['passed']
            assert receipt['final_state'] == result['final_state']
            assert receipt['final_resources'] == result['resources']
            assert receipt['final_CPD_s'] * 1e9 == result['CPD_ns']
            assert receipt['complete_imported_algorithm_workflow_seconds'] == result['imported_seconds']
            assert receipt['complete_single_configuration_algorithm_seconds'] is None
        native, paired = [case['pair'][k] for k in ['native', 'paired']]
        assert native['CPD_ns'] == paired['CPD_ns']
        assert case['paired_minus_native'] == {k: paired['resources'][k] - native['resources'][k]
                                               for k in native['resources']}
        previous = read(D / 'fused_resource_development_01' / f'{circuit}_A0_feedback_K8' / 'completion.json')
        key = 'bnn_A0' if circuit == 'bnn' else circuit
        assert previous['passed']
        assert comparisons[key + '_previous'] == previous['final_resources']['wirelength']
        assert comparisons[key + '_new'] == paired['resources']['wirelength']
        assert comparisons[key + '_delta'] == comparisons[key + '_new'] - comparisons[key + '_previous']
        for resource in ['SB_pairs', 'CB_sources']:
            assert previous['final_resources'][resource] == paired['resources'][resource]
        assert previous['final_CPD_s'] * 1e9 == paired['CPD_ns']
    r1 = summary['R1_paired']
    receipt = read(Path(r1['actor']) / 'completion.json')
    assert receipt['passed'] and receipt['accepted_steps'] == 8
    assert receipt['final_resources'] == r1['final_resources']
    assert r1['initial_CPD_s'] == r1['final_CPD_s'] == receipt['final_CPD_s']
    assert r1['root_to_final_resource_delta'] == {'wirelength': 1721, 'SB_pairs': -53, 'CB_sources': -1}
    assert r1['complete_imported_workflow_seconds'] == receipt['complete_imported_algorithm_workflow_seconds']
    mechanism = read(D / 'R1_fixed_seed_resource_mechanism_01.json')
    bindings(mechanism)
    assert all(row['equal_CPD'] and not row['native_accepted'] and row['paired_accepted']
               for row in mechanism['rows'][4:8])
    points = read(D / 'multiobjective_completed_seed_transfer_01/points.json')
    for sb, wire in [(37, 2070319), (33, 2070629)]:
        matches = [p for p in points if p['wirelength'] == wire and p['SB_pairs'] == sb
                   and p['CB_sources'] == 5071 and p['CPD_ns'] == r1['final_CPD_s'] * 1e9]
        assert matches and all(p['quality_status'] == 'nondominated_in_collected_population' for p in matches)
    return dict(passed=True, records=len(points), completed_roles=5, circuits=2, native_calls=0)


if __name__ == '__main__':
    print(verify_evidence(), flush=True)
