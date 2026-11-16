"""Stage a fixed, independently executable confirmation source; do not relabel old runs."""
import json
import shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

home=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home')
source=home/'confirmation_workspaces/whole_method_01/runtime'
whole=read(D/'standalone_whole_method_check_01/completion.json')
assert whole['passed'] and whole['whole_method_executed_and_verified']
assert read(D/'standalone_transaction_native_check_01/completion.json')['passed']
assert read(D/'standalone_native_observation_equivalence_01/completion.json')['passed']
component=read(D/'standalone_unified_method_component_03.json')
assert sha(source/'artifact_manifest.json')==sha(Path(component['package'])/'artifact_manifest.json')
for name,digest in read(source/'artifact_manifest.json')['sha256'].items():assert sha(source/name)==digest
root=home/'confirmation_releases/current_sta_cp1'
if root.exists():
    assert {p.name for p in root.iterdir()}=={'runtime'}, 'Only resume the exact incomplete source-copy stage'
else:
    root.mkdir(parents=True,exist_ok=False)
    shutil.copytree(source,root/'runtime',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
source_files={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
copied_files={str(p.relative_to(root/'runtime')):sha(p) for p in (root/'runtime').rglob('*') if p.is_file()}
assert copied_files==source_files
assert len([p for p in (root/'runtime').iterdir() if p.is_file()])==116
write(root/'dependency_inventory.json',dict(python='CPython3.10 Linux x86_64',numpy='2.2.6',lxml='6.1.3',
    transitive_runtime_files=len(copied_files),runtime_tree_sha256=copied_files,
    qualification='Copies include numpy,lxml,numpy.libs; not a standard-library-only package. Verified imports use release-local extension modules.'))
shutil.copy2(D/'confirmation_entry_cp1.py',root/'confirmation.py')
shutil.copy2(D/'packed_input_contract_v1.py',root/'packed_input_contract.py')
w=home/'confirmation_workspaces/whole_method_01'
template=read(w/'config.json');phase=read(w/'phase_runtime.json')
excluded={'route_command','phase_runtime_config','input_sha256','domain_mode','domain_feedback'}
fixed={k:v for k,v in template.items() if k not in excluded}
contract=dict(release_id='current_sta_cp1',frozen_for_prospective_confirmation=True,
    internal_compatibility_tag='development_v1 retained byte-exact in inherited runtime; outer release seal identifies future CP1 runs',
    fixed_configuration=fixed,
    route_fixed_options={'--num_workers':'1','--clock_modeling':'ideal','--check_route':'full','--verify_file_digests':'off',
      '--verify_route_file_switch_id':'on','--timing_report_npaths':'10','--max_router_iterations':'200',
      '--routing_failure_predictor':'off','--router_max_convergence_count':'8','--router_reconvergence_cpd_threshold':'1.01'},
    route_input_options=['--device','--route_chan_width','--seed','--read_rr_graph','--net_file','--place_file','--route_file','--sdc_file'],
    native_defaults={'merge_constant_generators':'on'},
    execution_environment=dict(python_major_minor=[3,10],platform='linux',machine='x86_64',numpy='2.2.6',lxml='6.1.3'),
    phase_binary_sha256={k:v['sha256'] for k,v in phase['phase_binaries'].items()},
    query_engine_sha256={k:v['sha256'] for k,v in phase['query_engines'].items()},
    query_validation_sha256={k:v['sha256'] for k,v in phase['query_validations'].items()},
    mechanism_order=[
      'Fresh route from declared physical inputs; initial failure has no legal root.',
      'Current STA/crossing selector: complete slack-eligible sharing cuts, deterministic groups of up to8 distinct nets.',
      'Native unrestricted or domain-first paired search; domain failure releases only affected network inside private transaction.',
      'Complete-group physical/capacity/FULL/STA checks and fixed-root resource acceptance.',
      'On resource-menu closure use capacity/slack owner selector, first3rank windows; unrestricted owner transactions in both arms; accepted owner commits reenter selection.',
      'At resource menu closure apply endpoint-nonregressing wire terminal selection over actual same-flow observations.',
      'Handoff FULL/STA then current critical/tied-path timing portfolio at fraction0.9, fixed absolute limits; final strict timing terminal.'],
    acceptance={'resource':'Root CPD cap, hold nonregression;ceil(root_wire*1.001),root SB/CB; nonincreasing SB/CB with one strict gain.',
      'timing':'Strict complete CPD improvement; wire cap from initial root, SB/CB caps from selected resource handoff, fixed throughout timing.',
      'terminal':'Endpoint-nonregressing wire handoff followed by strict-timing terminal. Never imported historical candidates.',
      'intermediate':'No per-module or per-connection CPD-improvement requirement.'},
    input_contract='Explicit packed-netlist provenance and constant-net interpretation must agree across initial route and all inherited analysis/repair commands. Historical file/seed names do not establish independence.',
    scope='Two-layer edge-encoded architectures; explicit matching physical files/phase binaries. No general CHANZ/multilayer or external application timing claim.',
    outcome_policy='Retain invalid input/load failure separately from routing congestion, legal no-cut, no-gain, tradeoff, worse and verified complete outcomes.',
    cost='Measured run-arm includes release admission plus original complete native command: indexes, route, resource/owner/timing search, rejection, STA, rollback and seals. Input provisioning and separate research verification are not spliced into algorithm time.',
    limits='Original per-child1800s,64GiB memory,80GiB disk reserve remain. No whole-research date/call/matrix stopping condition.',
    confirmation_results_available=False,
    unverified_paths=['Automatic positive owner commit followed by full source reselection and complete timing in one fresh-route execution.',
      'Positive full timing acceptance/rejection feedback in the relocated complete package.',
      'Actual corrected clstm/robot-p1 input execution; existing queues remain separate development versions.',
      'Independent paired confirmation and stable interleaved performance measurements.'])
write(root/'contract.json',contract)
write(root/'binary_inputs.json',{group:phase[group] for group in ['phase_binaries','query_engines','query_validations']})
proofs=[D/'standalone_native_observation_equivalence_01/completion.json',D/'standalone_transaction_native_check_01/completion.json',D/'standalone_whole_method_check_01/completion.json',D/'standalone_unified_method_component_03.json']
write(root/'execution_evidence.json',dict(runtime_manifest_sha256=sha(source/'artifact_manifest.json'),
    evidence_sha256={str(p):sha(p) for p in proofs},
    actual_core_execution=['Outside-project FULL/STA observation equivalent','Outside-project known R1 owner transaction equivalent','Outside-project tiny whole flow complete,0accepted repair'],
    qualification='Actual executed core is copied byte-for-byte. The new release admission wrapper is separately validated. Freezing source/rules does not mean positive mechanism-path or independent performance confirmation; no old result is reclassified as a CP1 confirmation run.'))
(root/'README.md').write_text('''# Current-STA confirmation source CP1

This is a fixed prospective confirmation version, not a completed confirmation cohort. The116-file runtime is byte-identical to the outside-project whole-method execution. Existing development jobs retain their original package and rules. The inherited runtime string `development_v1` is a compatibility tag; `release_manifest.json` and the measured `confirmation_input.json` identify CP1.

Dependencies are CPython3.10 on Linux x86_64, the bundled NumPy2.2.6/lxml6.1.3/shared-library files, Linux process supervision, the exact phase binaries/query executables declared in `binary_inputs.json`, and explicitly provided architecture/RRG/BLIF/packing/placement files. Binaries and large input data are explicit external inputs, not bundled or fetched automatically. Source compilation and packing/placement generation are upstream. No historical project Python imports or hidden state aliases are required.

Use an input directory outside the historical project. Make native/domain configs with exactly the fields in `contract.json`: fixed configuration plus route command, phase-runtime configuration, input SHA256 map and the two arm switches. Native is unrestricted/false, domain is paired/true. Both arms use identical current selectors, owner opportunities and fixed route controls. The route command explicitly disables the failure predictor and fixes8convergences/1.01threshold; device, channel width, seed and physical paths belong to the preregistered input, not per-arm tuning.

Copy the actual provenance manifest whose `outputs.packed.net.sha256` identifies the input packing. Preserve its `--merge_constant_generators off` when present; an omitted flag means the bound native default on. The checker rejects an off-to-default mismatch before native work. Add SHA256 bindings for the release manifest, contract and provenance manifest to both configs' input maps. Physical/binary bytes are fully checked by the original runtime inside the measured command; cheap admission alone is not a byte-integrity or legality proof.

Before preregistering a cohort:

```
python3 confirmation.py check --native INPUT/native.json --domain INPUT/domain.json --packing-manifest INPUT/source_manifest.json --forbid-prefix HISTORICAL_PROJECT
```

Run each arm serially, using a new CASE directory and an external queue's shared execution lock. Do not run both arms concurrently. The exact measured command is:

```
python3 runtime/measure_process_tree_v1.py --output CASE/measurement -- python3 runtime/supervise_method_phase.py --receipt CASE/supervision.json -- python3 confirmation.py run-arm --native INPUT/native.json --domain INPUT/domain.json --packing-manifest INPUT/source_manifest.json --forbid-prefix HISTORICAL_PROJECT --arm native --case CASE
python3 runtime/guarded_entry.py --forbid-prefix HISTORICAL_PROJECT --script runtime/verify_complete_unified_method_v1.py --root CASE
```

Use `--arm domain` and a different CASE for the other arm. Verification is a separate research audit. Preserve every failed command and its complete measured cost. Only complete verified outputs may carry legal quality. Match initial route bodies, full vectors, physical identities and constraints before reporting paired differences. A native/domain pair jointly changes restriction/release and cannot isolate them; separate fixed-scope ablations remain necessary.

Freeze the cohort's input/config/release digests before any outcome. No old development run becomes confirmation merely because its runtime bytes match. Changes after this source freeze require a new release/cohort. Keep no-cut/no-gain/worse/initial-routing outcomes and distinguish input loading errors. Positive owner reentry, positive timing feedback and independent complete benefits remain unconfirmed; consult `contract.json` for exact rules and gaps.
''')
manifest=dict(release_id='current_sta_cp1',status='fixed_confirmation_source',
    runtime_byte_identical_to_executed_dev03=True,runtime_files=116,
    public_evidence_base='9734eee',confirmation_results_available=False,
    files_sha256={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()})
write(root/'release_manifest.json',manifest)
out=D/'confirmation_release_cp1_01';out.mkdir(exist_ok=False)
write(out/'preparation.json',dict(passed=True,release=str(root),runtime_files=116,release_manifest_sha256=sha(root/'release_manifest.json'),
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'confirmation_entry_cp1.py',source/'artifact_manifest.json',*proofs]},
    native_calls_new=0,status='source_staged_not_yet_sealed'))
print(dict(staged=str(root),runtime_files=116,native_calls_new=0))
