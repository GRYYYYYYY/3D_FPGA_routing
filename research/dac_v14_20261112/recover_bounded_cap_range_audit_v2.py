#!/usr/bin/env python3
"""Recover packaging only; no native route, no invented prelaunch pair receipt."""
import fcntl,sys,resource,signal
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
ROOT=D.parents[1];OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from audit_final_guides import audit as guide_audit

def main():
    resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));signal.alarm(1800)
    lock=(D/'critical_scope_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    b=D/'bounded_cap_range_eltwise_dev_02';r=read(b/'registration.json');expected={};proof={}
    def bind(p,h,origin,ident=None):
        p=str(Path(p).resolve());assert p not in expected or expected[p]==h,('conflicting_digest',p)
        expected[p]=h;proof.setdefault(p,[]).append(dict(origin=origin,stat_identity=ident))
    prior=[D/n/'input_seal.json' for n in ['bounded_cap_eltwise_dev_01','bounded_critical_count1_eltwise_dev_01','bounded_cap_count1_eltwise_dev_01','native_reconvergence_eltwise_dev_01','bounded_critical_eltwise_dev_01','candidate_path_delay_eltwise_dev_01']]
    catalog={}
    for p in prior:
        q=read(p);assert q['passed']
        for path,v in q['inputs'].items():catalog.setdefault(path,[]).append((v['sha256'],str(p)))
    for p in [D/'bounded_cap_eltwise_dev_01/bounded_cap_analysis.json',D/'guide_policy_development_01.json']:
        for path,h in read(p)['source_sha256'].items():catalog.setdefault(path,[]).append((h,str(p)))
    def prior_bind(p):
        p=str(p.resolve());items=catalog.get(p,[]);assert items,('no_original_binding',p)
        digests={h for h,o in items};assert len(digests)==1,('prior_conflict',p)
        bind(p,items[0][0],items[0][1])
    for p,h in r['support_scripts_sha256'].items():bind(p,h,'original_registration.support_scripts_sha256')
    bind(b/'bin/vpr',r['binary_sha256'],'original_registration.binary_sha256')
    bind(b/'runner.py',r['runner_sha256'],'original_registration.runner_sha256')
    for p,h in r['source_sha256'].items():bind(b/'source'/p,h,'original_registration.source_sha256')
    binding=read(b/'candidate_binding.json');assert binding['binary_sha256']==r['binary_sha256'] and binding['source_sha256']==r['source_sha256']
    assert read(D/'bounded_cap_range_experiment_01.json')==r['protocol']
    paths={Path(p) for group in list(r['references'].values())+list(r['controls'].values()) for p in group.values()}|{Path(p) for p in r['parent_runs'].values()}
    receipts=[]
    for rd in sorted(paths):
        m=read(rd/'manifest.json');assert m['status']=='completed' and read(rd/'independent_audit.json')['audit']['passed']
        for p,v in m['shared_inputs'].items():bind(p,v['sha256'],str(rd/'manifest.json')+'.shared_inputs',v['stat_identity'])
        for n,v in m['outputs'].items():bind(rd/n,v['sha256'],str(rd/'manifest.json')+'.outputs')
        for n in ['manifest.json','independent_audit.json','final_guide_audit.json','h3d_final_guides.csv']:
            if (rd/n).exists():
                if n=='h3d_final_guides.csv' and str((rd/n).resolve()) not in catalog:
                    bind(rd/n,read(rd/'final_guide_audit.json')['trace_sha256'],str(rd/'final_guide_audit.json')+'.trace_sha256 (audit itself prior-bound)')
                else:prior_bind(rd/n)
    for a in r['arms']:
        rd=b/'runs'/('eltwise_layer_'+a);m=read(rd/'manifest.json');assert m['status']=='completed' and m['metrics']['native_full_check_passed'];receipts.append(m)
        for p,v in m['shared_inputs'].items():bind(p,v['sha256'],str(rd/'manifest.json')+'.shared_inputs',v['stat_identity'])
        for p,h in m['private_input_sha256'].items():bind(p,h,str(rd/'manifest.json')+'.private_input_sha256')
        for n,v in m['outputs'].items():bind(rd/n,v['sha256'],str(rd/'manifest.json')+'.outputs')
    # Original process memory is unavailable. All expected digests above derive from saved runtime/pre-existing receipts.
    checks={p:dict(expected_sha256=h,actual_sha256=sha(p),provenance=proof[p]) for p,h in expected.items()}
    for p,v in checks.items():assert v['expected_sha256']==v['actual_sha256'],('digest_mismatch',p)
    current=b/'recovery_binding_v2.json';assert not current.exists()
    write(current,dict(passed=True,native_route_calls=0,checks=checks,script_sha256=sha(__file__),qualification='Postrun recovery, using original persisted bindings; lost supervisor hash cache is not reconstructed by assumption. Original manifests record per-process input stat checks; this recovery independently rechecks saved digests. Protocol compared canonically to originally runtime-bound registration.'))
    write(b/'postrun_failure_v2.json',dict(stage='post_native_packaging',reason='pair_check.json omitted by original runner; audit_batch FileNotFoundError after four completed native roles',completed_native_routes=4,recovery_native_route_calls=0,original_runner=str(b/'runner.py')))
    for m in receipts:
        rd=b/'runs'/m['name'];parent=Path(r['parent_runs'][str(m['tags']['max_convergences'])]);rows={}
        for n in ['packed.net','placed.place']:
            p=rd/n;digest=sha(p);rows[n]=dict(actual=digest,runtime_private=m['private_input_sha256'][str(p)],frozen_parent=sha(parent/n))
            assert len(set(rows[n].values()))==1
        if (rd/'pair_check.json').exists():
            existing=read(rd/'pair_check.json');assert existing['passed'] and existing['checks']==rows
        else:write(rd/'pair_check.json',dict(passed=True,scope='postrun digest verification against original private-input snapshots and preregistered frozen parent; not a prelaunch receipt',checks=rows))
    for p,h in expected.items():io.frozen_hash(p,h)
    io.frozen_hash(current,sha(current));io.frozen_hash(__file__,sha(__file__))
    ctx=study.context('eltwise_layer','hybrid_o',11,100);study.BASE=b
    study.audit_batch(ctx,receipts,b/'independent_cap_range_native_audit.json')
    for m in receipts:guide_audit(b/'runs'/m['name'])
    io.seal_inputs(b/'input_seal.json')
    seal=read(b/'input_seal.json');seal['qualification']='Recovered postrun seal: expected native inputs/outputs and reused baselines checked against original persisted bindings; stat stability here covers recovery interval only.';seal['recovery_binding']=str(current);write(b/'input_seal.json',seal)
    prefix={a:read(b/'runs'/('eltwise_layer_'+a)/'first_legal_prefix_reproduction.json') for a in ['L1','H1']};assert all(v['passed'] for v in prefix.values())
    write(b/'completion.json',dict(status='cap_range_terminal_not_research_complete',gate_passed=True,disabled_gate_passed=True,control_reuse_passed=read(b/'control_reuse.json')['passed'],firstlegal_checks=prefix,missing_arms=[],recovery_native_route_calls=0,packaging_recovery=str(current)))
    print('RECOVERY PASSED; native_route_calls=0',flush=True)
if __name__=='__main__':main()
