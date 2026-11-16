"""Inventory interrupted actors, then audit existing bytes in the serial slot.

Never launches a native process or changes an original receipt. A successful
audit qualifies an existing stage for a later explicit recovery adapter; it
does not create a worker completion, accept a candidate, or complete a flow.
"""
import argparse
import os
import re
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

ROOT = D/'interrupted_stage_reconciliation_01'
BASE = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces')
CASES = [
    ('clstm_input_contract_pair_02','native','timing/round_000/proposal_01/transaction','current_group',2),
    ('clstm_input_contract_pair_02','domain','resource_flow/repair/round_001/candidate_00','reuse_on',1),
    ('reduction_pair_01','native','resource_flow/repair/round_010/candidate_00','reuse_off',10),
    ('reduction_pair_01','domain','resource_flow/repair/round_004/candidate_00','reuse_on',4),
]

def tail(path, size=16384):
    with Path(path).open('rb') as f:
        f.seek(max(0, f.seek(0,2)-size)); return f.read().decode(errors='replace')

def snapshot():
    rows=[]; bound={}
    for pair,arm,relative,role,count in CASES:
        flow=BASE/pair/arm/'flow';tx=flow/relative;worker=tx/role
        repair=flow/'resource_flow/repair';current=read(repair/'current_state.json')
        assert current['accepted_steps']==count
        paths=[repair/'current_state.json',repair/'steps.json',repair/'attempts.json',repair/'registration.json',tx/'registration.json',worker/'registration.json',worker/'runs/state/manifest.json']
        audit=tx/(role+'_audit/analysis.json');domain=tx/(role+'_domain_audit.json');evaluation=tx/(role+'_evaluation')
        for p in [worker/'completion.json',worker/'input_seal.json',audit,domain,tx/'process_costs.json']:
            if p.exists():paths.append(p)
        # Metadata only: no large route, graph, vector or trace read/hash here.
        for p in paths:
            assert p.stat().st_size<4*1024*1024,('Unexpected large metadata',str(p))
            bound[str(p)]=sha(p)
        rows.append(dict(pair=pair,arm=arm,flow=str(flow),transaction=str(tx),role=role,
            accepted_resource_steps=count,current_resource_state=current['state'],
            resource_closed=(repair/'completion.json').exists() and read(repair/'completion.json')['passed'],
            worker_completion_present=(worker/'completion.json').exists(),
            worker_manifest_status=read(worker/'runs/state/manifest.json')['status'],
            candidate_audit_present=audit.exists(),domain_audit_present=domain.exists(),
            candidate_STA_directory_present=evaluation.exists(),
            candidate_STA_payload_present=evaluation.exists() and any(evaluation.iterdir()),
            raw_native_terminal_line=tail(worker/'runs/state/joint_native.log',4096).splitlines()[-1],
            gnu_exit_status=re.findall(r'Exit status:\s*(\d+)',tail(worker/'runs/state/time.txt')),
            new_native_calls=0,full_method_complete=False,adoption_authorized=False))
    return dict(status='metadata_inventory_only',passed=True,rows=rows,source_sha256=bound,
        new_independent_inputs=0,new_native_calls=0,
        qualification='Pending serial byte/STA audit. Existing empty STA directories do not prove a completed evaluation. No old running manifest is rewritten; no raw log alone authorizes adoption.')

def audit_one(row, evidence):
    from recovery_prefix_v1 import live_identity
    from run_native_scope_policy_v4 import native_config
    from endpoint_timing_policy_streaming_v2 import load
    from observation_timing_identity_v2 import check
    from state_resource_assurance import require_publication_proof
    # Parser is the exact frozen parser, not an approximation of stdout success.
    import importlib.util
    parser=BASE.parent/'confirmation_releases/current_sta_cp1r2/runtime/runtime_metrics.py'
    evidence.bind(parser)
    spec=importlib.util.spec_from_file_location('interrupted_frozen_metrics',parser)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    tx=Path(row['transaction']);role_name=row['role'];role=read(tx/'registration.json')['roles'][role_name]
    worker=tx/role_name;run=worker/'runs/state';m=read(run/'manifest.json');reg=read(worker/'registration.json')
    assert not live_identity(reg['pid'],reg['start_ticks']),'Original worker live'
    actor=Path(row['flow'])/'resource_flow/repair';areg=read(actor/'registration.json')
    assert not live_identity(areg['pid'],areg['start_ticks']),'Original actor live'
    for path in tx.glob('*supervision*.json'):
        evidence.bind(path);supervision=read(path)
        for key in ['supervisor','child']:
            identity=supervision.get(key)
            if identity and 'start_ticks' in identity:
                assert not live_identity(identity['pid'],identity['start_ticks']),('Original stage live',str(path),key)
    evidence.verify(reg['source_sha256']);evidence.verify(role['source_sha256'])
    for p,item in m['shared_inputs'].items():evidence.bind(p,item['sha256'])
    evidence.verify(m['private_input_sha256'])
    source=Path(role['source']);source_manifest=read(source/'manifest.json')
    assert native_config(run)==native_config(source),'Source command changed'
    for name in ['packed.net','placed.place','routed.route']:
        assert evidence.bind(run/name)==evidence.bind(source/name),name
    # A legal source needs its own physical proof; a successful native command
    # is not a substitute for candidate route assurance.
    require_publication_proof(Path(role['state']))
    evidence.bind(source/'independent_audit.json')
    env=m['environment'];request=Path(role['request']);evidence.bind(request)
    assert evidence.bind(env['VPR_JOINT_NATIVE_REQUEST'])==evidence.bind(request)
    assert env['VPR_JOINT_NATIVE_OBJECTIVE']==role['objective']
    for key,field in [('VPR_JOINT_NATIVE_SEED_ORDER','seed_order'),('VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE','domain_failure_release')]:
        if field in role:
            expected=('1' if role[field] else '0') if field=='domain_failure_release' else role[field]
            assert env[key]==expected,key
    if role.get('crossing_reuse_enabled'):
        assert evidence.bind(env['VPR_JOINT_NATIVE_REUSE_CROSSINGS'])==evidence.bind(role['crossing_domain'])
    else:assert env['VPR_JOINT_NATIVE_REUSE_CROSSINGS']==''
    evidence.bind(run/'stdout.log');metrics=mod.parse_metrics((run/'stdout.log').read_text(errors='replace'))
    assert metrics['native_full_check_passed']
    assert 'VPR succeeded' in tail(run/'stdout.log',65536)
    evidence.bind(run/'time.txt');assert re.findall(r'Exit status:\s*(\d+)',(run/'time.txt').read_text())==['0']
    evidence.bind(run/'joint_native.log');terminal=tail(run/'joint_native.log',4096).splitlines()[-1].split()
    assert len(terminal)==6 and terminal[0]=='COMPLETE' and terminal[1]=='1' and terminal[-1]=='occupancy_restored',terminal
    lines=request.read_text().splitlines();net_count=int(lines[0]);requests=[x.split() for x in lines[1:1+net_count]]
    assert len(requests)==net_count and all(len(x)==int(x[1])+2 for x in requests)
    query_count=sum(int(x[1]) for x in requests)
    assert int(terminal[2])==int(terminal[3])==query_count
    vector=Path(role['state'])/'endpoint_vector.json';trace=run/'native_sta_frontier.jsonl'
    evidence.bind(vector);evidence.bind(trace)
    identity=check(metrics['critical_path_ns'],source_manifest['metrics']['critical_path_ns'],read(vector),load(trace))
    assert identity['passed'],identity
    done=worker/'completion.json'
    if done.exists():
        completion=read(done)
        assert completion['observation_only'] and completion['process_status']=='completed'
        assert all(v for k,v in completion['checks'].items() if k!='CPD_matches_original')
        assert m['status']=='completed' and m['returncode']==0
        evidence.bind(worker/'input_seal.json');assert read(worker/'input_seal.json')['passed']
    else:
        assert m['status']=='running','Unexpected unsealed terminal state'
        assert not (worker/'input_seal.json').exists()
    stages={'native_source_control':dict(verified_existing_execution=True,query_count=query_count,
        exact_observation=identity,receipt_kind='sealed_worker' if done.exists() else 'raw_success_unsealed_manifest',
        original_manifest_unchanged=True,new_native_calls=0)}
    for name,path in [('candidate_physical_audit',tx/(role_name+'_audit/analysis.json')),('domain_audit',tx/(role_name+'_domain_audit.json'))]:
        if path.exists():
            evidence.bind(path);result=read(path);assert result['passed'],str(path)
            if result.get('candidate_route'):evidence.bind(result['candidate_route'])
            stages[name]=dict(existing_passed_receipt=True,receipt=str(path))
        else:stages[name]=dict(existing_passed_receipt=False)
    evaluation=tx/(role_name+'_evaluation')
    assert not evaluation.exists() or not any(evaluation.iterdir()),'Partial candidate STA requires separate reconciliation'
    # A dead process and empty directory establish absence of persisted STA
    # payload, not a claim that no Python prelaunch work was ever charged.
    stages['candidate_STA']=dict(completed=False,persisted_payload_present=False,
        original_prelaunch_or_failure_cost_retained=True)
    return dict(passed=True,pair=row['pair'],arm=row['arm'],stages=stages,
        source_state=role['state'],fixed_original_budget=role['original_budget'],
        full_method_complete=False,adoption_implemented=False,new_native_calls=0,
        qualification='Existing stage evidence only. Recovery adapter must retain original root, all accepted/rejected legal states and selection/acceptance rules; suffix cost stays separate. No new candidate quality or independent evidence.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--inventory',action='store_true');a=p.parse_args()
    if a.inventory:
        ROOT.mkdir(exist_ok=False);write(ROOT/'inventory.json',snapshot());return
    assert os.environ.get('H3D_INTERRUPTED_AUDIT_SERIAL_OWNER'),'Serial queue required'
    from recovery_prefix_v1 import Evidence
    inventory=read(ROOT/'inventory.json');evidence=Evidence();evidence.verify(inventory['source_sha256']);rows=[]
    reconciliation=D/'execution_reconciliation_20261116_01/completion.json'
    evidence.bind(reconciliation);assert read(reconciliation)['passed']
    for row in inventory['rows']:
        try:result=audit_one(row,evidence)
        except Exception as e:result=dict(passed=False,pair=row['pair'],arm=row['arm'],error=repr(e),adoption_implemented=False,new_native_calls=0)
        rows.append(result);write(ROOT/(row['pair']+'_'+row['arm']+'_audit.json'),result)
    evidence.unchanged()
    write(ROOT/'completion.json',dict(passed=all(x['passed'] for x in rows),rows=rows,source_sha256=evidence.bound,
        new_native_calls=0,new_independent_inputs=0,original_receipts_changed=False,full_method_complete=False,adoption_implemented=False))

if __name__=='__main__':main()
