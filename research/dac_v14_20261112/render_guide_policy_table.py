#!/usr/bin/env python3
"""Render exact stopping-rule comparison from the sealed unified rollup."""
from retained_prefix_workflow import D,read,write,sha
from pathlib import Path

def main():
    report=D/'guide_policy_development_01.json';binding=read(D/'guide_policy_development_01_binding.json');assert sha(report)==binding['report_sha256'];d=read(report);rows=d['observations']
    def get(g,a,c):return next(r for r in rows if r['group']==g and r['arm']==a and r['max_convergences']==c)
    choices=[('Native A0',('native','A0'),('native','A0')),('Old R1',('native','R1'),('native','R1')),('Native A1',('native','A1'),('native','A1')),('Original C',('fixed_count1','C'),('fixed_traceoff','C')),('Critical off Z',('fixed_count1','Z'),('fixed_traceoff','Z')),('Fixed 0.25',('fixed_count1','T'),('fixed_traceoff','T')),('Cap 0.25',('cap_count1','K'),('cap','K')),('After legal: off',None,('after_legal','P0')),('After legal: 0.25',('after_count1','P1'),('after_legal','P'))]
    tex=['\\begin{table}[t]','\\centering','\\caption{One seen eltwise case under matched native convergence limits. CPD is final physical STA in ns; SB/CB are actual count-two net occupancies. A dash is unmeasured, not a tie. First-legal quality and later recovery are kept separate.}','\\label{tab:guide-policy-stops}','\\scriptsize','\\begin{tabular}{lrrrrrr}','\\hline','& \\multicolumn{2}{c}{Count one} & \\multicolumn{2}{c}{Count two} & & \\\\','Policy & CPD & Iter. & CPD & Iter. & SB & CB \\\\','\\hline']
    for label,one,two in choices:
        a=get(*one,1) if one else None;b=get(*two,2);p=b['physical_metrics'];left=f"{a['legal_cpd_ns']:.5f} & {a['iterations']}" if a else '-- & --'
        tex.append(f"{label} & {left} & {b['legal_cpd_ns']:.5f} & {b['iterations']} & {p['sb_pair_net_occupancy']} & {p['cb_crossing_output_source_net_occupancy']} \\\\")
    tex+=['\\hline','\\end{tabular}','\\end{table}'];out=D/'paper/data/guide_policy_v14.tex';assert not out.exists();out.write_text('\n'.join(tex)+'\n')
    write(D/'guide_policy_table_binding_01.json',dict(status='sealed_stopping_rule_table',report_sha256=sha(report),renderer_sha256=sha(Path(__file__)),artifacts_sha256={str(out.relative_to(D)):sha(out)},rows=len(choices),scope='Actual full STA/physical occupancies only; no formal runtime or broad circuit aggregation.'))
    print('rendered9stopping-rule rows from27sealed observations')

if __name__=='__main__':main()
