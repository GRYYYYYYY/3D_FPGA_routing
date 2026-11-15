"""Choose a fully observed wire improvement from a closed resource menu.

The original actor remains immutable. This optional terminal branch requires
unchanged SB/CB, lower wire, exact CPD/setup non-regression and no additional
hold violation. It ranks only actual same-current-source candidates already
evaluated by the actor, never predicted or manually named nets/candidates.
"""
import argparse
from pathlib import Path
import time

from retained_prefix_workflow import read, write, sha, route_body
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof
from endpoint_timing_policy import compare


def select(actor, output):
    started=time.monotonic()
    actor, output=Path(actor).resolve(), Path(output).resolve()
    output.mkdir(exist_ok=False)
    closed=read(actor/'completion.json')
    assert closed['passed']
    assert closed['operator_stop']=='no_admissible_candidate_in_registered_current_scope_probe'
    current=Path(closed['final_state'])
    current_run=run_dir(current)
    before=read(current/'endpoint_vector.json')
    resources=require_publication_proof(current)['resource_axes']
    body=route_body(current_run/'routed.route')
    files=[Path(__file__).resolve(),Path(__file__).with_name('endpoint_timing_policy.py'),
           Path(__file__).with_name('state_resource_assurance.py'),actor/'completion.json',
           actor/'attempts.json',current/'completion.json',current/'endpoint_vector.json',
           current_run/'routed.route',current_run/'independent_audit.json']
    rows=[]
    for index, attempt in enumerate(read(actor/'attempts.json')):
        source=Path(attempt['current_state'])
        if source.resolve()!=current.resolve():
            continue
        assert route_body(run_dir(source)/'routed.route')==body
        tx=Path(attempt['transaction'])
        registration=read(tx/'registration.json')
        progress=read(tx/'progress.json')
        files += [tx/'registration.json',tx/'progress.json']
        for role, result in progress.items():
            if result['status']!='legal_evaluated':
                continue
            assert Path(registration['roles'][role]['state']).resolve()==current.resolve()
            state=Path(result['evaluation'])
            axes=require_publication_proof(state)['resource_axes']
            vector=read(state/'endpoint_vector.json')
            evidence=compare(before,vector)
            run=run_dir(state);manifest=read(run/'manifest.json')
            assert manifest['metrics']['native_full_check_passed']
            assert sha(run/'packed.net')==sha(current_run/'packed.net')
            assert sha(run/'placed.place')==sha(current_run/'placed.place')
            checks=dict(same_vertical_resources=all(axes[k]==resources[k] for k in ['SB_pairs','CB_sources']),
                strictly_less_wire=axes['wirelength']<resources['wirelength'],
                endpoint_identity=evidence['compatible'],
                exact_CPD_nonworse=evidence.get('cpd_nonworse',False),
                setup_nonworse=evidence.get('setup_regressed')==0,
                no_increased_hold_violation=evidence.get('hold_violation_regressions')==0)
            rows.append(dict(attempt_index=index,role=role,state=str(state),resources=axes,
                eligible=all(checks.values()),checks=checks,
                setup_improved=evidence.get('setup_improved'),setup_regressed=evidence.get('setup_regressed'),
                original_primary_accepted=result['policies']['resources_under_timing']['accepted']))
            files += [state/'completion.json',state/'endpoint_vector.json',run/'manifest.json',run/'independent_audit.json',run/'routed.route']
    choices=[r for r in rows if r['eligible']]
    choices.sort(key=lambda r:(r['resources']['wirelength'],r['attempt_index'],r['role']))
    selected=choices[0] if choices else None
    write(output/'observed_candidates.json',rows)
    payload=dict(passed=True,actor=str(actor),state=str(current),current_resources=resources,
        selected=selected,actual_same_source_candidates=len(rows),eligible_candidates=len(choices),
        rule='After original vertical menu closes, choose least wire among actual same-source FULL/STA/independently audited candidates with equal SB/CB, exact CPD/setup non-regression and no increased hold violation; then first observed attempt and role name. No net/candidate IDs in algorithm.',
        native_calls_new=0,committed_to_original_actor=False,
        complete_selection_seconds=time.monotonic()-started,
        source_sha256={str(p):sha(p) for p in dict.fromkeys(files)},
        artifact_sha256={'observed_candidates.json':sha(output/'observed_candidates.json')},
        qualification='Retrospective development of a fixed terminal-selection rule on an already closed menu, not a prospective confirmation or new route. All chosen metrics/vectors are actual observations already preserved in the archive; selecting one creates no additional legal sample. Further combination and native validation are separate. Primary vertical-resource policy is unchanged in old runs. Acceptance-mode differences remain explicit.')
    write(output/'completion.json',payload)
    return payload


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--actor',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=select(a.actor,a.output)
    print(dict(passed=True,candidates=result['actual_same_source_candidates'],selected=result['selected']),flush=True)
