#!/usr/bin/env python3
"""Reconcile exact native reproduction with independently checked witness data."""
import argparse
from pathlib import Path
from retained_prefix_workflow import read, write, sha, route_body, original_records, normalized_command
from analyze_native_reconvergence_v2 import observe


def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);ap.add_argument('--audit',type=Path,required=True);args=ap.parse_args()
    b=args.batch.resolve();audit=args.audit.resolve();reg=read(b/'registration.json');done=read(b/'completion.json')
    assert read(b/'input_seal.json')['passed'] and done['gate_passed'] and not done['missing_arms']
    physics=read(audit/'analysis.json');assert physics['passed'] and read(audit/'input_seal.json')['passed']
    c=b/'runs/eltwise_layer_C';t=b/'runs/eltwise_layer_T';cm=read(c/'manifest.json');tm=read(t/'manifest.json')
    assert normalized_command(cm['command'])==normalized_command(tm['command'])
    for arm,m in [('C',cm),('T',tm)]:
        env=dict(m['environment']);assert env.pop('VPR_H3D_TRACE_PATH_WITNESS')==('0' if arm=='C' else '1')
        assert env==reg['environment'] and env['VPR_H3D_POST_LEGAL_RELEASE']==env['VPR_H3D_POST_LEGAL_FREEZE']=='0'
        assert sha(m['command'][0])==reg['binary_sha256']
    for n in ['packed.net','placed.place','h3d_final_guides.csv']:assert sha(c/n)==sha(t/n)
    assert route_body(c/'routed.route')==route_body(t/'routed.route')
    base=(c/'stdout.log').read_text().splitlines();trace=(t/'stdout.log').read_text().splitlines()
    allowed={line.split()[0] for line in base if line.startswith('H3D_')}
    assert original_records(base,allowed)==original_records(trace,allowed)
    assert [x for x in base if x.startswith('H3D_PREFIX_')]==[x for x in trace if x.startswith('H3D_PREFIX_')]
    assert not any(x.startswith('H3D_PATH_') for x in base)
    for p,h in physics['sources_sha256'].items():assert sha(p)==h,p
    result=[];bindings={}
    for arm,p in reg['references'].items():
        rd=Path(p);r=observe(rd);r.update(arm=arm,reused=True);result.append(r)
    for arm,rd in [('C',c),('T',t)]:
        r=observe(rd);assert r['status']=='legal';r.update(arm=arm,reused=False);result.append(r)
    for r in result:
        rd=Path(r['path'])
        for name in ['manifest.json','independent_audit.json','final_guide_audit.json','disabled_reproduction.json','trace_equivalence.json']:
            if (rd/name).exists():bindings[str(rd/name)]=sha(rd/name)
    for p in [b/'registration.json',b/'completion.json',b/'input_seal.json',audit/'analysis.json',audit/'input_seal.json']:
        bindings[str(p)]=sha(p)
    out=dict(status='validated_read_only_path_witness_diagnostic',passed=True,observations=result,
        same_complete_route_guides_tables_prefix_and_query_work=True,witness_analysis=physics,
        sources_sha256=bindings,analyzer_sha256=sha(__file__),
        qualification='No scoring or routing change, no new delay queries, no QoR gain or acceleration claim. Physical witness paths and reported ownership-aware proxy formulas checked; temporal occupancy/ownership is not independently replayed, equal-delay alternatives may have different congestion. Select a score experiment only after interpreting coverage and risk evidence.')
    write(b/'path_witness_analysis.json',out)
    print(dict(status=out['status'],records=physics['records'],measured_leaf_side_events=physics['measured_leaf_side_events'],groups=physics['groups']))


if __name__=='__main__':main()
