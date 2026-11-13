#!/usr/bin/env python3
"""Reuse both completed controls; continue only the two predeclared quality roles."""
import fcntl,os,re,shutil,socket,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,normalized_command,require_formal_terminal
from run_outside_native import check
from bounded_critical_records import records
from run_bounded_cap import prefix
from routing_log_metrics import ROW
ROOT=D.parents[1];OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from audit_final_guides import audit as guide_audit

def main():
    require_formal_terminal();lock=(D/'critical_scope_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    old=D/'outside_native_eltwise_dev_01';oldreg=read(old/'registration.json');assert read(old/'input_seal.json')['passed']
    controls={a:old/'runs'/('eltwise_layer_'+a) for a in ['C2','Z2']}
    gate=read(controls['Z2']/'control_reproduction.json');assert gate['checks']['records']==False and all(v for k,v in gate['checks'].items() if k!='records')
    from run_outside_native import original
    x=original((controls['C2']/'stdout.log').read_text().splitlines());y=original((controls['Z2']/'stdout.log').read_text().splitlines());strip=lambda ls:[l for l in ls if not l.startswith('H3D_FINAL_OUTSIDE')]
    assert strip(x)==strip(y);zlines=(controls['Z2']/'stdout.log').read_text().splitlines();assert not any(l.startswith('H3D_FINAL_OUTSIDE ') or l.startswith('H3D_OUTSIDE_ASSIGN ') and 'kind=outside' in l for l in zlines)
    stage=D/'outside_native_stage_01';binding=read(stage/'binding.json');assert sha(stage/'bin/vpr')==binding['binary_sha256']
    out=D/'outside_native_eltwise_dev_02';out.mkdir(exist_ok=False);(out/'bin').mkdir();shutil.copy2(stage/'bin/vpr',out/'bin/vpr');shutil.copytree(stage/'src',out/'source');shutil.copy2(stage/'binding.json',out/'candidate_binding.json');shutil.copy2(__file__,out/'runner.py');shutil.copy2(OLD/'runtime_dependency_binding.json',out/'runtime_dependency_binding.json')
    reg=dict(protocol=oldreg['protocol'],native_arms=['N2','N1'],all_arms=['C2','Z2','N2','N1'],controls={a:str(p) for a,p in controls.items()},references=oldreg['references'],old_controls=oldreg['controls'],binary_sha256=binding['binary_sha256'],source_sha256=binding['source_sha256'],pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],host=socket.gethostname(),timeout=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,support_scripts_sha256={m.__file__:sha(m.__file__) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and m.__file__.endswith('.py') and str(ROOT) in m.__file__})
    write(out/'registration.json',reg);write(out/'control_reuse.json',dict(passed=True,C2=read(controls['C2']/'control_reproduction.json'),Z2=dict(passed=True,old_checks=gate['checks'],old_records_excluding_new_final_descriptors=True,new_final_state_rows=sum(l.startswith('H3D_FINAL_OUTSIDE_STATE ') for l in zlines),zero_outside_choices=True),qualification='Original comparator missed new H3D_FINAL_OUTSIDE_STATE diagnostic class. Only new descriptors removed from old-record comparison; all original records/costs/query/heap/prefix/guide/route exact and no eta0 outside selection. New final descriptors independently audited separately. Completed controls are not rerouted.'))
    io.BASE=out;io.ADDRESS_SPACE_BYTES=reg['memory_bytes']
    for p in [Path(__file__),old/'registration.json',old/'completion.json',old/'input_seal.json',stage/'binding.json',D/'outside_native_experiment_01.json',out/'control_reuse.json']:io.frozen_hash(p,sha(p))
    for p,h in reg['support_scripts_sha256'].items():io.frozen_hash(p,h)
    for p,v in read(old/'input_seal.json')['inputs'].items():io.frozen_hash(p,v['sha256'])
    for rd in controls.values():
        m=read(rd/'manifest.json');assert m['status']=='completed' and read(rd/'independent_audit.json')['audit']['passed'] and read(rd/'final_guide_audit.json')['passed']
        for p,v in m['shared_inputs'].items():io.frozen_hash(p,v['sha256'])
        for n,v in m['outputs'].items():io.frozen_hash(rd/n,v['sha256'])
        for n in ['manifest.json','independent_audit.json','final_guide_audit.json','h3d_final_guides.csv','control_reproduction.json']:io.frozen_hash(rd/n,sha(rd/n))
    receipts=[];pm=read(controls['C2']/'manifest.json');ctx=study.context('eltwise_layer','hybrid_o',11,100)
    for arm,count in [('N2',2),('N1',1)]:
        assert shutil.disk_usage(D).free>=reg['disk_reserve_bytes'];rd=out/'runs'/('eltwise_layer_'+arm);rd.mkdir(parents=True)
        for n in ['packed.net','placed.place']:shutil.copy2(controls['C2']/n,rd/n)
        cmd=list(pm['command']);cmd[0]=str(out/'bin/vpr')
        for opt,n in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/n)
        assert normalized_command(cmd)==normalized_command(pm['command']);cmd[cmd.index('--router_max_convergence_count')+1]=str(count)
        env=dict(pm['environment'],VPR_H3D_OUTSIDE_ETA='0.25')
        m=io.run(rd.name,cmd,environment=env,timeout=reg['timeout'],frozen=[cmd[0],cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],out/'registration.json'],private_inputs=[rd/'packed.net',rd/'placed.place'],tags=dict(circuit='eltwise_layer',arm=arm,max_convergences=count,phase='development',hypothesis='bounded_outside_DP_quality'))
        receipts.append(m);write(rd/'pair_check.json',dict(passed=all(sha(rd/n)==sha(controls['C2']/n) for n in ['packed.net','placed.place'])))
        if arm=='N1' and m['status']=='completed' and m['metrics'].get('native_full_check_passed'):
            other=out/'runs/eltwise_layer_N2';its=int(m['metrics']['iterations'])
            try:
                left=prefix((rd/'stdout.log').read_text().splitlines(),its);right=prefix((other/'stdout.log').read_text().splitlines(),its);norm=lambda ls:records([re.sub(r'\bseconds=\S+','seconds=<elapsed>',l) if l.startswith('H3D_RESIDUAL_') else l for l in ls]);checks=dict(records=norm(left)==norm(right),prefix=[l for l in left if l.startswith('H3D_PREFIX_')]==[l for l in right if l.startswith('H3D_PREFIX_')],numeric_rows=[l.split()[:1]+l.split()[2:] for l in left if ROW.match(l)]==[l.split()[:1]+l.split()[2:] for l in right if ROW.match(l)]);result=dict(passed=all(checks.values()),checks=checks,first_legal_iteration=its,reference=str(other))
            except ValueError as e:result=dict(passed=False,reason=str(e),reference=str(other))
            write(rd/'first_legal_prefix_reproduction.json',result)
    study.BASE=out;study.audit_batch(ctx,receipts,out/'independent_outside_quality_native_audit.json')
    for m in receipts:
        if m['status']=='completed' and m['metrics'].get('native_full_check_passed'):guide_audit(out/'runs'/m['name'])
    io.seal_inputs(out/'input_seal.json');write(out/'completion.json',dict(status='outside_native_quality_terminal_not_research_complete',gate_passed=True,disabled_gate_passed=True,control_reuse_passed=True,missing_arms=[a for a in reg['native_arms'] if a not in [m['tags']['arm'] for m in receipts]],original_control_attempt=str(old),new_native_route_calls=2,reused_completed_controls=2))
    print('quality pair terminal; no controls rerouted',flush=True)
if __name__=='__main__':main()
