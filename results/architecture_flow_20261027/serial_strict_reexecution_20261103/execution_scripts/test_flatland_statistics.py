#!/usr/bin/env python3
"""Regression checks for seed weighting, missing cases and dual-reference claims."""
import math

from flatland_statistics import paired,dual,architecture_rankings,factorial_interaction
from flatland_benchmark import BASE
from pathlib import Path
from lazagna_common import ROOT,sha256,utc,write_json


def row(cpd,name='fixture'):
    return dict(status='legal',metrics=dict(critical_path_ns=cpd),run=name)


def main():
    circuits=['a','b','incomplete'];seeds=[21,23,25]
    n={};d={};two={}
    for c,ns,ds,ts in [('a',[2,8,8],[1,8,8],[4,8,8]),('b',[.5,1,3],[1,2,6],[.1,1,3]),('incomplete',[1,1,1],[1,1,1],[1,1,1])]:
        for s,a,b,t in zip(seeds,ns,ds,ts):n[c,s]=row(a);d[c,s]=row(b);two[c,s]=row(t)
    n['incomplete',25]=dict(status='timeout')
    result=paired(n,d,circuits,seeds)
    assert result['registered_samples']==9 and result['paired_legal_samples']==8
    assert result['complete_circuits']==['a','b']
    assert math.isclose(result['geomean_ratio'],math.sqrt((18/17)*.5))
    result=dual(n,d,two,circuits,seeds)
    best=result['maximum_vs_3d_same_sample']
    assert (best['circuit'],best['seed'])==('b',21)
    assert best['improvement_vs_3d_percent']==50 and best['improvement_vs_2d_percent']==-400
    assert result['maximum_vs_2d_same_sample']['circuit']=='a'
    two['b',25]=dict(status='failed')
    result=dual(n,d,two,circuits,seeds)
    assert result['common_complete_circuits']==['a']
    assert result['vs_3d']['complete_circuits']==result['vs_2d']['complete_circuits']==['a']
    assert paired({},d,circuits,seeds)['geomean_ratio'] is None
    families=['sb','cb_o','hybrid_o'];cells=['p0_A0','p0_R1','p1_A0','p1_R1']
    tables={}
    for f,base,final in [('sb',3,2),('cb_o',2,3),('hybrid_o',4,1)]:
        for cell in cells:
            score=final if cell=='p1_R1' else base
            tables[f,cell]={(c,s):row(score*(2 if c=='b' else 1)) for c in ['a','b'] for s in seeds}
    two={(c,s):row(10 if c=='a' else 4) for c in ['a','b'] for s in seeds}
    ranks=architecture_rankings(tables,two,['a','b'],seeds,families,cells)
    assert ranks['by_flow']['p0_A0']['rank_groups']==[['cb_o'],['sb'],['hybrid_o']]
    assert ranks['by_flow']['p1_R1']['rank_groups']==[['hybrid_o'],['sb'],['cb_o']]
    assert len(ranks['strict_pairwise_reversals'])==3
    tables['hybrid_o','p1_R1']['b',23]=dict(status='failed')
    ranks=architecture_rankings(tables,two,['a','b'],seeds,families,cells)
    assert ranks['complete_common_circuits']==['a']
    interaction=factorial_interaction({c:tables['sb',c] for c in cells},['a','b'],seeds)
    assert math.isclose(interaction['geomean_interaction_ratio'],2/3)
    output=BASE/'statistics_validation.json'
    if output.exists():raise FileExistsError(output)
    write_json(output,dict(utc=utc(),passed=True,source_sha256=sha256(Path(__file__).parent/'flatland_statistics.py'),
        test_source_sha256=sha256(__file__),checks=['mean seeds before circuit ratios','incomplete seed cohort excluded without dropping denominator',
        'dual maximum uses same circuit/seed even when reference2D result is worse','dual geomeans use commoncomplete cohort',
        'empty cohort returns null','absolute/common2D ranks agree','strict reversals detected and failed cases excluded consistently',
        'factorial multiplicative interaction']))
    print('Statistical aggregation invariants passed')


if __name__=='__main__':main()
