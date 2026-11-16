"""Bind the verified timing supplement without changing paper18 or its scope."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

out = D / 'BNN_timing03_balanced_claim_binding_01.json'
assert not out.exists()
receipt = D / 'BNN_timing03_balanced_receipt_01/completion.json'
r = read(receipt)
assert r['passed'] and r['paired_cost_observation_available']
assert all(sha(p) == h for p, h in r['source_sha256'].items())
assert all(sha(receipt.parent / p) == h for p, h in r['artifact_sha256'].items())
paper = D / 'paper/current_repair_main.tex'
assert sha(paper) == '56a3f70ae2bf3a79ab83af8dc519d950b912dbe1dd647bdec413ea523081afd4'
sources = [receipt, D / 'sharing_prior_art_paper_binding_18.json',
           D / 'BNN_interleaved_timing_03/comparison.json', Path(__file__).resolve()]
write(out, dict(
    passed=True, status='matched_complete_cost_supplement_no_new_independent_benefit_claim',
    current_paper='sharing_prior_art_paper_binding_18.json', paper_source_unchanged=True,
    unchanged_paper_source_sha256=sha(paper), main_table_rows=43, new_main_table_rows=0,
    new_independent_circuits=0, new_independent_placements=0, new_independent_architectures=0,
    matched_complete_measurements=4, all_four_matching_passed=True,
    supported_claims=[
        'Same known BNN resource/timing tradeoff is reproduced in all four complete observations.',
        'Full trajectories, requests, native work, actual graph bytes, environments and fresh-root/full-endpoint gates passed.',
        'Complete D/N pair ratios are descriptive observations of 1.2479595975532651 and 1.2502618238620997.',
        'Ratio of arm means is1.249107492987853; historical approximately22.95percent remains a separate original observation.',
        'At equal13.228145689936355ns,SB82to43 is47.56097561percent;SBplusCB5144to5103 is0.79704510percent.',
        'Setup534improved/803regressed and zero extra hold-violation regressions preserve the endpoint tradeoff.',
    ],
    unsupported_claims=[
        'New independent circuit, placement, architecture or CP1r3 confirmation outcome.',
        'Statistical speedup or controlled shared-host/cold-cache causal improvement.',
        'General full-method resource benefit or universal cost worthiness.',
        'Failure-release or owner-coordination attribution from these timing repetitions.',
        'All endpoint timing is nonregressing, or resource counts establish area/power savings.',
        'External-router reproduction, cross-paper numeric ranking or new primitive novelty.',
    ],
    cost_scope='Actual matched complete-command wall intervals; no component sum or observer CPU subtraction.',
    paper_prior_art_and_contribution_boundaries_unchanged=True,
    all_historical_failures_and_costs_retained=True, goal_status='active',
    source_sha256={str(p): sha(p) for p in sources},
))
print(dict(passed=True, paper18_unchanged=True, matched_observations=4, new_independent_inputs=0))
