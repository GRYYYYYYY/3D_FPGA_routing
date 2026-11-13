#!/usr/bin/env python3
"""Describe retained-prefix costs after native neutrality passes; never rerank DP."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics

from analyze_retained_prefix import parse_trace


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def distribution(values):
    values = list(values)
    assert all(math.isfinite(v) for v in values)
    return dict(count=len(values), minimum=min(values) if values else None,
                median=statistics.median(values) if values else None,
                maximum=max(values) if values else None)


def summarize(lines):
    lines = list(lines)
    schema = parse_trace(lines)
    tables, entries, exits, reaches, decisions, pairs = {}, {}, defaultdict(list), {}, {}, []
    for line in lines:
        if not line.startswith('H3D_PREFIX_'):
            continue
        tag, *tokens = line.split()
        r = dict(token.split('=', 1) for token in tokens)
        p = int(r['plan'])
        if tag == 'H3D_PREFIX_TABLE':
            tables[p] = r
        elif tag == 'H3D_PREFIX_ENTRY':
            entries[p, int(r['entry'])] = r
        elif tag == 'H3D_PREFIX_EXIT':
            exits[p, int(r['entry'])].append(r)
        elif tag == 'H3D_PREFIX_REACH':
            reaches[p, int(r['pin']), int(r['entry']), int(r['exit'])] = int(r['reaches'])
        elif tag == 'H3D_PREFIX_PAIR':
            pairs.append(r)
        elif tag == 'H3D_PREFIX_DECISION':
            decisions[p] = int(r['accepted'])
    rows = []
    for r in pairs:
        p, pin, entry = int(r['plan']), int(r['pin']), int(r['entry'])
        e = entries[p, entry]
        unit = float(tables[p]['unit_seconds'])
        assert math.isfinite(unit) and unit > 0
        source, opening = float(e['source_units']), float(e['opening_units'])
        branch = float(r['branch_units'])
        assert all(math.isfinite(v) and v >= 0 for v in [source, opening, branch])
        charge = opening - source
        assert charge >= -1e-12
        reachable = [x for x in exits[p, entry] if reaches[p, pin, entry, int(x['exit'])]]
        expandable = [x for x in reachable if int(x['re_expand'])]
        best_reach = min((float(x['tdel_seconds']) for x in reachable), default=None)
        best_expand = min((float(x['tdel_seconds']) for x in expandable), default=None)
        known_view = bool(int(r['sink_view']))
        owned = bool(int(e['owned']))
        if not owned:
            state = 'not_owned'
        elif not exits[p, entry]:
            state = 'owned_no_crossing_child'
        elif not known_view:
            state = 'crossing_child_view_unknown'
        elif not reachable:
            state = 'crossing_child_not_reaching'
        elif not expandable:
            state = 'reachable_child_none_expandable'
        else:
            state = 'reachable_expandable_child'
        tree_entry_units = float(e['tdel_seconds']) / unit if owned else None
        rows.append(dict(plan=p, net=int(r['net']), pin=pin, entry=entry,
                         accepted=bool(decisions[p]), prior=bool(int(r['prior'])),
                         proposed=bool(int(r['proposed'])), state=state,
                         source_measured=bool(int(e['source_known'])),
                         source_units=source, opening_units=opening,
                         opening_non_source_units=charge, branch_units=branch,
                         entry_tree_delay_units=tree_entry_units,
                         entry_tree_minus_source_units=tree_entry_units-source if owned else None,
                         entry_overused=int(e['occupancy']) > int(e['capacity']),
                         best_reachable_exit_seconds=best_reach,
                         best_expandable_reachable_exit_seconds=best_expand,
                         fastest_reachable_is_not_expandable=(best_expand is not None and best_reach < best_expand),
                         direct_expandable_minus_best_reachable_seconds=best_expand-best_reach if best_expand is not None else None))
    strata = {}
    for accepted in [False, True]:
        for proposed in [False, True]:
            for measured in [False, True]:
                group = [r for r in rows if (r['accepted'], r['proposed'], r['source_measured']) == (accepted, proposed, measured)]
                key = f'accepted={int(accepted)} proposed={int(proposed)} source_measured={int(measured)}'
                strata[key] = dict(candidate_events=len(group), plans=len({r['plan'] for r in group}),
                                   nets=len({r['net'] for r in group}), states=dict(Counter(r['state'] for r in group)),
                                   overused_entry_events=sum(r['entry_overused'] for r in group),
                                   faster_nonexpandable_events=sum(r['fastest_reachable_is_not_expandable'] for r in group),
                                   opening_non_source_units=distribution(r['opening_non_source_units'] for r in group),
                                   entry_tree_minus_source_units=distribution(r['entry_tree_minus_source_units'] for r in group if r['entry_tree_minus_source_units'] is not None))
    return dict(schema_summary=schema, candidate_events=rows, strata=strata,
                qualification=[
                    'Descriptive repeated refresh events; candidate rows and repeated nets are not independent samples.',
                    'Proposed is before hysteresis; rejected proposals are not installed guides.',
                    'Direct child re_expand plus cached reachability does not certify actual heap insertion, bounding-box eligibility or feasible extension. Descendants may be expandable even when the child is not.',
                    'Entry partial-tree Tdel includes current RC/loading; source_units is a measured switch-distance or estimated surrogate. Their difference diagnoses model discrepancy, not physical error or a final-delay bound.',
                    'Opening minus source is the existing negotiated opening component, not a measured removable physical delay or a prescription to remove congestion cost.',
                    'No independent-leaf ranking, shared-DP counterfactual, confidence interval or QoR gain is inferred.'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--trace', type=Path, required=True)
    ap.add_argument('--verified-analysis', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    verified = json.loads(args.verified_analysis.read_text())
    assert verified['passed'] and verified['exact_native_reproduction']
    here = Path(__file__).resolve().parent
    assert sha(here/'analyze_retained_prefix.py') == verified['script_sha256']
    assert sha(here/'retained_prefix_workflow.py') == verified['helper_sha256']
    bindings = {str(Path(k).resolve()): v for k, v in verified['input_sha256'].items()}
    for name in ['stdout.log', 'manifest.json']:
        path = (args.trace/name).resolve()
        assert sha(path) == bindings[str(path)], name
    m = json.loads((args.trace/'manifest.json').read_text())
    assert m['status'] == 'completed' and m['metrics']['native_full_check_passed']
    result = summarize((args.trace/'stdout.log').read_text().splitlines())
    assert result['schema_summary'] == verified['summary']
    result.update(passed=True, native_evidence_inherited_from=str(args.verified_analysis.resolve()),
                  binding_sha256={str(args.verified_analysis.resolve()):sha(args.verified_analysis),
                                  str((args.trace/'stdout.log').resolve()):sha(args.trace/'stdout.log'),
                                  str(Path(__file__).resolve()):sha(__file__)},
                  audit_scope='Inherits native route/input equivalence from primary receipt; rechecks receipt parser/helper and trace/manifest bindings. Does not rerun native routing or full graph audit.')
    assert not args.out.exists(), 'Preserve prior analysis; choose a new output path'
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'passed':True,'candidate_events':len(result['candidate_events']),'strata':result['strata']}, indent=2))

if __name__ == '__main__':
    main()
