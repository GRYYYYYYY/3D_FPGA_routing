"""Export immutable research stage overlays; independently apply-check each patch."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from prepare_source_snapshot_20261113 import patch_component,run,ROOT,VENDOR

out=ROOT/'patches/snapshot_20261114_verified';out.mkdir(exist_ok=True)
assert not (out/'manifest.json').exists()
base=run(['git','-C',str(VENDOR),'rev-parse','HEAD'])
assert base=='0b912334fdd83bb754b302146ac0d1ec9edc9a0e'
modules={r.split('\t')[1]:r.split()[2] for r in run(['git','-C',str(VENDOR),'ls-tree','-r',base]).splitlines() if r.startswith('160000 ')}
result=dict(passed=True,upstream='https://github.com/verilog-to-routing/vtr-verilog-to-routing.git',
    base_commit=base,stages={},qualification='Each patch applies independently to the stated upstream tree; do not stack these complete overlays or older R1 patches. Runtime binaries/raw routing inputs remain on server. Dependency hashes are local content evidence, not remote gitlink authentication.')
for name in ['resource_domain_stage_01','repair_seed_order_stage_01','native_resource_census_stage_01']:
    stage=D/name;binding=read(stage/'binding.json');manifest=read(stage/'all_source_hashes.json')
    assert sha(stage/'all_source_hashes.json')==binding['all_source_manifest_sha256']
    workspace=Path(read(stage/'registration.json')['workspace'])
    for rel,digest in manifest.items():assert sha(workspace/rel)==digest,(name,rel)
    for rel,digest in binding['source_sha256'].items():assert sha(stage/'src'/rel)==digest
    present={p for p in manifest if not any(p.startswith(m+'/') for m in modules)}
    record=patch_component(VENDOR,workspace,base,present,out/(name+'.patch'))
    record.update(stage_binding_sha256=sha(stage/'binding.json'),original_binary_sha256=binding['binary_sha256'],
        all_source_manifest_sha256=sha(stage/'all_source_hashes.json'),
        external_dependencies={m:dict(declared_gitlink=c,remote_checkout_identity_verified=False,
            files_sha256={p[len(m)+1:]:h for p,h in manifest.items() if p.startswith(m+'/')}) for m,c in modules.items()})
    result['stages'][name]=record
    print(name,len(record['changed_files_sha256']),'changed files, apply check passed',flush=True)
write(out/'manifest.json',result)
