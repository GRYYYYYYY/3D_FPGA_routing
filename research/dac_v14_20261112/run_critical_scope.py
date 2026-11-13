#!/usr/bin/env python3
"""Independent native search-domain experiment; no crossing guide in any arm."""
from pathlib import Path
import argparse
import fcntl
import os
import shutil
import socket
import sys
from retained_prefix_workflow import D, read, write, sha, normalized_command, route_body, require_formal_terminal

ROOT = D.parents[1]
OLD = ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0] = [str(OLD/'execution_scripts'), str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    ap.add_argument('--circuit', choices=['eltwise_layer','attention_layer'], required=True)
    ap.add_argument('--stage', default='critical_scope_candidate_02'); args = ap.parse_args()
    require_formal_terminal()
    lock=(D/'critical_scope_runner.lock').open('w'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert shutil.disk_usage(D).free >= 80*1024**3
    stage=D/args.stage; binding=read(stage/'binding.json'); assert sha(stage/'bin/vpr')==binding['binary_sha256']
    for p,h in binding['source_sha256'].items(): assert sha(stage/'src'/p)==h
    aggregate=read(D/'scope_six_circuit_summary.json')
    refs={r['arm']:Path(r['path']) for r in aggregate['observations'] if r['circuit']==args.circuit and r['arm'] in ['A0','R1','A1']}
    assert set(refs)=={'A0','R1','A1'}
    prior=read(refs['A0']/'manifest.json'); reference_global=read(refs['A1']/'manifest.json')
    assert reference_global['metrics']['native_full_check_passed']
    assert prior['command'][prior['command'].index('--seed')+1]=='11'
    ctx=study.context(args.circuit,'hybrid_o',11,100)  # Resolve OLD protocol before redirecting outputs.
    out=D/args.out; out.mkdir(exist_ok=False); (out/'bin').mkdir()
    shutil.copy2(stage/'bin/vpr',out/'bin/vpr'); shutil.copytree(stage/'src',out/'source')
    shutil.copy2(stage/'binding.json',out/'candidate_binding.json'); shutil.copy2(__file__,out/'runner.py')
    env={k:v for k,v in prior['environment'].items() if not k.startswith('VPR_H3D_')}
    env.update(VPR_H3D_MODE='off',VPR_H3D_ALL_LAYER_BB='0',VPR_H3D_LAYER_BB_FEEDBACK='0',VPR_H3D_LAYER_BB_DELAYED='0')
    reg=dict(circuit=args.circuit,seed=11,family='hybrid_o',flow='p0',width=100,
        arms=['C','O','Z','K'],execution_order=['C','Z','O','K'],threshold=.9,
        hypothesis=read(D/'critical_scope_experiment_01.json'),environment=env,binary_sha256=sha(out/'bin/vpr'),
        source_sha256=binding['source_sha256'],runner_sha256=sha(__file__),
        pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],host=socket.gethostname(),
        timeout=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,
        qualification='Native guide-off scope experiment, development process times only; preserve failures and scope controls.')
    write(out/'registration.json',reg); io.BASE=out; io.ADDRESS_SPACE_BYTES=reg['memory_bytes']
    for p in [stage/'binding.json',D/'critical_scope_experiment_01.json',D/'retained_prefix_workflow.py',Path(__file__)]:io.frozen_hash(p,sha(p))
    reference_rows=[]
    for arm,rd in refs.items():
        m=read(rd/'manifest.json'); assert normalized_command(m['command'])==normalized_command(prior['command'])
        for n in ['packed.net','placed.place']:assert sha(rd/n)==sha(refs['A0']/n)
        for p,h in m['shared_inputs'].items():io.frozen_hash(p,h['sha256'])
        for n,h in m['outputs'].items():io.frozen_hash(rd/n,h['sha256'])
        io.frozen_hash(rd/'manifest.json',sha(rd/'manifest.json'))
        audit=read(rd/'independent_audit.json') if (rd/'independent_audit.json').exists() else None
        if audit:io.frozen_hash(rd/'independent_audit.json',sha(rd/'independent_audit.json'))
        legal=m['status']=='completed' and m['metrics'].get('native_full_check_passed') and bool(audit and audit['audit']['passed'])
        reference_rows.append(dict(circuit=args.circuit,arm=arm,path=str(rd),status='legal' if legal else m['status'],
            metrics=m['metrics'],physical_metrics=audit['physical_metrics'] if legal else None,reused=True))
    write(out/'references.json',reference_rows)
    receipts=[]; gates={}
    for arm in reg['execution_order']:
        assert shutil.disk_usage(D).free>=reg['disk_reserve_bytes']; name=f'{args.circuit}_{arm}'; rd=out/'runs'/name;rd.mkdir(parents=True)
        for n in ['packed.net','placed.place']:shutil.copy2(refs['A0']/n,rd/n)
        cmd=list(prior['command']);cmd[0]=str(out/'bin/vpr')
        for opt,n in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/n)
        settings=dict(env,VPR_H3D_LAYER_BB_FEEDBACK='0' if arm=='C' else '1')
        if arm in ['Z','K']:settings['VPR_H3D_LAYER_BB_CRITICALITY']='0' if arm=='Z' else '.9'
        m=io.run(name,cmd,environment=settings,timeout=reg['timeout'],frozen=[cmd[0],cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],out/'registration.json'],
                 private_inputs=[rd/'packed.net',rd/'placed.place'],tags=dict(circuit=args.circuit,arm=arm,phase='development',hypothesis='early_critical_scope'))
        write(rd/'pair_check.json',dict(passed=all(sha(rd/n)==sha(refs['A0']/n) for n in ['packed.net','placed.place']),source=str(refs['A0'])))
        receipts.append(m)
        expected=refs['A0'] if arm=='C' else refs['A1'] if arm=='Z' else None
        if expected:
            rm=read(expected/'manifest.json');checks=dict(native_status=m['status']==rm['status'],
                metrics=all(m['metrics'].get(k)==rm['metrics'].get(k) for k in ['critical_path_ns','iterations','wirelength','native_full_check_passed','routing_success_reported']),
                route_body=(rd/'routed.route').exists() and route_body(rd/'routed.route')==route_body(expected/'routed.route'))
            gates[arm]=all(checks.values());write(rd/'scope_equivalence.json',dict(passed=gates[arm],checks=checks,reference=str(expected)))
            if not gates[arm]:break
    study.BASE=out;study.audit_batch(ctx,receipts,out/'independent_scope_audit.json')
    rows=list(reference_rows)
    for m in receipts:
        rd=out/'runs'/m['name'];audit=read(rd/'independent_audit.json') if (rd/'independent_audit.json').exists() else None
        legal=m['status']=='completed' and m['metrics'].get('native_full_check_passed') and bool(audit and audit['audit']['passed'])
        rows.append(dict(circuit=args.circuit,arm=m['tags']['arm'],path=str(rd),status='legal' if legal else m['status'],metrics=m['metrics'],
            physical_metrics=audit['physical_metrics'] if legal else None,planning_seconds=0.,process_seconds=m['wall_seconds']))
    io.seal_inputs(out/'input_seal.json');write(out/'observations.json',rows)
    write(out/'completion.json',dict(status='scope_batch_terminal_not_research_complete',gates=gates,gate_passed=all(gates.values()) and set(gates)=={'C','Z'},
        missing_arms=[a for a in reg['arms'] if a not in {m['tags']['arm'] for m in receipts}]))

if __name__=='__main__':main()
