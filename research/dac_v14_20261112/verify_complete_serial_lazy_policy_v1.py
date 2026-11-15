"""Verify actual per-role seed/domain controls on complete single-binary flows."""
import argparse
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir

p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
root=a.root.resolve();structural=read(root/'completion.json')
assert structural['passed'] and structural['complete_configuration_verified']
assert all(sha(p)==h for p,h in structural['source_sha256'].items())
config=read(root/'config.json');flow=read(root/'flow/completion.json');actor=root/'flow/repair'
assert sha(root/'config.json')==sha(flow['config'])
assert config['seed_order'] in ['native','rr_id','delay_rr_id']
assert config['domain_feedback']==(config['domain_mode']=='paired')
reg=read(actor/'registration.json')
assert reg['seed_order']==config['seed_order'] and reg['domain_feedback']==config['domain_feedback']
assert reg['local_probe']==dict(accepted_steps=0,rank_windows=3)
binary=read(D/'native_resource_census_stage_01/binding.json')['binary_sha256']
files=[Path(__file__).resolve(),root/'completion.json',root/'config.json',root/'flow/completion.json',actor/'registration.json']
counts=dict(optional_native_skipped=0,native_transactions=0,queries=0,search_attempts=0,domain_releases=0)
for attempt in read(actor/'attempts.json'):
    tx=Path(attempt['transaction']);roles=read(tx/'registration.json')['roles'];progress=read(tx/'progress.json')
    files += [tx/'registration.json',tx/'progress.json']
    for name,role in roles.items():
        assert role['seed_order']==config['seed_order']
        assert role['domain_failure_release']==(role['crossing_reuse_enabled'] and config['domain_feedback'])
        if progress[name]['status']=='not_executed_domain_candidate_accepted':
            assert name=='reuse_off' and progress['reuse_on']['status']=='legal_evaluated' and progress['reuse_on']['policies']['resources_under_timing']['accepted']
            assert not (tx/name).exists() and progress[name]['acceptance_evaluated'] is False
            counts['optional_native_skipped']+=1;continue
        manifest=read(run_dir(tx/name)/'manifest.json');env=manifest['environment']
        assert sha(manifest['command'][0])==binary
        assert env['VPR_JOINT_NATIVE_SEED_ORDER']==config['seed_order']
        assert env['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE']==('1' if role['domain_failure_release'] else '0')
        audit=read(tx/(name+'_audit/analysis.json'));assert audit['passed']
        counts['native_transactions']+=1;counts['queries']+=len(audit['queries']);counts['search_attempts']+=len(audit['attempts'])
        if role['crossing_reuse_enabled']:
            domain=read(tx/(name+'_domain_audit.json'));assert domain['passed']
            counts['domain_releases']+=len(domain.get('released_queries',[]));files.append(tx/(name+'_domain_audit.json'))
        result=progress[name];assert result['status']=='legal_evaluated' and not result['native_reused']
        state=Path(result['evaluation']);m=read(run_dir(state)/'manifest.json');assert sha(m['command'][0])==binary
        files += [run_dir(tx/name)/'manifest.json',tx/(name+'_audit/analysis.json'),run_dir(state)/'manifest.json']
initial=Path(flow['initial_state']);assert sha(read(run_dir(initial)/'manifest.json')['command'][0])==binary
payload=dict(structural)
payload.update(seed_order=config['seed_order'],domain_mode=config['domain_mode'],domain_failure_release=config['domain_feedback'],
    one_binary_sha256=binary,actual_native_work=counts,structural_verification=str(root/'completion.json'),
    source_sha256={str(f):sha(f) for f in files},
    qualification='Actual complete current-binary serial configuration. Explicit seed and per-role domain-failure-release controls verified from registered roles and executed native environments; initial routing, native repairs and all candidate STA use the same frozen binary. Domain-first lazy execution stops after fully checked ON resource acceptance; skipped OFF diagnostics are counted without inferred metrics. Full native/domain branch opportunity and accepted successors stay as registered. No external route/candidate/query result reuse. Single shared-host development observation with sampled tree memory and uncontrolled OS cache; not a pooled-runtime or statistical speedup claim.')
write(root/'explicit_policy_verification.json',payload)
print({k:payload[k] for k in ['passed','seed_order','domain_mode','CPD_ns','resources','complete_wall_seconds','actual_native_work']},flush=True)
