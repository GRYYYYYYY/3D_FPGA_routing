#!/usr/bin/env python3
"""Registered paired development runs; no frozen-directory writes or implicit retries."""
import sys, json, pathlib, shutil, re, os, fcntl, argparse, hashlib, subprocess, socket
D=pathlib.Path(__file__).resolve().parent
ROOT=D.parents[1]
OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from lazagna_common import sha256,utc,write_json
from validate_lazagna_vtr9_pilot import placements

def body_hash(p):
    text=p.read_text(); start=text.find('Net ')
    if start<0: raise ValueError('Missing route net body')
    return hashlib.sha256(text[start:].encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--circuits',nargs='+',default=['spmv','softmax']);ap.add_argument('--arms',nargs='+',choices=['F','M','T','Q'],default=['F','M','T','Q']);args=ap.parse_args()
    assert args.arms[0]=='F' and len(args.arms)==len(set(args.arms))
    out=D/args.out;out.mkdir(exist_ok=False)
    lock=(D/'target_query_quota_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stage=D/'target_query_quota_candidate_01'
    built=stage/'bin/vpr';assert built.is_file()
    (out/'bin').mkdir();shutil.copy2(built,out/'bin/vpr');binary=out/'bin/vpr'
    shutil.copy2(__file__,out/'runner.py')
    shutil.copy2(stage/'CMakeCache.txt',out/'CMakeCache.txt')
    source={str(p.relative_to(stage/'src')):sha256(p) for p in (stage/'src/vpr/src/route').glob('h3d*')}
    for name in ['connection_router.tpp','route_net.tpp','SerialNetlistRouter.tpp','route.cpp']:
        p=stage/'src/vpr/src/route'/name;source[str(p.relative_to(stage/'src'))]=sha256(p)
    (out/'source').mkdir()
    for relative in source:shutil.copy2(stage/'src'/relative,out/'source'/pathlib.Path(relative).name)
    shutil.copy2(OLD/'runtime_dependency_binding.json',out/'runtime_dependency_binding.json')
    # Existing validated seccomp runner, redirected only via module variables.
    io.BASE=out
    env=json.loads((OLD/'selected_configs.json').read_text())['selections']['hybrid_o']['R1']['environment']
    contexts={c:study.context(c,'hybrid_o',11,100) for c in args.circuits}
    registration=dict(utc=utc(),hypothesis='Fair per-candidate Q=256 versus T=remaining-budget, retaining 4096 cumulative endpoint budget; unchanged F/M/T reproduction and selected-guide measurement coverage',
        circuits=args.circuits,arms=args.arms,references=['frozen A0','frozen R1'],environment=env,
        source_sha256=source,support_scripts_sha256={m.__file__:sha256(m.__file__) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and m.__file__.endswith('.py') and str(ROOT) in m.__file__},binary=str(binary),binary_sha256=sha256(binary),runner_sha256=sha256(__file__),
        timeout=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,workers=1,
        host=socket.gethostname(),pid=os.getpid(),boot_id=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        timing_use='Development diagnostics only, not formal speedup; paired formal repeats pending',
        note='F reproduces frozen R1; M reproduces h1_dev_02 mixed scoring; T changes only query measurement selection, retaining calibrated missing-distance estimates. At most K diverse current feasible targets per pin, both bidirectional fronts charged to one endpoint budget. No H or feedback. Final route audit and final-guide trace required. Q alone limits each candidate request to 256 settlements, counting discarded work. F/M/T reproduction required before Q; selected-guide counters added without changing cost. Not formal timing.')
    write_json(out/'registration.json',registration)
    rows=[]
    for circuit,ctx in contexts.items():
        size=ctx['size'];stem=f'training_{circuit}_s11_hybrid_o_n{size}_w100_p0'
        oldrun=OLD/'runs'/f'{stem}_delay_critical_c6'
        old=json.loads((oldrun/'manifest.json').read_text())
        refs={}
        # Verify actual matching reference inputs, binaries and existing route audits.
        for label,suffix in [('A0','a0'),('R1','delay_critical_c6')]:
            rd=OLD/'runs'/f'{stem}_{suffix}';m=json.loads((rd/'manifest.json').read_text())
            def normalized_command(command):
                command=list(command[1:])
                for opt in ['--net_file','--place_file','--route_file']:
                    command[command.index(opt)+1]='<private-output-or-paired-input>'
                return command
            assert normalized_command(m['command'])==normalized_command(old['command'])
            for opt in ['--seed','--read_rr_graph','--route_chan_width','--max_router_iterations','--num_workers']:
                assert m['command'][m['command'].index(opt)+1]==old['command'][old['command'].index(opt)+1]
            assert m['command'][1:3]==old['command'][1:3]
            if label=='R1': assert all(m['environment'].get(k)==v for k,v in env.items())
            for p,expected in m['shared_inputs'].items():io.frozen_hash(p,expected['sha256'])
            for fname in ['packed.net','placed.place']:
                assert sha256(rd/fname)==sha256(oldrun/fname)
            audit=json.loads((rd/'independent_audit.json').read_text()) if (rd/'independent_audit.json').exists() else None
            legal=m['status']=='completed' and m['metrics']['native_full_check_passed'] and audit and audit['audit']['passed']
            refs[label]=dict(path=str(rd),manifest_sha256=sha256(rd/'manifest.json'),status='legal' if legal else m['status'],metrics=m['metrics'],physical_metrics=audit['physical_metrics'] if audit else None)
            if legal:assert sha256(rd/'routed.route')==m['outputs']['routed.route']['sha256']
            rows.append(dict(circuit=circuit,arm=label,**refs[label]))
        write_json(out/f'{circuit}_references.json',refs)
        receipts=[]
        for arm in args.arms:
            if shutil.disk_usage(out).free < 80*1024**3:raise RuntimeError('Disk reserve reached; preserve prior cases')
            name=f'{circuit}_{arm}';rd=out/'runs'/name;rd.mkdir(parents=True)
            for fname in ['packed.net','placed.place']:shutil.copy2(oldrun/fname,rd/fname)
            cmd=list(old['command']);cmd[0]=str(binary)
            for opt,fname in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/fname)
            settings=dict(env,VPR_H3D_TRACE_TABLE='1',VPR_H3D_FINAL_TRACE='1',VPR_H3D_MIXED_DELAY='1' if arm in ['M','T','Q'] else '0',VPR_H3D_TARGET_DELAY='1' if arm in ['T','Q'] else '0',VPR_H3D_TARGET_QUOTA='256' if arm=='Q' else '0',VPR_H3D_TIMING_GUIDE='0',VPR_H3D_ASSIGNMENT='shared',VPR_H3D_FEEDBACK='0')
            receipt=io.run(name,cmd,environment=settings,timeout=1800,
                frozen=[binary,cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],oldrun/'packed.net',oldrun/'placed.place',out/'registration.json'],
                private_inputs=[rd/'packed.net',rd/'placed.place'],tags=dict(circuit=circuit,arm=arm,phase='development',hypothesis='candidate_directed_delay_same_endpoint_budget'))
            checks=dict(packed_identical=sha256(rd/'packed.net')==sha256(oldrun/'packed.net'),placement_identical=placements(rd/'placed.place')==placements(oldrun/'placed.place'))
            write_json(rd/'pair_check.json',dict(passed=all(checks.values()),checks=checks,source=str(oldrun)))
            assert all(checks.values())
            if arm=='F' and receipt['status']=='completed' and refs['R1']['status']=='legal':
                checks=dict(route_body=body_hash(rd/'routed.route')==body_hash(oldrun/'routed.route'),metrics=all(receipt['metrics'].get(k)==old['metrics'].get(k) for k in ['critical_path_ns','wirelength','iterations']))
                write_json(rd/'equivalence.json',dict(passed=all(checks.values()),checks=checks,scope='Header excluded; complete Net records preserved'))
                assert all(checks.values()),'Default-off differs; diagnose before scoring experiments'
            if arm=='M' and receipt['status']=='completed':
                previous=D/'h1_dev_02/runs'/f'{circuit}_M'
                prior=json.loads((previous/'manifest.json').read_text())
                assert sha256(rd/'packed.net')==sha256(previous/'packed.net')
                assert placements(rd/'placed.place')==placements(previous/'placed.place')
                checks=dict(route_body=body_hash(rd/'routed.route')==body_hash(previous/'routed.route'),metrics=all(receipt['metrics'].get(k)==prior['metrics'].get(k) for k in ['critical_path_ns','wirelength','iterations']))
                write_json(rd/'mixed_equivalence.json',dict(passed=all(checks.values()),checks=checks,reference=str(previous)))
                assert all(checks.values()),'Mixed control changed; diagnose before T'
            if arm=='T' and receipt['status']=='completed':
                previous=D/'target_query_dev_01/runs'/f'{circuit}_T'
                prior=json.loads((previous/'manifest.json').read_text())
                checks=dict(route_body=body_hash(rd/'routed.route')==body_hash(previous/'routed.route'),metrics=all(receipt['metrics'].get(k)==prior['metrics'].get(k) for k in ['critical_path_ns','wirelength','iterations']))
                write_json(rd/'target_equivalence.json',dict(passed=all(checks.values()),checks=checks,reference=str(previous)))
                assert all(checks.values()),'Uncapped T changed; diagnose before Q'
            receipts.append(receipt)
            if arm in ['F','M','T'] and (receipt['status'] not in ['completed','failed','timeout'] or (refs['R1']['status']=='legal' and receipt['status']!='completed')):
                write_json(out/f'{circuit}_gate_failure.json',dict(status=receipt['status'],dependent_arms='missing_not_launched'))
                break
        study.BASE=out
        study.audit_batch(ctx,receipts,out/f'{circuit}_audit.json')
        study.BASE=OLD
        for receipt in receipts:
            rd=out/'runs'/receipt['name'];audit=json.loads((rd/'independent_audit.json').read_text()) if (rd/'independent_audit.json').exists() else None
            if audit and audit['audit']['passed']:
                from audit_final_guides import audit as audit_guides
                audit_guides(rd)
            log=(rd/'stdout.log').read_text()
            h3d=[s for s in log.splitlines() if s.startswith('H3D_')]
            row=dict(circuit=circuit,arm=receipt['tags']['arm'],status='legal' if audit and audit['audit']['passed'] else receipt['status'],metrics=receipt['metrics'],physical_metrics=audit['physical_metrics'] if audit else None,process_seconds=receipt['wall_seconds'],h3d=h3d,path=str(rd))
            rows.append(row)
        write_json(out/'observations.json',rows)
    io.seal_inputs(out/'input_seal.json')
    write_json(out/'completion.json',dict(utc=utc(),status='development_batch_complete_not_research_complete',observations=len(rows)))
if __name__=='__main__':main()
