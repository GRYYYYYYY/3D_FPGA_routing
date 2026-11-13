#!/usr/bin/env python3
"""Read-only physical evidence for every declared failed scope artifact."""
import argparse
from pathlib import Path
import fcntl
import os
import resource
import shutil
import signal
import time
from retained_prefix_workflow import D, read, write, sha, route_body
import diagnose_failed_transfer as diagnostic


def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);ap.add_argument('--out',required=True);args=ap.parse_args()
    lock=(D/'critical_scope_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));signal.alarm(1800)
    b=args.batch.resolve();assert read(b/'input_seal.json')['passed'] and (b/'completion.json').exists()
    reg=read(b/'registration.json');refs=read(b/'references.json')
    sources={r['arm']:Path(r['path']) for r in refs}
    sources.update({a:b/'runs'/f"{reg['circuit']}_{a}" for a in reg['arms']})
    sources={a:p for a,p in sources.items() if (p/'manifest.json').exists() and read(p/'manifest.json')['status']=='failed'}
    assert sources and shutil.disk_usage(D).free>=80*1024**3
    out=D/args.out;out.mkdir(exist_ok=False);shutil.copy2(__file__,out/'runner.py')
    paths=[b/'input_seal.json',b/'completion.json',b/'registration.json',b/'references.json',out/'runner.py',Path(diagnostic.__file__),Path(diagnostic.cr.__file__),Path(diagnostic.study.__file__)]
    manifests={a:read(p/'manifest.json') for a,p in sources.items()}
    m=next(iter(manifests.values()));graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);graph_hash=sha(graph);paths.append(graph)
    unique={};aliases={}
    for a,p in sources.items():
        m=manifests[a];g=m['command'][m['command'].index('--read_rr_graph')+1]
        assert m['shared_inputs'][g]['sha256']==graph_hash
        assert sha(p/'routed.route')==m['outputs']['routed.route']['sha256']
        for n in ['manifest.json','routed.route','stdout.log','h3d_final_guides.csv']:
            if (p/n).exists():paths.append(p/n)
        # The descendant guide-membership diagnostic must also match. Route
        # equality alone does not allow guide statistics to be reused.
        identity=(route_body(p/'routed.route'),sha(p/'h3d_final_guides.csv') if (p/'h3d_final_guides.csv').exists() else None)
        if identity in unique:aliases[a]=unique[identity]
        else:unique[identity]=a
    bindings={str(p):sha(p) for p in paths}
    write(out/'registration.json',dict(question='Quantify saved failed-route physical resources, overuse and affected planar/remote connections. Preserve failure and exclude CPD.',sources={a:str(p) for a,p in sources.items()},
        reused_identical_route_and_guide_aliases=aliases,bindings=bindings,pid=os.getpid(),
        start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],native_route_calls=0,
        timeout_seconds=1800,memory_bytes=32*1024**3,disk_reserve_bytes=80*1024**3))
    start=time.monotonic();cr=diagnostic.cr;cr.graph_records=diagnostic.records
    evidence=cr.batch_graph_evidence(graph,[sources[a]/'routed.route' for a in unique.values()]);evidence['graph_path']=graph
    result={}
    for a in unique.values():
        (out/a).mkdir();result[a]=diagnostic.analyze_saved(sources[a],evidence,out/a)
    for a,base in aliases.items():
        result[a]=dict(result[base],source=str(sources[a]),reused_from=base,
            qualification='Exact graph, route body and guide bytes match. Physical and descendant statistics reused; not an independent route observation.')
    checks={p:sha(p)==h for p,h in bindings.items()};write(out/'input_seal.json',dict(passed=all(checks.values()),checks=checks));assert all(checks.values())
    write(out/'summary.json',dict(passed=True,results=result,native_route_calls=0,
        qualification='Saved failed artifacts only. Native status remains failed, legal CPD absent; graph scoped-audit failure is expected for overuse. Not necessarily native final iteration state.'))
    write(out/'completion.json',dict(status='read_only_diagnostic_complete',wall_seconds=time.monotonic()-start))
    print({a:r['summary'] for a,r in result.items()})


if __name__=='__main__':main()
