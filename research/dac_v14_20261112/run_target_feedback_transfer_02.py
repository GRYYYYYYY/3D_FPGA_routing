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
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--circuits',nargs='+',default=['clstm_like.small','conv_layer']);ap.add_argument('--arms',nargs='+',choices=['F','V','Tf','A1'],default=['F','V','Tf','A1']);args=ap.parse_args()
    assert args.arms==['F','V','Tf','A1']
    selection=json.loads((D/'target_feedback_transfer_selection.json').read_text())
    assert args.circuits==[r['circuit'] for r in selection['selected']]
    out=D/args.out;out.mkdir(exist_ok=False)
    lock=(D/'target_feedback_transfer_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stage=D/'target_feedback_candidate_01'
    built=stage/'bin/vpr';assert built.is_file()
    (out/'bin').mkdir();shutil.copy2(built,out/'bin/vpr');binary=out/'bin/vpr'
    shutil.copy2(__file__,out/'runner.py')
    shutil.copy2(stage/'CMakeCache.txt',out/'CMakeCache.txt')
    source={str(p.relative_to(stage/'src')):sha256(p) for p in (stage/'src/vpr/src/route').glob('h3d*')}
    for name in ['connection_router.tpp','route_net.tpp','SerialNetlistRouter.tpp','route.cpp','route_common.cpp','route_common.h']:
        p=stage/'src/vpr/src/route'/name;source[str(p.relative_to(stage/'src'))]=sha256(p)
    (out/'source').mkdir()
    for relative in source:shutil.copy2(stage/'src'/relative,out/'source'/pathlib.Path(relative).name)
    shutil.copy2(OLD/'runtime_dependency_binding.json',out/'runtime_dependency_binding.json')
    # Existing validated seccomp runner, redirected only via module variables.
    io.BASE=out
    io.ADDRESS_SPACE_BYTES=64*1024**3
    env=json.loads((OLD/'selected_configs.json').read_text())['selections']['hybrid_o']['R1']['environment']
    contexts={c:study.context(c,'hybrid_o',21,100) for c in args.circuits}
    registration=dict(utc=utc(),hypothesis='Fixed original-scope target-feedback transfer beyond sixtrainingcircuits: F staticmustreproduce frozenR1, Vfullfeedback vsTf targetfeedback isolatesrefresh scope. Reuse exactA0/R1 inputs/config; separatelyrun A1nativeinitialglobalscope as strongeralternative-scope control. Select seed21HybridO/P0/W100 firsttwo eligiblecircuits bygridside thenname beforeoutcomeinspection, includingoldfailedconv_layer. No per-input tuning, no querybudgetchange, preserveallfailure/missingstates. ScopeA1 contrasts are notguide-only effects.',
        circuits=args.circuits,arms=args.arms,references=['frozen A0','frozen R1','matched prior U'],reference_arms=['A0','R1'],seed=21,family='hybrid_o',flow='p0',width=100,selection_sha256=sha256(D/'target_feedback_transfer_selection.json'),environment=env,
        source_sha256=source,support_scripts_sha256={m.__file__:sha256(m.__file__) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and m.__file__.endswith('.py') and str(ROOT) in m.__file__},binary=str(binary),binary_sha256=sha256(binary),runner_sha256=sha256(__file__),
        timeout=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,workers=1,
        host=socket.gethostname(),pid=os.getpid(),boot_id=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        timing_use='Development diagnostics only, not formal speedup; paired formal repeats pending',
        note='Previouslyunexecuted-by-Tf circuit transfer, notclaimedblindtest. Oldbaselines retained includingfailures. Samebinary/per-arm environments for new executions. Formal timingnotclaimed,1800s64GiB80GiBmax3owners; protect frozen stage andallinputs.')
    write_json(out/'registration.json',registration)
    rows=[]
    for circuit,ctx in contexts.items():
        size=ctx['size'];stem=f'heldout_{circuit}_s21_hybrid_o_n{size}_w100_p0'
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
            io.frozen_hash(rd/'manifest.json',refs[label]['manifest_sha256'])
            for fn,record in m['outputs'].items():io.frozen_hash(rd/fn,record['sha256'])
            rows.append(dict(circuit=circuit,arm=label,**refs[label]))
        write_json(out/f'{circuit}_references.json',refs)
        receipts=[]
        for arm in args.arms:
            if shutil.disk_usage(out).free < 80*1024**3:raise RuntimeError('Disk reserve reached; preserve prior cases')
            name=f'{circuit}_{arm}';rd=out/'runs'/name;rd.mkdir(parents=True)
            for fname in ['packed.net','placed.place']:shutil.copy2(oldrun/fname,rd/fname)
            cmd=list(old['command']);cmd[0]=str(binary)
            for opt,fname in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/fname)
            settings=dict(env,VPR_H3D_TRACE_TABLE='1',VPR_H3D_FINAL_TRACE='1',VPR_H3D_MIXED_DELAY='0',VPR_H3D_TIMING_GUIDE='0',VPR_H3D_ASSIGNMENT='shared',VPR_H3D_FEEDBACK='1' if arm in ['V','Tf'] else '0',VPR_H3D_PLAN_PROFILE='1',VPR_H3D_GENERATION_CLOSURE='1',VPR_H3D_SHARED_CLOSURE='1',VPR_H3D_COMPACT_CLOSURE='1',VPR_H3D_CLOSURE_VIEW='1',VPR_H3D_TRACE_PRIOR='0',VPR_H3D_TRACE_PLANAR_FEEDBACK='0',VPR_H3D_PLANAR_FEEDBACK='0',VPR_H3D_TARGET_FEEDBACK='1' if arm in ['Tf','X'] else '0',VPR_H3D_EXIT_PRICE='0',VPR_H3D_TRACE_UPDATE_PINS='1' if arm in ['V','Tf'] else '0',VPR_H3D_TIMING_GUIDE_MODE='coverage',VPR_H3D_EQUIVALENT_GUIDES='0',VPR_H3D_TARGET_DELAY='0',VPR_H3D_TARGET_FRONTIER='0',VPR_H3D_SOURCE_GEOMETRY_FLOOR='0',VPR_H3D_REVERSE_RERANK='0',VPR_H3D_QUERY_CRITICALITY_ORDER='0',VPR_H3D_SOURCE_QUERY_SHARE='0',VPR_H3D_LAYER_BB_DELAYED='0',VPR_H3D_ALL_LAYER_BB='0',VPR_H3D_LAYER_BB_FEEDBACK='0')
            if arm=='A1':settings.update(VPR_H3D_MODE='off',VPR_H3D_ALL_LAYER_BB='1')
            receipt=io.run(name,cmd,environment=settings,timeout=1800,
                frozen=[binary,cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],oldrun/'packed.net',oldrun/'placed.place',out/'registration.json',D/'target_feedback_transfer_selection.json'],
                private_inputs=[rd/'packed.net',rd/'placed.place'],tags=dict(circuit=circuit,arm=arm,phase='development',hypothesis='fixed_parameter_new_circuit_transfer',diagnostic_only=False))
            checks=dict(packed_identical=sha256(rd/'packed.net')==sha256(oldrun/'packed.net'),placement_identical=placements(rd/'placed.place')==placements(oldrun/'placed.place'))
            write_json(rd/'pair_check.json',dict(passed=all(checks.values()),checks=checks,source=str(oldrun)))
            assert all(checks.values())
            if arm=='F' and old['status'] in ['completed','failed'] and (oldrun/'routed.route').exists() and old['metrics'].get('critical_path_ns') is not None:
                from routing_log_metrics import last_iteration
                oldlines=(oldrun/'stdout.log').read_text().splitlines();newlines=(rd/'stdout.log').read_text().splitlines()
                checks=dict(status=receipt['status']==old['status'],route_body=(rd/'routed.route').exists() and body_hash(rd/'routed.route')==body_hash(oldrun/'routed.route'),metrics=all(receipt['metrics'].get(k)==old['metrics'].get(k) for k in ['critical_path_ns','wirelength']),last_iteration=last_iteration(oldlines)==last_iteration(newlines))
                write_json(rd/'static_reproduction.json',dict(passed=all(checks.values()),checks=checks,reference=str(oldrun),scope='Complete legal or terminal failed native trajectory endpoint; failed CPD remains provisional and excluded from quality.'))
                assert all(checks.values()),'Static control differs; diagnose before feedback interpretation'
            receipts.append(receipt)
        study.BASE=out
        study.audit_batch(ctx,receipts,out/f'{circuit}_audit.json')
        study.BASE=OLD
        for receipt in receipts:
            rd=out/'runs'/receipt['name'];audit=json.loads((rd/'independent_audit.json').read_text()) if (rd/'independent_audit.json').exists() else None
            if receipt['environment'].get('VPR_H3D_MODE','off')!='off' and audit and audit['audit']['passed']:
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
