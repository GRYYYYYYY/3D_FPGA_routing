#!/usr/bin/env python3
"""Analyze tied groups and criticality scaling from already validated exports."""
import collections
import json
import struct
from retained_prefix_workflow import D, read, write, sha, route_body

b = D / 'native_sta_frontier_dev_03'
validation = read(b / 'frontier_validation.json')
assert validation['passed']
frontiers = read(b / 'ranked_frontiers.json')
summary = {}
for role, rows in frontiers.items():
    worst = rows[0]['setup_slack_s']
    magnitude_bits = struct.unpack('<I', struct.pack('<f', abs(worst)))[0]
    ulp = struct.unpack('<f', struct.pack('<I', magnitude_bits + 1))[0] - abs(worst)
    assert ulp > 0
    ties = [r for r in rows if r['setup_slack_s'] <= worst + 8 * ulp]
    critical_one = [r for r in rows if r['setup_criticality_raw'] == 1.]
    def entry(row):
        return dict(net=row['net'], pin=row['pin'], slack_s=row['setup_slack_s'],
                    gap_from_worst_ns=(row['setup_slack_s'] - worst) * 1e9,
                    criticality_raw=row['setup_criticality_raw'], native_delay_s=row['native_net_delay_s'],
                    atoms=[a['name'] for a in row['atoms']],
                    setup_tags=[t for a in row['atoms'] for t in a['setup_tags']])
    summary[role] = dict(ulp_seconds=ulp, grouping_tolerance_seconds=8 * ulp,
                         worst_slack_seconds=worst, tie_group=[entry(r) for r in ties],
                         raw_criticality_exact_one=[entry(r) for r in critical_one],
                         exact_one_misses_tied=sum(r['setup_criticality_raw'] != 1. for r in ties),
                         near_within_0p2ns=sum(r['setup_slack_s'] <= worst + .2e-9 for r in rows),
                         interpretation='Eight float ULPs groups numerical ties only; 0.2ns window is a separate descriptive near-critical population. Raw criticality is per-constraint normalized and is not a globally comparable CPD rank.')
binding = {str(b / name): sha(b / name) for name in ['frontier_validation.json', 'ranked_frontiers.json', 'completion.json']}
binding[str(D / 'analyze_native_sta_frontier.py')] = sha(__file__)
cases = D / 'actual_search_tree_eltwise_dev_01/actual_cases.jsonl'
observed = collections.Counter()
with cases.open() as stream:
    for line in stream:
        c = json.loads(line)['context']
        observed[int(c['net']), int(c['pin'])] += 1
summary['Tf']['guided_history_overlap'] = [dict(net=r['net'], pin=r['pin'], contexts=observed[r['net'], r['pin']])
                                           for r in summary['Tf']['tie_group']]
binding[str(cases)] = sha(cases)
write(b / 'frontier_mechanism_analysis.json', dict(passed=True, roles=summary, source_sha256=binding,
      native_analysis_calls_added=0, route_search_calls=0,
      conclusions=['A single rounded worst-path report omits simultaneously critical branches. Full native pin mapping reveals them without placement-location ambiguity.',
                   'Do not select by criticality == 1 or compare per-domain normalized criticality as a global CPD ranking.',
                   'The 0.2ns near-frontier grows after the joint repair; future gains may require more groups/CPD-aware resource trades. This count is not proof that each connection needs rerouting.'],
      pending='Same complete repair policy applied to A0/R1/Tf; multi-domain CPD normalization; generic joint candidate search; integrated and formal timing.'))
print({role: dict(tied=len(s['tie_group']), near=s['near_within_0p2ns'], exact_one_misses=s['exact_one_misses_tied'],
                  guided=s.get('guided_history_overlap')) for role, s in summary.items()})
