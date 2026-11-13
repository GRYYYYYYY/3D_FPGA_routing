#!/usr/bin/env python3
"""Circuit-level count1/count2 comparisons, with unfinished cases retained."""
import argparse
import collections
import math
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

CASES={'eltwise_layer':D/'native_reconvergence_eltwise_dev_01',
       **{c:D/f'native_reconvergence_{c}_dev_01' for c in ['spmv','softmax','bnn']}}
ARMS=['A0','R1','Tf','A1']


def paired(label, pairs):
    comparable=[p for p in pairs if p['comparable']]
    ratios=[p['new_cpd_ns']/p['reference_cpd_ns'] for p in comparable]
    improvements=[(1-r)*100 for r in ratios]
    return dict(label=label,declared_circuit_count=len(pairs),comparable_circuit_count=len(comparable),
        improve=sum(r<1 for r in ratios),tie=sum(r==1 for r in ratios),regress=sum(r>1 for r in ratios),
        circuit_geomean_improvement_pct=(1-math.exp(sum(map(math.log,ratios))/len(ratios)))*100 if ratios else None,
        worst_circuit_improvement_pct=min(improvements) if improvements else None,
        pairs=pairs,regression_tail=sorted([p for p in comparable if p['new_cpd_ns']>p['reference_cpd_ns']],
            key=lambda p:p['new_cpd_ns']/p['reference_cpd_ns'],reverse=True))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args()
    destination=D/args.out;assert not destination.exists()
    bindings={};observations=[];case_states={}
    for circuit,batch in CASES.items():
        analysis=batch/'reconvergence_analysis.json'
        if not analysis.exists() or not (batch/'input_seal.json').exists():
            case_states[circuit]='pending'
            for count in [1,2]:
                for arm in ARMS:observations.append(dict(circuit=circuit,count=count,arm=arm,status='pending_batch_seal',legal_cpd_ns=None,prefix_gate_passed=None))
            continue
        assert read(batch/'input_seal.json')['passed']
        a=read(analysis);assert not a['missing_arms']
        for path,h in a['binding_sha256'].items():assert sha(path)==h,path
        for p in [analysis,batch/'input_seal.json',batch/'completion.json']:bindings[str(p)]=sha(p)
        case_states[circuit]='sealed'
        for r in a['observations']:
            rd=Path(r['path']);m=read(rd/'manifest.json')
            gate=True if r['count']==1 else a['comparisons'][r['arm']]['prefix_gate_passed']
            if r['status']=='legal':
                assert m['status']=='completed' and m['metrics']['native_full_check_passed'] and m['metrics']['routing_success_reported']
                assert r['legal_cpd_ns']==m['metrics']['critical_path_ns']
                audit=read(rd/'independent_audit.json');assert audit['audit']['passed'] and r['physical_metrics']==audit['physical_metrics']
            else:assert r['legal_cpd_ns'] is None
            observations.append(dict(r,circuit=circuit,prefix_gate_passed=gate))
    lookup={(r['circuit'],r['count'],r['arm']):r for r in observations}
    comparisons={}
    definitions=[(f'{a}:count1->count2',1,a,2,a) for a in ARMS]
    definitions += [(f'count{count}:{ref}->Tf',count,ref,count,'Tf') for count in [1,2] for ref in ['A0','R1','A1']]
    for label,oldcount,oldarm,newcount,newarm in definitions:
        pairs=[]
        for circuit in CASES:
            x=lookup[circuit,oldcount,oldarm];y=lookup[circuit,newcount,newarm]
            comparable=x['status']==y['status']=='legal' and x['prefix_gate_passed'] and y['prefix_gate_passed']
            pairs.append(dict(circuit=circuit,reference_status=x['status'],new_status=y['status'],
                comparable=bool(comparable),reference_cpd_ns=x['legal_cpd_ns'],new_cpd_ns=y['legal_cpd_ns']))
        comparisons[label]=paired(label,pairs)
    out=dict(status='sealed_four_case_aggregate' if all(s=='sealed' for s in case_states.values()) else 'partial_aggregate_not_final',
        case_states=case_states,status_counts=dict(collections.Counter(r['status'] for r in observations)),
        observations=observations,comparisons=comparisons,source_sha256=bindings,aggregator_sha256=sha(__file__),
        broader_cohort_qualification='Count2 study covers four seen circuits, one seed each. Gemm remains unmeasured in this extension, and original attention A0/R1 failures remain in the broader six-circuit quality denominator. This is not a success-rate improvement or blind transfer result.',
        timing_qualification='Planning, router and full-process costs are retained per run. No historical-count1/count2 wall-time ratios are formal acceleration evidence; native legal-cycle counts may be below the maximum.')
    write(destination,out)
    print(dict(status=out['status'],cases=case_states,comparisons={k:{f:v[f] for f in ['comparable_circuit_count','improve','tie','regress','circuit_geomean_improvement_pct','worst_circuit_improvement_pct']} for k,v in comparisons.items()}))


if __name__=='__main__':main()
