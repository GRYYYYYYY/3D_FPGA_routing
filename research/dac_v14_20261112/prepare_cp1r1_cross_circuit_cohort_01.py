"""Preserve original prospective input selection; change only release/output identity."""
import copy
import json
import subprocess
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from cp1r1_confirmation_cohort_v1 import ROOT,confirmation_arguments,environment

home=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home')
old_root=D/'cp1_cross_circuit_cohort_01'
original=read(old_root/'plan.json')
old_release=Path(original['release'])
release=home/'confirmation_releases/current_sta_cp1r1'
old_workspace=home/'confirmation_workspaces/cp1_cross_circuit_01'
workspace=home/'confirmation_workspaces/cp1r1_cross_circuit_01'
assert read(D/'confirmation_release_cp1r1_01/completion.json')['passed']
assert not ROOT.exists() and not workspace.exists()
ROOT.mkdir();workspace.mkdir()

def relocate(v):
    if isinstance(v,str):return v.replace(str(old_workspace),str(workspace)).replace(str(old_release),str(release))
    if isinstance(v,list):return [relocate(x) for x in v]
    if isinstance(v,dict):return {relocate(k):relocate(x) for k,x in v.items()}
    return v

plan=copy.deepcopy(original)
plan.update(release=str(release),release_manifest_sha256=sha(release/'release_manifest.json'),
    contract_sha256=sha(release/'contract.json'),predecessor=str(D/'execution_reconciliation_20261116_01'),
    original_unexecuted_plan=str(old_root/'plan.json'),original_unexecuted_plan_sha256=sha(old_root/'plan.json'),
    registered_before_new_CP1r1_outcomes=True,
    qualification='Same prospectively selected circuit/placement inputs as unexecuted CP1 cohort. New release CP1r1 only fixes disappeared-proc handling; algorithm and rules unchanged. Original cohort/receipts preserved. No previous arm or failed attempt repeated. No result inferred from source equivalence. Full paired checks and failed outcomes retained.')
bound=original['source_sha256'].copy()
inputs=[];checks={}
for old_item in original['inputs']:
    old=Path(old_item['workspace'])
    assert not (old/'provisioning.json').exists() and all(not (old/a).exists() for a in ['native','domain'])
    item=relocate(old_item);w=Path(item['workspace']);w.mkdir()
    for name in ['packing_manifest.json','phase_runtime.json','native_config.json','domain_config.json']:
        value=relocate(read(old/name))
        if name.endswith('_config.json'):
            value['input_sha256'][str(release/'release_manifest.json')]=sha(release/'release_manifest.json')
            value['input_sha256'][str(release/'contract.json')]=sha(release/'contract.json')
            # Provenance bytes remain exact; only its declared path changes.
        write(w/name,value)
        if name=='packing_manifest.json':(w/name).write_bytes((old/name).read_bytes())
        bound[str(w/name)]=sha(w/name)
        (ROOT/(item['id']+'_'+name)).write_bytes((w/name).read_bytes())
    assert item['physical_identity']==old_item['physical_identity']
    a=subprocess.run(['/usr/bin/python3',str(release/'confirmation.py'),'check',*confirmation_arguments(plan,item)],cwd=release,env=environment(),capture_output=True,text=True,timeout=120)
    (w/'registration_admission.stdout').write_text(a.stdout);(w/'registration_admission.stderr').write_text(a.stderr)
    assert a.returncode==0,a.stderr
    checks[item['id']]=json.loads(a.stdout)
    assert checks[item['id']]['passed'] and checks[item['id']]['release_id']=='current_sta_cp1r1'
    inputs.append(item)
scripts=[Path(__file__).resolve(),D/'queue_cp1r1_cross_circuit_cohort_01.py',D/'cp1r1_confirmation_cohort_v1.py']
for p in scripts:compile(p.read_text(),str(p),'exec')
for p in [*scripts,release/'release_manifest.json',release/'contract.json',old_root/'plan.json',D/'execution_reconciliation_20261116_01/completion.json',D/'confirmation_release_cp1r1_01/completion.json']:
    bound[str(p)]=sha(p)
plan['source_sha256']=bound;plan['inputs']=inputs
write(ROOT/'plan.json',plan)
write(ROOT/'preflight.json',dict(passed=True,actual_frozen_checker_passed=checks,
    configuration_inputs=2,registered_roles=4,new_native_calls=0,
    original_input_selection_preserved=True,algorithm_rule_changes=0,
    large_graph_or_packing_copies=0,large_physical_provisioning_deferred=True,
    plan_sha256=sha(ROOT/'plan.json')))
print(dict(passed=True,inputs=2,roles=4,release='current_sta_cp1r1',native_calls_new=0))
