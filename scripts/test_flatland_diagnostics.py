#!/usr/bin/env python3
"""Check cumulative counters and absence-aware delay coverage aggregation."""
from analyze_flatland_evaluation import guide_diagnostics
from analyze_flatland_diagnostics import summarize
from flatland_benchmark import BASE
from lazagna_common import ROOT,sha256,utc,write_json


def main():
    text='H3D_SCORE eligible=1 skipped=0 delay_scored=1 unmeasured=0\nH3D_SCORE eligible=10 skipped=2 delay_scored=3 unmeasured=7\nH3D_DELAY queries=4 settled=12 truncated=2 cache_hits=1 cached_endpoints=3\nH3D_PLAN plans=2 groups=3 planning_seconds=0.125\n'
    counters=guide_diagnostics(text)
    assert counters['guide_coverage']['eligible']==10 and counters['guide_coverage']['delay_scored']==3
    assert counters['planner']['planning_seconds']==.125 and counters['delay_search']['truncated']==2
    def row(role,eligible,measured,unknown,status='legal'):
        return dict(phase='heldout',family='sb',flow='p0',role=role,status=status,configuration=dict(router='R1'),
            guide_coverage=dict(eligible=eligible,skipped=0,delay_scored=measured,unmeasured=unknown))
    result=summarize([row('R1',1,1,0),row('R1',100,0,100),row('R1',1,1,0,'timeout'),row('fixed_geometry',20,0,0)])
    by_role={r['role']:r for r in result['groups']};a=by_role['R1'];g=by_role['fixed_geometry']
    assert a['registered_roles']==3 and a['legal_roles']==2
    assert a['run_mean_fractions']['fully_delay_scored_pin_fraction']==dict(mean=.5,valid_runs=2)
    assert a['count_totals']['eligible']==101
    assert 'fully_delay_scored_pin_fraction' not in g['run_mean_fractions']
    assert 'truncated_query_fraction' not in a['run_mean_fractions']
    path=BASE/'diagnostics_validation.json';assert not path.exists()
    write_json(path,dict(utc=utc(),passed=True,sources={str(ROOT/'scripts'/n):sha256(ROOT/'scripts'/n)
        for n in ['analyze_flatland_evaluation.py','analyze_flatland_diagnostics.py','test_flatland_diagnostics.py']},
        checks=['use last cumulative counters, do not sum repeated log snapshots','parse measured planning time',
            'average run fractions without unintended pin-count weighting','retain failed roles in denominator',
            'disabled/zero-denominator delay queries are unavailable, not zero coverage']))
    print('Diagnostic counter and coverage checks passed')


if __name__=='__main__':main()
