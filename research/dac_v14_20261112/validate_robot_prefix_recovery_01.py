"""Actual metadata and negative guards; heavy prefix/STA proof waits for serial slot."""
import ast,copy,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from retained_prefix_workflow import D,read,write,sha

root=D/'robot_p1_prefix_recovery_01';ext=root/'runtime_extension'
runtime=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1r2/runtime')
sys.path[:0]=[str(runtime),str(ext),str(D)]
from recovery_prefix_v1 import compatible_roles,original_envelope,completed_observation_gate
actor=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/robot_p1_input_contract_pair_02/native/flow/resource_flow/repair')
reg=read(actor/'registration.json');checkpoint=read(actor/'current_state.json')
assert checkpoint['accepted_steps']==len(read(actor/'steps.json'))==7
role=read(actor/'round_007/candidate_00/registration.json')['roles']['reuse_off']
worker=actor/'round_007/candidate_00/reuse_off';completion=read(worker/'completion.json');manifest=read(worker/'runs/state/manifest.json');seal=read(worker/'input_seal.json')
args=SimpleNamespace(**{k:reg[k] for k in ['bundle_size','domain_mode','seed_order','domain_feedback','owner_rank_windows']},disable_owner_escalation=not reg['owner_escalation'])
original_envelope(reg,checkpoint,reg['initial_state'],reg['anchor'],reg['resource_limits'],args)
completed_observation_gate(completion,manifest,seal);compatible_roles(role,copy.deepcopy(role))
guards=[]
def reject(name,fn):
    try:fn()
    except AssertionError:guards.append(name);return
    raise AssertionError('Guard did not reject '+name)
for key,value in [('objective','physical_soft'),('seed_order','native'),('domain_failure_release',True),('crossing_reuse_enabled',True),('removed_pins',{})]:
    changed=copy.deepcopy(role);changed[key]=value;reject('role_'+key,lambda c=changed:compatible_roles(role,c))
changed=copy.deepcopy(role);changed['queries']=list(reversed(changed['queries']));assert changed['queries']!=role['queries'];reject('query_order',lambda:compatible_roles(role,changed))
with tempfile.TemporaryDirectory(prefix='prefix-recovery-metadata-') as folder:
    folder=Path(folder);same=folder/'same.txt';same.write_bytes(Path(role['request']).read_bytes());changed=copy.deepcopy(role);changed['request']=str(same);compatible_roles(role,changed)
    same.write_bytes(same.read_bytes()+b'\n');reject('request_bytes',lambda:compatible_roles(role,changed))
for key in ['CPD_s','wirelength','SB_pairs','CB_sources']:
    anchor=dict(reg['anchor']);anchor[key]+=1;reject('original_anchor_'+key,lambda a=anchor:original_envelope(reg,checkpoint,reg['initial_state'],a,reg['resource_limits'],args))
for key in reg['resource_limits']:
    limits=dict(reg['resource_limits']);limits[key]+=1;reject('absolute_limit_'+key,lambda lim=limits:original_envelope(reg,checkpoint,reg['initial_state'],reg['anchor'],lim,args))
for key in completion['checks']:
    if key=='CPD_matches_original':continue
    bad=copy.deepcopy(completion);bad['checks'][key]=False;reject('original_gate_'+key,lambda c=bad:completed_observation_gate(c,manifest,seal))
bad=copy.deepcopy(manifest);bad['status']='timeout';reject('native_timeout',lambda:completed_observation_gate(completion,bad,seal))
reject('input_seal',lambda:completed_observation_gate(completion,manifest,{'passed':False}))
bad=copy.deepcopy(completion);del bad['checks']['inputs_sealed'];reject('missing_input_gate',lambda:completed_observation_gate(bad,manifest,seal))
revisions=read(root/'controller_revision.json')
for name,row in revisions['revisions'].items():
    text=(ext/name).read_text();ast.parse(text);assert sha(ext/name)==row['source_sha256']
    prefix="import os,sys\nsys.path.insert(0,os.environ['H3D_RECOVERY_RUNTIME'])\n";assert text.startswith(prefix);text=text[len(prefix):]
    for old,new in reversed(row['replacements']):assert text.count(new)==1;text=text.replace(new,old)
    assert text==Path(row['parent']).read_text() and sha(row['parent'])==row['parent_sha256']
files=[Path(__file__).resolve(),root/'controller_revision.json',actor/'registration.json',actor/'current_state.json',actor/'steps.json',actor/'attempts.json',worker/'completion.json',worker/'runs/state/manifest.json',worker/'input_seal.json',*ext.glob('*.py')]
write(root/'metadata_validation.json',dict(passed=True,actual_original_prefix_steps=7,actual_metadata_match=True,
    negative_guards=guards,controller_transform_reverses_to_exact_parent=True,new_native_calls=0,
    heavy_full_prefix_and_worker_trace_verification_pending=True,source_sha256={str(f):sha(f) for f in files},
    qualification='Actual recorded role/envelope/worker gates and source transforms tested without graph mapping or STA parsing. Heavy checkpoint/archive/native-trace proof is mandatory inside the registered recovery command before new work; this metadata validation is not execution or behavior-equivalence evidence.'))
print(dict(passed=True,negative_guards=len(guards),prefix_steps=7,new_native_calls=0))
