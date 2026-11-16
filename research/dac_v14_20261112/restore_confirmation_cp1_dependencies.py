"""Rebuild fixed CP1 from its public source archive and two hash-pinned wheels.

No native binaries, physical inputs, network access, or historical runtime are used.
"""
import argparse,hashlib,json,os,sys,tarfile,zipfile
from pathlib import Path
SOURCE_SHA='c6dad6727dd8c9620cd8ea66e3289dc1b904477e923f708818303390119d8bdf'
MANIFEST_SHA='c970883e5e017a657c98455011b7d760944948d3116b5576927222d4665f72cb'
WHEELS={
 'numpy-2.2.6-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl':'fc7b73d02efb0e18c000e9ad8b83480dfcd5dfd11065997ed4c6747470ae8915',
 'lxml-6.1.3-cp310-cp310-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl':'f6449672f9c93316deb5e2839e18931f468670e44d5bd9b1301a5a9655d45c07',
}
VENDOR={'numpy','numpy.libs','lxml'}
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def restore(source,wheel_dir,output):
 source,wheel_dir,output=[Path(p).resolve() for p in [source,wheel_dir,output]]
 assert not output.exists(),'Choose a fresh output directory; no overwrite or in-place installation'
 assert sha(source)==SOURCE_SHA,'Wrong CP1 source archive'
 for name,digest in WHEELS.items():assert sha(wheel_dir/name)==digest,('Wheel digest mismatch',name)
 # Validate every member before writing. The public CP1 archive contains only regular files.
 with tarfile.open(source,'r:gz') as archive:
  members=archive.getmembers();names=[]
  for entry in members:
   p=Path(entry.name);assert entry.isfile() and not p.is_absolute() and '..' not in p.parts and p.parts[0]=='current_sta_cp1'
   rel=Path(*p.parts[1:]);assert rel.parts and str(rel) not in names;names.append(str(rel))
  output.mkdir(parents=True)
  for entry,name in zip(members,names):
   dest=output/name;dest.parent.mkdir(parents=True,exist_ok=True)
   with dest.open('xb') as f:f.write(archive.extractfile(entry).read())
 assert sha(output/'release_manifest.json')==MANIFEST_SHA
 manifest=json.loads((output/'release_manifest.json').read_text());bound=manifest['files_sha256']
 expected={name for name in bound if name.startswith('runtime/') and Path(name).parts[1] in VENDOR};restored=set();ignored=[]
 for filename in WHEELS:
  with zipfile.ZipFile(wheel_dir/filename) as wheel:
   for entry in wheel.infolist():
    p=Path(entry.filename)
    if entry.is_dir() or p.parts[0] not in VENDOR:continue
    assert not p.is_absolute() and '..' not in p.parts
    name=str(Path('runtime')/p)
    if name not in expected:ignored.append(name);continue
    assert name not in restored
    data=wheel.read(entry);assert hashlib.sha256(data).hexdigest()==bound[name],name
    dest=output/name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(data)
    restored.add(name)
 assert restored==expected
 assert all(sha(output/name)==digest for name,digest in bound.items())
 actual={str(f.relative_to(output)) for f in output.rglob('*') if f.is_file()}
 assert actual==set(bound)|{'release_manifest.json','freeze_receipt.json'}
 for f in sorted(output.rglob('*'),key=lambda x:len(x.parts),reverse=True):f.chmod(0o555 if f.is_dir() else 0o444)
 output.chmod(0o555)
 return dict(passed=True,release_id='current_sta_cp1',output=str(output),source_archive_sha256=SOURCE_SHA,release_manifest_sha256=MANIFEST_SHA,restored_dependency_files=len(restored),verified_bound_files=len(bound),wheel_sha256=WHEELS,ignored_unbound_wheel_files=ignored,native_calls=0,qualification='Byte-exact reconstruction from public source and pinned distribution wheels. Import and actual fixed admission are separate checks; external native binaries/physical inputs remain required.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-archive',type=Path,required=True);p.add_argument('--wheel-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(restore(a.source_archive,a.wheel_dir,a.output),indent=2))
