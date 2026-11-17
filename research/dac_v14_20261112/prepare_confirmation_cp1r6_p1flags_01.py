"""Freeze a parser-only CP1r6 variant; all routing and policies stay byte-identical."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,shutil,time
D=Path(__file__).resolve().parent;HOME=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home');OLD=HOME/'confirmation_releases/current_sta_cp1r6';NEW=HOME/'confirmation_releases/current_sta_cp1r6_p1flags';OUT=D/'confirmation_release_cp1r6_p1flags_01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x);return x
start=time.monotonic();assert not NEW.exists() and not OUT.exists();base=read(OLD/'release_manifest.json');assert base['release_id']=='current_sta_cp1r6' and all(sha(OLD/n)==h for n,h in base['files_sha256'].items());source=(OLD/'confirmation.py').read_text();a="if key in ['--route','--analysis','--pack','--place']:result[key]=None;i+=1";b="if key in ['--route','--analysis','--pack','--place','--partition_post_pack']:result[key]=None;i+=1";assert source.count(a)==1
shutil.copytree(OLD,NEW,symlinks=True);entry=NEW/'confirmation.py';entry.write_text(source.replace(a,b));assert entry.read_text().replace(b,a)==source
new=read(NEW/'release_manifest.json');assert new==base;new['files_sha256']['confirmation.py']=sha(entry);new['variant_id']='current_sta_cp1r6_p1flags';new['variant_description']='Only recognize actual --partition_post_pack as a valueless provenance flag; unchanged route controller, contract, policies, numerical budgets and terminal selection.';new['variant_parent_manifest_sha256']=sha(OLD/'release_manifest.json');write(NEW/'release_manifest.json',new)
for n,h in base['files_sha256'].items():
 if n!='confirmation.py':assert sha(NEW/n)==h
assert (OLD/'contract.json').read_bytes()==(NEW/'contract.json').read_bytes()
for name,mode in base['executable_modes'].items():assert (NEW/name).stat().st_mode & 0o777==mode
orig=load(OLD/'confirmation.py','old_confirm');fixed=load(entry,'p1_confirm');p0=read(D/'VTR_s38417_input_01/place_01/registration.json')['command'];p1=read(D/'VTR_diffeq_p1_input_02/place_01/registration.json')['command'];assert orig.options(p0)==fixed.options(p0);parsed=fixed.options(p1);assert '--partition_post_pack' in parsed and parsed['--partition_post_pack'] is None
try:orig.options(p1)
except AssertionError:pass
else:raise AssertionError('Parent must retain original unsupported-flag failure')
for bad in [p0+['--seed','3'],p0+['--synthetic_missing_value']]:
 for fn in [orig.options,fixed.options]:
  try:fn(bad)
  except AssertionError:pass
  else:raise AssertionError('Duplicate/missing value guard changed')
OUT.mkdir();write(OUT/'completion.json',dict(passed=True,status='parser_only_variant_frozen',base_release=str(OLD),variant_release=str(NEW),base_manifest_sha256=sha(OLD/'release_manifest.json'),variant_manifest_sha256=sha(NEW/'release_manifest.json'),contract_sha256=sha(NEW/'contract.json'),all_other_release_files_byte_identical=True,exact_reversible_patch=True,existing_P0_options_equal=True,actual_P1_valueless_flag_parsed=True,parent_P1_rejection_preserved=True,duplicate_and_missing_guards_preserved=True,native_or_STA_calls_new=0,complete_preparation_seconds=time.monotonic()-start,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),OLD/'release_manifest.json',OLD/'confirmation.py',NEW/'release_manifest.json',NEW/'confirmation.py',NEW/'contract.json',D/'VTR_s38417_input_01/place_01/registration.json',D/'VTR_diffeq_p1_input_02/place_01/registration.json']},qualification='Only provenance argument parsing differs; release_id stays the legacy contract ID but variant_id and package manifest uniquely identify this new frozen package. No original release or prior failure changed. New scientific results still need actual independent frozen gates.'))
print(json.dumps(dict(passed=True,variant=str(NEW),files_verified=len(base['files_sha256']))))
