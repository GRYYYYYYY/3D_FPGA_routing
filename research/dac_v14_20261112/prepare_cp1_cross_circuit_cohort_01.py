"""Preregister two genuinely different circuits on fixed CP1 before any new run."""
import copy,json,subprocess,hashlib
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from cp1_confirmation_cohort_v1 import ROOT,confirmation_arguments,environment,measured_command
release=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1')
workspace=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/cp1_cross_circuit_01')
prior=workspace.parent/'whole_method_01';contract=read(release/'contract.json');manifest=release/'release_manifest.json'
predecessor=D/'robot_p1_input_contract_pair_02/queue';reg=read(predecessor/'registration.json');live=process_identity(reg['pid']);assert live and live['state']!='Z' and live['start_ticks']==reg['start_ticks']
assert not ROOT.exists() and not workspace.exists();ROOT.mkdir();workspace.mkdir()
selections=[('conv_hls','heldout_conv_layer_hls_s21_hybrid_o_n80_w100_p0_a0'),('tpu_ws','heldout_tpu_like.small.ws_s21_hybrid_o_n60_w100_p0_a0')]
inputs=[];bound={};checks={};historical_netlists={r['netlist_sha256'] for r in read(D/'confirmation_input_inventory_01/inputs.json')}
for identifier,name in selections:
    source=D.parents[1]/'results/architecture_flow_20261027/runs'/name;sm=source/'manifest.json';m=read(sm);cmd=m['command'];w=workspace/identifier;w.mkdir()
    paths=dict(architecture=Path(cmd[1]),circuit=Path(cmd[2]),graph=Path(cmd[cmd.index('--read_rr_graph')+1]),packed=source/'packed.net',placement=source/'placed.place')
    hashes={k:m['shared_inputs'][str(paths[k])]['sha256'] for k in ['architecture','circuit','graph']};hashes.update(packed=m['outputs']['packed.net']['sha256'],placement=m['outputs']['placed.place']['sha256'])
    # Bounded identity checks now; large graph/packing copies and hashes wait for the serial slot.
    assert sha(paths['circuit'])==hashes['circuit'] and hashes['circuit'] not in historical_netlists
    assert sha(paths['placement'])==hashes['placement']
    coords=[]
    for line in paths['placement'].read_text().splitlines():
        fields=line.split()
        if len(fields)>=5 and all(x.lstrip('-').isdigit() for x in fields[1:5]):coords.append([fields[0],*map(int,fields[1:5])])
    assert coords;coords.sort();coordinate_sha=hashlib.sha256(json.dumps(coords,separators=(',',':')).encode()).hexdigest()
    provenance=w/'packing_manifest.json';provenance.write_bytes(sm.read_bytes());copies={k:dict(source=str(f),destination=str(w/'inputs'/(k+f.suffix)),sha256=hashes[k],bytes=f.stat().st_size) for k,f in paths.items()}
    spec=read(prior/'phase_runtime.json');spec['physical_files']={k:dict(path=r['destination'],sha256=r['sha256']) for k,r in copies.items()};spec.pop('full_graph_cache_completion_sha256',None);phase=w/'phase_runtime.json';write(phase,spec)
    route=[spec['phase_binaries']['resource']['path'],copies['architecture']['destination'],copies['circuit']['destination'],'--route','--analysis']
    for flag,value in contract['route_fixed_options'].items():route += [flag,value]
    for flag in ['--device','--route_chan_width','--seed']:route += [flag,cmd[cmd.index(flag)+1]]
    for flag,key in [('--read_rr_graph','graph'),('--net_file','packed'),('--place_file','placement')]:route += [flag,copies[key]['destination']]
    route += ['--route_file',str(w/'UNCREATED_ROUTE_OUTPUT')]
    assert '--sdc_file' not in cmd
    if '--merge_constant_generators' in cmd:route += ['--merge_constant_generators',cmd[cmd.index('--merge_constant_generators')+1]]
    config=copy.deepcopy(contract['fixed_configuration']);config.update(route_command=route,phase_runtime_config=str(phase),input_sha256={r['path']:r['sha256'] for group in ['physical_files','phase_binaries','query_engines','query_validations'] for r in spec[group].values()})
    config['input_sha256'].update({str(f):sha(f) for f in [manifest,release/'contract.json',provenance]})
    cases={}
    for arm in ['native','domain']:
        c=copy.deepcopy(config);c.update(domain_mode='unrestricted' if arm=='native' else 'paired',domain_feedback=arm=='domain');path=w/(arm+'_config.json');write(path,c);cases[arm]=str(path);bound[str(path)]=sha(path)
    item=dict(id=identifier,source_name=name,workspace=str(w),configs=cases,packing_manifest=str(provenance),copies=copies,physical_identity=dict(circuit_sha256=hashes['circuit'],architecture_sha256=hashes['architecture'],graph_sha256=hashes['graph'],packed_sha256=hashes['packed'],placement_sha256=hashes['placement'],normalized_coordinates_sha256=coordinate_sha,placed_blocks=len(coords),known_historical_input=True,explicit_SDC=False),historical_baseline_status=m['status'],historical_baseline_returncode=m['returncode'])
    inputs.append(item)
    for f in [sm,provenance,phase]:bound[str(f)]=sha(f)
    for group in ['phase_binaries','query_engines','query_validations']:
        for row in spec[group].values():bound[row['path']]=row['sha256']
    admission=subprocess.run(['/usr/bin/python3',str(release/'confirmation.py'),'check',*confirmation_arguments(dict(release=str(release)),item)],cwd=release,env=environment(),capture_output=True,text=True,timeout=120)
    (w/'registration_admission.stdout').write_text(admission.stdout);(w/'registration_admission.stderr').write_text(admission.stderr);assert admission.returncode==0,admission.stderr
    checks[identifier]=json.loads(admission.stdout);assert checks[identifier]['passed'] and not checks[identifier]['large_input_bytes_checked']
    for arm in ['native','domain']:
        measured=measured_command(dict(release=str(release)),item,arm,w/arm)
        assert str(release/'confirmation.py') in measured and 'run-arm' in measured and str(release/'runtime/measure_process_tree_v1.py') in measured
    for filename in ['native_config.json','domain_config.json','phase_runtime.json','packing_manifest.json']: (ROOT/(identifier+'_'+filename)).write_bytes((w/filename).read_bytes())
scripts=[D/n for n in ['prepare_cp1_cross_circuit_cohort_01.py','queue_cp1_cross_circuit_cohort_01.py','cp1_confirmation_cohort_v1.py','packed_input_contract_v1.py','retained_prefix_workflow.py','seed_census_analysis_pool_v2.py','endpoint_timing_policy_streaming_v2.py']]
for f in scripts:compile(f.read_text(),str(f),'exec')
for f in [*scripts,manifest,release/'contract.json',D/'confirmation_release_cp1_01/completion.json',D/'confirmation_release_cp1_01/archive_relocation.json']:bound[str(f)]=sha(f)
assert len({x['physical_identity']['circuit_sha256'] for x in inputs})==2
plan=dict(passed=True,registered_before_new_CP1_outcomes=True,release=str(release),release_manifest_sha256=sha(manifest),contract_sha256=sha(release/'contract.json'),predecessor=str(predecessor),inputs=inputs,fixed_arm_order=['native','domain'],source_sha256=bound,confirmation_batch=True,large_physical_provisioning_deferred=True,requires_exclusive_serial_slot=True,selection_reason='Different circuit families outside existing current-method input inventory; one historical route success and one failure retained. Physical inputs selected before CP1 outcomes without inspecting new policy results. No success-only filtering or BNN wire tuning.',independence='Two distinct circuit/netlist and placement identities, not seeds of an existing tree. Both are known historical baselines, not unseen holdouts; two arms per input do not double sample count. Hybrid-O n80/n60 sizes are not different architecture families.',explicit_application_timing_claim=False,full_method_time_cap=None,research_total_call_cap=None,qualification='First prospective CP1 confirmation cohort; every full legal output needs original whole-method verifier and actual measured release admission. Initial roots must match before pair attribution. Retain no-cut/no-gain/worse, initial routing failure, invalid input and execution failure separately. Past development is not reclassified. Shared-host serial descriptive times, not interleaved statistical speedup. Existing queues/source rules untouched.')
write(ROOT/'plan.json',plan)
write(ROOT/'preflight.json',dict(passed=True,actual_frozen_checker_passed=checks,configuration_inputs=2,registered_roles=4,new_native_calls=0,large_graph_or_packing_copies=0,large_graph_or_packing_rehashes=0,actual_native_provisioning=False,predecessor_identity=live,plan_sha256=sha(ROOT/'plan.json'),qualification='Actual immutable CP1 checker verifies rule/provenance consistency; physical graph/packing bytes and native compatibility are not yet verified.'))
print(dict(passed=True,inputs=2,roles=4,new_native_calls=0,deferred_copy_bytes=sum(r['bytes'] for item in inputs for r in item['copies'].values())))
