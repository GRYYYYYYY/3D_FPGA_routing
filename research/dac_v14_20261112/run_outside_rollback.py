#!/usr/bin/env python3
import fcntl,os,shutil,socket,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,require_formal_terminal
ROOT=D.parents[1];OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103';sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from audit_final_guides import audit as guide_audit

def main():
    require_formal_terminal();lock=(D/'critical_scope_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    parent=D/'outside_native_eltwise_dev_02/runs/eltwise_layer_N2';pm=read(parent/'manifest.json');assert read(parent.parent.parent/'input_seal.json')['passed'] and pm['status']=='completed'
    b=D/'outside_rollback_dev_01';b.mkdir(exist_ok=False);(b/'bin').mkdir();shutil.copy2(pm['command'][0],b/'bin/vpr');shutil.copy2(__file__,b/'runner.py');shutil.copy2(OLD/'runtime_dependency_binding.json',b/'runtime_dependency_binding.json')
    reg=dict(status='registered_before_execution',question='Does an actual forced transaction rejection remove newly introduced outside metadata or restore an existing changed outside vector, with the prior complete native route restored?',arms=['Xnew','Xret'],parent=str(parent),cases=dict(Xnew='new',Xret='retained'),binary_sha256=sha(b/'bin/vpr'),pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],host=socket.gethostname(),timeout=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,qualification='Test-only first actual differing-metadata opportunity with prior complete native tree; not quality samples or a route-effect-equivalence experiment. Zero opportunity stays unexercised. Immutable physical cache remains reusable and is revalidated against restored tree.',support_scripts_sha256={m.__file__:sha(m.__file__) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and m.__file__.endswith('.py') and str(ROOT) in m.__file__})
    write(b/'registration.json',reg);io.BASE=b;io.ADDRESS_SPACE_BYTES=reg['memory_bytes'];ctx=study.context('eltwise_layer','hybrid_o',11,100)
    for p in [Path(__file__),parent/'manifest.json',parent.parent.parent/'input_seal.json',D/'outside_native_stage_01/binding.json']:io.frozen_hash(p,sha(p))
    for p,v in pm['shared_inputs'].items():io.frozen_hash(p,v['sha256'])
    for p,h in reg['support_scripts_sha256'].items():io.frozen_hash(p,h)
    receipts=[]
    for arm,mode in reg['cases'].items():
        assert shutil.disk_usage(D).free>=reg['disk_reserve_bytes'];rd=b/'runs'/('eltwise_layer_'+arm);rd.mkdir(parents=True)
        for n in ['packed.net','placed.place']:shutil.copy2(parent/n,rd/n)
        cmd=list(pm['command']);cmd[0]=str(b/'bin/vpr')
        for opt,n in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/n)
        env=dict(pm['environment'],VPR_H3D_TEST_OUTSIDE_ROLLBACK=mode)
        m=io.run(rd.name,cmd,environment=env,timeout=reg['timeout'],frozen=[cmd[0],cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],b/'registration.json'],private_inputs=[rd/'packed.net',rd/'placed.place'],tags=dict(circuit='eltwise_layer',arm=arm,max_convergences=2,phase='transaction_diagnostic',hypothesis='actual_changed_outside_transaction_restore'))
        receipts.append(m);write(rd/'pair_check.json',dict(passed=all(sha(rd/n)==sha(parent/n) for n in ['packed.net','placed.place'])))
    study.BASE=b;study.audit_batch(ctx,receipts,b/'independent_outside_rollback_native_audit.json')
    for m in receipts:
        if m['status']=='completed' and m['metrics'].get('native_full_check_passed'):guide_audit(b/'runs'/m['name'])
    io.seal_inputs(b/'input_seal.json');write(b/'completion.json',dict(status='rollback_diagnostic_terminal_not_research_complete',gate_passed=True,disabled_gate_passed=True,missing_arms=[a for a in reg['arms'] if a not in [m['tags']['arm'] for m in receipts]]))
    print('rollback native cases terminal',flush=True)
if __name__=='__main__':main()
