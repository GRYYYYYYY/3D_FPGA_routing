#!/usr/bin/env python3
"""Failure-aware paired statistics for the preregistered architecture study."""
import math
from statistics import fmean


def geomean(values):
    values=list(values)
    if not values:return None
    if any(not math.isfinite(x) or x<=0 for x in values):raise ValueError('Invalid positive ratio/value')
    return math.exp(fmean(math.log(x) for x in values))


def legal(row):
    return row is not None and row.get('status')=='legal'


def value(row,metric='critical_path_ns'):
    result=row.get('metrics',{}).get(metric)
    if result is None:result=row.get('physical_metrics',{}).get(metric)
    if result is None or not math.isfinite(result) or result<=0:raise ValueError(f'Invalid {metric}')
    return result


def complete_circuits(tables,circuits,seeds):
    return [c for c in circuits if all(legal(t.get((c,s))) for t in tables for s in seeds)]


def paired(numerator,denominator,circuits,seeds,metric='critical_path_ns',cohort=None):
    """Average each circuit's paired seeds first, then geometrically average ratios."""
    complete=complete_circuits([numerator,denominator],circuits,seeds)
    if cohort is not None:
        assert set(cohort)<=set(complete)
        complete=[c for c in circuits if c in cohort]
    per_circuit=[];per_sample=[]
    for c in circuits:
        for s in seeds:
            a,b=numerator.get((c,s)),denominator.get((c,s))
            if legal(a) and legal(b):
                ratio=value(a,metric)/value(b,metric)
                per_sample.append(dict(circuit=c,seed=s,numerator=value(a,metric),denominator=value(b,metric),
                    ratio=ratio,improvement_percent=100*(1-ratio),numerator_run=a.get('run'),denominator_run=b.get('run')))
        if c in complete:
            a=fmean(value(numerator[(c,s)],metric) for s in seeds)
            b=fmean(value(denominator[(c,s)],metric) for s in seeds)
            per_circuit.append(dict(circuit=c,numerator_mean=a,denominator_mean=b,ratio=a/b,improvement_percent=100*(1-a/b)))
    ratio=geomean(x['ratio'] for x in per_circuit)
    best=min(per_sample,key=lambda x:x['ratio']) if per_sample else None
    worst=max(per_sample,key=lambda x:x['ratio']) if per_sample else None
    return dict(metric=metric,registered_circuits=len(circuits),registered_samples=len(circuits)*len(seeds),
        numerator_legal_samples=sum(legal(numerator.get((c,s))) for c in circuits for s in seeds),
        denominator_legal_samples=sum(legal(denominator.get((c,s))) for c in circuits for s in seeds),
        paired_legal_samples=len(per_sample),complete_circuits=complete,
        geomean_ratio=ratio,geomean_improvement_percent=100*(1-ratio) if ratio is not None else None,
        improved_samples=sum(x['ratio']<1 for x in per_sample),tied_samples=sum(x['ratio']==1 for x in per_sample),
        regressed_samples=sum(x['ratio']>1 for x in per_sample),
        maximum_improvement=best,worst_regression=worst,per_circuit=per_circuit,per_sample=per_sample,
        scope='Aggregates require every registered seed for a circuit. Single-sample extrema use all paired legal samples and are explicitly identified; failures remain in coverage counts.')


def dual(numerator,baseline_3d,baseline_2d,circuits,seeds):
    common=complete_circuits([numerator,baseline_3d,baseline_2d],circuits,seeds)
    a=paired(numerator,baseline_3d,circuits,seeds,cohort=common)
    b=paired(numerator,baseline_2d,circuits,seeds,cohort=common)
    joint=[]
    for c in circuits:
        for s in seeds:
            rows=[t.get((c,s)) for t in [numerator,baseline_3d,baseline_2d]]
            if all(map(legal,rows)):
                cpds=list(map(value,rows))
                joint.append(dict(circuit=c,seed=s,cpd_ns=cpds[0],baseline_3d_cpd_ns=cpds[1],baseline_2d_cpd_ns=cpds[2],
                    improvement_vs_3d_percent=100*(1-cpds[0]/cpds[1]),improvement_vs_2d_percent=100*(1-cpds[0]/cpds[2]),
                    numerator_run=rows[0].get('run'),baseline_3d_run=rows[1].get('run'),baseline_2d_run=rows[2].get('run')))
    return dict(common_complete_circuits=common,vs_3d=a,vs_2d=b,joint_successful_samples=len(joint),
        maximum_vs_3d_same_sample=max(joint,key=lambda x:x['improvement_vs_3d_percent']) if joint else None,
        maximum_vs_2d_same_sample=max(joint,key=lambda x:x['improvement_vs_2d_percent']) if joint else None,
        display_contract='Paired headline parentheses use the same circuit/seed. Geomean 3D/2D figures share exactly the same complete circuit cohort.')


def ranked_groups(scores):
    """Represent numerical ties explicitly instead of inventing an ordering."""
    groups=[];previous=None
    for family,score in sorted(scores.items(),key=lambda x:(x[1],x[0])):
        if previous is None or not math.isclose(score,previous,rel_tol=1e-10,abs_tol=1e-12):groups.append([])
        groups[-1].append(family);previous=score
    return groups


def architecture_rankings(tables,reference_2d,circuits,seeds,families,cells):
    common=complete_circuits([reference_2d,*[tables[(f,cell)] for f in families for cell in cells]],circuits,seeds)
    result=dict(registered_circuits=len(circuits),complete_common_circuits=common,by_flow={},by_seed={},strict_pairwise_reversals=[])
    if not common:
        result['status']='no_complete_common_cohort';return result
    def panel(active_seeds):
        panel_result={}
        for cell in cells:
            absolute={};normalized={}
            for f in families:
                table=tables[(f,cell)]
                means=[fmean(value(table[(c,s)]) for s in active_seeds) for c in common]
                refs=[fmean(value(reference_2d[(c,s)]) for s in active_seeds) for c in common]
                absolute[f]=geomean(means);normalized[f]=geomean(a/b for a,b in zip(means,refs))
            groups=ranked_groups(absolute);assert groups==ranked_groups(normalized)
            panel_result[cell]=dict(absolute_geomean_cpd_ns=absolute,common_2d_geomean_ratio=normalized,rank_groups=groups)
        return panel_result
    result['by_flow']=panel(seeds)
    for seed in seeds:result['by_seed'][str(seed)]=panel([seed])
    baseline=result['by_flow']['p0_A0']['common_2d_geomean_ratio']
    for cell in cells:
        after=result['by_flow'][cell]['common_2d_geomean_ratio']
        for i,a in enumerate(families):
            for b in families[i+1:]:
                before_gap=baseline[a]-baseline[b];after_gap=after[a]-after[b]
                if before_gap*after_gap<0 and not math.isclose(baseline[a],baseline[b],rel_tol=1e-10) and not math.isclose(after[a],after[b],rel_tol=1e-10):
                    result['strict_pairwise_reversals'].append(dict(comparison='p0_A0 -> '+cell,architectures=[a,b],before_difference=before_gap,after_difference=after_gap))
    result['status']='complete_common_cohort_available'
    return result


def factorial_interaction(tables,circuits,seeds):
    cells=['p0_A0','p0_R1','p1_A0','p1_R1']
    common=complete_circuits([tables[c] for c in cells],circuits,seeds);rows=[]
    for circuit in common:
        means={cell:fmean(value(tables[cell][(circuit,s)]) for s in seeds) for cell in cells}
        p0=means['p0_R1']/means['p0_A0'];p1=means['p1_R1']/means['p1_A0']
        rows.append(dict(circuit=circuit,means=means,p0_routing_ratio=p0,p1_routing_ratio=p1,interaction_ratio=p1/p0))
    return dict(complete_common_circuits=common,per_circuit=rows,
        geomean_interaction_ratio=geomean(r['interaction_ratio'] for r in rows),
        interpretation='(P1R1/P1A0)/(P0R1/P0A0); below one means a stronger relative routing benefit under P1 on this common cohort, without asserting statistical significance.')
