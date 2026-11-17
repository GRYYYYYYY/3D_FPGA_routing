"""Bind the selected TPU-OS pair and reconstruct CP1r5 before any native execution."""
import copy
import fcntl
import hashlib
import json
import subprocess
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from cp1r5_clstm_sb_cohort_01 import ROOT, confirmation_arguments, environment
from package_cp1r5_public_source_01 import package


def activate():
    started = time.monotonic()
    home = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home')
    release = home/'confirmation_releases/current_sta_cp1r5'
    workspace = home/'confirmation_workspaces/cp1r5_clstm_sb_pair_01'
    assert not ROOT.exists() and not workspace.exists()
    assert read(D/'confirmation_release_cp1r5_01/completion.json')['passed']
    preflight = read(D/'CLSTM_SB_input_preflight_01/completion.json')
    assert preflight['passed']
    selected = read(D/'CLSTM_SB_input_preflight_01/selected_input.json')
    source = Path(selected['physical_files']['packed']['path']).parent
    provenance_source = source.with_name(source.name.removesuffix('_a0')+'_place')/'manifest.json'
    manifest_path = source/'manifest.json'
    manifest, provenance = read(manifest_path), read(provenance_source)
    assert all(manifest['outputs'][n]['sha256']==provenance['outputs'][n]['sha256']
               for n in ['packed.net','placed.place'])
    command = manifest['command']
    assert '--sdc_file' not in command
    assert command[command.index('--merge_constant_generators')+1]=='off'
    assert selected['not_previously_registered_complete_confirmation']
    for name, digest in selected['declared_sha256'].items():
        assert next(x for x in preflight['physical_inputs'] if x['kind']==name)['sha256']==digest
    ROOT.mkdir()
    workspace.mkdir()
    w = workspace/'clstm_sb'
    w.mkdir()
    copies = {k:dict(source=row['path'], destination=str(w/'inputs'/(k+Path(row['path']).suffix)),
                     sha256=selected['declared_sha256'][k], bytes=row['bytes'])
              for k,row in selected['physical_files'].items()}
    packing = w/'packing_manifest.json'
    packing.write_bytes(provenance_source.read_bytes())
    contract = read(release/'contract.json')
    template = D/'cp1r2_cross_circuit_cohort_01/conv_hls_phase_runtime.json'
    spec = read(template)
    spec['physical_files'] = {k:dict(path=row['destination'],sha256=row['sha256']) for k,row in copies.items()}
    spec.pop('full_graph_cache_completion_sha256',None)
    phase = w/'phase_runtime.json'
    write(phase,spec)
    route = [spec['phase_binaries']['resource']['path'],copies['architecture']['destination'],
             copies['circuit']['destination'],'--route','--analysis']
    for flag,value in contract['route_fixed_options'].items():route += [flag,value]
    for flag in ['--device','--route_chan_width','--seed']:route += [flag,command[command.index(flag)+1]]
    for flag,key in [('--read_rr_graph','graph'),('--net_file','packed'),('--place_file','placement')]:route += [flag,copies[key]['destination']]
    route += ['--route_file',str(w/'UNCREATED_ROUTE_OUTPUT'),'--merge_constant_generators','off']
    config = copy.deepcopy(contract['fixed_configuration'])
    config.update(route_command=route,phase_runtime_config=str(phase),
                  input_sha256={row['path']:row['sha256'] for group in ['physical_files','phase_binaries','query_engines','query_validations'] for row in spec[group].values()})
    config['input_sha256'].update({str(f):sha(f) for f in [release/'release_manifest.json',release/'contract.json',packing]})
    configs = {}
    for arm in ['native','domain']:
        current = copy.deepcopy(config)
        current.update(domain_mode='unrestricted' if arm=='native' else 'paired',domain_feedback=arm=='domain')
        path = w/(arm+'_config.json')
        write(path,current)
        configs[arm] = str(path)
        (ROOT/path.name).write_bytes(path.read_bytes())
    item = dict(id='clstm_sb',workspace=str(w),source_name=source.name,copies=copies,
                configs=configs,packing_manifest=str(packing),
                physical_identity=dict(selected['declared_sha256'],
                    normalized_coordinates_sha256=preflight['actual_layout']['coordinate_semantic_sha256'],
                    placed_blocks=preflight['actual_layout']['placed_blocks'],
                    known_historical_input=True,explicit_SDC=False),
                purpose='Known CLSTM-small circuit, SB-only configuration and actual distinct placement from historical Hybrid-O; no old route import, no new circuit or architecture-family claim')
    files = [Path(__file__).resolve(),D/'cp1r5_clstm_sb_cohort_01.py',D/'run_cp1r5_clstm_sb_pair_01.py',
             D/'package_cp1r5_public_source_01.py',D/'packed_input_contract_v1.py',
             D/'seed_census_analysis_pool_v2.py',D/'retained_prefix_workflow.py',
             D/'endpoint_timing_policy_streaming_v2.py',D/'CLSTM_SB_input_preflight_01/completion.json',
             D/'CLSTM_SB_input_preflight_01/measurement/completion.json',
             D/'CLSTM_SB_input_preflight_01/selected_input.json',D/'CLSTM_SB_input_preflight_01/actual_start_comparison.json',
             D/'confirmation_release_cp1r5_01/completion.json',release/'release_manifest.json',
             release/'contract.json',manifest_path,provenance_source,template,phase,packing,
             *map(Path,configs.values())]
    bound = {str(p):sha(p) for p in files}
    for group in ['phase_binaries','query_engines','query_validations']:
        for row in spec[group].values():bound[row['path']]=row['sha256']
    plan = dict(passed=True,registered_before_new_outcomes=True,release=str(release),
                release_manifest_sha256=sha(release/'release_manifest.json'),
                contract_sha256=sha(release/'contract.json'),workspace=str(workspace),
                inputs=[item],fixed_arm_order=['native','domain'],registered_inputs=1,registered_roles=2,
                source_sha256=bound,confirmation_batch=True,large_physical_provisioning_deferred=True,
                requires_exclusive_serial_slot=True,full_method_time_cap=None,research_total_call_cap=None,
                source_runtime_or_algorithm_selected_from_outcomes=False,
                explicit_application_timing_claim=False,source_route_will_be_imported=False,
                independence='One actual CLSTM-small SB-only physical instance, distinct graph/layout from historical Hybrid-O recovery. Two roles are one input; not a new circuit or architecture family, unseen holdout, or causal architecture comparison. Fresh paired roots and complete output admission remain required.',
                qualification='Frozen CP1r5 checker-only owner identity correction over CP1r4 numeric planner; CP1r3 budgets, acceptance, search/owner/domain/release and terminal rules retained. Seed21/constant-merge off follow actual upstream command. All failure, timeout, no-cut/no-gain and degraded outcomes retained. Provisioning, reconstruction and research verification costs are separate from measured complete run-arm. No date/call/matrix Goal stopping condition.')
    check = subprocess.run(['/usr/bin/python3',str(release/'confirmation.py'),'check',
                            *confirmation_arguments(plan,item)],cwd=release,env=environment(),
                           capture_output=True,text=True,timeout=120)
    (ROOT/'registration_admission.stdout').write_text(check.stdout)
    (ROOT/'registration_admission.stderr').write_text(check.stderr)
    assert check.returncode==0,check.stderr
    assert json.loads(check.stdout)['passed']
    draft = ROOT/'admission_plan.json'
    write(draft,plan)
    reconstruction = D/'confirmation_release_cp1r5_01/public_source_reconstruction.json'
    assert read(reconstruction)['passed']
    for p in [draft,reconstruction,D/'restore_confirmation_cp1r5_dependencies.py',
              D/'confirmation_release_cp1r5_01/current_sta_cp1r5_source.tar.gz']:
        bound[str(p)] = sha(p)
    plan['source_sha256'] = bound
    write(ROOT/'plan.json',plan)
    write(ROOT/'preflight.json',dict(passed=True,registered_inputs=1,registered_roles=2,
          actual_frozen_checker=json.loads(check.stdout),actual_public_reconstruction=True,
          actual_restored_guard_and_worker_imports=True,actual_relocated_admission=False,prior_release_reconstruction_reused=True,
          complete_activation_seconds=time.monotonic()-started,large_physical_provisioning_passed=False,
          new_native_or_STA_calls=0,qualification='Actual fixed-release config check plus unchanged release source reconstruction reused; this new input was not rechecked in a relocated copy. No new route or full-method quality yet.'))


if __name__=='__main__':
    with (D/'critical_scope_runner.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        activate()
