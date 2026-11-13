#!/usr/bin/env python3
"""Keep stopping rules, suppression controls and true physical metrics separate."""
import argparse,collections,csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from analyze_native_reconvergence_v2 import observe

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--include-cap',action='store_true');ap.add_argument('--include-cap-count1',action='store_true');args=ap.parse_args()
    report=D/args.out;assert not report.exists();groups=[
        ('mechanism','guide_influence_eltwise_dev_01',2,['C','T']),
        ('fixed_traced','bounded_critical_eltwise_dev_01',2,['C','Z','T']),
        ('fixed_traceoff','bounded_critical_traceoff_eltwise_dev_01',2,['C','Z','T']),
        ('fixed_count1','bounded_critical_count1_eltwise_dev_01',1,['C','Z','T']),
        ('after_legal','bounded_after_legal_eltwise_dev_01',2,['C','P0','P']),
        ('after_count1','bounded_after_legal_count1_eltwise_dev_01',1,['P1'])]
    if args.include_cap:groups.append(('cap','bounded_cap_eltwise_dev_01',2,['C','Z','K']))
    if args.include_cap_count1:groups.append(('cap_count1','bounded_cap_count1_eltwise_dev_01',1,['K']))
    rows=[];sources={str(Path(__file__)):sha(Path(__file__))}
    ref=D/'native_reconvergence_eltwise_dev_01';reg=read(ref/'registration.json')
    for count in [1,2]:
        for a in ['A0','R1','Tf','A1']:
            rd=Path(reg['references'][a]) if count==1 else ref/'runs'/('eltwise_layer_'+a)
            r=dict(observe(rd),group='native',arm=a,max_convergences=count,reused=True);rows.append(r)
    for group,batch,count,arms in groups:
        b=D/batch;assert read(b/'input_seal.json')['passed'];done=read(b/'completion.json');assert done['disabled_gate_passed'] and not done['missing_arms']
        for n in ['registration.json','completion.json','input_seal.json']:sources[str(b/n)]=sha(b/n)
        for a in arms:
            rd=b/'runs'/('eltwise_layer_'+a);r=dict(observe(rd),group=group,arm=a,max_convergences=count,reused=False);rows.append(r)
            for n in ['manifest.json','stdout.log','h3d_final_guides.csv','independent_audit.json','final_guide_audit.json','traceoff_reproduction.json','first_legal_prefix_reproduction.json','first_legal_preserved.json','count1_policy_reproduction.json']:
                p=rd/n
                if p.exists():sources[str(p)]=sha(p)
    def get(group,arm,count):return next(r for r in rows if r['group']==group and r['arm']==arm and r['max_convergences']==count)
    pairs={}
    for group,c,t,count in [('fixed_count1','C','Z',1),('fixed_count1','Z','T',1),('fixed_count1','C','T',1),('fixed_traceoff','C','Z',2),('fixed_traceoff','Z','T',2),('fixed_traceoff','C','T',2),('after_legal','C','P0',2),('after_legal','P0','P',2),('after_legal','C','P',2)]+([('cap','C','Z',2),('cap','Z','K',2),('cap','C','K',2)] if args.include_cap else []):
        cr,tr=get(group,c,count),get(group,t,count);ok=cr['status']==tr['status']=='legal';pairs[f'{group}:{c}->{t}']=dict(comparable=ok,reference_cpd_ns=cr['legal_cpd_ns'],new_cpd_ns=tr['legal_cpd_ns'],cpd_improvement_pct=(1-tr['legal_cpd_ns']/cr['legal_cpd_ns'])*100 if ok else None,reference_iterations=cr['iterations'],new_iterations=tr['iterations'])
    for group,arm,count in [('fixed_count1','T',1),('fixed_traceoff','T',2),('after_legal','P',2)]+([('cap','K',2)] if args.include_cap else [])+([('cap_count1','K',1)] if args.include_cap_count1 else []):
        for c in ['A0','R1','A1']:
            cr,tr=get('native',c,count),get(group,arm,count);ok=cr['status']==tr['status']=='legal';pairs[f'count{count}:{c}->{group}/{arm}']=dict(comparable=ok,reference_cpd_ns=cr['legal_cpd_ns'],new_cpd_ns=tr['legal_cpd_ns'],cpd_improvement_pct=(1-tr['legal_cpd_ns']/cr['legal_cpd_ns'])*100 if ok else None)
    result=dict(status='sealed_one_seen_circuit_guide_policy_development',observations=rows,status_counts=dict(collections.Counter(r['status'] for r in rows)),pairs=pairs,source_sha256=sources,
        qualification='One seen circuit/seed, multiple stopping rules and repeated controls. No geomean across roles or independent-circuit claim. Native count1 and count2 references are kept separate. Full STA CPD/real SB-CB and all legal/failure/timeout/missing statuses retained; prior broader failures unchanged. Ordered traced/development costs not formal runtime. All-stage fixed seconds has first-legal degradation despite count2 recovery; phase and cap hypotheses evaluated separately, no automatic promotion.')
    write(report,result)
    csvpath=D/'paper/data'/(report.stem+'.csv');assert not csvpath.exists()
    with csvpath.open('w') as stream:
        w=csv.writer(stream);w.writerow(['group','arm','max_convergences','reused','status','CPD_ns','iterations','SB','CB','plan_s','router_s','process_s'])
        for r in rows:
            m=r['physical_metrics'] or {};w.writerow([r['group'],r['arm'],r['max_convergences'],r['reused'],r['status'],r['legal_cpd_ns'],r['iterations'],m.get('sb_pair_net_occupancy'),m.get('cb_crossing_output_source_net_occupancy'),r['planning_seconds'],r['router_seconds'],r['process_seconds']])
    write(D/(report.stem+'_binding.json'),dict(status='sealed_report',report_sha256=sha(report),exporter_sha256=sha(Path(__file__)),artifacts_sha256={str(csvpath.relative_to(D)):sha(csvpath)},new_roles=sum(not r['reused'] for r in rows),reused_native_roles=sum(r['reused'] for r in rows)))
    print({k:v for k,v in pairs.items() if k.startswith(('fixed_count1:C','fixed_traceoff:C','after_legal:C','cap:C','count1:','count2:'))})

if __name__=='__main__':main()
