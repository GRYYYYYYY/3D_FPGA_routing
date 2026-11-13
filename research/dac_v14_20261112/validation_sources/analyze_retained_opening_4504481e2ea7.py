#!/usr/bin/env python3
"""Audit the opening-credit mechanism and report every declared quality status."""
import argparse
import collections
import json
import math
from pathlib import Path
import re
from retained_prefix_workflow import read, write, sha, normalized_command, route_body
from analyze_retained_prefix import parse_trace

def credit_records(lines, weight, alpha):
    count = owned = credited = premium = 0
    for line in lines:
        if not line.startswith('H3D_PREFIX_ENTRY '):
            continue
        r = dict(t.split('=', 1) for t in line.split()[1:])
        own = int(r['owned']); occupancy = int(r['occupancy'])
        demand = occupancy + (0 if own else 1)
        negotiated = float(r['acc_cost']) * (1 + float(r['pres_fac']) * max(0, demand-int(r['capacity'])))
        expected_credit = alpha * min(1, negotiated) if own else 0
        observed = float(r['opening_units'])-float(r['source_units'])
        assert math.isclose(observed, weight*(negotiated-expected_credit), rel_tol=1e-11, abs_tol=1e-9), r
        # Independently check that all above-baseline negotiated cost survives.
        assert observed + 1e-9 >= weight*max(0, negotiated-1)
        count += 1; owned += own; credited += expected_credit > 0; premium += negotiated > 1
    return dict(entry_table_records=count, owned_entry_table_records=owned,
                credited_entry_table_records=credited, negotiated_premium_records=premium,
                formula_passed=True, scope='Unique plan/entry records; repeated trajectory observations, not independent samples.')

def initial_tables(lines):
    result = []
    for line in lines:
        if line.startswith('H3D_TARGET_REFRESH '):
            break
        if line.startswith('H3D_TABLE '):
            result.append(line)
    return result

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('batch', type=Path); args = ap.parse_args()
    b = args.batch; reg = read(b/'registration.json'); done = read(b/'completion.json')
    assert read(b/'input_seal.json')['passed']
    bindings = {str(p):sha(p) for p in [b/'registration.json', b/'completion.json', b/'input_seal.json']}
    refs = read(b/f"{reg['circuits'][0]}_references.json")
    rows = []; logs = {}; native = {}
    for arm in ['A0', 'R1', 'Tf', 'C', 'Mo']:
        rd = Path(refs[arm]['path']) if arm in refs else b/'runs'/f"{reg['circuits'][0]}_{arm}"
        mp = rd/'manifest.json'
        if not mp.exists():
            rows.append(dict(arm=arm, status='missing', legal_cpd_ns=None)); continue
        m = read(mp); bindings[str(mp)] = sha(mp)
        assert normalized_command(m['command']) == normalized_command(read(Path(refs['Tf']['path'])/'manifest.json')['command'])
        for n,v in m['outputs'].items(): assert sha(rd/n) == v['sha256'], rd/n
        audit = read(rd/'independent_audit.json') if (rd/'independent_audit.json').exists() else None
        legal = m['status']=='completed' and m['metrics'].get('native_full_check_passed') and bool(audit and audit['audit']['passed'])
        if legal:
            bindings[str(rd/'independent_audit.json')] = sha(rd/'independent_audit.json')
            if arm in ['Tf','C','Mo']:
                assert read(rd/'final_guide_audit.json')['passed']
                bindings[str(rd/'final_guide_audit.json')] = sha(rd/'final_guide_audit.json')
        lines = (rd/'stdout.log').read_text().splitlines(); plans = re.findall(r'^H3D_PLAN .*?planning_seconds=([\d.]+)', '\n'.join(lines), re.M)
        rows.append(dict(arm=arm, path=str(rd), status='legal' if legal else m['status'] if m['status']!='completed' else 'completed_not_certified',
            legal_cpd_ns=m['metrics'].get('critical_path_ns') if legal else None,
            native_cpd_ns=m['metrics'].get('critical_path_ns'), iterations=m['metrics'].get('iterations'),
            planning_seconds=float(plans[-1]) if plans else 0. if arm=='A0' else None,
            process_seconds=m['wall_seconds'], physical_metrics=audit['physical_metrics'] if legal else None,
            route_body_sha256=route_body(rd/'routed.route') if (rd/'routed.route').exists() else None))
        if arm in ['C','Mo']:
            logs[arm] = lines; native[arm] = m
            if legal:
                summary = parse_trace(lines) if any(x.startswith('H3D_PREFIX_TABLE ') for x in lines) else dict(finite_tables=0)
                rows[-1]['mechanism'] = dict(trace=summary, credit=credit_records(lines,16.,0. if arm=='C' else reg['retained_opening_credit']))
    if 'C' in native:
        assert read(b/'runs'/f"{reg['circuits'][0]}_C"/'disabled_reproduction.json')['passed'] == done['gate_passed']
    if 'C' in native and 'Mo' in native:
        c,m = native['C'],native['Mo']; e0,e1 = dict(c['environment']),dict(m['environment'])
        assert e0.pop('VPR_H3D_RETAINED_OPENING_CREDIT')=='0'
        assert float(e1.pop('VPR_H3D_RETAINED_OPENING_CREDIT'))==reg['retained_opening_credit']
        assert e0 == e1
        assert c['command'][0] == m['command'][0]
        assert sha(c['command'][0]) == reg['binary_sha256']
        assert normalized_command(c['command']) == normalized_command(m['command'])
        for n in ['packed.net','placed.place']:
            assert sha(Path(c['cwd'])/n)==sha(Path(m['cwd'])/n)
        assert initial_tables(logs['C'])==initial_tables(logs['Mo'])
    index = {r['arm']:r for r in rows}; comparisons = {}
    for ref in ['A0','R1','Tf','C']:
        x,y = index[ref],index['Mo']; valid = x['status']==y['status']=='legal'
        comparisons[ref+'->Mo'] = dict(both_legal=valid,
            cpd_improvement_pct=(x['legal_cpd_ns']-y['legal_cpd_ns'])/x['legal_cpd_ns']*100 if valid else None,
            same_route=x.get('route_body_sha256')==y.get('route_body_sha256') if valid else None)
    result = dict(passed=True, circuit=reg['circuits'][0], seed=reg['seed'], statuses=dict(collections.Counter(r['status'] for r in rows)),
        observations=rows, comparisons=comparisons, input_sha256=bindings, script_sha256=sha(__file__),
        qualification='Same-parameter development ablation. Raw failure delay excluded from legal CPD. Process costs include tracing and are not formal speedup evidence. Ownership credit does not guarantee retained-child adoption.')
    write(b/'opening_analysis.json', result)
    print(json.dumps({k:result[k] for k in ['passed','circuit','statuses','comparisons']},indent=2))

if __name__=='__main__':main()
