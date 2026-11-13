#!/usr/bin/env python3
"""Sealed search-domain ablation; retain all declared outcomes and both controls."""
import argparse
import collections
import math
from pathlib import Path
import re
import struct
from retained_prefix_workflow import read, write, sha, normalized_command
from routing_log_metrics import last_iteration

def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);args=ap.parse_args();b=args.batch
    reg=read(b/'registration.json');done=read(b/'completion.json');assert read(b/'input_seal.json')['passed']
    refs={r['arm']:r for r in read(b/'references.json')};rows=[];bindings={str(p):sha(p) for p in [b/'registration.json',b/'completion.json',b/'input_seal.json']}
    reference_command=read(Path(refs['A0']['path'])/'manifest.json')['command']
    for arm in ['A0','R1','A1']+reg['arms']:
        rd=Path(refs[arm]['path']) if arm in refs else b/'runs'/f"{reg['circuit']}_{arm}"
        if not (rd/'manifest.json').exists():rows.append(dict(arm=arm,status='missing',legal_cpd_ns=None));continue
        m=read(rd/'manifest.json');bindings[str(rd/'manifest.json')]=sha(rd/'manifest.json')
        assert normalized_command(m['command'])==normalized_command(reference_command)
        for name,v in m['outputs'].items():assert sha(rd/name)==v['sha256'], rd/name
        audit=read(rd/'independent_audit.json') if (rd/'independent_audit.json').exists() else None
        legal=m['status']=='completed' and m['metrics'].get('native_full_check_passed') and bool(audit and audit['audit']['passed'])
        if audit:bindings[str(rd/'independent_audit.json')]=sha(rd/'independent_audit.json')
        lines=(rd/'stdout.log').read_text().splitlines();last=last_iteration(lines);critical=[];overuse=[]
        planning=re.findall(r'^H3D_PLAN .*?planning_seconds=([\d.]+)', '\n'.join(lines), re.M)
        if arm in reg['arms']:
            assert m['environment']['VPR_H3D_MODE']=='off'
            assert sha(m['command'][0])==reg['binary_sha256']
            for line in lines:
                if not line.startswith(('H3D_LAYER_BB_CRITICAL ','H3D_LAYER_BB_REFRESH ')):continue
                tag,*tokens=line.split();r=dict(x.split('=',1) for x in tokens)
                assert int(r['new_min'])==0 and int(r['new_max'])>=int(r['old_max'])
                assert (int(r['old_min']),int(r['old_max']))!=(int(r['new_min']),int(r['new_max']))
                if tag=='H3D_LAYER_BB_CRITICAL':
                    assert arm in ['Z','K'] and int(r['remaining'])>0 and int(r['witness_pin'])>0
                    nominal=0. if arm=='Z' else reg['threshold'];cutoff=struct.unpack('f',struct.pack('f',nominal))[0]
                    assert float(r['threshold'])==cutoff and math.isfinite(float(r['criticality'])) and float(r['criticality'])>=cutoff
                    critical.append(r)
                else:
                    assert arm!='C' and int(r['iter'])>=2 and int(r['occ'])>int(r['cap']);overuse.append(r)
            if arm in ['C','O']:assert not critical
            if arm in ['C','Z']:
                eq=read(rd/'scope_equivalence.json');assert eq['passed']==done['gates'][arm]
                bindings[str(rd/'scope_equivalence.json')]=sha(rd/'scope_equivalence.json')
        rows.append(dict(arm=arm,path=str(rd),reused=arm in refs,status='legal' if legal else m['status'] if m['status']!='completed' else 'completed_not_certified',
            legal_cpd_ns=m['metrics'].get('critical_path_ns') if legal else None,native_cpd_ns=m['metrics'].get('critical_path_ns'),
            iterations=m['metrics'].get('iterations') or (last['iteration'] if last else None),last_overused_rr_nodes=last['overused_rr_nodes'] if last else None,
            physical_metrics=audit['physical_metrics'] if legal else None,planning_seconds=float(planning[-1]) if planning else 0. if arm in reg['arms'] or arm in ['A0','A1'] else None,
            process_seconds=m['wall_seconds'],critical_expansion_events=len(critical),critical_expanded_nets=len({r['net'] for r in critical}),
            initial_critical_expansions=sum(int(r['iter'])==1 for r in critical),overuse_expansion_events=len(overuse),
            overuse_expanded_nets=len({r['net'] for r in overuse}),trigger_scope='Logged witnesses checked; not an independent live criticality reconstruction.'))
    index={r['arm']:r for r in rows};pairs={}
    for ref in ['A0','R1','A1','C','O','Z']:
        x,y=index[ref],index['K'];valid=x['status']==y['status']=='legal'
        pairs[ref+'->K']=dict(both_legal=valid,recovered=x['status'] not in ['legal','missing'] and y['status']=='legal',lost=x['status']=='legal' and y['status'] not in ['legal','missing'],
            cpd_improvement_pct=(x['legal_cpd_ns']-y['legal_cpd_ns'])/x['legal_cpd_ns']*100 if valid else None)
    result=dict(passed=True,gate_passed=done['gate_passed'],circuit=reg['circuit'],observations=rows,comparisons=pairs,
        input_sha256=bindings,script_sha256=sha(__file__),statuses=dict(collections.Counter(r['status'] for r in rows)),
        qualification='Guide-off, previously seen seed11 development scope experiment. Failed CPD excluded; all declared roles retained. No guide-causality, general success-rate or formal runtime claim. Missing physical failure counts require a separate failed-route audit.')
    write(b/'scope_analysis.json',result)
    print({k:result[k] for k in ['passed','gate_passed','circuit','statuses','comparisons']})

if __name__=='__main__':main()
