"""Two explicit terminal wire policies over already completed legal menu observations."""
import argparse,time
from pathlib import Path
from retained_prefix_workflow import read,write,sha
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof
from endpoint_timing_policy_streaming_v2 import compare


def select(actor,output,mode='endpoint'):
    assert mode in ['endpoint','fixed_timing']
    actor,output=Path(actor).resolve(),Path(output).resolve();output.mkdir(exist_ok=False)
    started=time.monotonic();closed=read(actor/'completion.json');reg=read(actor/'registration.json')
    assert closed['passed'] and closed['operator_stop'] in ['no_admissible_candidate_in_registered_current_scope_probe','no_admissible_move_in_registered_current_rank_windows']
    current=Path(closed['final_state']);before=read(current/'endpoint_vector.json');rd=run_dir(current)
    br=require_publication_proof(current)['resource_axes'];anchor=reg['anchor']
    caps=anchor.get('resource_limits',reg.get('resource_limits'));assert caps is not None
    cpd_limit=anchor['CPD_s'];bound={};stats={}
    def bind(path):
        path=Path(path).resolve();key=str(path)
        if key not in bound:
            bound[key]=sha(path);s=path.stat();stats[key]=[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
        return bound[key]
    def sealed_state(state):
        done=read(state/'completion.json');assert done['passed']
        bind(state/'completion.json');bind(state/'endpoint_vector.json')
        sealpath=done.get('requires_final_input_seal')
        if sealpath:
            seal=read(sealpath);assert seal['passed'];bind(sealpath)
            if 'pool_completion' in seal:
                pool=Path(seal['pool_completion']);assert read(pool)['passed'] and bind(pool)==seal['pool_completion_sha256']
        proof=require_publication_proof(state);run=run_dir(state);manifest=read(run/'manifest.json')
        assert manifest['metrics']['native_full_check_passed']
        assert all(bind(run/name)==manifest['outputs'][name]['sha256'] for name in ['packed.net','placed.place','routed.route'])
        bind(run/'manifest.json');bind(run/'independent_audit.json')
        return proof['resource_axes']
    assert sealed_state(current)==br
    for f in [Path(__file__).resolve(),Path(__file__).with_name('endpoint_timing_policy_streaming_v2.py'),Path(__file__).with_name('state_resource_assurance.py'),actor/'completion.json',actor/'registration.json',actor/'attempts.json']:bind(f)
    rows=[]
    for index,attempt in enumerate(read(actor/'attempts.json')):
        if Path(attempt['current_state']).resolve()!=current.resolve():continue
        if 'pair' in attempt:
            observed=attempt['pair'];schema='seed_census_pair'
        else:
            tx=Path(attempt['transaction']);registration=read(tx/'registration.json');observed=read(tx/'progress.json');schema='transaction_progress'
            bind(tx/'registration.json');bind(tx/'progress.json')
            assert all(Path(registration['roles'][role]['state']).resolve()==current.resolve() for role in observed)
        for role,item in observed.items():
            if item['status']!='legal_evaluated':continue
            state=Path(item['evaluation']);axes=sealed_state(state);after=read(state/'endpoint_vector.json');evidence=compare(before,after);run=run_dir(state)
            assert bind(run/'packed.net')==bind(rd/'packed.net') and bind(run/'placed.place')==bind(rd/'placed.place')
            original=item['decision'] if schema=='seed_census_pair' else item['policies']['resources_under_timing']
            checks=dict(same_vertical_resources=all(axes[k]==br[k] for k in ['SB_pairs','CB_sources']),strictly_less_wire=axes['wirelength']<br['wirelength'],endpoint_identity=evidence['compatible'],no_increased_hold_violation=evidence.get('hold_violation_regressions')==0,original_root_resource_envelope=all(axes[k]<=caps[k] for k in caps),original_root_CPD_envelope=after['cpd_s']<=cpd_limit)
            if mode=='endpoint':checks.update(exact_CPD_nonworse=evidence.get('cpd_nonworse',False),setup_nonworse=evidence.get('setup_regressed')==0)
            rows.append(dict(attempt_index=index,role=role,state=str(state),schema=schema,resources=axes,CPD_s=after['cpd_s'],eligible=all(checks.values()),checks=checks,setup_improved=evidence.get('setup_improved'),setup_regressed=evidence.get('setup_regressed'),original_primary_accepted=original['accepted']))
    choices=sorted((r for r in rows if r['eligible']),key=lambda r:(r['resources']['wirelength'],r['attempt_index'],r['role']))
    for path,stat in stats.items():
        s=Path(path).stat();assert [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]==stat,'Immutable observed evidence changed'
    write(output/'observed_candidates.json',rows)
    result=dict(passed=True,actor=str(actor),state=str(current),mode=mode,current_resources=br,fixed_CPD_limit_s=cpd_limit,fixed_resource_limits=caps,actual_same_source_candidates=len(rows),eligible_candidates=len(choices),selected=choices[0] if choices else None,native_calls_new=0,committed_to_original_actor=False,complete_selection_seconds=time.monotonic()-started,source_sha256=bound,artifact_sha256={'observed_candidates.json':sha(output/'observed_candidates.json')},qualification='Retrospective deterministic terminal rule over already executed same-source native FULL/freshSTA/independently audited candidates of a closed menu. Both global modes require equal SB/CB, strictly lower wire, original root CPD/resource envelope and no increased hold violation. Endpoint mode additionally requires current CPD/setup non-regression; fixed_timing explicitly permits setup tradeoffs within the declared root cap. Rank by wire then original attempt/role; no circuit/net/candidate special cases. No new routing observation, native execution, original-actor commit, independent confirmation sample or complete workflow timing is created. Historical creation times are not borrowed.')
    write(output/'completion.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--actor',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',choices=['endpoint','fixed_timing'],default='endpoint');a=p.parse_args();r=select(a.actor,a.output,a.mode);print({k:r[k] for k in ['passed','mode','actual_same_source_candidates','eligible_candidates','selected']},flush=True)
