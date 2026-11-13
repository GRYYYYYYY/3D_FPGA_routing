#!/usr/bin/env python3
"""Check a versioned paper package in an isolated temporary working directory."""
import argparse, hashlib, json, os, subprocess, tarfile, tempfile
from pathlib import Path
from pypdf import PdfReader

P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('package',type=Path)
args=parser.parse_args()
package=args.package.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='dac2027-package-build-') as tmp:
 with tarfile.open(package) as tar:
  members=tar.getmembers()
  if any(not m.isfile() or not m.name.startswith('dac2027/') or '..' in Path(m.name).parts for m in members):
   raise RuntimeError('Unexpected member in paper archive')
  tar.extractall(tmp,filter='data')
 work=Path(tmp)/'dac2027'
 original=work/'build/main.pdf'
 original_pages=[p.extract_text() for p in PdfReader(original).pages]
 original.unlink()
 env=os.environ.copy()
 env['PATH']=str(P/'tools')+os.pathsep+env.get('PATH','')
 build=subprocess.run(['bash','build.sh'],cwd=work,env=env,capture_output=True,text=True,timeout=120)
 if build.returncode: raise RuntimeError(f'Packaged build failed: {build.stderr[-2000:]}')
 rebuilt=work/'build/main.pdf'
 pages=[p.extract_text() for p in PdfReader(rebuilt).pages]
 if pages!=original_pages or len(pages)!=7: raise RuntimeError('Packaged build text or page count differs')
 result={'status':'passed','source_package':str(package),'source_package_sha256':sha(package),
         'compiler':'external Tectonic supplied from existing local tools; package itself excludes compiler',
         'pages':len(pages),'page_text_matches_packaged_pdf':True,'rebuilt_pdf_sha256':sha(rebuilt),
         'scope':'Unpacked package, existing compiler and current user TeX cache; no clean-network or bit-for-bit reproducibility claim.'}
(P/'data/packaged_build_check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
