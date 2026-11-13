#!/usr/bin/env python3
"""Small-file checks for the development claim ledger, not a native/PDF audit."""
import hashlib
import json
import math
from pathlib import Path
import re
import time

PAPER = Path(__file__).resolve().parent
DEV = PAPER.parent
DOCUMENTS = ['claims_evidence.md', 'mechanisms_and_ablation.md', 'acceptance_13.md', 'README.md']

def read(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ledger_path = PAPER / 'data/evidence_v14_ledger.json'
    ledger = read(ledger_path)
    for rel, expected in ledger['sources_sha256'].items():
        assert sha(DEV / rel) == expected, rel
    links = []
    for name in DOCUMENTS:
        for dest in re.findall(r'\]\(([^)]+)\)', (PAPER / name).read_text()):
            if '://' in dest or dest.startswith('#'):
                continue
            assert (PAPER / dest.split('#')[0]).exists(), (name, dest)
            links.append((name, dest))
    sources = {
        'static_independent_vs_shared': ('static_ablation_circuit_summary.json', 'comparisons', 'N'),
        'refresh_independent_vs_shared': ('refresh_assignment_circuit_summary.json', 'comparisons', 'Tf->Ri'),
        'seen_Tf_vs_V': ('target_feedback_six_circuit_summary.json', 'paired', 'V->Tf'),
        'transfer_Tf_vs_R1': ('target_feedback_transfer_circuit_summary.json', 'paired', 'R1->Tf'),
        'transfer_Tf_vs_A0': ('target_feedback_transfer_circuit_summary.json', 'paired', 'A0->Tf'),
    }
    for key, (filename, group, arm) in sources.items():
        original = read(DEV / filename)[group][arm]
        # The static ledger omits the long individual-pair table; all retained
        # fields must match the sealed aggregate exactly, including populations.
        for field, value in ledger[key].items():
            assert original[field] == value, (key, field)
    cut = read(DEV / 'source_escape_verification_01.json')
    assert cut['passed'] and cut['aggregate'] == ledger['source_cut']
    formal = read(DEV / 'formal_timing_01/final_report_binding.json')
    assert formal == ledger['formal_timing'] and formal['status'] == 'sealed_export_passed'
    for relative, expected in formal['source_sha256'].items():
        assert sha(DEV / 'formal_timing_01' / relative) == expected
    for relative, expected in formal['artifacts_sha256'].items():
        assert sha(DEV / relative) == expected
    timing = read(DEV / 'formal_timing_01/analysis.json')
    assert timing['sealed'] and timing['batch_complete'] and timing['statuses'] == {'legal': 45}
    assert formal['process_reduction_vs_R1_pct'] == (1-timing['comparisons']['R1->U']['circuit_geomean_new_over_reference'])*100
    assert formal['process_overhead_vs_A0_pct'] == (timing['comparisons']['A0->U']['circuit_geomean_new_over_reference']-1)*100
    claims = (PAPER / 'claims_evidence.md').read_text()
    candidate_report = read(DEV / 'candidate_path_report_binding_01.json')
    assert candidate_report == ledger['candidate_path_development_report']
    assert sha(DEV / 'candidate_path_development_summary_01.json') == candidate_report['summary_sha256']
    assert sha(DEV / 'export_candidate_path_results.py') == candidate_report['exporter_sha256']
    for relative, expected in candidate_report['artifacts_sha256'].items():
        assert sha(DEV / relative) == expected
    candidate_summary = read(DEV / 'candidate_path_development_summary_01.json')
    assert candidate_summary['status_counts'] == {'legal': 17}
    assert len(candidate_summary['observations']) == candidate_report['roles'] == 17
    assert sum(row['reused'] for row in candidate_summary['observations']) == 4
    gate_binding = read(DEV / 'source_coverage_gate_report_binding_01.json')
    assert gate_binding == ledger['source_coverage_gate']['report_binding']
    assert sha(DEV / 'source_coverage_gate_summary_01.json') == gate_binding['report_sha256']
    assert sha(DEV / 'report_source_coverage_gate.py') == gate_binding['exporter_sha256']
    for relative, expected in gate_binding['artifacts_sha256'].items():
        assert sha(DEV / relative) == expected
    gate = read(DEV / 'source_coverage_gate_summary_01.json')
    assert gate['status_counts'] == {'legal': 10} and len(gate['observations']) == 10
    assert sum(row['reused'] for row in gate['observations']) == 4
    old_gate, new_gate = gate['pairs']['G->E'], gate['pairs']['F->N']
    assert all(old_gate[name] for name in ['same_complete_route', 'same_final_guides', 'same_all_base_table_fingerprints', 'same_all_prefix_tables_and_decisions'])
    assert new_gate['same_complete_route'] and not new_gate['same_final_guides'] and not new_gate['same_all_prefix_tables_and_decisions']
    assert old_gate['acceptance_changes'] == new_gate['acceptance_changes'] == 0
    assert gate['availability_oracle']['candidate_availability_checks'] == ledger['source_coverage_gate']['candidate_flags_checked'] == 765936
    ratio = int(old_gate['counters']['E']['delay']['queries']) / int(old_gate['counters']['G']['delay']['queries'])
    assert f"{(1-ratio)*100:.6f}%" in claims
    policy_binding = read(DEV / 'guide_policy_development_01_binding.json')
    table_binding = read(DEV / 'guide_policy_table_binding_01.json')
    assert policy_binding == ledger['guide_policy']['report_binding']
    assert table_binding == ledger['guide_policy']['table_binding']
    assert sha(DEV / 'guide_policy_development_01.json') == policy_binding['report_sha256'] == table_binding['report_sha256']
    assert sha(DEV / 'export_guide_policy_results.py') == policy_binding['exporter_sha256']
    assert sha(DEV / 'render_guide_policy_table.py') == table_binding['renderer_sha256']
    for binding in [policy_binding, table_binding]:
        for relative, expected in binding['artifacts_sha256'].items():
            assert sha(DEV / relative) == expected
    policy = read(DEV / 'guide_policy_development_01.json')
    assert policy['status_counts'] == {'legal': 27} and len(policy['observations']) == 27
    assert policy_binding['new_roles'] == 19 and policy_binding['reused_native_roles'] == 8
    assert sum(row['reused'] for row in policy['observations']) == 8
    for label, signed in [('fixed_count1:C->T', False), ('fixed_traceoff:C->T', True), ('after_legal:C->P', True)]:
        value = policy['pairs'][label]['cpd_improvement_pct']
        assert (value > 0) == signed
        assert f"{abs(value):.6f}%" in claims
    assert policy['pairs']['count2:A0->fixed_traceoff/T']['cpd_improvement_pct'] == 0.
    for count in [1, 2]:
        row = next(r for r in policy['observations'] if r['group'] == ('cap_count1' if count == 1 else 'cap') and r['arm'] == 'K')
        original = next(r for r in policy['observations'] if r['group'] == ('fixed_count1' if count == 1 else 'fixed_traceoff') and r['arm'] == 'T')
        assert row['legal_cpd_ns'] == original['legal_cpd_ns'] and row['iterations'] == original['iterations']
    native = read(DEV / 'native_reconvergence_report_binding.json')
    assert native == ledger['native_reconvergence'] and native['status'] == 'sealed_count2_export_passed'
    for path, expected in native['source_sha256'].items():
        assert sha(Path(path)) == expected
    for relative, expected in native['artifacts_sha256'].items():
        assert sha(DEV / relative) == expected
    assert sha(DEV / 'export_native_reconvergence.py') == native['exporter_sha256']
    reconvergence = read(DEV / 'native_reconvergence_circuit_summary.json')
    assert reconvergence['status'] == 'sealed_four_case_aggregate'
    assert reconvergence['status_counts'] == {'legal': 32} and len(reconvergence['observations']) == 32
    assert all(r['prefix_gate_passed'] for r in reconvergence['observations'])
    for label in ['count1:R1->Tf', 'count2:R1->Tf', 'count2:A0->Tf', 'count2:A1->Tf']:
        comparison = reconvergence['comparisons'][label]
        assert comparison['comparable_circuit_count'] == 4
        ratios = [p['new_cpd_ns']/p['reference_cpd_ns'] for p in comparison['pairs'] if p['comparable']]
        recomputed = (1-math.exp(math.fsum(math.log(r) for r in ratios)/len(ratios)))*100
        assert math.isclose(comparison['circuit_geomean_improvement_pct'], recomputed, abs_tol=1e-12)
        displayed = f"{comparison['circuit_geomean_improvement_pct']:+.6f}%".replace('-', '−')
        assert displayed in claims, (label, displayed)
    for key, field in [
        ('static_independent_vs_shared', 'geomean_improvement_pct'),
        ('refresh_independent_vs_shared', 'circuit_geomean_improvement_pct'),
        ('seen_Tf_vs_V', 'circuit_geomean_improvement_pct'),
        ('transfer_Tf_vs_A0', 'circuit_geomean_improvement_pct'),
        ('transfer_Tf_vs_A0', 'worst_improvement_pct'),
    ]:
        formatted = f"{ledger[key][field]:+.6f}%".replace('-', '−')
        assert formatted in claims, (key, formatted)
    result = {
        'updated_at': time.time(), 'status': 'passed',
        'scope': 'Bound small-file digests, local links, exact aggregate field matches and displayed CPD percentages; no PDF build or native/source audit',
        'source_count': len(ledger['sources_sha256']), 'local_link_count': len(links),
        'documents_sha256': {name: sha(PAPER / name) for name in DOCUMENTS},
        'ledger_sha256': sha(ledger_path), 'validator_sha256': sha(Path(__file__)),
    }
    (PAPER / 'data/evidence_v14_ledger_validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
