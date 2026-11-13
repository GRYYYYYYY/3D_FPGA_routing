#!/usr/bin/env python3
"""Validate sealed count2 controls without inferring minimum-CPD selection."""
import argparse
from pathlib import Path
import re
from retained_prefix_workflow import read, write, sha, normalized_command, route_body
from routing_log_metrics import ROW


def rows(path):
    return [line.split() for line in path.read_text().splitlines() if ROW.match(line)]


def observe(rd):
    m=read(rd/'manifest.json');log=(rd/'stdout.log').read_text();table=rows(rd/'stdout.log')
    for n,h in m['outputs'].items():assert sha(rd/n)==h['sha256'],rd/n
    audit=read(rd/'independent_audit.json') if (rd/'independent_audit.json').exists() else None
    legal=m['status']=='completed' and m['metrics'].get('native_full_check_passed') and bool(audit and audit['audit']['passed'])
    if legal and (rd/'h3d_final_guides.csv').exists():
        g=read(rd/'final_guide_audit.json');assert g['passed']
        assert g['route_sha256']==sha(rd/'routed.route') and g['trace_sha256']==sha(rd/'h3d_final_guides.csv')
    planning=re.findall(r'^H3D_PLAN .*?planning_seconds=([\d.eE+-]+)',log,re.M)
    return dict(path=str(rd),status='legal' if legal else m['status'] if m['status']!='completed' else 'completed_not_certified',
        legal_cpd_ns=m['metrics'].get('critical_path_ns') if legal else None,
        iterations=m['metrics'].get('iterations') or (int(table[-1][0]) if table else None),
        legal_iteration_numbers=[int(r[0]) for r in table if int(r[7])==0],
        planning_seconds=float(planning[-1]) if planning else 0.,process_seconds=m['wall_seconds'],
        router_seconds=m['metrics'].get('routing_seconds'),physical_metrics=audit['physical_metrics'] if legal else None,
        restored_best='Restoring best routing' in log,
        early_exit_messages=[line for line in log.splitlines() if line.startswith('Giving up routing since additional routing convergences')],
        qualification='Legal iteration rows are observed feasibility, not independently reconstructed native convergence state. Best route ranks setup slack then other timing metrics and wirelength, not minimum CPD alone.')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);a=ap.parse_args();b=a.batch.resolve()
    reg=read(b/'registration.json');done=read(b/'completion.json');assert read(b/'input_seal.json')['passed']
    out=[];comparisons={};bindings={str(p):sha(p) for p in [b/'registration.json',b/'completion.json',b/'input_seal.json']}
    for arm in reg['arms']:
        src=Path(reg['references'][arm]);rd=b/'runs'/f'eltwise_layer_{arm}'
        c=observe(src);c.update(arm=arm,count=1,reused=True);out.append(c)
        if not (rd/'manifest.json').exists():out.append(dict(arm=arm,count=2,status='missing',legal_cpd_ns=None));continue
        old=read(src/'manifest.json');m=read(rd/'manifest.json');cmd=list(m['command'])
        i=cmd.index('--router_max_convergence_count');assert cmd[i+1]=='2';del cmd[i:i+2]
        assert normalized_command(cmd)==normalized_command(old['command'])
        assert m['environment']==old['environment'] and sha(cmd[0])==sha(old['command'][0])
        for name in ['packed.net','placed.place']:assert sha(src/name)==sha(rd/name)
        gate=read(rd/'first_convergence_prefix.json');assert gate['passed']==done['prefix_gates'][arm]
        cr=rows(src/'stdout.log');tr=rows(rd/'stdout.log');strip=lambda r:r[:1]+r[2:]
        assert gate['passed']==(len(tr)>=len(cr) and list(map(strip,tr[:len(cr)]))==list(map(strip,cr)))
        log=(rd/'stdout.log').read_text();assert 'router_opts.max_convergence_count: 2' in log
        t=observe(rd);t.update(arm=arm,count=2,reused=False,prefix_gate_passed=gate['passed']);out.append(t)
        if t['status']=='legal':assert t['restored_best']
        both=c['status']==t['status']=='legal'
        comparisons[arm]=dict(both_legal=both,prefix_gate_passed=gate['passed'],
            cpd_improvement_pct=(1-t['legal_cpd_ns']/c['legal_cpd_ns'])*100 if both else None,
            same_route=route_body(src/'routed.route')==route_body(rd/'routed.route') if both else None,
            additional_iterations=t['iterations']-c['iterations'] if t['iterations'] is not None and c['iterations'] is not None else None)
        for d in [src,rd]:
            for n in ['manifest.json','independent_audit.json','final_guide_audit.json','first_convergence_prefix.json']:
                if (d/n).exists():bindings[str(d/n)]=sha(d/n)
    result=dict(status='sealed_native_reconvergence_analysis',observations=out,comparisons=comparisons,
        missing_arms=done['missing_arms'],binding_sha256=bindings,analyzer_sha256=sha(__file__),
        qualification='Development paired QoR only; no formal process-time ratio, no causal guide attribution, no global research completion.')
    write(b/'reconvergence_analysis.json',result)
    print({a:c for a,c in comparisons.items()})


if __name__=='__main__':main()
