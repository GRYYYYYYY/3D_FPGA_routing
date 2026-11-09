#!/usr/bin/env python3
"""Read-only validation of historical GEMM route-input dedup candidates."""
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import time

BASE = Path(__file__).resolve().parent.parent
HIST = BASE.parent

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()

def main():
    with ExitStack() as stack:
        for root, names in [(HIST, ('registered_study_continuation.lock','training_continuation.lock',
                                   'serial_runner.lock','training_runner.lock','evaluation_runner.lock',
                                   'p1_training_preflight.lock','sensitivity_model_continuation.lock')),
                            (BASE, ('strict_continuation.lock','serial_runner.lock','training_runner.lock','evaluation_runner.lock'))]:
            for name in names:
                lock=stack.enter_context((root/name).open('a')); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for family in ('sb','cb_o','hybrid_o'):
            case=HIST/'training_cases'/('gemm_layer_'+family)
            assert json.loads((case/'result.json').read_text())['status']=='completed'
            assert json.loads((case/'audit_summary.json').read_text())['passed']
        candidates=json.loads((BASE/'disk_recovery_historical_candidates_20261105.json').read_text())
        groups=[g for g in candidates['groups'] if any('training_gemm_layer_s11_cb_o_n200_w100_p0_delay_critical_c7/packed.net' in x[0] for x in g['paths'])]
        assert len(groups)==1; group=groups[0]
        members=[]
        for name,ino,nlink in group['paths']:
            p=Path(name).resolve(); s=p.lstat()
            assert stat.S_ISREG(s.st_mode) and s.st_ino==ino and s.st_nlink==nlink==1
            m=json.loads((p.parent/'manifest.json').read_text()); t=m['tags']
            assert t['stage']=='training' and t['operation']=='route' and t['circuit']=='gemm_layer'
            assert t['family'] in ('sb','cb_o','hybrid_o') and m['status'] not in ('running','starting')
            assert m['outputs']['packed.net']['sha256']==group['sha256']
            before=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
            assert sha(p)==group['sha256']
            s=p.lstat(); assert before==(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
            members.append(dict(path=str(p),inode=ino,nlink=nlink,mode=stat.S_IMODE(s.st_mode),bytes=s.st_size))
        out=BASE/'historical_gemm_dedup_verified_20261105.json'
        if out.exists():raise FileExistsError(out)
        out.write_text(json.dumps(dict(utc=time.time(),read_only=True,sha256=group['sha256'],files=members,
            potential_savings_bytes=group['bytes_each']*(len(members)-1),
            limitation='Content and known study locks verified; shared-input manifest scan was separate and must be repeated under lock before any mutation.'),indent=2)+'\n')
        print('verified',len(members),'potential GiB',round(group['bytes_each']*(len(members)-1)/2**30,2),flush=True)

if __name__=='__main__':main()
