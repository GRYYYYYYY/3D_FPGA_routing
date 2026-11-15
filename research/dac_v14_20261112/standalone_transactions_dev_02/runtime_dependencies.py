"""Resolve current executable dependencies; never copy an old run's library list."""
import os
from pathlib import Path
import subprocess
from runtime_common import sha256,write_json


def bind_runtime(binary,output):
    binary=Path(binary).resolve();output=Path(output).resolve()
    assert binary.is_file() and os.access(binary,os.X_OK)
    assert not output.exists(), 'Do not replace a runtime binding after execution'
    env=os.environ.copy()
    for key in ['LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']:env.pop(key,None)
    result=subprocess.run(['/usr/bin/ldd',str(binary)],capture_output=True,text=True,env=env,check=False)
    combined=result.stdout+result.stderr
    assert 'not found' not in combined, combined
    static=('not a dynamic executable' in combined or 'statically linked' in combined)
    assert result.returncode==0 or static,combined
    libraries={}
    for line in result.stdout.splitlines():
        tokens=line.split('=>')[-1].split()
        if tokens and tokens[0].startswith('/'):
            p=Path(tokens[0]).resolve();assert p.is_file();libraries[str(p)]=sha256(p)
    assert libraries or static, 'No dynamic dependency resolution evidence'
    receipt=dict(format='actual_executable_dependencies_v1',binary=str(binary),binary_sha256=sha256(binary),
                 command=['/usr/bin/ldd',str(binary)],returncode=result.returncode,
                 ldd_stdout=result.stdout,ldd_stderr=result.stderr,statically_linked=static,
                 missing=[],sha256=libraries,
                 qualification='Current environment dynamic dependency closure for this executable; loader override variables cleared exactly as at native launch. Not a historical runtime list or a whole-process Python dependency inventory.')
    write_json(output,receipt)
    return receipt
