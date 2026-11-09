#!/usr/bin/env python3
"""Exercise complete analysis schemas with known effects and missing evidence."""
import copy
import math

from analyze_flatland_evaluation import summarize
from analyze_flatland_serial import comparisons
from flatland_benchmark import BASE,read
from lazagna_common import ROOT,sha256,utc,write_json


def legal(cpd,seconds=2):
    return dict(status='legal',metrics=dict(critical_path_ns=cpd,router_seconds=seconds),
        physical_metrics=dict(planar_wirelength_excluding_sb_half_nodes=1000*cpd),
        process_wall_seconds=seconds+1,run='synthetic_fixture')


def main():
    protocol=read(BASE/'benchmark_protocol.json');tables={}
    circuits=protocol['heldout'];seeds=protocol['evaluation_seeds'];families=protocol['architectures']
    tables['heldout','matched_2d','p0','A0']={(c,s):legal(100) for c in circuits for s in seeds}
    for f,baseline,placed in [('sb',90,80),('cb_o',80,75),('hybrid_o',100,60)]:
        for flow in ['p0','p1']:
            value=baseline if flow=='p0' else placed
            for role,ratio in [('A0',1),('R1',.8),('B2',1.1)]:
                tables['heldout',f,flow,role]={(c,s):legal(value*ratio) for c in circuits for s in seeds}
                tables['width300',f,flow,role]={(c,11 if c in protocol['training'] else 21):legal(value*ratio)
                    for c in protocol['width_sensitivity']['circuits']}
        for kind in ['fixed','tuned']:
            for variant in protocol['tuning']['variants']:
                tables['heldout',f,'p1',kind+'_'+variant]={(c,21):legal(placed*.8) for c in circuits}
    result=summarize(protocol,tables)
    for f in families:
        for flow in ['p0','p1']:
            x=result['heldout'][f][flow]['routing_dual']['vs_3d']
            assert x['registered_samples']==42 and x['paired_legal_samples']==42
            assert math.isclose(x['geomean_ratio'],.8)
        assert math.isclose(result['factorial_interactions'][f]['geomean_interaction_ratio'],1)
    ranks=result['architecture_rankings']['by_flow']
    assert ranks['p0_A0']['rank_groups']==[['cb_o'],['sb'],['hybrid_o']]
    assert ranks['p1_A0']['rank_groups']==[['hybrid_o'],['cb_o'],['sb']]
    # A failing 2D reference affects dual/ranking cohorts, not routing-only coverage.
    c=circuits[0];tables['heldout','matched_2d','p0','A0'][c,25]=dict(status='timeout')
    # An ablation-only failure must fix the common cohort of all eight bars.
    tables['heldout','sb','p1','fixed_geometry'][circuits[1],21]=dict(status='timeout')
    result=summarize(protocol,tables)
    assert len(result['architecture_rankings']['complete_common_circuits'])==13
    assert len(result['heldout']['sb']['p0']['routing_dual']['common_complete_circuits'])==13
    assert result['heldout']['sb']['p0']['routing_dual']['vs_3d']['paired_legal_samples']==42
    groups=result['ablations']['sb']['joint_cohort']
    assert all(len(x['complete_circuits'])==13 for g in groups.values() for x in g.values())
    # Runtime ratios must use medians; one outlier must not become the typical time.
    case=dict(circuit='spmv',family='sb',flow='p0',split='training',repeats=[])
    for repeat,time in enumerate([1,1,1000],1):
        routes={a:legal(10,2) for a in ['A0','B2','R1off']};routes['R1']=legal(10,time)
        case['repeats'].append(dict(repeat=repeat,status='completed',routes=routes))
    value=comparisons([case])['R1_over_A0']['per_case'][0]
    assert value['router']['ratio']==.5 and value['router']['r1_range_seconds']==[1,1000]
    failed=copy.deepcopy(case);failed['repeats'][2]['routes']['A0']=dict(status='timeout')
    value=comparisons([failed])['R1_over_A0']['per_case'][0]
    assert value['paired_legal_repeats']==2 and 'router' not in value
    output=BASE/'analysis_schema_validation.json';assert not output.exists()
    sources={str(ROOT/'scripts'/p):sha256(ROOT/'scripts'/p) for p in [
        'analyze_flatland_evaluation.py','analyze_flatland_serial.py','flatland_statistics.py','test_flatland_analysis.py']}
    write_json(output,dict(utc=utc(),passed=True,sources=sources,checks=[
        'Complete heldout/width/ablation schema with known 20% routing effect',
        'No spurious factorial interaction under constant multiplicative routing effect',
        'Known placement-induced architecture rank reversal',
        'Missing 2D observation reduces common cohorts while keeping registered routing coverage',
        'Ablation failure changes all common-cohort bars consistently',
        'Serial median robust to one outlier; incomplete repeats retain denominator and produce no complete-case ratio']))
    print('Analysis schema and runtime aggregation checks passed')


if __name__=='__main__':main()
