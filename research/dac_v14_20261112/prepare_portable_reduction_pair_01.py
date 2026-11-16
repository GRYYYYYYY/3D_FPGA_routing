"""Register a structurally motivated new circuit pair without disturbing measured work."""
import copy
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

root = D / 'portable_reduction_pair_01'
home = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces')
w = home / 'reduction_pair_01'
prior = home / 'whole_method_01'
runtime = prior / 'runtime'
name = 'heldout_reduction_layer_s21_hybrid_o_n125_w100_p0_a0'
row = next(r for r in read(D / 'confirmation_input_inventory_01/inputs.json') if r['name'] == name)
source_manifest = Path(row['source_manifest'])
source = source_manifest.parent
m = read(source_manifest)
old_command = m['command']
screen = D / 'structural_input_screen_01' / name / 'completion.json'
diagnostic = read(screen)
assert diagnostic['passed'] and diagnostic['status'] == 'legal_historical_root_structural_screen'
assert diagnostic['counts']['structural_sharing_scopes'] == 268
assert diagnostic['counts']['supported_owner_escape_certificates'] == 0
package = read(runtime / 'artifact_manifest.json')
assert package['component_revision'] == 'complete_method_dev_03'
assert sha(runtime / 'artifact_manifest.json') == '3fa46bd7becb567dc9930f91805036fc347dc711d3e63e00e34e959156572679'
predecessor = D / 'complete_BNN_domain_engineering_01/queue'
identity = read(predecessor / 'registration.json')
live = process_identity(identity['pid'])
assert live and live['state'] != 'Z' and live['start_ticks'] == identity['start_ticks']
assert not root.exists() and not w.exists()
paths = dict(architecture=Path(old_command[1]), circuit=Path(old_command[2]),
             graph=Path(old_command[old_command.index('--read_rr_graph') + 1]),
             packed=source / 'packed.net', placement=source / 'placed.place')
digests = {key: m['shared_inputs'][str(paths[key])]['sha256'] for key in ['architecture', 'circuit', 'graph']}
digests.update(packed=m['outputs']['packed.net']['sha256'], placement=m['outputs']['placed.place']['sha256'])
assert digests['packed'] == row['packing_sha256']
assert digests['placement'] == row['placement_bytes_sha256']
assert digests['architecture'] == row['architecture_sha256'] and digests['circuit'] == row['netlist_sha256']
copies = {key: dict(source=str(path), destination=str(w / 'inputs' / (key + path.suffix)),
                   sha256=digests[key], bytes=path.stat().st_size) for key, path in paths.items()}
root.mkdir()
w.mkdir()
spec = read(prior / 'phase_runtime.json')
spec['physical_files'] = {key: dict(path=value['destination'], sha256=value['sha256']) for key, value in copies.items()}
spec.pop('full_graph_cache_completion_sha256', None)
phase = w / 'phase_runtime.json'
write(phase, spec)
template = read(prior / 'config.json')
command = list(template['route_command'])
command[1:3] = [copies['architecture']['destination'], copies['circuit']['destination']]
for flag, key in [('--read_rr_graph', 'graph'), ('--net_file', 'packed'), ('--place_file', 'placement')]:
    command[command.index(flag) + 1] = copies[key]['destination']
for flag in ['--device', '--route_chan_width', '--seed']:
    command[command.index(flag) + 1] = old_command[old_command.index(flag) + 1]
command[command.index('--route_file') + 1] = str(w / 'UNCREATED_ROUTE_OUTPUT')
assert command[command.index('--seed') + 1] == '21'
assert command[command.index('--router_max_convergence_count') + 1] == '8'
assert command[command.index('--router_reconvergence_cpd_threshold') + 1] == '1.01'
assert '--sdc_file' not in command
cases = {}
for arm in ['native', 'domain']:
    cfg = copy.deepcopy(template)
    cfg.update(route_command=command, phase_runtime_config=str(phase),
               domain_mode='unrestricted' if arm == 'native' else 'paired', domain_feedback=arm == 'domain')
    cfg['input_sha256'] = {r['path']: r['sha256'] for group in ['physical_files', 'phase_binaries', 'query_engines', 'query_validations'] for r in spec[group].values()}
    path = w / (arm + '_config.json')
    write(path, cfg)
    cases[arm] = str(path)
a, b = [read(cases[arm]) for arm in ['native', 'domain']]
assert {key for key in a if a[key] != b[key]} == {'domain_mode', 'domain_feedback'}
assert a['owner_escalation'] and a['owner_domain_mode'] == b['owner_domain_mode'] == 'unrestricted_in_both_arms'
assert not a['initial_route_imported'] and not a['external_history_allowed']
helper = w / 'admit_pair.py'
helper.write_bytes((home / 'clstm_pair_01/admit_pair.py').read_bytes())
scripts = [D / (prefix + '_portable_reduction_pair_01.py') for prefix in ['prepare', 'admit', 'queue', 'run', 'compare']]
for script in scripts:
    compile(script.read_text(), str(script), 'exec')
bound = {str(runtime / relative): digest for relative, digest in package['sha256'].items()}
for group in ['phase_binaries', 'query_engines', 'query_validations']:
    bound.update({record['path']: record['sha256'] for record in spec[group].values()})
reason_evidence = [D / 'attention_initial_failure_pair_01/completion.json',
                  D / 'unified_input_integration_01/robot_s23_SDC_native/flow/resource_flow/repair/completion.json']
assert read(reason_evidence[0])['passed'] and read(reason_evidence[1])['attempted_scopes'] == 0
small_files = scripts + [phase, helper, source_manifest, screen, runtime / 'artifact_manifest.json',
    prior / 'config.json', prior / 'phase_runtime.json', *map(Path, cases.values()), *reason_evidence]
bound.update({str(path): sha(path) for path in small_files})
plan = dict(passed=True, registered_before_new_method_outcomes=True,
    workspace=str(w), runtime=str(runtime), predecessor=str(predecessor),
    whole_method_prerequisite=str(D / 'standalone_whole_method_check_01/queue'),
    fixed_order=['native', 'domain'], cases=cases, source_sha256=bound,
    physical_input_copies=copies, physical_identity=row,
    package_manifest_sha256=sha(runtime / 'artifact_manifest.json'),
    deferred_physical_admission=True, admission_requires_shared_serial_slot=True,
    admission_script=str(D / 'admit_portable_reduction_pair_01.py'),
    structural_prior=dict(sharing_scopes=268, sharing_nets=62, owner_certificates=0, fresh_STA_eligibility_unknown=True),
    selection_reason='Attention paired initial-route failures and zero sharing/owner opportunities on the fresh robot-SDC root motivate a different circuit with historical crossing redundancy. Preserve all outcomes; do not tune BNN wire units or inject fixed targets.',
    full_method_frozen=False, confirmation_batch=False, explicit_SDC=False,
    whole_method_time_cap=None, total_call_cap=None, new_independent_outcomes_completed=0,
    qualification='One known historical reduction_layer physical input on n125 Hybrid-O, not an unseen holdout or a new architecture-family claim. Actual fresh route/root/STA must determine applicability; historical 268 scopes are not prospective successful repairs. Two fixed-dev03 arms share native convergence, owner scope, engineering and acceptance/terminal rules; only domain/release flags differ. Fresh routing and graph indexes are inside each measured method. Physical packaging/admission is outside, as in other portable pairs. No historical routed tree input. Combined domain+release does not isolate either mechanism. No external application requirement or statistical/interleaved timing claim. Existing queues and rules unchanged; append after domain engineering; normal failures/no-gain/worse retained.')
write(root / 'plan.json', plan)
write(root / 'preflight.json', dict(passed=True, native_calls_new=0, large_input_bytes_copied=0,
    large_input_rehashes=0, deferred_physical_admission=True, runtime_admission_executed=False,
    independent_runtime_already_packaged=str(runtime), package_revision=package['component_revision'],
    matching_two_arm_route_commands=True, treatment_only_flags_differ=True,
    predecessor_verified_live=live, scripts_compile=True,
    plan_sha256=sha(root / 'plan.json'),
    qualification='Registration/configuration checks only. Full digest verification, physical copies and guarded admission intentionally wait for the existing serial slot; no claim that native execution or this input admission already passed.'))
print(dict(registered=True, roles=2, circuit='reduction_layer', native_calls_new=0,
           deferred_input_bytes=sum(row['bytes'] for row in copies.values())), flush=True)
