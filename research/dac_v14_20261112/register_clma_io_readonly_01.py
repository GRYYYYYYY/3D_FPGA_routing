"""Bind existing admission stages and relocated entry before new confirmation."""
from pathlib import Path
import json,hashlib,subprocess,datetime
D=Path(__file__).resolve().parent;C=D/'cp1r6_clma_io_pair_01';B=D/'CLMA_IO_complete_admission_01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
plan=read(C/'plan.json');release=Path(plan['release']);home=release.parents[1];restored=home/'confirmation_releases/cp1r6_public_source_restore_01/rebuilt';dest=restored.parent/'clma_io_input_admission';dest.mkdir(exist_ok=False)
item=plan['inputs'][0];provenance=dest/'packing_manifest.json';provenance.write_bytes(Path(item['packing_manifest']).read_bytes())
for arm in ['native','domain']:
 c=read(item['configs'][arm]);bindings=c['input_sha256'];bindings[str(provenance)]=bindings.pop(item['packing_manifest'])
 for name in ['release_manifest.json','contract.json']:bindings[str(restored/name)]=bindings.pop(str(release/name))
 write(dest/(arm+'.json'),c)
cmd=['/usr/bin/python3',str(restored/'confirmation.py'),'check','--native',str(dest/'native.json'),'--domain',str(dest/'domain.json'),'--packing-manifest',str(provenance),'--forbid-prefix',str(D.parents[1])]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=120);assert r.returncode==0,r.stderr;check=json.loads(r.stdout);assert check['passed'];receipt=D/'confirmation_release_cp1r6_01/clma_io_relocated_admission.json';write(receipt,dict(passed=True,actual_relocated_admission=check,command=cmd,new_native_or_STA_calls=0))
plan['source_sha256'][str(receipt)]=sha(receipt);write(C/'plan.json',plan)
old=read(D/'FRISC_complete_admission_01/plan.json');B.mkdir(exist_ok=False)
files=[Path(p) for p in old['source_sha256']]
files += [Path(__file__).resolve(),D/'admit_cp1r6_clma_io_base_01.py',D/'admit_cp1r6_clma_io_pair_01.py',D/'queue_clma_io_admission_01.py',D/'cp1r6_clma_io_cohort_01.py',D/'run_cp1r6_clma_io_pair_01.py',C/'plan.json',receipt,release/'release_manifest.json',release/'runtime/verify_complete_unified_method_v1.py']
targets={arm:dict(input='clma_io',arm=arm,case=str(Path(item['workspace'])/arm),config=item['configs'][arm],config_sha256=sha(item['configs'][arm])) for arm in ['native','domain']}
new={**old,'release':str(release),'release_manifest_sha256':sha(release/'release_manifest.json'),'registered_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'predecessor':str(C/'queue'),'targets':targets,'source_sha256':{str(p):sha(p) for p in files},'qualification':'Same original success prerequisite and byte/request/FULL/STA/vector/physical/state-chain/pair gates; name-only adaptation to new clma_io input and CP1r6 report-only successor. Keep failures null and preserve original receipts; no automatic retries or new audit framework.'}
write(B/'plan.json',new);print(dict(passed=True,relocated_entry=True,registered_stages=new['registered_stages']))
