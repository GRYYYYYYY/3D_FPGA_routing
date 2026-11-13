#!/usr/bin/env python3
"""Check trace neutrality and separate owned entries from usable retained exits."""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import math
from retained_prefix_workflow import original_records


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_trace(lines):
    tables, entries, exits, pairs, reaches, decisions, skipped = {}, {}, {}, {}, {}, {}, {}
    for line in lines:
        if not line.startswith('H3D_PREFIX_'):
            continue
        tag, *tokens = line.split()
        r = dict(token.split('=', 1) for token in tokens)
        plan = int(r['plan'])
        if tag == 'H3D_PREFIX_TABLE':
            assert plan not in tables and plan not in skipped
            tables[plan] = r
        elif tag == 'H3D_PREFIX_SKIP':
            assert plan not in tables and plan not in skipped
            skipped[plan] = r
        else:
            assert plan in tables and r['net'] == tables[plan]['net']
            if tag == 'H3D_PREFIX_ENTRY':
                key, target = (plan, int(r['entry'])), entries
            elif tag == 'H3D_PREFIX_EXIT':
                key, target = (plan, int(r['entry']), int(r['exit'])), exits
            elif tag == 'H3D_PREFIX_PAIR':
                key, target = (plan, int(r['pin']), int(r['entry'])), pairs
            elif tag == 'H3D_PREFIX_REACH':
                key, target = (plan, int(r['pin']), int(r['entry']), int(r['exit'])), reaches
            elif tag == 'H3D_PREFIX_DECISION':
                key, target = plan, decisions
            else:
                raise AssertionError(tag)
            assert key not in target
            target[key] = r
    assert tables and set(tables) == set(decisions)
    assert sorted(set(tables) | set(skipped)) == list(range(1, len(tables) + len(skipped) + 1))
    exit_groups = collections.defaultdict(list)
    for (plan, entry, exit_id), r in exits.items():
        assert (plan, entry) in entries
        assert int(r['re_expand']) in [0, 1]
        for k in ['tdel_seconds', 'r_upstream', 'c_downstream']:
            assert math.isfinite(float(r[k])) and float(r[k]) >= 0
        exit_groups[plan, entry].append((exit_id, r))
    for (plan, entry), r in entries.items():
        owned = int(r['owned'])
        assert owned in [0, 1]
        assert int(r['retained_exits']) == len(exit_groups[plan, entry])
        assert owned or not exit_groups[plan, entry]
        assert float(r['opening_units']) >= float(r['source_units']) - 1e-12
        if owned:
            assert int(r['occupancy']) >= 1
            for k in ['tdel_seconds', 'r_upstream', 'c_downstream']:
                assert math.isfinite(float(r[k])) and float(r[k]) >= 0
            for _, child in exit_groups[plan, entry]:
                assert float(child['tdel_seconds']) + 1e-18 >= float(r['tdel_seconds'])
        else:
            assert math.isnan(float(r['tdel_seconds']))
    counts = collections.Counter()
    leaf_events = collections.defaultdict(list)
    reach_keys = set()
    for (plan, pin, entry), r in pairs.items():
        assert int(r['prior']) in [0, 1] and int(r['proposed']) in [0, 1]
        e = entries[plan, entry]
        reachable = []
        for exit_id, child in exit_groups[plan, entry]:
            key = (plan, pin, entry, exit_id)
            reach_keys.add(key)
            reach = reaches[key]
            assert reach['sink_view'] == r['sink_view']
            assert int(reach['reaches']) in [0, 1]
            if int(reach['reaches']):
                assert int(r['sink_view']) == 1
                reachable.append(child)
        assert int(r['reachable_exits']) == len(reachable)
        assert int(r['expandable_exits']) == sum(int(c['re_expand']) for c in reachable)
        if reachable:
            assert math.isclose(float(r['best_exit_tdel_seconds']), min(float(c['tdel_seconds']) for c in reachable), rel_tol=1e-12, abs_tol=1e-18)
        else:
            assert math.isnan(float(r['best_exit_tdel_seconds']))
        assert math.isfinite(float(r['branch_units']))
        counts['finite_candidate_events'] += 1
        counts['owned_candidate_events'] += int(e['owned'])
        counts['retained_crossing_candidate_events'] += bool(exit_groups[plan, entry])
        counts['retained_reachable_candidate_events'] += bool(reachable)
        counts['retained_expandable_candidate_events'] += int(r['expandable_exits']) > 0
        counts['proposed_retained_reachable_events'] += bool(reachable) and int(r['proposed']) == 1
        counts['missing_cached_view_events'] += int(r['sink_view']) == 0
        leaf_events[plan, pin].append(r)
    assert reach_keys == set(reaches)
    for plan, table in tables.items():
        assert int(decisions[plan]['accepted']) in [0, 1]
        assert sum(p == plan for p, _ in entries) == int(table['candidates'])
        assert sum(p == plan for p, _ in leaf_events) <= int(table['leaves'])
    assert all(sum(int(r['proposed']) for r in rs) <= 1 for rs in leaf_events.values())
    return dict(table_plans=len(tables), skipped_plans=len(skipped),
                skip_reasons=dict(collections.Counter(r['reason'] for r in skipped.values())),
                accepted_plans=sum(int(r['accepted']) for r in decisions.values()),
                leaf_events=len(leaf_events), leaves_with_retained_reachable_option=sum(any(int(r['reachable_exits']) for r in rs) for rs in leaf_events.values()),
                counters=dict(counts), scope='Repeated finite refresh events, not independent observations. '
                'Rejected proposals included. Reachability flags come from cached SCC views, not a new independent graph audit. '
                'Retained partial-tree Tdel/RC is not final STA or a certified extension-delay bound.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--control', type=Path, required=True)
    ap.add_argument('--trace', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    paths = []
    manifests, logs = [], []
    for rd in [args.control, args.trace]:
        for p in [rd.parent.parent / 'input_seal.json', rd / 'final_guide_audit.json']:
            assert json.loads(p.read_text())['passed']
            paths.append(p)
        audit = rd / 'independent_audit.json'
        assert json.loads(audit.read_text())['audit']['passed']
        m = json.loads((rd / 'manifest.json').read_text())
        assert m['status'] == 'completed' and m['metrics']['native_full_check_passed']
        for filename, expected in m['outputs'].items():
            assert sha(rd / filename) == expected['sha256']
        manifests.append(m)
        logs.append((rd / 'stdout.log').read_text().splitlines())
        paths.extend([audit, rd / 'manifest.json', rd / 'stdout.log', rd / 'routed.route', rd / 'h3d_final_guides.csv'])
    c, t = manifests
    assert c['shared_inputs'][c['command'][0]]['sha256'] == t['shared_inputs'][t['command'][0]]['sha256']
    env = dict(t['environment']); assert env.pop('VPR_H3D_TRACE_RETAINED_PREFIX') == '1'
    other = dict(c['environment']); assert other.pop('VPR_H3D_TRACE_RETAINED_PREFIX', '0') == '0'
    assert env == other
    def normalized(command):
        command = list(command[1:])
        for opt in ['--net_file', '--place_file', '--route_file']:
            command[command.index(opt) + 1] = '<private>'
        return command
    assert normalized(c['command']) == normalized(t['command'])
    for name in ['packed.net', 'placed.place', 'h3d_final_guides.csv']:
        assert sha(args.control / name) == sha(args.trace / name)
        paths.extend([args.control / name, args.trace / name])
    def body(p):
        s = p.read_text(); return s[s.index('Net '):]
    assert body(args.control / 'routed.route') == body(args.trace / 'routed.route')
    for k in ['critical_path_ns', 'wirelength', 'iterations']:
        assert c['metrics'][k] == t['metrics'][k]
    assert original_records(logs[0]) == original_records(logs[1])
    assert not any(l.startswith('H3D_PREFIX_') for l in logs[0])
    summary = parse_trace(logs[1])
    out = dict(passed=True, exact_native_reproduction=True, summary=summary,
               input_sha256={str(p): sha(p) for p in paths}, script_sha256=sha(Path(__file__)),
               helper_sha256=sha(Path(__file__).with_name('retained_prefix_workflow.py')))
    args.out.write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
