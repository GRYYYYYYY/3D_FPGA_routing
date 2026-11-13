#!/usr/bin/env python3
"""Predeclared four-role amplitude bracket, unchanged immutable router binary."""
import argparse,fcntl,os,shutil,socket,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,normalized_command,route_body,require_formal_terminal
from bounded_critical_records import records
ROOT=D.parents[1];OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from audit_final_guides import audit as guide_audit
from run_bounded_cap import prefix
from routing_log_metrics import ROW


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args();require_formal_terminal()
    lock=(D/'critical_scope_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stage=D/'bounded_cap_stage_01';binding=read(stage/'binding.json');assert sha(stage/'bin/vpr')==binding['binary_sha256']
    assert all(sha(stage/'src'/p)==h for p,h in binding['source_sha256'].items())
    protocol=read(D/'bounded_cap_range_experiment_01.json');cases=protocol['cases'];assert [r['arm'] for r in cases]==['L2','H2','L1','H1']
    base2=D/'bounded_cap_eltwise_dev_01';base1=D/'bounded_critical_count1_eltwise_dev_01';assert read(base2/'input_seal.json')['passed'] and read(base1/'input_seal.json')['passed']
    assert read(base2/'bounded_cap_analysis.json')['passed']
    native=D/'native_reconvergence_eltwise_dev_01';reg0=read(native/'registration.json')
    refs={str(c):{a:str(Path(reg0['references'][a]) if c==1 else native/'runs'/('eltwise_layer_'+a)) for a in ['A0','R1','Tf','A1']} for c in [1,2]}
    controls={str(c):{a:str((base1 if c==1 else base2)/'runs'/('eltwise_layer_'+a)) for a in ['C','Z']} for c in [1,2]}
    compat={}
    for a in ['C','Z']:
        old,new=Path(controls['1'][a]),Path(controls['2'][a]);om,nm=read(old/'manifest.json'),read(new/'manifest.json');its=int(om['metrics']['iterations'])
        assert nm['shared_inputs'][nm['command'][0]]['sha256']==binding['binary_sha256']
        left=prefix((old/'stdout.log').read_text().splitlines(),its);right=prefix((new/'stdout.log').read_text().splitlines(),its);allowed={l.split()[0] for l in left if l.startswith('H3D_')}
        checks=dict(projected_cost_records=records(left,allowed)==records(right,allowed),prefix=[l for l in left if l.startswith('H3D_PREFIX_')]==[l for l in right if l.startswith('H3D_PREFIX_')],
            numeric_rows=[l.split()[:1]+l.split()[2:] for l in left if ROW.match(l)]==[l.split()[:1]+l.split()[2:] for l in right if ROW.match(l)])
        compat[a]=dict(passed=all(checks.values()),checks=checks,first_legal_iteration=its,old=str(old),current=str(new));assert compat[a]['passed']
    parent={2:base2/'runs/eltwise_layer_K',1:D/'bounded_cap_count1_eltwise_dev_01/runs/eltwise_layer_K'}
    assert read(parent[1].parent.parent/'input_seal.json')['passed']
    out=D/args.out;out.mkdir(exist_ok=False);(out/'bin').mkdir();shutil.copy2(stage/'bin/vpr',out/'bin/vpr');shutil.copytree(stage/'src',out/'source')
    for n in ['binding.json','CMakeCache.txt']:shutil.copy2(stage/n,out/('candidate_binding.json' if n=='binding.json' else n))
    shutil.copy2(__file__,out/'runner.py');shutil.copy2(OLD/'runtime_dependency_binding.json',out/'runtime_dependency_binding.json')
    r=dict(protocol=protocol,arms=[x['arm'] for x in cases],references=refs,controls=controls,parent_runs={str(k):str(v) for k,v in parent.items()},compatibility=compat,binary_sha256=binding['binary_sha256'],source_sha256=binding['source_sha256'],
        pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],host=socket.gethostname(),timeout=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,
        runner_sha256=sha(__file__),support_scripts_sha256={m.__file__:sha(m.__file__) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and m.__file__.endswith('.py') and str(ROOT) in m.__file__})
    write(out/'registration.json',r);write(out/'control_reuse.json',dict(passed=True,compatibility=compat,qualification='Same cap binary count2 controls; older count1 controls have exact actual cost/heap/table/query firstlegal prefix compatibility plus independently tested default-operator compatibility. No formal timing identity across binaries claimed.'))
    io.BASE=out;io.ADDRESS_SPACE_BYTES=r['memory_bytes']
    for p in [Path(__file__),stage/'binding.json',D/'bounded_cap_range_experiment_01.json',base2/'bounded_cap_analysis.json',out/'control_reuse.json']:io.frozen_hash(p,sha(p))
    for p,h in r['support_scripts_sha256'].items():io.frozen_hash(p,h)
    paths=set(Path(p) for group in list(refs.values())+list(controls.values()) for p in group.values())|set(parent.values())
    for rd in paths:
        m=read(rd/'manifest.json');assert m['status']=='completed' and m['metrics']['native_full_check_passed'] and read(rd/'independent_audit.json')['audit']['passed']
        for n in ['packed.net','placed.place']:assert sha(rd/n)==sha(parent[2]/n)
        for p,h in m['shared_inputs'].items():io.frozen_hash(p,h['sha256'])
        for n,h in m['outputs'].items():io.frozen_hash(rd/n,h['sha256'])
        for n in ['manifest.json','independent_audit.json']:io.frozen_hash(rd/n,sha(rd/n))
        for n in ['final_guide_audit.json','h3d_final_guides.csv']:
            if (rd/n).exists():io.frozen_hash(rd/n,sha(rd/n))
    receipts=[];prefix_checks={};ctx=study.context('eltwise_layer','hybrid_o',11,100)
    for case in cases:
        arm,beta,count=case['arm'],case['beta'],case['max_convergences'];assert shutil.disk_usage(D).free>=r['disk_reserve_bytes']
        rd=out/'runs'/('eltwise_layer_'+arm);rd.mkdir(parents=True);pm=read(parent[count]/'manifest.json')
        for n in ['packed.net','placed.place']:shutil.copy2(parent[count]/n,rd/n)
        cmd=list(pm['command']);cmd[0]=str(out/'bin/vpr')
        for opt,n in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/n)
        assert normalized_command(cmd)==normalized_command(read(Path(refs[str(count)]['Tf'])/'manifest.json')['command'])
        env=dict(pm['environment'],VPR_H3D_TRACE_GUIDE_INFLUENCE='1',VPR_H3D_BOUNDED_CRITICAL_GUIDE=str(beta),VPR_H3D_BOUNDED_CRITICAL_CAP_ONLY='1',VPR_H3D_BOUNDED_AFTER_LEGAL='0')
        m=io.run(rd.name,cmd,environment=env,timeout=r['timeout'],frozen=[cmd[0],cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],out/'registration.json'],private_inputs=[rd/'packed.net',rd/'placed.place'],tags=dict(circuit='eltwise_layer',arm=arm,beta=beta,max_convergences=count,phase='development',hypothesis='cap_half_one_unit_bracket'))
        receipts.append(m)
        if count==1 and m['status']=='completed' and m['metrics'].get('native_full_check_passed'):
            other=out/'runs'/('eltwise_layer_'+arm[0]+'2');its=int(m['metrics']['iterations']);first=prefix((rd/'stdout.log').read_text().splitlines(),its);second=prefix((other/'stdout.log').read_text().splitlines(),its)
            checks=dict(cost_records=records(first)==records(second),prefix=[l for l in first if l.startswith('H3D_PREFIX_')]==[l for l in second if l.startswith('H3D_PREFIX_')],numeric_rows=[l.split()[:1]+l.split()[2:] for l in first if ROW.match(l)]==[l.split()[:1]+l.split()[2:] for l in second if ROW.match(l)])
            prefix_checks[arm]=dict(passed=all(checks.values()),checks=checks,reference=str(other),first_legal_iteration=its);write(rd/'first_legal_prefix_reproduction.json',prefix_checks[arm])
    study.BASE=out;study.audit_batch(ctx,receipts,out/'independent_cap_range_native_audit.json')
    for m in receipts:
        if m['status']=='completed' and m['metrics'].get('native_full_check_passed'):guide_audit(out/'runs'/m['name'])
    io.seal_inputs(out/'input_seal.json');write(out/'completion.json',dict(status='cap_range_terminal_not_research_complete',gate_passed=True,disabled_gate_passed=True,control_reuse_passed=True,firstlegal_checks=prefix_checks,missing_arms=[x['arm'] for x in cases if x['arm'] not in [m['tags']['arm'] for m in receipts]]))

if __name__=='__main__':main()
