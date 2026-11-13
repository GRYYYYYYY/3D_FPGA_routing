#!/usr/bin/env python3
"""Same-binary count1 reuse and uniform native count2 development control."""
from pathlib import Path
import argparse
import fcntl
import os
import shutil
import socket
import sys
from retained_prefix_workflow import D, read, write, sha, normalized_command, require_formal_terminal

ROOT = D.parents[1]
OLD = ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0] = [str(OLD/'execution_scripts'), str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from audit_final_guides import audit as guide_audit
from routing_log_metrics import ROW


def iteration_rows(path):
    # Only the elapsed-time column may differ before first convergence.
    return [line.split()[:1] + line.split()[2:] for line in path.read_text().splitlines() if ROW.match(line)]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--circuit',choices=['spmv','softmax','bnn'],required=True);args=ap.parse_args()
    require_formal_terminal()
    lock=(D/'critical_scope_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert shutil.disk_usage(D).free>=80*1024**3
    refs={a:Path(p) for a,p in read(D/'native_reconvergence_extension_01.json')['cases'][args.circuit]['references'].items()}
    prior=read(refs['A0']/'manifest.json');ctx=study.context(args.circuit,'hybrid_o',11,100)
    out=D/args.out;out.mkdir(exist_ok=False)
    shutil.copy2(__file__,out/'runner.py')
    shutil.copy2(OLD/'runtime_dependency_binding.json',out/'runtime_dependency_binding.json')
    reg=dict(circuit=args.circuit,protocol=read(D/'native_reconvergence_extension_01.json'),arms=['A0','R1','Tf','A1'],
        references={a:str(p) for a,p in refs.items()},pid=os.getpid(),host=socket.gethostname(),
        start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
        runner_sha256=sha(__file__),timeout=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,
        support_scripts_sha256={m.__file__:sha(m.__file__) for m in list(sys.modules.values())
            if getattr(m,'__file__',None) and m.__file__.endswith('.py') and str(ROOT) in m.__file__})
    write(out/'registration.json',reg);io.BASE=out;io.ADDRESS_SPACE_BYTES=reg['memory_bytes']
    for p in [Path(__file__),D/'native_reconvergence_extension_01.json',D/'scope_six_circuit_summary.json']:
        io.frozen_hash(p,sha(p))
    for p,h in reg['support_scripts_sha256'].items():io.frozen_hash(p,h)
    # Admit every reused control before any native treatment starts.
    for arm,rd in refs.items():
        m=read(rd/'manifest.json');assert m['status']=='completed' and m['metrics']['native_full_check_passed']
        assert read(rd/'independent_audit.json')['audit']['passed']
        assert normalized_command(m['command'])==normalized_command(prior['command'])
        assert '--router_max_convergence_count' not in m['command']
        log=(rd/'stdout.log').read_text();assert 'router_opts.max_convergence_count: 1' in log
        assert 'router_opts.reconvergence_cpd_threshold: 0.990000' in log
        for n in ['packed.net','placed.place']:assert sha(rd/n)==sha(refs['A0']/n)
        for p,h in m['shared_inputs'].items():io.frozen_hash(p,h['sha256'])
        for n,h in m['outputs'].items():io.frozen_hash(rd/n,h['sha256'])
        for n in ['manifest.json','independent_audit.json']:
            io.frozen_hash(rd/n,sha(rd/n))
        if (rd/'final_guide_audit.json').exists():
            assert read(rd/'final_guide_audit.json')['passed']
            io.frozen_hash(rd/'final_guide_audit.json',sha(rd/'final_guide_audit.json'))
        binary=Path(m['command'][0]);io.frozen_hash(binary,sha(binary))
    write(out/'control_reuse.json',dict(passed=True,new_control_route_calls=0,controls=reg['references']))
    receipts=[]
    for arm in reg['arms']:
        assert shutil.disk_usage(D).free>=reg['disk_reserve_bytes']
        src=refs[arm];m=read(src/'manifest.json');rd=out/'runs'/f'{args.circuit}_{arm}';rd.mkdir(parents=True)
        (out/'bin'/arm).mkdir(parents=True);binary=out/'bin'/arm/'vpr';shutil.copy2(m['command'][0],binary)
        assert sha(binary)==sha(m['command'][0])
        for n in ['packed.net','placed.place']:shutil.copy2(src/n,rd/n)
        cmd=list(m['command']);cmd[0]=str(binary)
        for opt,n in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/n)
        cmd+=['--router_max_convergence_count','2']
        receipt=io.run(rd.name,cmd,environment=m['environment'],timeout=reg['timeout'],
            frozen=[binary,cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],out/'registration.json'],
            private_inputs=[rd/'packed.net',rd/'placed.place'],tags=dict(circuit=args.circuit,arm=arm,phase='development',hypothesis='native_reconvergence'))
        write(rd/'pair_check.json',dict(passed=all(sha(rd/n)==sha(src/n) for n in ['packed.net','placed.place']),source=str(src)))
        old=iteration_rows(src/'stdout.log');new=iteration_rows(rd/'stdout.log')
        write(rd/'first_convergence_prefix.json',dict(passed=len(new)>=len(old) and new[:len(old)]==old,
            reference=str(src),control_iterations=len(old),treatment_iterations=len(new),
            qualification='Printed native iteration fields excluding elapsed time; not full intermediate route equivalence.'))
        receipts.append(receipt)
    study.BASE=out;study.audit_batch(ctx,receipts,out/'independent_reconvergence_audit.json')
    for m in receipts:
        rd=out/'runs'/m['name']
        if m['status']=='completed' and m['metrics'].get('native_full_check_passed') and (rd/'h3d_final_guides.csv').exists():guide_audit(rd)
    io.seal_inputs(out/'input_seal.json')
    write(out/'completion.json',dict(status='batch_terminal_not_research_complete',declared_arms=reg['arms'],
        missing_arms=[a for a in reg['arms'] if a not in [m['tags']['arm'] for m in receipts]],
        prefix_gates={m['tags']['arm']:read(out/'runs'/m['name']/'first_convergence_prefix.json')['passed'] for m in receipts}))


if __name__=='__main__':main()
