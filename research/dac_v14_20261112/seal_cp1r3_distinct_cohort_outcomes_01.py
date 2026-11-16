"""Account every registered input/role with exact cost/failure/quality boundaries."""
import csv,re
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from cp1r3_confirmation_cohort_v1 import ROOT

def seal():
    plan=read(ROOT/'plan.json');cohort=read(ROOT/'comparison.json');protocol=read(ROOT/'protocol.json')
    assert cohort['passed'] and cohort['registered_inputs']==3 and cohort['registered_roles']==6
    assert read(ROOT/'preflight.json')['passed'] and read(D/'confirmation_release_cp1r3_01/public_source_reconstruction.json')['passed']
    out=ROOT/'terminal_evidence_01';out.mkdir(exist_ok=False);files=[Path(__file__).resolve(),ROOT/'plan.json',ROOT/'protocol.json',ROOT/'comparison.json',ROOT/'preflight.json']
    rows=[];matched=[];legal=0;timeouts=0;unexecuted=0
    for item in plan['inputs']:
        pair_path=Path(cohort['input_comparisons'][item['id']]);pair=read(pair_path);assert pair['passed'];files.append(pair_path)
        if pair.get('matched_comparison') and pair['matched_comparison'].get('matched_initial_route_and_full_vector'):matched.append(item['id'])
        for arm in protocol['fixed_arm_order']:
            row=pair['results'][arm]
            if row['status']=='unexecuted_physical_input_admission_failed':
                assert row['quality'] is None and row['complete_seconds'] is None and row['native_calls_new']==0
                rows.append(dict(input=item['id'],arm=arm,status=row['status'],quality=None,complete_seconds=None,sampled_PSS_kib=None,missing_memory_observations=None,reason=row['reason']));unexecuted+=1;continue
            case=Path(row['case']);measurement=read(row['measurement']);supervision=read(row['supervision']);entry_path=case/'confirmation_input.json'
            entry=read(entry_path) if entry_path.exists() else None
            assert not measurement['live_descendants_after_command_exit'] and not supervision['residual_descendants']
            for pid,tick in measurement['process_identities'].items():
                try:fields=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
                except (FileNotFoundError,ProcessLookupError):continue
                assert fields[0]=='Z' or fields[19]!=str(tick),'Original measured descendant is still live'
            if entry is not None:
                assert entry['measured_entry'] and entry['release_id']=='current_sta_cp1r3'
                assert entry['release_manifest_sha256']==plan['release_manifest_sha256'] and entry['configuration_sha256'][arm]==sha(item['configs'][arm])
            else:assert row['status']!='complete_legal_verified' and row['quality'] is None
            assert measurement['complete_command_wall_seconds']==row['complete_seconds']
            summary=dict(input=item['id'],arm=arm,status=row['status'],quality=row['quality'],complete_seconds=row['complete_seconds'],
                sampled_PSS_kib=row['sampled_PSS_kib'],missing_memory_observations=row['missing_memory_observations'],
                independent_research_verification_seconds=row['independent_research_verification_seconds'],actual_confirmation_admission_present=entry is not None)
            if row['status']=='complete_legal_verified':
                done=read(case/'completion.json');assert done['passed'] and done['complete_configuration_verified']
                assert row['quality']=={k:done[k] for k in ['CPD_ns','resources']}
                summary.update(own_root_endpoints={k:v for k,v in pair['own_initial_to_final_endpoint_changes'][arm].items() if k!='changes'},
                    resource_commits=done['resource_accepted_steps'],owner_commits=done['owner_commits'],timing_commits=done['timing_accepted_steps']);legal+=1
                files += [case/'completion.json',case/'flow/completion.json']
            elif row['status']=='initial_routing_execution_timeout':
                initial=case/'flow/resource_flow/initial/runs/state';manifest=read(initial/'manifest.json');assert manifest['execution_status']=='timeout'
                assert row['quality'] is None and not (case/'flow/resource_flow/initial/completion.json').exists()
                iterations=[int(line.split()[0]) for line in (initial/'stdout.log').read_text().splitlines() if len(line.split())>=15 and line.split()[0].isdigit() and '%' in line and 1<=int(line.split()[0])<=200]
                summary.update(native_initial_seconds=manifest['wall_seconds'],native_timeout_seconds=manifest['timeout_seconds'],last_complete_iteration=max(iterations) if iterations else None,
                    interpretation='Execution-budget timeout, no legal root or paired quality; not an infeasibility certificate.')
                files += [initial/'manifest.json',initial/'stdout.log'];timeouts+=1
            else:assert row['quality'] is None,'An unverified role cannot have legal quality'
            rows.append(summary);files += [Path(row['measurement']),Path(row['supervision'])]
            if entry_path.exists():files.append(entry_path)
    assert len(rows)==6 and legal==cohort['verified_legal_roles'] and unexecuted==cohort['unexecuted_admission_roles']
    write(out/'roles.json',rows)
    with (out/'overview.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['input','arm','status','CPD_ns','wire','SB','CB','complete_seconds','sampled_PSS_kib','missing_memory_observations'])
        for r in rows:
            q=r['quality'];resources=None if q is None else q['resources'];writer.writerow([r['input'],r['arm'],r['status'],None if q is None else q['CPD_ns'],*[None if resources is None else resources[k] for k in ['wirelength','SB_pairs','CB_sources']],r['complete_seconds'],r['sampled_PSS_kib'],r['missing_memory_observations']])
    write(out/'completion.json',dict(passed=True,registered_physical_inputs=3,registered_roles=6,verified_legal_roles=legal,
        verified_matched_legal_inputs=matched,matched_new_circuit_identities=[x for x in matched if x in ['lstm','dla_small']],
        unexecuted_input_admission_roles=unexecuted,initial_execution_timeouts=timeouts,new_native_calls_by_sealer=0,complete_goal=False,
        source_sha256={str(p):sha(p) for p in files},artifact_sha256={'roles.json':sha(out/'roles.json'),'overview.csv':sha(out/'overview.csv')},
        qualification='Prospectively fixed CP1r3 protocol/configs. Two known distinct circuit/netlists plus one known SB-only architecture control, not unseen tests or six samples. Complete algorithm costs stay with their own exact outputs; provisioning/reconstruction and independent verification are separate. No research stop on closure or ordinary negatives.'))
    return out/'completion.json'

if __name__=='__main__':print(seal())
