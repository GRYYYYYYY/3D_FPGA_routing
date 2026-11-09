#!/usr/bin/env python3
"""Exercise the isolated study runner, separately from registered training."""
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[4]/'scripts'))
import flatland_benchmark as study
import flatland_experiment_io as io
from lazagna_common import sha256,utc,write_json


def main():
    base=study.BASE
    assert base==io.BASE and base.name=='serial_strict_reexecution_20261103'
    out=base/'integration_pilot_spmv_sb';out.mkdir(exist_ok=False)
    protocol=base/'benchmark_protocol.json'
    reg=dict(utc=utc(),circuit='spmv',family='sb',seed=11,width=100,
             flows=['p0','p1'],routers=['A0','R1','B2'],r1_variant='geometry',r1_config=0,
             stage='strict_integration_pilot',protocol_sha256=sha256(protocol),
             source_sha256=sha256(__file__),
             qualification='Diagnostic pilot, never included in training or heldout statistics.')
    write_json(out/'registration.json',reg)
    ctx=study.context('spmv','sb',11,100);results={}
    for flow in reg['flows']:
        placement=study.placement(ctx,reg['stage'],flow)
        if placement['status']!='completed':
            results[flow]=dict(status='placement_failed',receipt=placement['name']);continue
        routes=[]
        for router in reg['routers']:
            routes.append(study.route(ctx,reg['stage'],flow,router,
                'geometry' if router=='R1' else None,0 if router=='R1' else None))
        audit=study.audit_batch(ctx,routes,out/(flow+'_audit.json'))
        results[flow]=dict(status='completed',placement=placement['name'],
                           route_names=[x['name'] for x in routes],
                           route_statuses=[x['status'] for x in routes],
                           audit_legal=audit['legal_count'],audit_failed=audit['failed_count'])
    io.seal_inputs(out/'input_integrity.json')
    write_json(out/'summary.json',dict(utc=utc(),registration_sha256=sha256(out/'registration.json'),results=results))
    print(json.dumps(results),flush=True)


if __name__=='__main__':main()
