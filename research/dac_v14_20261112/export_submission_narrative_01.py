"""Rebuild a minimal submission source bundle independently of research files."""
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

parent=D/'submission_narrative_02';out=D/'submission_narrative_export_01'
assert not out.exists();proof=read(parent/'verification.json');assert proof['passed'] and proof['pages']==6
assert all(sha(p)==h for p,h in proof['source_sha256'].items())
out.mkdir();source=out/'source';source.mkdir();build=out/'validation_build';build.mkdir()
assets=['main.tex','data/dependency_mechanisms.pdf','data/references.tex']
for name in assets:
    target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((parent/name).read_bytes())
assert (source/'main.tex').read_bytes()==(parent/'main.tex').read_bytes()
tool=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/tools/tectonic-0.16.0/tectonic')
bundle=tool.parent/'cached-paper-bundle'
command=[str(tool),'--bundle',str(bundle),'--only-cached','--untrusted','--keep-logs','--keep-intermediates',
         '--outdir',str(build),'main.tex']
start=time.monotonic()
with (out/'rebuild_stdout.log').open('x') as log:
    result=subprocess.run(command,cwd=source,stdout=log,stderr=subprocess.STDOUT,timeout=120)
write(out/'rebuild_receipt.json',dict(command=command,cwd=str(source),returncode=result.returncode,
    seconds=time.monotonic()-start,tool_sha256=sha(tool),external_toolchain_bundle=str(bundle),
    source_assets={name:sha(source/name) for name in assets},network_used=False))
assert result.returncode==0
from pypdf import PdfReader
original=parent/'build/main.pdf';rebuilt=build/'main.pdf'
left,right=PdfReader(original),PdfReader(rebuilt)
assert len(left.pages)==len(right.pages)==6
assert [(tuple(p.mediabox),p.extract_text()) for p in left.pages]==[(tuple(p.mediabox),p.extract_text()) for p in right.pages]
sys.path.insert(0,'/tmp/peng_pdfium')
import pypdfium2 as pdfium
import numpy as np
old,new=pdfium.PdfDocument(original),pdfium.PdfDocument(rebuilt);render_rows=[]
for i in range(6):
    a=old[i].render(scale=1.5).to_pil();b=new[i].render(scale=1.5).to_pil()
    assert a.size==b.size and a.mode==b.mode
    av,bv=np.asarray(a),np.asarray(b)
    changed=int(np.count_nonzero(np.any(av!=bv,axis=-1)))
    render_rows.append(dict(page=i+1,pixels_changed=changed,render_sha256=hashlib.sha256(av.tobytes()).hexdigest()))
    if changed:
        a.save(out/f'original_page_{i+1}.png');b.save(out/f'rebuilt_page_{i+1}.png')
    assert changed==0,('Rebuild rendering differs',i+1)
log=(build/'main.log').read_text()
assert 'Overfull' not in log and 'undefined references' not in log.lower()
manifest={name:sha(source/name) for name in assets}
write(source/'source_manifest.json',dict(source_sha256=manifest,public_commit='bd949b916c5139c2bab799da35935b9decbf5a53',
    parent_verification_sha256=sha(parent/'verification.json'),original_PDF_sha256=sha(original),
    paper_asset_scope='All manuscript-specific LaTeX/figure/reference inputs. IEEEtran/fonts/packages remain external toolchain dependencies.'))
shutil.copy2(original,source/'candidate.pdf')
(source/'README.txt').write_text('''Dependency-Aware Reconstruction for Budgeted Cross-Layer Resource Release in 3D FPGA Routing

This bundle preserves the verified six-page narrative candidate. It changes no
method, numerical result, experimental rule or contribution boundary.

Manuscript-specific build inputs: main.tex, data/dependency_mechanisms.pdf,
data/references.tex. Requires IEEEtran and standard amsmath/amssymb/graphicx/url
and fontenc packages through a TeX toolchain. A cached Tectonic0.16.0 rebuild
in an independent directory passed six-page text and rendered-pixel equality.
External toolchain dependencies are not bundled.

Build from this directory using:
  mkdir -p build
  tectonic --untrusted --outdir build main.tex
With an already provisioned bundle, add --bundle PATH --only-cached.
candidate.pdf is the original verified PDF; validation_build is not a new paper.

The separate research repository retains all experimental receipts, failures,
relocated rows and supplementary evidence at public commit:
  bd949b916c5139c2bab799da35935b9decbf5a53
  research/dac_v14_20261112/submission_narrative_02/
Later progress does not alter this export. Incomplete CP1r3, cost-baseline or
historical recovery results supply no benefit claims in this candidate.
''')
archive=out/'dependency_reconstruction_candidate.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
    for path in sorted(source.rglob('*')):
        if not path.is_file():continue
        name=str(path.relative_to(source));info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.external_attr=0o100644<<16
        info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,path.read_bytes())
with zipfile.ZipFile(archive) as z:
    assert set(z.namelist())=={str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()}
    for name in z.namelist():assert z.read(name)==(source/name).read_bytes()
assert all(sha(p)==h for p,h in proof['source_sha256'].items())
write(out/'completion.json',dict(passed=True,verified_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    pages=6,minimal_manuscript_inputs=assets,text_and_page_geometry_exact=True,
    rendered_pixel_comparison=render_rows,PDF_byte_identical=sha(original)==sha(rebuilt),
    original_PDF_sha256=sha(original),rebuilt_PDF_sha256=sha(rebuilt),archive=str(archive),archive_sha256=sha(archive),
    archive_bytes=archive.stat().st_size,archive_roundtrip_verified=True,original_candidate_unchanged=True,
    new_native_or_STA_calls=0,new_experimental_results=0,external_toolchain_required=True,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),parent/'verification.json',
        *[source/name for name in assets],out/'rebuild_receipt.json',original,rebuilt,archive]},
    qualification='Independent manuscript source-asset closure and cached-toolchain reproducibility check. No new raw experimental validation or new-host toolchain portability claim.'))
print(dict(passed=True,pages=6,text_exact=True,all_six_renderings_pixel_exact=True,archive_bytes=archive.stat().st_size,archive=str(archive)))
