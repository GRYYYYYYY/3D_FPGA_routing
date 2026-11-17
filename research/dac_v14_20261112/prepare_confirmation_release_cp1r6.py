"""Repair only the missing report declaration; no routing or acceptance changes."""
import ast,copy,difflib,fcntl,hashlib,json,math,os,shutil,time
from pathlib import Path
from datetime import datetime,timezone
D=Path(__file__).resolve().parent
HOME_ROOT=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home')
OLD=HOME_ROOT/'confirmation_releases/current_sta_cp1r5';NEW=HOME_ROOT/'confirmation_releases/current_sta_cp1r6';OUT=D/'confirmation_release_cp1r6_01'
NAME='verify_complete_unified_method_v1.py'
BEFORE="clock_and_IO_spec=config['explicit_sdc_spec']"
AFTER="clock_and_IO_spec=dict(source='actual SHA256-bound SDC text',text=sdc.read_text(),interpretation='Native constraint echo is authoritative; no unstated IO delays or external application requirements inferred')"
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def run_dir(s):
 s=Path(s);v=read(s/'completion.json');return Path(v['run'])
def main():
 start=time.monotonic();OUT.mkdir(exist_ok=False);old=read(OLD/'release_manifest.json')
 sources=[Path(__file__).resolve(),OLD/'release_manifest.json',OLD/'contract.json',OLD/'runtime'/NAME,D/'FRISC_sdc_readonly_02/admission_decision.json']
 write(OUT/'plan.json',dict(registered_at=datetime.now(timezone.utc).isoformat(),parent='current_sta_cp1r5',only_runtime_change='SDC report expression derives actual bound file text; strict config keys retained',original_assertions_preserved=88,new_native_or_STA_calls=0,source_sha256={str(p):sha(p) for p in sources}))
 lock=(D/'critical_scope_runner.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert all(sha(OLD/n)==h for n,h in old['files_sha256'].items())
 text=(OLD/'runtime'/NAME).read_text();assert text.count(BEFORE)==1;new=text.replace(BEFORE,AFTER);assert new.replace(AFTER,BEFORE)==text
 oldast=ast.parse(text);newast=ast.parse(new)
 asserts=lambda t:[ast.dump(n) for n in ast.walk(t) if isinstance(n,ast.Assert)]
 assert asserts(oldast)==asserts(newast) and len(asserts(newast))==88
 block=next(n for n in newast.body if isinstance(n,ast.If) and "'--sdc_file'" in ast.unparse(n.test))
 code=compile(ast.Module(body=[block],type_ignores=[]),NAME,'exec');rows=[];guards=[]
 for arm in ['native','domain']:
  case=Path(read(D/'cp1r5_frisc_pair_01/frisc_results.json')[arm]['case']);config=read(case/'config.json');original=read(D/f'FRISC_sdc_readonly_02/supplement/cases/frisc/{arm}/replayed_verifier/completion.json')
  states={k:Path(original[v]) for k,v in [('initial','initial_state'),('resource_final','resource_final_state'),('handoff','resource_policy_final_state'),('final','final_state')]}
  def vector(s):return read(Path(s)/'endpoint_vector.json')
  env=dict(config=config,Path=Path,read=read,sha=sha,run_dir=run_dir,vector=vector,math=math,files=[],sdc_result=None,**states)
  exec(code,env);result=env['sdc_result'];sdc=Path(config['route_command'][config['route_command'].index('--sdc_file')+1])
  assert result['clock_and_IO_spec']['text']==sdc.read_text();assert result['sha256']==sha(sdc)
  assert result['observed_final_component_counts']==original['explicit_SDC_result']['observed_final_component_counts']
  rows.append(dict(arm=arm,result=result,states={k:str(v) for k,v in states.items()}))
  bad=copy.deepcopy(config);bad['input_sha256'][str(sdc)]='0'*64
  def bad_read(p):
   v=read(p)
   if Path(p).name=='manifest.json':
    v=copy.deepcopy(v);c=v['command'];i=c.index('--sdc_file');del c[i:i+2]
   return v
  def bad_vector(s):return {**vector(s),'constraints_sha256':'0'*64}
  for label,patch in [('changed_SDC_digest',dict(config=bad)),('missing_SDC_native_command',dict(read=bad_read)),('changed_constraint_echo_digest',dict(vector=bad_vector))]:
   mutant={**env,**patch,'files':[],'sdc_result':None}
   try:exec(code,mutant)
   except AssertionError:guards.append(dict(arm=arm,mutation=label,rejected=True))
   else:raise AssertionError(label+' not rejected')
 # Exact same code on an actual non-SDC configuration; no branch/read is entered.
 elliptic=read(D/'cp1r5_elliptic_pair_01/elliptic_results.json');case=Path(elliptic['native']['case']);config=read(case/'config.json');assert '--sdc_file' not in config['route_command']
 env=dict(config=config,sdc_result=None);exec(code,env);assert env['sdc_result'] is None
 validation=dict(passed=True,all88_original_assertions_byte_AST_identical=True,actual_SDC_arms=rows,adversarial_original_gates=guards,actual_no_SDC_branch_unchanged=True,new_native_or_STA_calls=0,whole_arm_replay=False,qualification='Exact report block on existing admitted artifacts; tests validate software/report compatibility, not new complete-method confirmation or new scientific quality.')
 write(OUT/'checker_validation.json',validation);(OUT/'checker.diff').write_text(''.join(difflib.unified_diff(text.splitlines(True),new.splitlines(True),fromfile='CP1r5',tofile='CP1r6')))
 assert not NEW.exists();shutil.copytree(OLD,NEW,copy_function=shutil.copyfile,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for p in [NEW,NEW/'runtime']:p.chmod(0o755)
 (NEW/'runtime'/NAME).write_text(new)
 artifact=read(OLD/'runtime/artifact_manifest.json');artifact['sha256'][NAME]=sha(NEW/'runtime'/NAME);artifact['component_revision']='complete_method_cp1r6_SDC_report_only';artifact['qualification']='CP1r5 algorithm unchanged; actual bound SDC text replaces unavailable report-only config key. All88 original assertions unchanged.';write(NEW/'runtime/artifact_manifest.json',artifact)
 changed=[n for n,h in old['files_sha256'].items() if n.startswith('runtime/') and sha(NEW/n)!=h];assert set(changed)=={'runtime/'+NAME,'runtime/artifact_manifest.json'}
 entry=(OLD/'confirmation.py').read_text();assert entry.count("m['release_id']=='current_sta_cp1r5'")==1;(NEW/'confirmation.py').write_text(entry.replace("m['release_id']=='current_sta_cp1r5'","m['release_id']=='current_sta_cp1r6'"))
 contract=read(OLD/'contract.json');contract.update(release_id='current_sta_cp1r6',internal_compatibility_tag='CP1r5 algorithms; report-only actual bound SDC text, no new config fields.',current_execution_boundary='Exact SDC report block validated on both frisc arms and no-SDC branch plus6 original-gate negatives. Prospective full confirmation pending.');write(NEW/'contract.json',contract)
 for k,v in read(OLD/'contract.json').items():
  if k not in ['release_id','internal_compatibility_tag','current_execution_boundary']:assert contract[k]==v
 inv=read(OLD/'dependency_inventory.json');inv['runtime_tree_sha256']={str(p.relative_to(NEW/'runtime')):sha(p) for p in (NEW/'runtime').rglob('*') if p.is_file()};write(NEW/'dependency_inventory.json',inv)
 evidence=dict(parent_manifest_sha256=sha(OLD/'release_manifest.json'),checker_validation_sha256=sha(OUT/'checker_validation.json'),changed_runtime_files=changed,algorithm_and_all_assertions_unchanged=True,new_native_or_STA_calls=0,confirmation_results_available=False,original_failures_unchanged=True)
 write(NEW/'execution_evidence.json',evidence);write(NEW/'SDC_report_revision.json',evidence)
 (NEW/'README.md').write_text('# CP1r6: bound SDC report declaration\n\nSeparate frozen CP1r5 successor. Only the independent report expression changes: emit actual SHA256-bound SDC text rather than a forbidden missing configuration field. Native constraints echoes and all88 original assertions remain authoritative. No I/O constraints or external application target is invented. All algorithms, native binaries, scopes, budgets, acceptance and terminal selection are unchanged. Original Frisc failures remain. This checker validation is not a new complete confirmation.\n')
 # Historical freeze receipt is kept as inherited provenance; this revision has its own receipt below.
 for n,mode in old['executable_modes'].items():(NEW/n).chmod(mode)
 manifest={**old,'release_id':'current_sta_cp1r6','parent_release_manifest_sha256':sha(OLD/'release_manifest.json'),'changed_runtime_files':changed,'added_runtime_files':[],'confirmation_results_available':False,'files_sha256':{str(p.relative_to(NEW)):sha(p) for p in sorted(NEW.rglob('*')) if p.is_file() and p.name!='release_manifest.json'}}
 write(NEW/'release_manifest.json',manifest);assert all(sha(NEW/n)==h for n,h in manifest['files_sha256'].items());assert all(sha(OLD/n)==h for n,h in old['files_sha256'].items())
 for name in ['release_manifest.json','contract.json','SDC_report_revision.json','execution_evidence.json','README.md']:shutil.copyfile(NEW/name,OUT/name)
 for p in sorted(NEW.rglob('*'),key=lambda p:len(p.parts),reverse=True):p.chmod(0o555 if p.is_dir() else old['executable_modes'].get(str(p.relative_to(NEW)),0o444))
 NEW.chmod(0o555)
 write(OUT/'completion.json',dict(passed=True,release=str(NEW),release_manifest_sha256=sha(NEW/'release_manifest.json'),old_CP1r5_preserved=True,changed_runtime_files=changed,algorithm_fixed_configuration_unchanged=True,new_native_or_STA_calls=0,complete_freeze_scope_seconds=time.monotonic()-start,public_reconstruction_pending=True,complete_confirmation_pending=True,source_sha256=read(OUT/'plan.json')['source_sha256']))
 print(dict(passed=True,original_assertions=88,negative_guards=len(guards),changed_runtime_files=changed,release=str(NEW)))
if __name__=='__main__':main()
