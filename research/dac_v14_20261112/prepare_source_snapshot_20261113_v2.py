#!/usr/bin/env python3
import os,subprocess
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from prepare_source_snapshot_20261113 import patch_component,run,ROOT,SRC,VENDOR

def main():
    out=ROOT/'patches/snapshot_20261113_verified';out.mkdir(exist_ok=False)
    base=run(['git','-C',str(VENDOR),'rev-parse','HEAD']);lines=run(['git','-C',str(VENDOR),'ls-tree','-r',base]).splitlines();modules={r.split('\t')[1]:r.split()[2] for r in lines if r.startswith('160000 ')}
    baseline=read(D/'baseline_source_sha256.json');paths=set(baseline)|set(read(D/'outside_native_stage_01/binding.json')['source_sha256']);present={p for p in paths if (SRC/p).is_file()};mainpaths={p for p in present if not any(p.startswith(m+'/') for m in modules)}
    result=dict(status='verified_source_snapshot_not_pushed',upstream_url='https://github.com/verilog-to-routing/vtr-verilog-to-routing.git',main=patch_component(VENDOR,SRC,base,mainpaths,out/'architecture_outside_native.patch'),external_dependencies={},source_stage='outside_native_stage_01',stage_binding_sha256=sha(D/'outside_native_stage_01/binding.json'),qualification='Main source overlay independently applied to exact upstream Git tree and target blobs checked. External dependency directories have no own Git metadata; they must not be misreported as checked out at their declared gitlink. They remain on shared storage and are independently content-hashed against original baseline. This snapshot is not an arbitrary-host standalone build bundle.')
    for module,commit in modules.items():
        files=sorted(p for p in present if p.startswith(module+'/'))
        if not files:continue
        hashes={p[len(module)+1:]:sha(SRC/p) for p in files};same_vendor=all(sha(VENDOR/p)==h for p,h in ((p,hashes[p[len(module)+1:]]) for p in files));same_baseline=all(sha(SRC/p)==baseline[p] for p in files)
        assert same_vendor and same_baseline,('dependency_content_changed_needs_separate_patch',module)
        result['external_dependencies'][module]=dict(declared_upstream_gitlink=commit,actual_git_checkout_identity_verified=False,reason='No .git metadata in this vendored dependency directory; parent Git HEAD is not its identity.',files_sha256=hashes,unchanged_from_original_server_source=True,unchanged_from_research_baseline=True,files=len(files),qualification='Hashes prove these files unchanged locally, not equivalence to remote gitlink content. Obtain exact dependency bundle from original shared storage or verify candidate dependency files against this manifest.')
    write(out/'manifest.json',result);write(ROOT/'patches/snapshot_20261113/attempt_failure.json',dict(status='superseded',reason='Attempt treated vendored dependency without .git as a Git submodule; git -C returned parent HEAD. Main patch had passed restoration; corrected verified snapshot records dependency-content scope explicitly.',replacement=str(out.relative_to(ROOT))))
    print(dict(passed=True,main_changed=len(result['main']['changed_files_sha256']),dependency_files=sum(v['files'] for v in result['external_dependencies'].values()),patch_bytes=(out/'architecture_outside_native.patch').stat().st_size))
if __name__=='__main__':main()
