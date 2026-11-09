#!/usr/bin/env python3
"""Run the unchanged physical-model preparation with cyclic GC suspended.

CPython reference counting remains active. This changes Python preparation
overhead only, never the VPR commands, router code, architecture, or audits.
"""
import argparse
import gc
import json
from pathlib import Path
import shutil
import time

import prepare_flatland_benchmark_models as preparation
from lazagna_common import ROOT,sha256,utc,write_json

BASE=preparation.BASE


def main(size,width):
    validation={}
    for count in [600000,2400000]:
        paths=[BASE/f'metadata_profile_{count}_{suffix}.json' for suffix in ['gc','no_gc']]
        a,b=[json.loads(p.read_text()) for p in paths]
        assert a['metadata_digest']==b['metadata_digest'] and a['nodes']==b['nodes']==count
        validation[str(count)]={str(p):sha256(p) for p in paths}
    output=BASE/'preparation_wrapper_runs'/f'n{size}_w{width}'
    output.mkdir(parents=True,exist_ok=False)
    sources={}
    for name in ['prepare_flatland_without_gc.py','prepare_flatland_benchmark_models.py',
                 'derive_flatland_common_plane.py','audit_flatland_controlled_planes.py',
                 'compare_lazagna_graphs.py','audit_flatland_graphs.py','flatland_formats.py',
                 'verify_flatland_import_stream.py','validate_flatland_common_plane.py']:
        path=ROOT/'scripts'/name;sources[str(path)]=sha256(path);shutil.copy2(path,output/name)
    write_json(output/'registration.json',dict(utc=utc(),size=size,width=width,
        protocol_sha256=sha256(BASE/'benchmark_protocol.json'),sources=sources,
        profile_equivalence=validation,amendment='Disable cyclic GC in this new Python preparation process; keep reference counting, original model-generation code and all exact audits.',
        scope='Preparation overhead only. Existing W100 processes and frozen training inputs remain unchanged.'))
    enabled=gc.isenabled();gc.collect();gc.disable();start=time.monotonic()
    try:
        preparation.main(size,width)
        manifest=BASE/'benchmark_models'/f'n{size}_w{width}'/'manifest.json'
        write_json(output/'completion.json',dict(utc=utc(),status='completed',elapsed_seconds=time.monotonic()-start,
            model_manifest=str(manifest),model_manifest_sha256=sha256(manifest)))
    except Exception as error:
        write_json(output/'failure.json',dict(utc=utc(),status='failed',error=str(error),elapsed_seconds=time.monotonic()-start))
        raise
    finally:
        if enabled:gc.enable()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--size',type=int,required=True)
    p.add_argument('--width',type=int,default=300);a=p.parse_args();main(a.size,a.width)
