#!/usr/bin/env python3
"""Unified same-input development observations; retain ordered process costs."""
from pathlib import Path
import collections,csv,json
from retained_prefix_workflow import D,read,write,sha,normalized_command
from analyze_native_reconvergence_v2 import observe

def main():
    out=D/'candidate_path_development_summary_01.json';assert not out.exists()
    refs=D/'native_reconvergence_eltwise_dev_01';spec=[('native',a,refs/'runs'/('eltwise_layer_'+a),True) for a in ['A0','R1','Tf','A1']]
    for stage,batch,arms in [
        ('query','candidate_path_queries_eltwise_dev_01',['C','Q0','Qh','Qp']),
        ('price','candidate_path_score_eltwise_dev_01',['S0','S1']),
        ('cache','candidate_path_cached_eltwise_dev_01',['K0','K1']),
        ('compact','compact_witness_eltwise_dev_01',['C0','C1']),
        ('delay','candidate_path_delay_eltwise_dev_01',['P','D0','D1'])]:
        b=D/batch;assert read(b/'input_seal.json')['passed'];assert not read(b/'completion.json')['missing_arms']
        spec += [(stage,a,b/'runs'/('eltwise_layer_'+a),False) for a in arms]
    rows=[];bindings={str(Path(__file__)) :sha(Path(__file__))};control=read(refs/'runs/eltwise_layer_Tf/manifest.json')
    control_inputs={n:sha(refs/'runs/eltwise_layer_Tf'/n) for n in ['packed.net','placed.place']}
    for stage,a,rd,reused in spec:
        m=read(rd/'manifest.json');assert normalized_command(m['command'])==normalized_command(control['command'])
        assert all(sha(rd/n)==h for n,h in control_inputs.items())
        for n,v in m['shared_inputs'].items():assert control['shared_inputs'][n]['sha256']==v['sha256']
        r=dict(observe(rd),stage=stage,arm=a,reused=reused,circuit='eltwise_layer',seed=11)
        r['process_accounting']={k:v for k,v in m.items() if any(s in k.lower() for s in ['rss','cpu','peak','timeout','returncode'])}
        rows.append(r)
        for n in ['manifest.json','stdout.log','independent_audit.json','final_guide_audit.json']:
            p=rd/n
            if p.exists():bindings[str(p)]=sha(p)
        for n in ['input_seal.json','completion.json']:
            p=rd.parent.parent/n
            if p.exists():bindings[str(p)]=sha(p)
    statuses=dict(collections.Counter(r['status'] for r in rows));assert statuses=={'legal':17}
    strong=next(r['legal_cpd_ns'] for r in rows if r['stage']=='native' and r['arm']=='R1')
    for r in rows:r['cpd_regression_vs_strong_count2_R1_pct']=(r['legal_cpd_ns']/strong-1)*100
    write(out,dict(status='sealed_one_circuit_development_rollup',observations=rows,status_counts=statuses,source_sha256=bindings,
        qualification='One seen circuit/seed,17 matched roles of which4 strictly matched reused native refs and13 new. Repeated method controls are not independent circuit samples. Ordered development costs are not formal runtime. Historical failed attention and source-cut conv cohorts remain in broader evidence, not replaced by this diagnostic subset.'))
    csv_path=D/'paper/data/candidate_path_v14.csv';assert not csv_path.exists()
    with csv_path.open('w') as stream:
        cols=['stage','arm','status','cpd_ns','iterations','SB','CB','planning_seconds','router_seconds','process_seconds','reused']
        w=csv.DictWriter(stream,fieldnames=cols);w.writeheader()
        for r in rows:
            p=r['physical_metrics'];w.writerow(dict(stage=r['stage'],arm=r['arm'],status=r['status'],cpd_ns=r['legal_cpd_ns'],iterations=r['iterations'],SB=p['sb_pair_net_occupancy'],CB=p['cb_crossing_output_source_net_occupancy'],planning_seconds=r['planning_seconds'],router_seconds=r['router_seconds'],process_seconds=r['process_seconds'],reused=r['reused']))
    selected={('native',a) for a in ['A0','R1','Tf']}|{('query','Qp'),('price','S1'),('cache','K1'),('compact','C1'),('delay','D1')}
    labels={('native','A0'):'A0',('native','R1'):'Old R1',('native','Tf'):'Tf',('query','Qp'):'Priced query',('price','S1'):'Price score',('cache','K1'):'Cached price',('compact','C1'):'Compact cache',('delay','D1'):'Physical sink'}
    tex=['\\begin{table}[t]','\\centering','\\caption{Selected same-input eltwise development observations at native convergence count two. All are legal. Planning and complete-process seconds are ordered development costs, not formal speedup measurements. The physical-sink arm disables price scoring; it is not a combination claim.}','\\label{tab:candidate-path-dev}','\\scriptsize','\\begin{tabular}{lrrrrrr}','\\hline','Method & CPD (ns) & Iter. & SB & CB & Plan (s) & Proc. (s) \\\\','\\hline']
    for r in rows:
        key=r['stage'],r['arm']
        if key not in selected:continue
        p=r['physical_metrics'];tex.append(f"{labels[key]} & {r['legal_cpd_ns']:.5f} & {r['iterations']} & {p['sb_pair_net_occupancy']} & {p['cb_crossing_output_source_net_occupancy']} & {r['planning_seconds']:.3f} & {r['process_seconds']:.3f} \\\\")
    tex+=['\\hline','\\end{tabular}','\\end{table}'];tex_path=D/'paper/data/candidate_path_v14.tex';assert not tex_path.exists();tex_path.write_text('\n'.join(tex)+'\n')
    binding=D/'candidate_path_report_binding_01.json';assert not binding.exists();write(binding,dict(status='sealed_development_export',summary_sha256=sha(out),exporter_sha256=sha(Path(__file__)),artifacts_sha256={str(p.relative_to(D)):sha(p) for p in [csv_path,tex_path]},roles=len(rows),qualification='Full13new+4matched reference roles in CSV; selected8 rows in paper. One case; no method promotion or formal time claim.'))
    print('sealed17legal development rows, fullCSV and selected8-row table')

if __name__=='__main__':main()
