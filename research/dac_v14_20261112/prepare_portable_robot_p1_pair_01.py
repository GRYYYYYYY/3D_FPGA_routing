"""Register a different actual robot packing/placement under unchanged standalone dev03."""
import copy,os,shutil,subprocess
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
root=D/'portable_robot_p1_pair_01';root.mkdir(exist_ok=False)
home=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces');w=home/'robot_p1_pair_01';w.mkdir(exist_ok=False)
prior=home/'whole_method_01';runtime=prior/'runtime'
name='heldout_robot_rl_s21_hybrid_o_n60_w100_p1_a0'
row=next(r for r in read(D/'confirmation_input_inventory_01/inputs.json') if r['name']==name)
source=Path(row['source_manifest']).parent;m=read(source/'manifest.json');original_command=m['command']
screen=D/'structural_input_screen_01'/name/'completion.json';diagnostic=read(screen)
assert diagnostic['passed'] and diagnostic['status']=='legal_historical_root_structural_screen'
spec=read(prior/'phase_runtime.json');paths=dict(architecture=Path(original_command[1]),circuit=Path(original_command[2]),graph=Path(original_command[original_command.index('--read_rr_graph')+1]),packed=source/'packed.net',placement=source/'placed.place')
originals={}
for key,path in paths.items():
    dest=w/'inputs'/(key+path.suffix);dest.parent.mkdir(exist_ok=True);shutil.copy2(path,dest)
    assert sha(dest)==sha(path);originals[str(path)]=sha(path);paths[key]=dest
assert sha(paths['packed'])==row['packing_sha256'] and sha(paths['placement'])==row['placement_bytes_sha256']
spec['physical_files']={key:dict(path=str(path),sha256=sha(path)) for key,path in paths.items()}
spec.pop('full_graph_cache_completion_sha256',None);phase=w/'phase_runtime.json';write(phase,spec)
template=read(prior/'config.json');command=list(template['route_command']);command[1:3]=[str(paths['architecture']),str(paths['circuit'])]
for flag,key in [('--read_rr_graph','graph'),('--net_file','packed'),('--place_file','placement')]:command[command.index(flag)+1]=str(paths[key])
for flag in ['--device','--route_chan_width','--seed']:command[command.index(flag)+1]=original_command[original_command.index(flag)+1]
command[command.index('--route_file')+1]=str(w/'UNCREATED_ROUTE_OUTPUT')
assert '--sdc_file' not in command and not Path(command[command.index('--route_file')+1]).exists()
cases={}
for arm in ['native','domain']:
    cfg=copy.deepcopy(template);cfg.update(route_command=command,phase_runtime_config=str(phase),domain_mode='unrestricted' if arm=='native' else 'paired',domain_feedback=arm=='domain')
    cfg['input_sha256']={r['path']:r['sha256'] for group in ['physical_files','phase_binaries','query_engines','query_validations'] for r in spec[group].values()}
    target=w/(arm+'_config.json');write(target,cfg);cases[arm]=str(target)
native,domain=[read(cases[arm]) for arm in ['native','domain']]
assert {k for k in native if native[k]!=domain[k]}=={'domain_mode','domain_feedback'}
# Actual route-command admission without starting either arm or building indexes.
helper=w/'admit_pair.py';helper.write_text('''import sys
from pathlib import Path
from retained_prefix_workflow import read,write,sha
from run_complete_unified_resource_flow_v1 import admit_route
from timing_runtime import activate
w=Path(sys.argv[1]);rows=[]
for arm in ['native','domain']:
 c=read(w/(arm+'_config.json'));cfg,physical,binaries,files=admit_route(c,Path(c['phase_runtime_config']));activate(c['phase_runtime_config'])
 assert c['cache_mode']=='joint_build_inside_flow' and not c['initial_route_imported'] and not c['external_history_allowed']
 assert c['owner_escalation'] and c['owner_domain_mode']=='unrestricted_in_both_arms'
 rows.append(dict(arm=arm,route_command=c['route_command'],physical_sha256={key:sha(path) for key,path in physical.items()}))
assert rows[0]['route_command']==rows[1]['route_command'] and rows[0]['physical_sha256']==rows[1]['physical_sha256']
write(w/'admission.json',dict(passed=True,rows=rows,native_calls_new=0))
''')
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')};env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
cmd=['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(helper),str(w)]
with (root/'admission.log').open('x') as log:r=subprocess.run(cmd,cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
assert r.returncode==0 and read(w/'admission.json')['passed']
files=[p for p in runtime.rglob('*') if p.is_file()]
files += [Path(r['path']) for group in ['physical_files','phase_binaries','query_engines','query_validations'] for r in spec[group].values()]
files += [phase,helper,w/'admission.json',*map(Path,cases.values()),screen,Path(__file__).resolve(),D/'queue_portable_robot_p1_pair_01.py',D/'run_portable_robot_p1_pair_01.py',D/'compare_portable_robot_p1_pair_01.py']
write(root/'plan.json',dict(passed=True,registered_before_new_method_outcomes=True,workspace=str(w),runtime=str(runtime),predecessor=str(D/'robot_owner_scope_pair_01/queue'),requires_successful_whole_method_check=True,fixed_order=['native','domain'],cases=cases,question='Does the unchanged complete dev03 method preserve legality and improve timing/resource/cost tradeoffs on a distinct robot packing/placement with prior capacity obstructions?',physical_change='packing_and_actual_placement_both_differ_from_modern_robot_p0',whole_method_prerequisite=str(D/'standalone_whole_method_check_01/queue'),source_sha256={str(f):sha(f) for f in files},original_physical_inputs=originals,physical_identity=row,structural_prior=dict(sharing_scopes=diagnostic['counts']['structural_sharing_scopes'],sharing_nets=diagnostic['counts']['structural_sharing_nets'],owner_certificates=diagnostic['counts']['supported_owner_escape_certificates'],STA_eligibility_unknown=True),package_manifest_sha256=sha(runtime/'artifact_manifest.json'),full_method_frozen=False,confirmation_batch=False,whole_method_time_cap=None,total_call_cap=None,explicit_SDC=False,new_independent_outcomes_completed=0,qualification='Complete portable serial-method development pair on robot_rl p1, with different actual packing and placement from the completed modern p0 robot input. This is a distinct physical start, not another seed on the same tree; packing and placement change together, so no placement-only causal claim. Historical packing/placement and structural root are known development evidence, not unseen holdout. Both roles start fresh routing and joint graph construction, use equal native convergence/owner scope/engineering and differ only in domain/release flags. The old routed tree is not an execution input. The historical p1 root has43sharing scopes and30supported owner-obstruction certificates; fresh routing may change eligibility. Current generic selectors choose all mechanisms; no target net is injected. This whole-method pair does not isolate domain, release or owner effects. No externally required timing closure or statistical speedup claim; retain every failed/no-gain/worse role.'))
print(dict(registered=True,circuit=row['circuit'],roles=2,structural_scopes=diagnostic['counts']['structural_sharing_scopes'],native_calls_new=0),flush=True)
