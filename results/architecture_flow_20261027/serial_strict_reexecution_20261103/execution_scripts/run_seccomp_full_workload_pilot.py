#!/usr/bin/env python3
"""Compare guarded P0/P1 and all route binaries against traced spmv fixtures.

The lock gate keeps this pilot out of the registered training/evaluation
window. Evidence is limited to this one circuit, architecture, and width.
"""
import fcntl
import hashlib
from pathlib import Path
import re
import traceback

import flatland_benchmark as study
import flatland_timing_io_candidate as timing
from lazagna_common import sha256,utc,write_json
from run_h3d_delay_study import route_body_hash
from validate_lazagna_vtr9_pilot import placements

study.io=timing


def packed_content_hash(path):
    """Normalize only the root's private output path; keep every other byte."""
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        declaration=f.readline();root=f.readline()
        assert declaration.startswith(b'<?xml') and root.startswith(b'<block name="')
        normalized,count=re.subn(rb'(?<=<block name=")[^"]*',b'<private-path>',root,count=1)
        assert count==1
        h.update(declaration);h.update(normalized)
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def main():
    base=study.BASE;locks=[]
    for name in ('serial_runner.lock','training_runner.lock','evaluation_runner.lock'):
        lock=(base/name).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(lock)
    output=base/'seccomp_full_workload_pilot'
    output.mkdir(exist_ok=False)
    proof_path=base/'seccomp_full_workload_validation.json'
    assert not proof_path.exists()
    stage='seccomp_workload_pilot';reference='strict_binding_pilot'
    sources=[Path(__file__),Path(timing.__file__),timing.GUARD,timing.GUARD_VALIDATION,
             base/'benchmark_protocol.json',base/'runtime_dependency_binding.json']
    registration=dict(utc=utc(),circuit='spmv',family='sb',seed=11,width=100,
        flows=['p0','p1'],routers=['A0','R1','B2'],r1_variant='geometry',r1_config=0,
        source_sha256={str(p):sha256(p) for p in sources},
        qualification='Diagnostic, not a serial timing sample; matching one case is not general equivalence.')
    write_json(output/'registration.json',registration)
    ctx=study.context('spmv','sb',11,100);results={};evidence=[output/'registration.json']
    try:
        for flow in registration['flows']:
            place=study.placement(ctx,stage,flow)
            assert place['status']=='completed',place
            current=base/'runs'/place['name']
            previous=base/'runs'/(study.prefix(ctx,reference,flow)+'_place')
            assert placements(current/'placed.place')==placements(previous/'placed.place')
            assert packed_content_hash(current/'packed.net')==packed_content_hash(previous/'packed.net')
            if flow=='p1':
                name='triton_evidence/triton_hypergraph.hgr.part.2'
                assert sha256(current/name)==sha256(previous/name)
                evidence.extend([current/name,previous/name])
            evidence.extend([current/'manifest.json',current/'placement_check.json',
                             previous/'manifest.json',previous/'placement_check.json'])
            routes=[];comparisons=[]
            for router in registration['routers']:
                variant='geometry' if router=='R1' else None
                config=0 if router=='R1' else None
                route=study.route(ctx,stage,flow,router,variant,config);routes.append(route)
                assert route['status']=='completed',route
                arm='geometry_c0' if router=='R1' else router.lower()
                old=base/'runs'/(study.prefix(ctx,reference,flow)+'_'+arm)
                new=base/'runs'/route['name'];old_manifest=study.read(old/'manifest.json')
                assert old_manifest['status']=='completed'
                assert route_body_hash(new/'routed.route')==route_body_hash(old/'routed.route')
                assert route['metrics']['critical_path_ns']==old_manifest['metrics']['critical_path_ns']
                comparisons.append(dict(router=router,route=route['name'],reference=old.name,
                                        cpd_ns=route['metrics']['critical_path_ns'],route_body_identical=True))
                evidence.extend([new/'manifest.json',new/'pair_check.json',new/'routed.route',
                                 old/'manifest.json',old/'routed.route'])
            audit_path=output/(flow+'_audit.json');audit=study.audit_batch(ctx,routes,audit_path)
            assert audit['legal_count']==3 and audit['failed_count']==0
            evidence.append(audit_path)
            evidence.extend(base/'runs'/r['name']/'independent_audit.json' for r in routes)
            results[flow]=dict(placement=place['name'],routes=comparisons,legal_routes=3)
        timing.seal_inputs(output/'input_integrity.json');evidence.append(output/'input_integrity.json')
        write_json(output/'summary.json',dict(utc=utc(),status='passed',results=results));evidence.append(output/'summary.json')
        proof=dict(utc=utc(),status='passed',covered_workloads=['A0','R1','B2','P1'],
            timing_runner_sha256=sha256(timing.__file__),guard_sha256=sha256(timing.GUARD),
            evidence_sha256={str(p):sha256(p) for p in [*sources,*evidence]},
            qualification='One spmv/SB/W100 case; guard changes syscall availability, sampling can miss transient processes, and seccomp/supervision add timing overhead. Wider designs and all workloads are not proven equivalent.')
        write_json(proof_path,proof)
        print('seccomp four-workload diagnostic passed; proof written',flush=True)
    except Exception as error:
        write_json(output/'failure.json',dict(utc=utc(),status='failed',error=str(error),
            traceback=traceback.format_exc(),partial_results=results))
        raise


if __name__=='__main__':main()
