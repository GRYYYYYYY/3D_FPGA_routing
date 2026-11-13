#!/usr/bin/env python3
import csv,collections
from retained_prefix_workflow import D,read,write,sha
b=D/'bounded_cap_range_eltwise_dev_02';a=read(b/'cap_range_analysis.json');assert a['passed'];p=D/'paper/data';rows=a['observations'];csvp=p/'cap_range_v14.csv';assert not csvp.exists()
with csvp.open('w') as f:
    w=csv.writer(f);w.writerow(['arm','max_convergences','reused','status','CPD_ns','iterations','SB_net_occupancy','CB_source_net_occupancy','planning_seconds','router_seconds','complete_process_seconds'])
    for r in rows:
        pm=r.get('physical_metrics') or {};w.writerow([r['arm'],r['count'],r['reused'],r['status'],r.get('legal_cpd_ns'),r.get('iterations'),pm.get('sb_pair_net_occupancy'),pm.get('cb_crossing_output_source_net_occupancy'),r.get('planning_seconds'),r.get('router_seconds'),r.get('process_seconds')])
new=[r for r in rows if not r['reused']];tex=p/'cap_range_v14.tex';assert not tex.exists()
lines=[r'\begin{table}[t]',r'\centering',r'\caption{Cap amplitude bracket on one seen eltwise input. Counts are native convergence limits, not repeats. Exact physical STA and actual final resource occupancies; all four roles are legal. Ordered development times are available in the bound CSV and are not formal speed ratios.}',r'\label{tab:cap-range}',r'\scriptsize',r'\begin{tabular}{lrrrrr}',r'\hline',r'Cap / count & CPD (ns) & Iter. & SB & CB & Plan (s) \\',r'\hline']
for r in new:
    pm=r['physical_metrics'];beta=next(x['beta'] for x in read(b/'registration.json')['protocol']['cases'] if x['arm']==r['arm'])
    lines.append(f"{beta:g} / {r['count']} & {r['legal_cpd_ns']:.5f} & {r['iterations']} & {pm['sb_pair_net_occupancy']} & {pm['cb_crossing_output_source_net_occupancy']} & {r['planning_seconds']:.3f} "+r'\\')
lines.extend([r'\hline',r'\end{tabular}',r'\end{table}']);tex.write_text('\n'.join(lines)+'\n')
write(D/'cap_range_report_binding_01.json',dict(passed=True,status_counts=dict(collections.Counter(r['status'] for r in rows)),new_native_roles=len(new),reused_rows=len(rows)-len(new),source_sha256={str(x):sha(x) for x in [__file__,b/'cap_range_analysis.json',b/'registration.json',b/'completion.json',b/'input_seal.json',csvp,tex]},qualification='One circuit/seed; stopping rules remain separate; no circuit-geometric aggregate over role/control duplicates. Packaging recovery generated no routes. Failures in earlier studies retained.'))
