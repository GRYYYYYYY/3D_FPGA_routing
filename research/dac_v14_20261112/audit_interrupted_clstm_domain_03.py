"""Read-only rerun of existing stage gates with exact empty-receipt evidence.

Original audit, supervision and recovery results remain untouched. This may
verify an existing native stage; it never supplies candidate STA or recovery.
"""
import argparse
import fcntl
import resource
import time
import traceback
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from recovery_prefix_v1 import Evidence, live_identity
from empty_interrupted_supervision_identity_v1 import corroborate

ROOT=D/'CLSTM_domain_manifest_audit_03'


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--execute',action='store_true',required=True)
    p.add_argument('--serial-lock-fd',type=int)
    a=p.parse_args()
    assert not (ROOT/'audit.json').exists(), 'Preserve every audit attempt'
    lock=None
    if a.serial_lock_fd is None:
        lock=(D/'critical_scope_runner.lock').open('r');fd=lock.fileno()
    else:
        fd=a.serial_lock_fd
        assert Path('/proc/self/fd',str(fd)).resolve()==(D/'critical_scope_runner.lock').resolve()
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    start=time.monotonic();e=Evidence();plan=read(ROOT/'registration.json')
    e.verify(plan['source_sha256'])
    assert read(D/'vertical_cost_admission_reconciliation_01/execution/completion.json')['status']=='readonly_reconciliation_terminal'
    import audit_interrupted_stages_01 as original
    inventory=read(D/'interrupted_stage_reconciliation_01/inventory.json')
    row=next(r for r in inventory['rows'] if r['pair']=='clstm_input_contract_pair_02' and r['arm']=='domain')
    assert row==plan['original_inventory_row']
    tx=Path(row['transaction']);bad=tx/'reuse_on_native_supervision.json'
    active_path=tx/'reuse_on_native_supervision.active.json'
    strict_read=original.read;corroborated=[]

    def independent_read(path):
        if Path(path).resolve()!=bad.resolve():
            return strict_read(path)
        assert Path(path).read_bytes()==b''
        active=e_document(active_path)
        worker=e_document(tx/'reuse_on/registration.json')
        done=e_document(tx/'reuse_on/completion.json')
        seal=e_document(tx/'reuse_on/input_seal.json')
        actor=e_document(Path(row['flow'])/'resource_flow/repair/registration.json')
        identities={**{k:not live_identity(active[k]['pid'],active[k]['start_ticks'])
                       for k in ['supervisor','child']},
                    'worker':not live_identity(worker['pid'],worker['start_ticks']),
                    'actor':not live_identity(actor['pid'],actor['start_ticks'])}
        proof=corroborate(str(bad),plan['exact_empty_path'],e.bind(bad),
                         plan['source_sha256'][str(bad)],active,worker,done,seal,identities)
        corroborated.append(proof)
        # Only the identities from the original active record are returned to
        # the unchanged old dead-identity loop. No exit/completion is invented.
        return {k:active[k] for k in ['supervisor','child']}

    def e_document(path):
        e.bind(path);return strict_read(path)

    result=None
    try:
        original.read=independent_read
        e.bind(tx/'reuse_on/runs/state/manifest.json')
        result=original.audit_one(row,e)
        assert len(corroborated)==1
        # Retain the existing stage checks and strengthen ordered-request proof.
        from cp1r3_raw_admission_v1 import parse_request, parse_native
        role=e_document(tx/'registration.json')['roles'][row['role']]
        e.bind(role['request'])
        expected=parse_request(Path(role['request']).read_text(),role)
        log=tx/'reuse_on/runs/state/joint_native.log';e.bind(log)
        native=parse_native(log.read_text().splitlines(),expected)
        assert native['success'] and native['requested']==23
        result['stages']['exact_complete_ordered_native_request']=native
        result['supervision_corroboration']=corroborated[0]
        assert result['stages']['candidate_STA']['completed'] is False
        result.update(adoption_implemented=False,complete_candidate_admitted=False,
                      full_method_complete=False,original_failure_rewritten=False)
        e.unchanged()
    except BaseException:
        result=dict(passed=False,error=traceback.format_exc(),partial_stage=result,
                    adoption_implemented=False,original_failure_rewritten=False)
    finally:
        original.read=strict_read
    result.update(source_sha256=e.bound,complete_readonly_seconds=time.monotonic()-start,
                  process_max_RSS_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  new_native_or_STA_calls=0,
                  qualification='Existing native source/control stage only; candidate physical/STA and full recovery require separately registered execution. Original empty receipt, failed audit, failed admission and costs are unchanged.')
    write(ROOT/'audit.json',result)
    assert result['passed'],result.get('error')


if __name__=='__main__':
    main()
