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
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--circuits',nargs='+',default=['attention_layer']);ap.add_argument('--arms',nargs='+',choices=['S','A3','F3','U3'],default=['S','A3','F3','U3']);args=ap.parse_args()
    assert args.arms==['S','A3','F3','U3']
    assert json.loads((D/'selective_attention_dev_01/input_seal.json').read_text())['passed']
    assert json.loads((D/'layer_bbox_dev_01/input_seal.json').read_text())['passed']
    out=D/args.out;out.mkdir(exist_ok=False)
    lock=(D/'delayed_attention_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stage=D/'delayed_layer_candidate_01'
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
    env=json.loads((OLD/'selected_configs.json').read_text())['selections']['hybrid_o']['R1']['environment']
    contexts={c:study.context(c,'hybrid_o',11,100) for c in args.circuits}
    registration=dict(utc=utc(),hypothesis='Transfer the delayed-vs-selective causal control to attention: selective A2/F2/U2 are legal at31/32/37iterations; delayed-global2 exactly reproduced each selective route on eltwise. S must reproduce sealed attentionF2; A3/F3/U3 then globallyexpand atiteration2 withoutforcedreroutes. Sameinputs/legacyguide/caps, retainoriginalfailures withoutCPDratios.',
        circuits=args.circuits,arms=args.arms,references=['frozen A0','frozen R1','sealed U'],reference_arms=['A0','R1','Uref','A1','F1','U1','A2','F2','U2'],environment=env,
        source_sha256=source,support_scripts_sha256={m.__file__:sha256(m.__file__) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and m.__file__.endswith('.py') and str(ROOT) in m.__file__},binary=str(binary),binary_sha256=sha256(binary),runner_sha256=sha256(__file__),
        timeout=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,workers=1,
        host=socket.gethostname(),pid=os.getpid(),boot_id=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        timing_use='Development diagnostics only, not formal speedup; paired formal repeats pending',
        note='The delayed control expands all layer BB intervals once at start of iteration2, preserving native net selection/retained trees and XY. It is mutually exclusive with initial-global and overuse-selective scope. Original F2 benefit alone cannot distinguish delayed warm start from selective targeting. No querypriority/P/L/H.64GiB1800s80GiBmax3VPR; noformal timing.')
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
        prior_dir=D/('feedback_expansion_01' if circuit in ['eltwise_layer','attention_layer'] else 'feedback_bnn_dev_01' if circuit=='bnn' else 'feedback_dev_01')/'runs'/f'{circuit}_U'
        prior=json.loads((prior_dir/'manifest.json').read_text());pa=json.loads((prior_dir/'independent_audit.json').read_text()) if (prior_dir/'independent_audit.json').exists() else None
        assert json.loads((prior_dir.parent.parent/'input_seal.json').read_text())['passed']
        assert normalized_command(prior['command'])==normalized_command(old['command'])
        prior_legal=prior['status']=='completed' and prior['metrics']['native_full_check_passed'] and pa and pa['audit']['passed']
        for fn in ['packed.net','placed.place']:assert sha256(prior_dir/fn)==sha256(oldrun/fn)
        for fn in ['manifest.json','routed.route','h3d_final_guides.csv']:io.frozen_hash(prior_dir/fn)
        refs['Uref']=dict(path=str(prior_dir),manifest_sha256=sha256(prior_dir/'manifest.json'),status='legal' if prior_legal else prior['status'],metrics=prior['metrics'],physical_metrics=pa['physical_metrics'] if pa else None,reused_reference=True,process_seconds=prior['wall_seconds'])
        rows.append(dict(circuit=circuit,arm='Uref',**refs['Uref']))
        for label in ['A1','F1','U1']:
            previous=D/'layer_bbox_dev_01/runs'/f'{circuit}_{label}'
            pm=json.loads((previous/'manifest.json').read_text());pa=json.loads((previous/'independent_audit.json').read_text())
            assert pm['status']=='completed' and pm['metrics']['native_full_check_passed'] and pa['audit']['passed']
            assert normalized_command(pm['command'])==normalized_command(old['command'])
            for fn in ['packed.net','placed.place']:assert sha256(previous/fn)==sha256(oldrun/fn)
            for fn in ['manifest.json','routed.route','independent_audit.json']:io.frozen_hash(previous/fn)
            refs[label]=dict(path=str(previous),manifest_sha256=sha256(previous/'manifest.json'),status='legal',metrics=pm['metrics'],physical_metrics=pa['physical_metrics'],reused_reference=True,process_seconds=pm['wall_seconds'])
            rows.append(dict(circuit=circuit,arm=label,**refs[label]))
        for label in ['A2','F2','U2']:
            previous=D/'selective_attention_dev_01/runs'/f'{circuit}_{label}'
            pm=json.loads((previous/'manifest.json').read_text());pa=json.loads((previous/'independent_audit.json').read_text())
            assert pm['status']=='completed' and pm['metrics']['native_full_check_passed'] and pa['audit']['passed']
            assert normalized_command(pm['command'])==normalized_command(old['command'])
            for fn in ['packed.net','placed.place']:assert sha256(previous/fn)==sha256(oldrun/fn)
            for fn in ['manifest.json','routed.route','independent_audit.json']:io.frozen_hash(previous/fn)
            refs[label]=dict(path=str(previous),manifest_sha256=sha256(previous/'manifest.json'),status='legal',metrics=pm['metrics'],physical_metrics=pa['physical_metrics'],reused_reference=True,process_seconds=pm['wall_seconds'])
            rows.append(dict(circuit=circuit,arm=label,**refs[label]))
        write_json(out/f'{circuit}_references.json',refs)
        receipts=[]
        for arm in args.arms:
            if shutil.disk_usage(out).free < 80*1024**3:raise RuntimeError('Disk reserve reached; preserve prior cases')
            name=f'{circuit}_{arm}';rd=out/'runs'/name;rd.mkdir(parents=True)
            for fname in ['packed.net','placed.place']:shutil.copy2(oldrun/fname,rd/fname)
            cmd=list(old['command']);cmd[0]=str(binary)
            for opt,fname in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/fname)
            settings=dict(env,VPR_H3D_TRACE_TABLE='1',VPR_H3D_FINAL_TRACE='1',VPR_H3D_MIXED_DELAY='0',VPR_H3D_TARGET_FRONTIER='0',VPR_H3D_BOUND_CLAMP='0',VPR_H3D_TIMING_GUIDE='0',VPR_H3D_ASSIGNMENT='shared',VPR_H3D_FEEDBACK='1' if arm=='U3' else '0',VPR_H3D_GENERATION_CLOSURE='1',VPR_H3D_SHARED_CLOSURE='1',VPR_H3D_COMPACT_CLOSURE='1',VPR_H3D_CLOSURE_VIEW='1',VPR_H3D_ALL_LAYER_BB='0',VPR_H3D_LAYER_BB_FEEDBACK='1' if arm=='S' else '0',VPR_H3D_LAYER_BB_DELAYED='0' if arm=='S' else '1')
            if arm=='A3':settings=dict(VPR_H3D_ALL_LAYER_BB='0',VPR_H3D_LAYER_BB_FEEDBACK='0',VPR_H3D_LAYER_BB_DELAYED='1')
            if arm=='X2':settings['VPR_H3D_TEST_ROLLBACK_ONCE']='1'
            if arm=='G':settings['VPR_H3D_CANDIDATE_COST']='geometry'
            receipt=io.run(name,cmd,environment=settings,timeout=1800,
                frozen=[binary,cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],oldrun/'packed.net',oldrun/'placed.place',out/'registration.json'],
                private_inputs=[rd/'packed.net',rd/'placed.place'],tags=dict(circuit=circuit,arm=arm,phase='development',hypothesis='selective_congestion_layer_scope'))
            checks=dict(packed_identical=sha256(rd/'packed.net')==sha256(oldrun/'packed.net'),placement_identical=placements(rd/'placed.place')==placements(oldrun/'placed.place'))
            write_json(rd/'pair_check.json',dict(passed=all(checks.values()),checks=checks,source=str(oldrun)))
            assert all(checks.values())
            if arm=='S':
                previous=pathlib.Path(refs['F2']['path'])
                prior=json.loads((previous/'manifest.json').read_text())
                for fn in ['manifest.json','routed.route','independent_audit.json']:io.frozen_hash(previous/fn)
                checks=dict(status=receipt['status']==prior['status'],route_body=body_hash(rd/'routed.route')==body_hash(previous/'routed.route'),metrics=all(receipt['metrics'].get(k)==prior['metrics'].get(k) for k in ['critical_path_ns','wirelength','iterations']))
                if arm=='S':checks['guides']=sha256(rd/'h3d_final_guides.csv')==sha256(previous/'h3d_final_guides.csv')
                events=lambda p:[l for l in (p/'stdout.log').read_text().splitlines() if l.startswith(('H3D_LAYER_BB_REFRESH ','H3D_TABLE '))]
                checks['scope_and_tables']=events(rd)==events(previous)
                checks['no_delayed_expansion']=not any(l.startswith('H3D_LAYER_BB_DELAYED ') for l in (rd/'stdout.log').read_text().splitlines())
                write_json(rd/'default_off_equivalence.json',dict(passed=all(checks.values()),checks=checks,reference=str(previous)))
                assert all(checks.values()),'Default-off changed route; diagnose before selective scope'
            if arm=='X2' and receipt['status']=='completed':
                log=(rd/'stdout.log').read_text();counts=re.findall(r'^H3D_TREE .*?rollbacks=(\d+)',log,re.M)
                assert counts and int(counts[-1])==1, 'Forced rollback diagnostic must exercise exactly one transaction'
                write_json(rd/'rollback_exercised.json',dict(passed=True,rollbacks=int(counts[-1]),scope='Forced completed replacement rollback, later FULL/native and independent final validation remain required'))
            receipts.append(receipt)
            if arm=='F' and (receipt['status'] not in ['completed','failed','timeout'] or (refs['R1']['status']=='legal' and receipt['status']!='completed')):
                write_json(out/f'{circuit}_gate_failure.json',dict(status=receipt['status'],dependent_arms='missing_not_launched'))
                break
        study.BASE=out
        study.audit_batch(ctx,receipts,out/f'{circuit}_audit.json')
        study.BASE=OLD
        for receipt in receipts:
            rd=out/'runs'/receipt['name'];audit=json.loads((rd/'independent_audit.json').read_text()) if (rd/'independent_audit.json').exists() else None
            if receipt['tags']['arm']!='A3' and audit and audit['audit']['passed']:
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
