#!/usr/bin/env python3
"""Seal evidence only after routing, auditing, collection and report review."""
from pathlib import Path
import math
from three_baseline_common import BASE, ROOT, read, sha256, utc, write_json


def main():
    output=BASE/'finalization.json'
    assert not output.exists()
    protocol=read(BASE/'protocol.json');validation=read(BASE/'validation.json');summary=read(BASE/'summary.json')
    assert read(BASE/'finisher_state.json')['stage']=='finished'
    assert validation['passed'] and summary['validated']
    assert summary['validation_sha256']==sha256(BASE/'validation.json')
    assert validation['protocol_sha256']==sha256(BASE/'protocol.json')
    state=read(BASE/'route_state.json');assert state['stage']=='finished'
    expected={j['name'] for j in state['jobs'] if j.get('native_legal')}
    assert expected=={a['name'] for a in validation['audits'] if a['passed']}
    assert len(expected)==len(validation['audits'])
    assert all(sha256(ROOT/p)==h for p,h in protocol['preserved_sources'].items())
    qa=read(BASE/'qa.json');assert qa['passed']
    resources=read(BASE/'native_resource_metrics.json')
    assert resources['summary_sha256']==sha256(BASE/'summary.json')
    rows={(r['case'],r['arm']):r for r in summary['rows']}
    valid_cases={case for case in protocol['cases'] if all(rows[(case,arm)]['valid_solution'] for arm in ('a0','a3'))}
    for metric, record in resources['metrics'].items():
        assert {p['case'] for p in record['pairs']}==valid_cases
        assert len(record['pairs'])==record['paired_cases']==len(valid_cases)
        for pair in record['pairs']:
            assert pair['a0']==rows[(pair['case'],'a0')]['route'][metric]
            assert pair['a3']==rows[(pair['case'],'a3')]['route'][metric]
            assert pair['ratio']==pair['a3']/pair['a0']
        gm=math.exp(sum(math.log(p['ratio']) for p in record['pairs'])/len(record['pairs']))
        assert gm==record['geomean_ratio'] and (gm-1)*100==record['change_percent']
    identity=read(BASE/'algorithm_identity.json')
    assert identity['passed'] and len(identity['runs'])==len(valid_cases)
    report=ROOT/'docs/三基线对比_2026-10-27.md'
    assert '运行与独立审计尚在进行' not in report.read_text()
    assert '待本轮全部运行结束' not in report.read_text()
    sources=[ROOT/'scripts'/n for n in (
        'three_baseline_common.py','run_three_baselines.py','audit_three_baseline_graphs.py',
        'validate_three_baselines.py','collect_three_baselines.py','finish_three_baselines.py',
        'finalize_three_baselines.py','check_route.py','compare_lazagna_graphs.py',
        'audit_lazagna_vertical.py','audit_lazagna_dsp_correspondence.py',
        'check_lazagna_clock_graph_mode.py','run_vpr.py','lazagna_common.py',
        'validate_lazagna_vtr9_pilot.py','prepare_lazagna_study.py')]
    sources += [ROOT/'tests/test_three_baseline_statistics.py']
    sources += [Path(v['manifest']) for v in protocol['binaries'].values()]
    sources += [ROOT/'patches/lazagna-vtr9-build-portability.patch']
    sources += [ROOT/'configs/variants_a0_a4.json']
    metadata=list(BASE.glob('*.json'))+list((BASE/'sources').glob('*.json'))
    metadata += list((BASE/'runs').glob('*/manifest.json'))+list((BASE/'runs').glob('*/result.json'))
    metadata += [BASE/'per_case.csv',report,ROOT/'README.md',ROOT/'docs/reproduction.md',
                 ROOT/'docs/研究结论.md',ROOT/'docs/交接说明_2026-10-25.md']
    write_json(output,dict(utc=utc(),completed=True,registered_jobs=len(state['jobs']),
        attempted_routes=validation['attempted_routes'],audited_successful_routes=len(expected),
        frozen_files_unchanged=len(protocol['preserved_sources']),
        counts=summary['counts'],source_files={str(p.relative_to(ROOT)):sha256(p) for p in sources},
        evidence_files={str(p.relative_to(ROOT)):sha256(p) for p in sorted(set(metadata))},
        scope='Registered 11-case diagnostic comparison completed. B1 remains a literature reference without a numerical A3/published ratio; see the report for cohort, clock and graph-model limits.'))
    print(output,flush=True)


if __name__=='__main__':
    main()
