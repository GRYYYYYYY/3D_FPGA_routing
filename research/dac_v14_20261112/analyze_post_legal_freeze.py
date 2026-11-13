#!/usr/bin/env python3
"""Sealed guide-release controls, first-legal equivalence and strong baselines."""
import argparse
from pathlib import Path
from retained_prefix_workflow import read, write, sha, normalized_command, original_records, route_body
from analyze_native_reconvergence_v2 import observe
from run_post_legal_freeze import prefix


def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);args=ap.parse_args();b=args.batch.resolve()
    reg=read(b/'registration.json');done=read(b/'completion.json');assert read(b/'input_seal.json')['passed']
    bindings={str(p):sha(p) for p in [b/'registration.json',b/'completion.json',b/'input_seal.json']}
    result=[]
    for a,p in reg['references'].items():
        rd=Path(p);r=observe(rd);r.update(arm=a,reused=True);result.append(r)
        for n in ['manifest.json','independent_audit.json','final_guide_audit.json']:
            if (rd/n).exists():bindings[str(rd/n)]=sha(rd/n)
    checks={};control=b/'runs/eltwise_layer_C';cm=read(control/'manifest.json')
    disabled=read(control/'disabled_reproduction.json');assert disabled['passed']==done['gate_passed']
    for arm in reg['arms']:
        rd=b/'runs'/f'eltwise_layer_{arm}'
        if not (rd/'manifest.json').exists():result.append(dict(arm=arm,status='missing',legal_cpd_ns=None));continue
        m=read(rd/'manifest.json');assert sha(m['command'][0])==reg['binary_sha256']
        assert normalized_command(m['command'])==normalized_command(cm['command'])
        env=dict(m['environment']);assert env.pop('VPR_H3D_POST_LEGAL_FREEZE')==('0' if arm=='C' else '1')
        assert env==reg['environment']
        for n in ['packed.net','placed.place']:assert sha(rd/n)==sha(control/n)
        lines=(rd/'stdout.log').read_text().splitlines();events=[(i,line) for i,line in enumerate(lines) if line.startswith('H3D_POST_LEGAL_FREEZE ')]
        if arm=='C':checks['disabled_exact']=disabled['passed'];checks['no_control_freeze_event']=not events
        else:
            first=reg['first_legal_iteration']
            cp=prefix((control/'stdout.log').read_text().splitlines(),first);pp=prefix(lines,first)
            strip=lambda table:[r[:1]+r[2:] for r in table]
            # Use the same strict iteration parser as the registered native control.
            from routing_log_metrics import ROW
            checks['first_legal_native_prefix']=strip([x.split() for x in cp if ROW.match(x)])==strip([x.split() for x in pp if ROW.match(x)])
            checks['first_legal_planning_records']=original_records(cp)==original_records(pp)
            checks['single_native_legal_freeze']=len(events)==1 and events[0][1]==f'H3D_POST_LEGAL_FREEZE iter={first} guide_use=1 feedback_plans=0' and events[0][0]>=len(pp)
            checks['no_release_combination']=not any(x.startswith('H3D_POST_LEGAL_RELEASE ') for x in lines)
            if events:
                cut=events[0][0]
                for tag in ['H3D_PLAN ','H3D_FEEDBACK ','H3D_DELAY ','H3D_TARGET_DELAY ']:
                    before=[x for x in lines[:cut] if x.startswith(tag)];after=[x for x in lines[cut+1:] if x.startswith(tag)]
                    if before:checks[tag.strip()+'_unchanged_after_freeze']=bool(after) and all(x==before[-1] for x in after)
                skipped=[int(x.split('skipped_prepare_calls=')[1]) for x in lines if x.startswith('H3D_POST_LEGAL_FREEZE_SUMMARY ')]
                checks['native_prepare_calls_skipped']=bool(skipped) and skipped[-1]>0 and skipped==sorted(skipped)
        r=observe(rd);r.update(arm=arm,reused=False);result.append(r)
        for n in ['manifest.json','independent_audit.json','final_guide_audit.json','disabled_reproduction.json']:
            if (rd/n).exists():bindings[str(rd/n)]=sha(rd/n)
    rs={r['arm']:r for r in result};pairs={}
    if 'F' in rs:
        for ref in ['C','A0','R1','Tf','A1']:
            x,y=rs[ref],rs['F'];both=x['status']==y['status']=='legal'
            pairs[ref+'->F']=dict(both_legal=both,cpd_improvement_pct=(1-y['legal_cpd_ns']/x['legal_cpd_ns'])*100 if both else None,
                same_route=route_body(Path(x['path'])/'routed.route')==route_body(Path(y['path'])/'routed.route') if both else None)
    out=dict(status='sealed_post_legal_freeze_analysis',gates=checks,gate_passed=all(checks.values()) and not done['missing_arms'],observations=result,comparisons=pairs,
        missing_arms=done['missing_arms'],bindings_sha256=bindings,analyzer_sha256=sha(__file__),
        support_sha256={str(Path(__file__).parent/n):sha(Path(__file__).parent/n) for n in ['analyze_native_reconvergence_v2.py','run_post_legal_freeze.py','routing_log_metrics.py']},
        qualification='Independent planning-freeze ablation after first legal native convergence; existing guide lookup/pressure remain enabled. Final guide overlap is descriptive, not causal adoption. Development timing only, not blind transfer or formal acceleration.')
    write(b/'freeze_analysis.json',out);print(dict(gates=checks,comparisons=pairs))


if __name__=='__main__':main()
