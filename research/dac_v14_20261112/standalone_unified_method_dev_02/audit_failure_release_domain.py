#!/usr/bin/env python3
"""Verify per-query domain enforcement and failure-triggered, one-time net release."""
import argparse
import collections
from pathlib import Path
from retained_prefix_workflow import read, write, sha
from resource_opportunity_census import stream_trace
from coordinated_repair_tree import from_trace, prune_sinks
from run_native_scope_policy_v4 import run_dir

p = argparse.ArgumentParser()
p.add_argument('--batch', type=Path, required=True)
p.add_argument('--role', required=True)
a = p.parse_args()
b = a.batch.resolve()
role = read(b / 'registration.json')['roles'][a.role]
rd = run_dir(b / a.role)
audit = read(b / (a.role + '_audit/analysis.json'))
assert audit['passed'] and role['crossing_reuse_enabled'] and role['domain_failure_release']
tokens = Path(role['crossing_domain']).read_text().split()
initial = set(map(int, tokens[1:]))
assert len(initial) == int(tokens[0]) == len(tokens) - 1
assert initial <= set(map(int, role['removed_pins']))
source = Path(role['source'])
expected = {}
for record in stream_trace(source / 'routed.route'):
    net = record['net']
    if net not in initial:
        continue
    points = {n.inode: n for n in record['trace']}
    original = from_trace(record['trace'], collections.defaultdict(float))
    retained = prune_sinks(original, role['removed_pins'][str(net)])
    expected[net] = {up for n, (up, sw, w) in retained['edges'].items() if points[n].low[2] != points[up].low[2]}
assert set(expected) == initial
queries = [[q['net'], q['pin']] for q in audit['queries']]
assert queries == [[q['net'], q['pin']] for q in role['queries']][:len(queries)]
lines = (rd / 'joint_native.log').read_text().splitlines()
release_rows = []
attempts = []
for line in lines:
    row = line.split()
    if row[0] == 'ATTEMPT':
        attempts.append(row)
    if row[0] == 'DOMAIN_RELEASE':
        target = tuple(map(int, row[1:3]))
        assert attempts and tuple(map(int, attempts[-1][1:3])) == target and attempts[-1][-1] == '0'
        release_rows.append(list(target))
active = set(initial)
allowed = set()
released = []
checks = []
trace = [line.split() for line in (rd / 'vertical_domain.log').read_text().splitlines()]
assert trace[-1][0] == 'COMPLETE' and trace[-1][-1] == 'occupancy_restored'
for row in trace[:-1]:
    net, pin = map(int, row[1:3])
    key = (net, pin)
    assert [net, pin] in queries
    if row[0] == 'ALLOW':
        assert net in active and key not in allowed
        sources = set(map(int, row[4:]))
        assert len(sources) == int(row[3]) and sources == expected[net]
        allowed.add(key)
    elif row[0] == 'RELEASE':
        assert key in allowed and net in active and row[3] == 'domain_search_infeasible'
        active.remove(net)
        released.append([net, pin])
    else:
        assert row[0] == 'CHECK' and key in allowed and net in active and row[3] == '1'
        checks.append([net, pin])
assert released == release_rows
assert len(released) == len({q[0] for q in released})
# Reconstruct expected trace decisions in real query order, including later pins.
active_at_query = set(initial)
for net, pin in queries:
    if net in active_at_query:
        assert (net, pin) in allowed
        if [net, pin] in released:
            active_at_query.remove(net)
        else:
            # The last incomplete query need not reach the tree-domain CHECK.
            q = next(q for q in audit['queries'] if q['net'] == net and q['pin'] == pin)
            if q['feasible']:
                assert [net, pin] in checks
    else:
        assert (net, pin) not in allowed
assert active_at_query == active
actual = {}
if audit.get('candidate_route'):
    for record in stream_trace(audit['candidate_route']):
        if record['net'] not in active:
            continue
        sources = {x.inode for x, y in zip(record['trace'], record['trace'][1:]) if x.switch != -1 and x.low[2] != y.low[2]}
        assert sources <= expected[record['net']]
        actual[str(record['net'])] = sorted(sources)
files = [Path(__file__).resolve(), b / 'registration.json', b / a.role / 'completion.json',
         b / (a.role + '_audit/analysis.json'), rd / 'joint_native.log', rd / 'vertical_domain.log',
         source / 'routed.route', Path(role['crossing_domain'])]
write(b / (a.role + '_domain_audit.json'), dict(passed=True, enabled=True,
      initial_domain_nets=sorted(initial), final_domain_nets=sorted(active), released_queries=released,
      actual_candidate_guided_sources=actual, source_sha256={str(p): sha(p) for p in files},
      qualification='Release follows an observed failed search before tree update; it is not by itself a mathematical capacity proof. Independent physical audit validates all branches/capacities, including released nets. All still-guided nets obey the original retained-crossing domain. Candidate native FULL/STA remains mandatory.'))
print(dict(passed=True, released=released, guided_nets=len(active)), flush=True)
