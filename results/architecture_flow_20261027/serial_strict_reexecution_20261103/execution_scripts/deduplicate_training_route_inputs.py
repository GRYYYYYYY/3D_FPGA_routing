#!/usr/bin/env python3
"""Optionally deduplicate immutable, byte-identical finished training inputs.

Dry-run is the default. Apply only after every training case and its input
seal have completed, with all study locks held. Historical artifacts and
placement source files are outside the permitted target set.
"""
import argparse
from collections import defaultdict
import fcntl
import os
from pathlib import Path
import stat

import flatland_benchmark as study
from lazagna_common import sha256,utc,write_json


def link_group(paths, expected, apply=False):
    """Verify all bytes before replacing any path; never follow a symlink."""
    paths=[Path(p) for p in paths]
    assert len(paths)>1 and len(set(paths))==len(paths)
    metadata=[p.lstat() for p in paths]
    assert all(stat.S_ISREG(s.st_mode) and s.st_nlink==1 for s in metadata)
    assert len({s.st_dev for s in metadata})==1
    assert len({s.st_size for s in metadata})==1
    assert all(sha256(p)==expected for p in paths)
    before=sum(s.st_size for s in metadata)
    if apply:
        canonical=paths[0]
        os.chmod(canonical,0o444)
        for path in paths[1:]:
            temp=path.with_name('.'+path.name+'.dedup.'+str(os.getpid()))
            assert not temp.exists()
            os.link(canonical,temp)
            try:os.replace(temp,path)
            finally:
                if temp.exists():temp.unlink()
        assert all(sha256(p)==expected and p.stat().st_ino==canonical.stat().st_ino for p in paths)
    return dict(sha256=expected,files=[str(p) for p in paths],
                logical_bytes=before,estimated_physical_bytes=metadata[0].st_size,
                saved_bytes=before-metadata[0].st_size,applied=apply)


def main(apply):
    base=study.BASE;locks=[]
    for name in ('serial_runner.lock','training_runner.lock','evaluation_runner.lock'):
        lock=(base/name).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(lock)
    cases=list((base/'training_cases').glob('*/result.json'))
    assert len(cases)==18 and all(study.read(p)['status']=='completed' for p in cases)
    seals=list((base/'training_invocations').glob('*_input_integrity.json'))
    assert seals and all(study.read(p)['passed'] for p in seals)
    manifests=list((base/'runs').glob('*/manifest.json'));all_records=[];shared=set()
    for p in manifests:
        m=study.read(p)
        assert m['status'] not in ('running','starting'),p
        shared.update(str(Path(x).resolve()) for x in m.get('shared_inputs',{}))
        all_records.append((p,m))
    groups=defaultdict(list)
    for p,m in all_records:
        if m.get('tags',{}).get('stage')!='training' or m['tags'].get('operation')!='route':continue
        output=m.get('outputs',{}).get('packed.net')
        if output is None:continue
        target=p.parent/'packed.net'
        assert str(target.resolve()) not in shared, f'Output is a frozen input elsewhere: {target}'
        groups[output['sha256']].append(target)
    # Validate all groups before mutation, so a mismatch cannot silently cause
    # a partially applied transformation. A crash still requires manual audit.
    candidates=[(digest,paths) for digest,paths in groups.items() if len(paths)>1]
    previews=[link_group(paths,digest,False) for digest,paths in candidates]
    output=base/('training_deduplication_applied.json' if apply else 'training_deduplication_dry_run.json')
    if output.exists():raise FileExistsError(output)
    if apply:
        records=[link_group(paths,digest,True) for digest,paths in candidates]
    else:records=previews
    write_json(output,dict(utc=utc(),applied=apply,groups=records,
        estimated_saved_bytes=sum(r['saved_bytes'] for r in records),
        qualification='Only finished training route private packed.net files; paths remain readable and become shared read-only in apply mode. No historical output or placement source is changed. A crash during apply requires manual inode/hash audit.'))
    print('dedup groups',len(records),'estimated saved bytes',sum(r['saved_bytes'] for r in records),'apply',apply,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');main(p.parse_args().apply)
