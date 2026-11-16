"""Account actual prospective cohort outputs/failures; do not infer legal quality."""
from datetime import datetime,timezone
from pathlib import Path
import shutil
from retained_prefix_workflow import D,read,write,sha

root=D/'cp1r2_cross_circuit_cohort_01';out=root/'terminal_evidence_01'
plan=read(root/'plan.json');terminal=read(root/'queue/completion.json')
assert terminal['passed'] and terminal['status']=='registered_cohort_terminal'
cohort=read(root/'comparison.json');assert cohort['passed']
assert cohort['registered_inputs']==2 and cohort['registered_roles']==4
assert not out.exists();out.mkdir()
files=[Path(__file__).resolve(),root/'plan.json',root/'comparison.json',root/'queue/completion.json']
outcomes={};legal=0;timeouts=0;matched_legal_inputs=0
for item in plan['inputs']:
    pair_path=Path(cohort['input_comparisons'][item['id']]);pair=read(pair_path)
    assert pair['passed'] and pair['release_manifest_sha256']==plan['release_manifest_sha256']
    assert set(pair['results'])=={'native','domain'}
    files.append(pair_path);arms={}
    for arm,row in pair['results'].items():
        case=Path(row['case']);measurement=read(case/'measurement/completion.json');supervision=read(case/'supervision.json')
        entry=read(case/'confirmation_input.json')
        assert entry['measured_entry'] and entry['arm']==arm and entry['release_id']=='current_sta_cp1r2'
        assert entry['release_manifest_sha256']==plan['release_manifest_sha256']
        assert entry['configuration_sha256'][arm]==sha(item['configs'][arm])
        assert not measurement['live_descendants_after_command_exit'] and not supervision['residual_descendants']
        assert measurement['complete_command_wall_seconds']==row['complete_seconds']
        alive=[]
        for pid,tick in measurement['process_identities'].items():
            try:state=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
            except (FileNotFoundError,ProcessLookupError):continue
            if state[0]!='Z' and state[19]==str(tick):alive.append(pid)
        assert not alive,(case,alive)
        initial=case/'flow/resource_flow/initial/runs/state'
        manifest=read(initial/'manifest.json')
        names=['confirmation_input.json','config.json','measurement/completion.json','supervision.json','flow/resource_flow/initial/runs/state/manifest.json']
        result=dict(original_status=row['status'],quality=None,
            complete_attempt_seconds=row['complete_seconds'],
            sampled_PSS_kib=measurement['sampled_tree_PSS_peak_kib'],
            missing_memory_observations=measurement['missing_memory_observations'],
            actual_process_identities_rechecked=len(measurement['process_identities']),
            live_original_descendants=0)
        if row['status']=='complete_legal_verified':
            complete=read(case/'completion.json')
            assert complete['passed'] and complete['complete_configuration_verified']
            assert complete['resources']==row['quality']['resources'] and complete['CPD_ns']==row['quality']['CPD_ns']
            result.update(classification='complete_legal_verified',quality=row['quality'],
                resource_commits=complete['resource_accepted_steps'],owner_commits=complete['owner_commits'],
                timing_commits=complete['timing_accepted_steps'],timing_proposals=complete['timing_attempted_proposals'],
                own_root_endpoint_summary={k:v for k,v in pair['own_initial_to_final_endpoint_changes'][arm].items() if k!='changes'})
            names+=['completion.json','flow/completion.json'];legal+=1
        elif manifest['status']=='timeout':
            assert manifest['execution_status']=='timeout' and manifest['timeout_seconds']==1800
            assert row['quality'] is None and not (case/'flow/resource_flow/initial/completion.json').exists()
            text=(initial/'stdout.log').read_text()
            assert 'Routing failed.' not in text and 'Circuit is unroutable with a channel width factor' not in text
            result.update(classification='initial_routing_execution_timeout',
                native_command_seconds=manifest['wall_seconds'],native_timeout_seconds=1800,
                native_returncode=manifest['returncode'],initial_legal=False,
                interpretation='Stopped by fixed execution budget; not200iteration route failure, infeasibility or algorithm no-gain.')
            names.append('flow/resource_flow/initial/runs/state/stdout.log');timeouts+=1
        else:
            result.update(classification=row['status'],native_terminal_status=manifest['status'])
        folder=out/item['id']/arm;folder.mkdir(parents=True)
        for name in names:
            original=case/name;dest=folder/name;dest.parent.mkdir(exist_ok=True,parents=True)
            shutil.copy2(original,dest);assert sha(dest)==sha(original);files.append(original)
        arms[arm]=result
    matched=pair.get('matched_comparison')
    if matched and matched['matched_initial_route_and_full_vector']:matched_legal_inputs+=1
    outcomes[item['id']]=dict(physical_identity=item['physical_identity'],arms=arms,
        matched_legal_pair=bool(matched and matched['matched_initial_route_and_full_vector']),
        endpoint_summary=None if not matched else {k:v for k,v in matched['endpoint_changes'].items() if k!='changes'},
        quality_deltas=None if not matched else matched['delta_domain_minus_native'])
assert legal==cohort['verified_legal_roles']
write(out/'completion.json',dict(passed=True,sealed_at=datetime.now(timezone.utc).isoformat(),
    registered_physical_inputs=2,registered_roles=4,verified_legal_roles=legal,
    verified_matched_legal_physical_inputs=matched_legal_inputs,initial_execution_timeouts=timeouts,
    outcomes=outcomes,release_manifest_sha256=plan['release_manifest_sha256'],
    native_calls_new=0,complete_goal=False,source_sha256={str(f):sha(f) for f in files},
    qualification='Prospectively fixed CP1r2 cohort on two selected known distinct circuits/placements. A legal native/domain pair counts once. Timeout roles retain actual complete costs and no legal quality, endpoints or paired mechanism delta. Original plans, processes and failures preserved. Fixed-menu no-op and execution applicability remain evidence; neither the cohort nor this seal stops research.'))
print(dict(passed=True,registered_inputs=2,roles=4,legal_roles=legal,timeouts=timeouts,matched_legal_inputs=matched_legal_inputs))
