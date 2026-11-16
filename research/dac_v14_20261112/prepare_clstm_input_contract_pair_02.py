"""Reconcile actual pre-routing failures and register a distinct corrected input pair."""
import ast
import copy
import json
import shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from packed_input_contract_v1 import preserve_packed_input_options,classify_initial_failure

oldroot=D/'portable_clstm_pair_01'
old=read(oldroot/'plan.json')
oldw=Path(old['workspace'])
root=D/'clstm_input_contract_pair_02'
root.mkdir(exist_ok=False)
w=oldw.parent/'clstm_input_contract_pair_02'
w.mkdir(exist_ok=False)
historical_manifest=Path(old['physical_identity']['source_manifest'])
historical=read(historical_manifest)['command']
assert historical[historical.index('--merge_constant_generators')+1]=='off'
original=read(oldroot/'comparison.json')
assert original['passed'] and original['verified_legal_roles']==0
files=[historical_manifest,oldroot/'plan.json',oldroot/'comparison.json',Path(__file__).resolve(),D/'packed_input_contract_v1.py']
outcomes={}
cases={}
for arm in ['native','domain']:
    state=oldw/arm/'flow/resource_flow/initial/runs/state'
    m=read(state/'manifest.json');log=(state/'stdout.log').read_text()
    assert sha(state/'stdout.log')==m['outputs']['stdout.log']['sha256']
    assert m['returncode']==1 and not (state/'routed.route').exists()
    assert 'unknown net $undef found in .net file' in log
    assert '--merge_constant_generators' not in m['command']
    category=classify_initial_failure(m,log)
    assert category=='input_netlist_compatibility_failed'
    outcomes[arm]=dict(original_status=original['results'][arm]['status'],corrected_status=category,
        actual_native_returncode=1,native_process_seconds=m['wall_seconds'],
        complete_seconds=original['results'][arm]['complete_seconds'],quality=None,
        routing_started=False,receipt=str(state/'manifest.json'),stdout=str(state/'stdout.log'))
    files += [state/'manifest.json',state/'stdout.log',Path(original['results'][arm]['measurement'])]
    config=copy.deepcopy(read(old['cases'][arm]))
    command,options=preserve_packed_input_options(historical,config['route_command'])
    assert options=={'--merge_constant_generators':'off'}
    config['route_command']=command
    command[command.index('--route_file')+1]=str(w/'UNCREATED_ROUTE_OUTPUT')
    cp=w/(arm+'_config.json');write(cp,config);cases[arm]=str(cp);files.append(cp)
native,domain=[read(cases[a]) for a in ['native','domain']]
assert {k for k in native if native[k]!=domain[k]}=={'domain_mode','domain_feedback'}
runtime=Path(old['runtime'])
tree=ast.parse((runtime/'observe.py').read_text())
optional=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OPTIONAL_FIXED' for t in n.targets))
assert optional['--merge_constant_generators']=='off'
# Execute the actual command-inheritance function in isolation; no graph loading.
tree=ast.parse((runtime/'run_native_scope_policy_v4.py').read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='native_config')
namespace={'json':json,'read':read}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(runtime/'run_native_scope_policy_v4.py'),'exec'),namespace)
fixture=root/'command_fixture';fixture.mkdir();write(fixture/'manifest.json',dict(command=native['route_command']))
inherited=json.loads(namespace['native_config'](fixture))
assert '--route' not in inherited and inherited[inherited.index('--merge_constant_generators')+1]=='off'
try:preserve_packed_input_options(historical,native['route_command']+['--merge_constant_generators','on'])
except AssertionError:pass
else:raise AssertionError('Duplicate/conflicting flags accepted')
assert classify_initial_failure({'returncode':2},'Routing failed.')=='initial_route_failed'
assert classify_initial_failure({'returncode':1},'unexpected crash')=='execution_or_verification_failed'
helper=w/'admit_pair.py';shutil.copy2(oldw/'admit_pair.py',helper)
files += [helper,runtime/'observe.py',runtime/'run_native_scope_policy_v4.py',fixture/'manifest.json']
write(root/'failure_reclassification.json',dict(passed=True,roles=outcomes,source_sha256={str(p):sha(p) for p in files if p not in list(map(Path,cases.values()))},
    cause='Historical packed-netlist input requires explicit merge_constant_generators=off; template dropped it. Actual native error is unknown$undef during packing load, before routing.',
    original_receipts_preserved=True,failed_attempts_retained=2,new_native_calls=0,
    qualification='Input compatibility failure, not routing-congestion failure or negative repair quality. Fix correctness still requires actual execution; no successful route or mechanism benefit inferred.'))
files.append(root/'failure_reclassification.json')
plan=copy.deepcopy(old)
plan.update(workspace=str(w),cases=cases,predecessor=str(D/'portable_reduction_pair_01/queue'),
    whole_method_prerequisite=str(D/'standalone_whole_method_check_01/queue'),
    previous_failed_pair=str(oldroot),input_contract_options=options,
    guarded_admission_helper=str(helper),physical_files_reused_byte_exact=True,
    source_sha256={**old['source_sha256'],**{str(p):sha(p) for p in files},
        **{str(D/n):sha(D/n) for n in ['queue_clstm_input_contract_pair_02.py','run_clstm_input_contract_pair_02.py','compare_clstm_input_contract_pair_02.py']}},
    new_independent_outcomes_completed=0,confirmation_batch=False,full_method_frozen=False,
    qualification='New explicitly corrected input configuration, appended after all registered work. Original failed attempts preserved, no automatic retry or overwritten case. Same dev03 package/binaries/physical bytes and routing/repair rules; both arms inherit historical constant-net interpretation. Complete new costs measured separately. Same known physical input, not a new independent sample; all failure classes retained.')
write(root/'plan.json',plan)
write(root/'preflight.json',dict(passed=True,native_calls=0,large_input_hashes_or_copies=0,
    paired_flags_only=True,historical_input_option_preserved=True,actual_native_config_inheritance_passed=True,
    duplicate_and_failure_classification_checks_passed=True,full_guarded_admission_deferred_until_serial_slot=True,
    package_changed=False,source_sha256={str(root/'plan.json'):sha(root/'plan.json')}))
print(dict(passed=True,original_failures_reclassified=2,new_native_calls=0,registered_corrected_roles=2))
