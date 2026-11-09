#!/usr/bin/env python3
"""Deduplicate verified historical GEMM route inputs with a durable journal."""
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import time

BASE=Path(__file__).resolve().parent.parent
HIST=BASE.parent
ROOT=HIST.parent.parent

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def main():
    with ExitStack() as stack:
        for root,names in [(HIST,('registered_study_continuation.lock','training_continuation.lock','serial_runner.lock',
                                  'training_runner.lock','evaluation_runner.lock','p1_training_preflight.lock',
                                  'sensitivity_model_continuation.lock')),
                           (BASE,('strict_continuation.lock','serial_runner.lock','training_runner.lock','evaluation_runner.lock'))]:
            for name in names:
                f=stack.enter_context((root/name).open('a'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        verified=json.loads((BASE/'historical_gemm_dedup_verified_20261105.json').read_text())
        assert verified['read_only'] and len(verified['files'])==99
        paths=[Path(x['path']) for x in verified['files']]
        identities=set()
        for path,entry in zip(paths,verified['files']):
            s=path.lstat(); assert stat.S_ISREG(s.st_mode) and s.st_ino==entry['inode'] and s.st_nlink==1
            assert s.st_size==entry['bytes'] and stat.S_IMODE(s.st_mode)==entry['mode']
            identities.add((s.st_dev,s.st_ino))
        assert len(identities)==len(paths)
        for manifest in (ROOT/'results').rglob('manifest.json'):
            try: m=json.loads(manifest.read_text())
            except (OSError,ValueError) as e:raise RuntimeError('unreadable manifest '+str(manifest)) from e
            if manifest.parent in [p.parent for p in paths]: assert m['status'] not in ('running','starting')
            for name in m.get('shared_inputs',{}):
                s=os.stat(name)
                if (s.st_dev,s.st_ino) in identities:raise RuntimeError('candidate is shared input: '+name)
        for p in paths:
            before=p.lstat(); assert sha(p)==verified['sha256'];after=p.lstat()
            assert (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
        journal=BASE/'historical_gemm_dedup_journal_20261105.jsonl'
        if journal.exists():raise FileExistsError(journal)
        with journal.open('x') as log:
            def record(row):log.write(json.dumps(row,sort_keys=True)+'\n');log.flush();os.fsync(log.fileno())
            source=paths[0];record(dict(event='validated',utc=time.time(),verification_sha256=sha(BASE/'historical_gemm_dedup_verified_20261105.json'),source=str(source),files=verified['files'],digest=verified['sha256']))
            os.chmod(source,0o444)
            for path in paths[1:]:
                temp=path.with_name('.packed.net.historical-dedup')
                if temp.exists():raise FileExistsError(temp)
                record(dict(event='before',path=str(path),source=str(source)))
                os.link(source,temp);os.replace(temp,path)
                assert path.stat().st_ino==source.stat().st_ino
                record(dict(event='after',path=str(path),source=str(source)))
            record(dict(event='complete',utc=time.time(),digest=sha(source)))
        print('deduplicated',len(paths),'files, logical GiB saved',round(verified['potential_savings_bytes']/2**30,2),flush=True)

if __name__=='__main__':main()
