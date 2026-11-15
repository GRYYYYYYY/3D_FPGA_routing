"""Explicit, hash-bound timing backends; no implicit research-directory lookup."""
import os
from pathlib import Path
from retained_prefix_workflow import read,sha
from controller_runtime import configuration,package_files,admit_controller

KEY='H3D_EXPLICIT_RUNTIME_CONFIG'

def activate(path):
    path=Path(path).resolve()
    cfg,physical,binaries,files=configuration(path)
    assert set(binaries)=={'resource','owner','timing_repair','timing_observer'}
    assert set(cfg['query_engines'])=={'capacity','relaxed'}
    assert set(cfg['query_validations'])=={'capacity'}
    os.environ[KEY]=str(path)
    return cfg,physical,binaries,files

def runtime_files():
    path=Path(os.environ[KEY]).resolve()
    _,_,_,files=activate(path)
    return [path,*files]

def binary(phase):
    return activate(os.environ[KEY])[2][phase]

def query_driver(kind):
    cfg,_,_,_=activate(os.environ[KEY])
    return Path(cfg['query_engines'][kind]['path'])

def query_validation():
    cfg,_,_,_=activate(os.environ[KEY])
    path=Path(cfg['query_validations']['capacity']['path'])
    assert read(path)['passed']
    return path

def admit_timing(path,state,cache):
    activate(path)
    return [*package_files(),*runtime_files(),*admit_controller(path,state,cache)]
