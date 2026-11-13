#!/usr/bin/env python3
"""Default-off exact count2 Tf and isolated post-legal planning-freeze test."""
import argparse
import fcntl
import os
from pathlib import Path
import shutil
import socket
import sys
from retained_prefix_workflow import D, read, write, sha, normalized_command, route_body, original_records, require_formal_terminal

ROOT=D.parents[1];OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from audit_final_guides import audit as guide_audit
from routing_log_metrics import ROW


def prefix(lines, iteration):
    for i,line in enumerate(lines):
        m=ROW.match(line)
        if m and int(m[1])==iteration:return lines[:i+1]
    raise ValueError(f'Missing native iteration {iteration}')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--stage',default='post_legal_freeze_candidate_01');args=ap.parse_args()
    require_formal_terminal()
    lock=(D/'critical_scope_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stage=D/args.stage;binding=read(stage/'binding.json');assert sha(stage/'bin/vpr')==binding['binary_sha256']
    for p,h in binding['source_sha256'].items():assert sha(stage/'src'/p)==h
    refbatch=D/'native_reconvergence_eltwise_dev_01';assert read(refbatch/'input_seal.json')['passed']
    refs={a:refbatch/'runs'/f'eltwise_layer_{a}' for a in ['A0','R1','Tf','A1']}
    prior=read(refs['Tf']/'manifest.json');first_iteration=read(refbatch/'registration.json')['references']['Tf']
    first_iteration=read(Path(first_iteration)/'manifest.json')['metrics']['iterations']
    ctx=study.context('eltwise_layer','hybrid_o',11,100)
    out=D/args.out;out.mkdir(exist_ok=False);(out/'bin').mkdir();shutil.copy2(stage/'bin/vpr',out/'bin/vpr')
    shutil.copytree(stage/'src',out/'source');shutil.copy2(stage/'binding.json',out/'candidate_binding.json')
    shutil.copy2(stage/'CMakeCache.txt',out/'CMakeCache.txt');shutil.copy2(__file__,out/'runner.py')
    shutil.copy2(OLD/'runtime_dependency_binding.json',out/'runtime_dependency_binding.json')
    reg=dict(protocol=read(D/'post_legal_freeze_experiment_01.json'),arms=['C','F'],references={a:str(p) for a,p in refs.items()},
        first_legal_iteration=first_iteration,environment=dict(prior['environment'],VPR_H3D_POST_LEGAL_RELEASE='0'),binary_sha256=sha(out/'bin/vpr'),source_sha256=binding['source_sha256'],
        pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],host=socket.gethostname(),
        timeout=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,runner_sha256=sha(__file__),
        support_scripts_sha256={m.__file__:sha(m.__file__) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and m.__file__.endswith('.py') and str(ROOT) in m.__file__})
    write(out/'registration.json',reg);io.BASE=out;io.ADDRESS_SPACE_BYTES=reg['memory_bytes']
    for p in [Path(__file__),stage/'binding.json',D/'post_legal_freeze_experiment_01.json',refbatch/'input_seal.json']:
        io.frozen_hash(p,sha(p))
    for p,h in reg['support_scripts_sha256'].items():io.frozen_hash(p,h)
    for a,rd in refs.items():
        m=read(rd/'manifest.json');assert m['status']=='completed' and m['metrics']['native_full_check_passed']
        assert read(rd/'independent_audit.json')['audit']['passed']
        assert normalized_command(m['command'])==normalized_command(prior['command'])
        for n in ['packed.net','placed.place']:assert sha(rd/n)==sha(refs['Tf']/n)
        for p,h in m['shared_inputs'].items():io.frozen_hash(p,h['sha256'])
        for n,h in m['outputs'].items():io.frozen_hash(rd/n,h['sha256'])
        for n in ['manifest.json','independent_audit.json','final_guide_audit.json']:
            if (rd/n).exists():io.frozen_hash(rd/n,sha(rd/n))
    receipts=[];gate=False
    for arm in reg['arms']:
        assert shutil.disk_usage(D).free>=reg['disk_reserve_bytes']
        rd=out/'runs'/f'eltwise_layer_{arm}';rd.mkdir(parents=True)
        for n in ['packed.net','placed.place']:shutil.copy2(refs['Tf']/n,rd/n)
        cmd=list(prior['command']);cmd[0]=str(out/'bin/vpr')
        for opt,n in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/n)
        env=dict(prior['environment'],VPR_H3D_POST_LEGAL_RELEASE='0',VPR_H3D_POST_LEGAL_FREEZE='0' if arm=='C' else '1')
        m=io.run(rd.name,cmd,environment=env,timeout=reg['timeout'],
            frozen=[cmd[0],cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],out/'registration.json'],
            private_inputs=[rd/'packed.net',rd/'placed.place'],tags=dict(circuit='eltwise_layer',arm=arm,phase='development',hypothesis='post_legal_planning_freeze'))
        receipts.append(m);write(rd/'pair_check.json',dict(passed=all(sha(rd/n)==sha(refs['Tf']/n) for n in ['packed.net','placed.place'])))
        if arm=='C':
            checks=dict(native=m['status']==prior['status'],metrics=all(m['metrics'].get(k)==prior['metrics'].get(k) for k in ['critical_path_ns','wirelength','iterations','native_full_check_passed','routing_success_reported']))
            if m['status']=='completed':
                checks.update(route_body=route_body(rd/'routed.route')==route_body(refs['Tf']/'routed.route'),
                    guides=sha(rd/'h3d_final_guides.csv')==sha(refs['Tf']/'h3d_final_guides.csv'),
                    original_records=original_records((rd/'stdout.log').read_text().splitlines())==original_records((refs['Tf']/'stdout.log').read_text().splitlines()))
            gate=all(checks.values());write(rd/'disabled_reproduction.json',dict(passed=gate,checks=checks,reference=str(refs['Tf'])))
            if not gate:break
    study.BASE=out;study.audit_batch(ctx,receipts,out/'independent_freeze_audit.json')
    for m in receipts:
        rd=out/'runs'/m['name']
        if m['status']=='completed' and m['metrics'].get('native_full_check_passed'):guide_audit(rd)
    io.seal_inputs(out/'input_seal.json');write(out/'completion.json',dict(status='freeze_batch_terminal_not_research_complete',gate_passed=gate,
        missing_arms=[a for a in reg['arms'] if a not in [m['tags']['arm'] for m in receipts]]))


if __name__=='__main__':main()
