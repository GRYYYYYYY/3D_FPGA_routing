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
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--circuits',nargs='+',default=['spmv','eltwise_layer']);ap.add_argument('--arms',nargs='+',choices=['Pn','En'],default=['Pn','En']);args=ap.parse_args()
    assert args.arms==['Pn','En']
    for dependency in ['source_floor_dev_01','complete_distance_dev_02']:
        assert json.loads((D/dependency/'input_seal.json').read_text())['passed']
    out=D/args.out;out.mkdir(exist_ok=False)
    lock=(D/'distance_dp_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stage=D/'source_floor_candidate_01'
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
    registration=dict(utc=utc(),hypothesis='Same-table DP interaction: Pn uses bounded P distances with independent top1; En uses complete Ed distances with independent top1. Reuse sealed shared P and Ed. Require identical candidate-table fingerprints and distance-query counters against the corresponding shared reference. Separates shared-objective effects from measurement completeness; no extra query method, no timing speedup claim',
        circuits=args.circuits,arms=args.arms,references=['frozen A0','frozen R1','matched sealed P'],reference_arms=['A0','R1','P','Ed'],environment=env,
        source_sha256=source,support_scripts_sha256={m.__file__:sha256(m.__file__) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and m.__file__.endswith('.py') and str(ROOT) in m.__file__},binary=str(binary),binary_sha256=sha256(binary),runner_sha256=sha256(__file__),
        timeout=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,workers=1,
        host=socket.gethostname(),pid=os.getpid(),boot_id=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        timing_use='Development diagnostics only, not formal speedup; paired formal repeats pending',
        note='Diagnostic only, two declared seen development circuits. Broad distance acquisition differs from bounded P; separates measurement limitation from full-distance surrogate quality, not maximum achievable CPD. Extra cost recorded without performance claims. No Rq/Bq/Cq/Sf/H/L/feedback/layer combination. Perprocess1800s64GiB80GiBmax3VPR')
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
        previous=D/'source_floor_dev_01/runs'/f'{circuit}_P'
        prior=json.loads((previous/'manifest.json').read_text());audit=json.loads((previous/'independent_audit.json').read_text())
        assert prior['status']=='completed' and prior['metrics']['native_full_check_passed'] and audit['audit']['passed']
        assert json.loads((previous/'final_guide_audit.json').read_text())['passed']
        assert normalized_command(prior['command'])==normalized_command(old['command'])
        for name in ['packed.net','placed.place']:assert sha256(previous/name)==sha256(oldrun/name)
        for name in ['manifest.json','stdout.log','routed.route','h3d_final_guides.csv','independent_audit.json','final_guide_audit.json']:io.frozen_hash(previous/name)
        refs['P']=dict(path=str(previous),manifest_sha256=sha256(previous/'manifest.json'),status='legal',metrics=prior['metrics'],physical_metrics=audit['physical_metrics'],reused_reference=True,process_seconds=prior['wall_seconds'])
        rows.append(dict(circuit=circuit,arm='P',**refs['P']))
        previous_ed=D/'complete_distance_dev_02/runs'/f'{circuit}_Ed'
        m_ed=json.loads((previous_ed/'manifest.json').read_text())
        assert normalized_command(m_ed['command'])==normalized_command(old['command'])
        assert m_ed['status']=='completed' and m_ed['metrics']['native_full_check_passed']
        a_ed=json.loads((previous_ed/'independent_audit.json').read_text());assert a_ed['audit']['passed']
        assert json.loads((previous_ed/'final_guide_audit.json').read_text())['passed']
        for fname in ['packed.net','placed.place']:assert sha256(previous_ed/fname)==sha256(oldrun/fname)
        for fname in ['manifest.json','stdout.log','routed.route','h3d_final_guides.csv','independent_audit.json','final_guide_audit.json']:io.frozen_hash(previous_ed/fname)
        refs['Ed']=dict(path=str(previous_ed),manifest_sha256=sha256(previous_ed/'manifest.json'),status='legal',metrics=m_ed['metrics'],physical_metrics=a_ed['physical_metrics'],reused_reference=True,process_seconds=m_ed['wall_seconds'])
        rows.append(dict(circuit=circuit,arm='Ed',**refs['Ed']))
        write_json(out/f'{circuit}_references.json',refs)
        receipts=[]
        for arm in args.arms:
            if shutil.disk_usage(out).free < 80*1024**3:raise RuntimeError('Disk reserve reached; preserve prior cases')
            name=f'{circuit}_{arm}';rd=out/'runs'/name;rd.mkdir(parents=True)
            for fname in ['packed.net','placed.place']:shutil.copy2(oldrun/fname,rd/fname)
            cmd=list(old['command']);cmd[0]=str(binary)
            for opt,fname in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/fname)
            graph_binding=json.loads((D/'query_prototype/rrg_spmv/binding.json').read_text())
            graph_path=cmd[cmd.index('--read_rr_graph')+1]
            assert old['shared_inputs'][graph_path]['sha256']==graph_binding['graph_sha256']
            bound=json.loads((D/'complete_distance_bounds.json').read_text());assert bound['passed']
            io.frozen_hash(D/'complete_distance_bounds.json')
            control=previous if arm=='Pn' else previous_ed
            control_manifest=json.loads((control/'manifest.json').read_text())
            settings=dict(control_manifest['environment'],VPR_H3D_ASSIGNMENT='independent')
            receipt=io.run(name,cmd,environment=settings,timeout=1800,
                frozen=[binary,cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],oldrun/'packed.net',oldrun/'placed.place',out/'registration.json'],
                private_inputs=[rd/'packed.net',rd/'placed.place'],tags=dict(circuit=circuit,arm=arm,phase='development',hypothesis='same_table_distance_dp_interaction',diagnostic_only=True))
            checks=dict(packed_identical=sha256(rd/'packed.net')==sha256(oldrun/'packed.net'),placement_identical=placements(rd/'placed.place')==placements(oldrun/'placed.place'))
            write_json(rd/'pair_check.json',dict(passed=all(checks.values()),checks=checks,source=str(oldrun)))
            assert all(checks.values())
            if receipt['status']=='completed':
                current_lines=(rd/'stdout.log').read_text().splitlines()
                old_lines=(control/'stdout.log').read_text().splitlines()
                prefixes=['H3D_TABLE ','H3D_DELAY ','H3D_TARGET_DELAY ','H3D_PERSISTENT_DELAY ']
                checks={prefix.strip():[l for l in current_lines if l.startswith(prefix)]==[l for l in old_lines if l.startswith(prefix)] for prefix in prefixes}
                write_json(rd/'same_table_gate.json',dict(passed=all(checks.values()),checks=checks,reference=str(control)))
                assert all(checks.values()),'Assignment ablation changed pre-solver table or query work'
            receipts.append(receipt)
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
