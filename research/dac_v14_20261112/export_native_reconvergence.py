#!/usr/bin/env python3
"""Publish the sealed four-circuit control table without formal timing claims."""
import csv
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha


def main():
    source=D/'native_reconvergence_circuit_summary.json';a=read(source)
    assert a['status']=='sealed_four_case_aggregate' and len(a['case_states'])==4
    for p,h in a['source_sha256'].items():assert sha(p)==h,p
    rows=a['observations'];assert len(rows)==32
    data=D/'paper/data';csv_path=data/'native_reconvergence_v14.csv';tex_path=data/'native_reconvergence_v14.tex'
    columns=['circuit','arm','max_convergence_count','status','legal_cpd_ns','iterations','legal_iteration_numbers',
        'sb_pair_net_occupancy','cb_crossing_output_source_net_occupancy','planar_wirelength_excluding_sb_half_nodes',
        'planning_seconds','router_seconds','process_seconds','prefix_gate_passed','reused','source']
    with csv_path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        for r in rows:
            p=r.get('physical_metrics') or {}
            writer.writerow(dict(circuit=r['circuit'],arm=r['arm'],max_convergence_count=r['count'],status=r['status'],
                legal_cpd_ns=r['legal_cpd_ns'],iterations=r['iterations'],legal_iteration_numbers=';'.join(map(str,r['legal_iteration_numbers'])),
                **{k:p.get(k) for k in columns[7:10]},**{k:r.get(k) for k in columns[10:15]},source=r['path']))
    lookup={(r['circuit'],r['arm'],r['count']):r for r in rows}
    tex=[r'\begin{table*}[t]',r'\centering\scriptsize',
        r'\caption{Native reconvergence control on four seen circuits (one seed each). Cells show final legal CPD in ns for maximum convergence count 1 / 2. The count is an upper limit; native early exits and best-route restoration remain enabled. Failures and other statuses remain in the accompanying CSV; gemm and original attention failures are outside this four-circuit extension, not removed from the broader quality cohort.}',
        r'\label{tab:native-reconvergence}',r'\begin{tabular}{lrrrr}',r'\hline',
        r'Circuit & A0 & Old R1 & Tf & Initial-global A1 \\',r'\hline']
    for circuit in a['case_states']:
        cells=[]
        for arm in ['A0','R1','Tf','A1']:
            values=[]
            for count in [1,2]:
                r=lookup[circuit,arm,count];values.append(f"{r['legal_cpd_ns']:.5f}" if r['status']=='legal' else r['status'].replace('_',r'\_'))
            cells.append(' / '.join(values))
        tex.append(circuit.replace('_',r'\_')+' & '+' & '.join(cells)+r' \\')
    tex.extend([r'\hline',r'\end{tabular}',r'\end{table*}'])
    tex_path.write_text('\n'.join(tex)+'\n')
    binding=dict(status='sealed_count2_export_passed',source_sha256={str(source):sha(source)},
        artifacts_sha256={str(p.relative_to(D)):sha(p) for p in [csv_path,tex_path]},exporter_sha256=sha(__file__),
        observation_rows=len(rows),status_counts=a['status_counts'],
        qualification='Paired development CPD/resources/iterations and native convergence controls. CSV costs are observations, not formally rotated same-environment speedup ratios. Four seen cases and one seed do not establish blind generalization or success-rate gains.')
    write(D/'native_reconvergence_report_binding.json',binding);print(binding)


if __name__=='__main__':main()
