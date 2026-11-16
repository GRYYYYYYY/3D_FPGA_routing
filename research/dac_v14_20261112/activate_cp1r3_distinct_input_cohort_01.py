"""Seal actual CP1r3 configs before outcomes, only after the registered serial wait."""
import copy,hashlib,json,os,subprocess
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from cp1r3_confirmation_cohort_v1 import ROOT,InputAdmissionError,verify_copy_source,confirmation_arguments,environment
from package_cp1r3_public_source_01 import package

def activate():
    protocol=read(ROOT/'protocol.json')
    assert os.environ.get('H3D_CP1R3_COHORT_SERIAL_OWNER')==str(os.getppid())
    assert all(sha(f)==h for f,h in protocol['source_sha256'].items())
    release=Path(protocol['release']);parent=Path(protocol['parent_release']);manifest=read(release/'release_manifest.json');contract=read(release/'contract.json')
    assert read(D/'confirmation_release_cp1r3_01/completion.json')['passed']
    assert manifest['release_id']=='current_sta_cp1r3' and manifest['parent_release_manifest_sha256']==protocol['parent_release_manifest_sha256']
    assert all(sha(release/n)==h for n,h in manifest['files_sha256'].items())
    original=read(parent/'contract.json')
    for name in protocol['unchanged_contract_fields']:assert contract[name]==original[name],name
    assert manifest['executable_modes']==read(parent/'release_manifest.json')['executable_modes']
    for name,h in protocol['expected_precision_runtime_sha256'].items():assert sha(release/'runtime'/name)==h,name
    assert not (ROOT/'plan.json').exists()
    workspace=Path(protocol['workspace']);workspace.mkdir(exist_ok=False);inputs=[];checks={};bound=dict(protocol['source_sha256'])
    bound[str(ROOT/'protocol.json')]=sha(ROOT/'protocol.json')
    for selected in protocol['selected_inputs']:
        w=workspace/selected['id'];w.mkdir()
        item=dict(id=selected['id'],source_name=selected['source_name'],workspace=str(w),physical_identity=dict(selected['declared_physical_identity']),copies=copy.deepcopy(selected['copies']),purpose=selected['purpose'])
        m=read(selected['source_manifest']);cmd=m['command'];packing=read(selected['packing_manifest_source'])
        assert all(m['outputs'][name]['sha256']==packing['outputs'][name]['sha256'] for name in ['packed.net','placed.place'])
        try:
            # Bounded placement/netlist checks; large graph/packing verification is in provision().
            for key in ['circuit','placement']:verify_copy_source(item['copies'][key]['source'],item['copies'][key])
            coords=[]
            for line in Path(item['copies']['placement']['source']).read_text().splitlines():
                fields=line.split()
                if len(fields)>=5 and all(x.lstrip('-').isdigit() for x in fields[1:5]):coords.append([fields[0],*map(int,fields[1:5])])
            if not coords:raise InputAdmissionError('No block coordinates in selected placement')
            coords.sort();item['physical_identity'].update(normalized_coordinates_sha256=hashlib.sha256(json.dumps(coords,separators=(',',':')).encode()).hexdigest(),placed_blocks=len(coords),known_historical_input=True,explicit_SDC=False)
        except InputAdmissionError as error:
            item['admission_failure']=repr(error);inputs.append(item);write(ROOT/(item['id']+'_activation_admission_failure.json'),dict(passed=False,classifier='physical_input_admission_failed',native_calls=0,error=repr(error)));continue
        provenance=w/'packing_manifest.json';provenance.write_bytes(Path(selected['packing_manifest_source']).read_bytes())
        spec=read(protocol['phase_runtime_template']);spec['physical_files']={k:dict(path=r['destination'],sha256=r['sha256']) for k,r in item['copies'].items()};spec.pop('full_graph_cache_completion_sha256',None)
        phase=w/'phase_runtime.json';write(phase,spec)
        route=[spec['phase_binaries']['resource']['path'],item['copies']['architecture']['destination'],item['copies']['circuit']['destination'],'--route','--analysis']
        for flag,value in contract['route_fixed_options'].items():route += [flag,value]
        for flag in ['--device','--route_chan_width','--seed']:route += [flag,cmd[cmd.index(flag)+1]]
        for flag,key in [('--read_rr_graph','graph'),('--net_file','packed'),('--place_file','placement')]:route += [flag,item['copies'][key]['destination']]
        route += ['--route_file',str(w/'UNCREATED_ROUTE_OUTPUT'),'--merge_constant_generators','off']
        assert '--sdc_file' not in cmd
        config=copy.deepcopy(contract['fixed_configuration']);config.update(route_command=route,phase_runtime_config=str(phase),input_sha256={r['path']:r['sha256'] for group in ['physical_files','phase_binaries','query_engines','query_validations'] for r in spec[group].values()})
        config['input_sha256'].update({str(f):sha(f) for f in [release/'release_manifest.json',release/'contract.json',provenance]})
        cases={}
        for arm in protocol['fixed_arm_order']:
            c=copy.deepcopy(config);c.update(domain_mode='unrestricted' if arm=='native' else 'paired',domain_feedback=arm=='domain')
            path=w/(arm+'_config.json');write(path,c);cases[arm]=str(path);bound[str(path)]=sha(path)
        item.update(configs=cases,packing_manifest=str(provenance));inputs.append(item)
        for f in [phase,provenance]:bound[str(f)]=sha(f)
        for group in ['phase_binaries','query_engines','query_validations']:
            for row in spec[group].values():bound[row['path']]=row['sha256']
        result=subprocess.run(['/usr/bin/python3',str(release/'confirmation.py'),'check',*confirmation_arguments(dict(release=str(release)),item)],cwd=release,env=environment(),capture_output=True,text=True,timeout=120)
        (w/'registration_admission.stdout').write_text(result.stdout);(w/'registration_admission.stderr').write_text(result.stderr)
        assert result.returncode==0,result.stderr;checks[item['id']]=json.loads(result.stdout);assert checks[item['id']]['passed'] and checks[item['id']]['release_id']=='current_sta_cp1r3'
        for name in ['native_config.json','domain_config.json','phase_runtime.json','packing_manifest.json']:(ROOT/(item['id']+'_'+name)).write_bytes((w/name).read_bytes())
    plan=dict(passed=True,registered_before_new_CP1r3_outcomes=True,release=str(release),release_manifest_sha256=sha(release/'release_manifest.json'),contract_sha256=sha(release/'contract.json'),
        workspace=str(workspace),inputs=inputs,fixed_arm_order=protocol['fixed_arm_order'],source_sha256=bound,
        confirmation_batch=True,large_physical_provisioning_deferred=True,requires_exclusive_serial_slot=True,protocol=str(ROOT/'protocol.json'),protocol_sha256=sha(ROOT/'protocol.json'),
        source_runtime_or_algorithm_selected_from_outcomes=False,explicit_application_timing_claim=False,full_method_time_cap=None,research_total_call_cap=None,
        independence=protocol['independence'],qualification='Actual release/config seals are fixed before any CP1r3 role executes. Two distinct historical circuit/netlists plus one known SB-only architecture control; three inputs/six roles are not six samples. No old route or candidate imported. All outcomes retained; no date/call/matrix research stop. Preparation/provisioning and external research verification are separate from complete measured run-arm time.')
    draft=ROOT/'admission_plan.json';write(draft,plan)
    public_receipt=package(plan);assert read(public_receipt)['passed']
    for f in [draft,public_receipt,D/'restore_confirmation_cp1r3_dependencies.py',D/'confirmation_release_cp1r3_01/current_sta_cp1r3_source.tar.gz',release/'release_manifest.json',release/'contract.json',D/'confirmation_release_cp1r3_01/completion.json']:
        bound[str(f)]=sha(f)
    plan['source_sha256']=bound;write(ROOT/'plan.json',plan)
    write(ROOT/'preflight.json',dict(passed=True,actual_frozen_checker=checks,actual_public_reconstruction=True,
        actual_restored_guard_and_worker_imports=True,actual_relocated_admission=bool(checks),
        selected_inputs=3,registered_roles=6,pre_activation_input_failures=sum(bool(i.get('admission_failure')) for i in inputs),
        native_calls_new=0,large_physical_copies_or_graph_rehashes=0,large_graph_and_packing_admission_pending=True,
        plan_sha256=sha(ROOT/'plan.json'),qualification='Actual fixed source/admission checks and publicly reconstructible dependencies precede every role. Large source graph/packing hashes and copies are deferred to per-input provisioning; no native result inferred.'))
    print(dict(passed=True,registered_inputs=3,roles=6,native_calls_new=0,plan=str(ROOT/'plan.json')))

if __name__=='__main__':activate()
