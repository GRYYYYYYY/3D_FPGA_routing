"""Register frisc using actual upstream receipts and the unchanged CP1r5 rules."""
import copy
import fcntl
import json
import subprocess
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from cp1r5_frisc_cohort_01 import ROOT, confirmation_arguments, environment


def main():
    started = time.monotonic()
    home = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home')
    release = home/'confirmation_releases/current_sta_cp1r5'
    workspace = home/'confirmation_workspaces/cp1r5_frisc_pair_01'
    upstream = D/'VTR_frisc_input_01'
    prepared = read(upstream/'completion.json')
    assert prepared['passed'] and not prepared['route_quality_admitted']
    assert all(sha(p)==h for p,h in prepared['source_sha256'].items())
    assert read(D/'confirmation_release_cp1r5_01/completion.json')['passed']
    reconstruction = D/'confirmation_release_cp1r5_01/public_source_reconstruction.json'
    assert read(reconstruction)['passed']
    assert not ROOT.exists() and not workspace.exists()
    ROOT.mkdir(); workspace.mkdir()
    w = workspace/'frisc'; w.mkdir()
    copies = {k:dict(source=row['path'], destination=str(w/'inputs'/(k+Path(row['path']).suffix)),
                    sha256=row['sha256'], bytes=row['bytes'])
              for k,row in prepared['physical_files'].items()}
    packing = w/'packing_manifest.json'
    packing.write_bytes((upstream/'packing_provenance.json').read_bytes())
    contract = read(release/'contract.json')
    template = D/'cp1r2_cross_circuit_cohort_01/conv_hls_phase_runtime.json'
    spec = read(template)
    spec['physical_files'] = {k:dict(path=row['destination'],sha256=row['sha256']) for k,row in copies.items()}
    spec.pop('full_graph_cache_completion_sha256',None)
    phase = w/'phase_runtime.json'; write(phase,spec)
    command = read(upstream/'place_01/registration.json')['command']
    route = [spec['phase_binaries']['resource']['path'],copies['architecture']['destination'],
             copies['circuit']['destination'],'--route','--analysis']
    for flag,value in contract['route_fixed_options'].items(): route += [flag,value]
    for flag in ['--device','--route_chan_width','--seed']: route += [flag,command[command.index(flag)+1]]
    for flag,key in [('--read_rr_graph','graph'),('--net_file','packed'),('--place_file','placement')]:
        route += [flag,copies[key]['destination']]
    route += ['--route_file',str(w/'UNCREATED_ROUTE_OUTPUT'),'--merge_constant_generators','off']
    assert 'sdc' in copies
    route += ['--sdc_file',copies['sdc']['destination']]
    config = copy.deepcopy(contract['fixed_configuration'])
    config.update(route_command=route,phase_runtime_config=str(phase),
        input_sha256={row['path']:row['sha256'] for group in ['physical_files','phase_binaries','query_engines','query_validations'] for row in spec[group].values()})
    config['input_sha256'].update({str(f):sha(f) for f in [release/'release_manifest.json',release/'contract.json',packing]})
    configs = {}
    for arm in ['native','domain']:
        current = copy.deepcopy(config)
        current.update(domain_mode='unrestricted' if arm=='native' else 'paired', domain_feedback=arm=='domain')
        path = w/(arm+'_config.json'); write(path,current)
        configs[arm] = str(path); (ROOT/path.name).write_bytes(path.read_bytes())
    item = dict(id='frisc',workspace=str(w),source_name='VTR_frisc_pack11_place21_hybrid_o_n25_w100_clock20ns',
        copies=copies,configs=configs,packing_manifest=str(packing),
        physical_identity=dict({k:r['sha256'] for k,r in prepared['physical_files'].items()},
            normalized_coordinates_sha256=prepared['actual_layout']['coordinate_semantic_sha256'],
            placed_blocks=prepared['actual_layout']['placed_blocks'],explicit_SDC=True,
            new_circuit_to_current_CP1_confirmation=True,new_architecture_family=False),
        purpose='Test dependency-aware tradeoffs on a distinct public mapped sequential circuit and a newly produced placement. No historical route imported; source selection and size use no routing QoR. Both arms share explicit20ns benchmark SDC; no external application requirement.')
    files = [Path(__file__).resolve(), D/'cp1r5_frisc_cohort_01.py', D/'run_cp1r5_frisc_pair_01.py',
        D/'cp1r5_clstm_sb_cohort_01.py', D/'run_cp1r5_clstm_sb_pair_01.py',
        D/'packed_input_contract_v1.py',D/'seed_census_analysis_pool_v2.py',D/'retained_prefix_workflow.py',
        D/'endpoint_timing_policy_streaming_v2.py',upstream/'completion.json',upstream/'packing_provenance.json',
        upstream/'registration.json',upstream/'place_01/registration.json',upstream/'capacity_selection.json',
        D/'confirmation_release_cp1r5_01/completion.json', reconstruction,release/'release_manifest.json',
        release/'contract.json',template,phase,packing,*map(Path,configs.values())]
    bound = {str(p):sha(p) for p in files}
    for group in ['phase_binaries','query_engines','query_validations']:
        for row in spec[group].values(): bound[row['path']]=row['sha256']
    plan = dict(passed=True,registered_before_new_outcomes=True,release=str(release),
        release_manifest_sha256=sha(release/'release_manifest.json'), contract_sha256=sha(release/'contract.json'),
        workspace=str(workspace),inputs=[item],fixed_arm_order=['native','domain'],registered_inputs=1,registered_roles=2,
        source_sha256=bound,confirmation_batch=True,large_physical_provisioning_deferred=True,
        requires_exclusive_serial_slot=True,full_method_time_cap=None,research_total_call_cap=None,
        source_runtime_or_algorithm_selected_from_outcomes=False,explicit_application_timing_claim=False,
        source_route_will_be_imported=False,
        independence='One distinct public circuit new to current CP1 confirmation, with one fresh actual seed21 placement. Two roles are one input. Same Hybrid-O architecture family; no unseen holdout, new-architecture or application-SDC claim.',
        qualification='Immutable CP1r5 rules and binaries; original phase time/memory guards, budgets, acceptance and terminal selection unchanged. Existing cohort implementation differs only in output names and input-scope description. Preserve routing failures, timeouts, no-cut/no-gain and degradation. Derived upstream provenance explicitly binds original successful pack/place receipts and retained preparation failures; no historical completion fabricated. Complete times start at run-arm; upstream and independent audits remain separate. Single N/D sequence is not interleaved speedup evidence.')
    check = subprocess.run(['/usr/bin/python3',str(release/'confirmation.py'),'check',*confirmation_arguments(plan,item)],
        cwd=release,env=environment(),capture_output=True,text=True,timeout=120)
    (ROOT/'registration_admission.stdout').write_text(check.stdout)
    (ROOT/'registration_admission.stderr').write_text(check.stderr)
    assert check.returncode==0,check.stderr
    admitted = json.loads(check.stdout); assert admitted['passed']
    write(ROOT/'plan.json',plan)
    write(ROOT/'preflight.json',dict(passed=True,registered_inputs=1,registered_roles=2,
        actual_frozen_checker=admitted,prior_release_reconstruction_reused=True,
        new_input_relocated_admission=False,large_physical_provisioning_passed=False,
        complete_activation_seconds=time.monotonic()-started,new_native_or_STA_calls=0,
        qualification='Configuration and provenance registration only. Provisioning, per-arm full input byte checks and actual route/output admission remain required.'))
    print(json.dumps(dict(passed=True,plan=str(ROOT/'plan.json'),registered_roles=2)))


if __name__=='__main__':
    with (D/'critical_scope_runner.lock').open() as lock:
        fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        main()
