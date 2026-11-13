#!/usr/bin/env python3
import csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from analyze_native_reconvergence_v2 import observe
b=D/'search_domain_eltwise_dev_01';box=D/'box_guide_eltwise_dev_01';r=read(box/'box_guide_analysis.json');assert r['passed'] and read(b/'search_domain_analysis.json')['passed'];sources={str(Path(__file__)):sha(__file__)}
for label,rows in [('search_domain',[dict(observe(b/'runs'/('eltwise_layer_'+a)),arm=a,count=2,reused=False) for a in ['C','T']]),('box_guide',r['observations'])]:
    p=D/'paper/data'/(label+'_v14.csv');assert not p.exists()
    with p.open('w') as f:
        w=csv.writer(f);w.writerow(['arm','max_convergences','reused','status','CPD_ns','iterations','SB_net_occupancy','CB_source_net_occupancy','planning_seconds','router_seconds','complete_process_seconds'])
        for x in rows:
            pm=x.get('physical_metrics') or {};w.writerow([x['arm'],x['count'],x['reused'],x['status'],x.get('legal_cpd_ns'),x.get('iterations'),pm.get('sb_pair_net_occupancy'),pm.get('cb_crossing_output_source_net_occupancy'),x.get('planning_seconds'),x.get('router_seconds'),x.get('process_seconds')])
    sources[str(p)]=sha(p)
for p in [b/'search_domain_analysis.json',b/'input_seal.json',b/'completion.json',box/'box_guide_analysis.json',box/'input_seal.json',box/'completion.json']:sources[str(p)]=sha(p)
write(D/'search_context_report_binding_01.json',dict(passed=True,source_sha256=sources,new_native_roles=5,qualification='Two decision-neutral tracing roles plus three local-admission ablation roles. Exact route/guide reproduction checked separately from trajectory. One seen circuit/seed; baseline rows reused by native convergence limit. Full costs retained; no formal speedup.'))
