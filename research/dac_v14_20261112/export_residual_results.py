#!/usr/bin/env python3
import csv,collections,math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'residual_native_eltwise_dev_01';r=read(b/'residual_native_analysis.json');assert r['passed'];P=D/'paper/data';sources={str(Path(__file__)):sha(__file__)}
p=P/'residual_query_v14.csv';assert not p.exists()
with p.open('w') as f:
    w=csv.writer(f);w.writerow(['arm','max_convergences','reused','status','CPD_ns','iterations','SB_net_occupancy','CB_source_net_occupancy','planning_seconds','router_seconds','complete_process_seconds'])
    for x in r['observations']:
        pm=x.get('physical_metrics') or {};w.writerow([x['arm'],x['count'],x['reused'],x['status'],x.get('legal_cpd_ns'),x.get('iterations'),pm.get('sb_pair_net_occupancy'),pm.get('cb_crossing_output_source_net_occupancy'),x.get('planning_seconds'),x.get('router_seconds'),x.get('process_seconds')])
sources[str(p)]=sha(p);p=P/'residual_query_work_v14.csv';assert not p.exists()
with p.open('w') as f:
    w=csv.writer(f);w.writerow(['arm','requests','queries','paths','cache_hits','expansions','labels','probe_seconds','cache_records','cache_stops'])
    for a,x in r['results'].items():w.writerow([a]+[x[k] for k in ['requests','queries','paths','hits','expansions','labels','probe_seconds','cache_records','cache_stops']])
sources[str(p)]=sha(p)
p=P/'residual_query_v14.tex';assert not p.exists();lines=[r'\begin{table}[t]',r'\centering',r'\caption{Read-only residual queries on one seen eltwise input: 3,809 guided searches, with 974 skipped for having no sink-layer source. Each fresh query permits 256 expansions. All modes exactly retain the original full route and 6.20812 ns CPD. Probe seconds exclude source collection and trace output; complete process costs are retained separately.}',r'\label{tab:residual-query}',r'\scriptsize',r'\begin{tabular}{lrrrrr}',r'\hline',r'Mode & Fresh & Paths & Hits & Expand & Probe (s) \\',r'\hline']
for a,x in r['results'].items():lines.append(f"{a} & {x['queries']:,} & {x['paths']:,} & {x['hits']:,} & {x['expansions']:,} & {x['probe_seconds']:.3f} "+r'\\')
lines.extend([r'\hline',r'\end{tabular}',r'\end{table}']);p.write_text('\n'.join(lines)+'\n');sources[str(p)]=sha(p)
q={a:{x['search']:x for x in r['results'][a]['rows']} for a in ['Qh','Qs']};stats={'better':0,'worse':0,'equal':0,'new_path':0};worse=[]
for search,a in q['Qh'].items():
    s=q['Qs'][search]
    if not a['has_path'] and s['has_path']:stats['new_path']+=1
    if a['has_path']:
        assert s['has_path'];ratio=s['upper_seconds']/a['upper_seconds'];tag='better' if ratio<1-1e-10 else 'worse' if ratio>1+1e-10 else 'equal';stats[tag]+=1
        if tag=='worse':worse.append(dict(search=search,ratio=ratio,criticality=s['criticality'],Qh_seconds=a['upper_seconds'],Qs_seconds=s['upper_seconds']))
for p in [b/'residual_native_analysis.json',b/'input_seal.json',b/'completion.json',D/'residual_query_offline_01/analysis.json',D/'residual_path_reuse_offline_01/analysis.json',D/'residual_query_adapter_unit_01/validation.json']:sources[str(p)]=sha(p)
write(D/'residual_query_report_binding_01.json',dict(passed=True,new_native_roles=4,reused_reference_rows=4,status_counts=dict(collections.Counter(x['status'] for x in r['observations'])),source_sha256=sources,Qs_vs_Qh_work_reduction_pct=100*(1-r['results']['Qs']['expansions']/r['results']['Qh']['expansions']),witness_upper_comparison=stats,worse_upper_rows=worse,max_worse_upper_ratio=max(x['ratio'] for x in worse),quality_promoted=False,qualification='One seen circuit, chronological query information/reuse study only. Static valid path UB can be much worse than a fresh valid UB; cache hit is not timing/QoR confidence. All original failures retained. Ordered detailed development times not formal speedup.'))
print(stats,'max UB ratio',max(x['ratio'] for x in worse))
