#!/usr/bin/env python3
"""Resume after a preregistration NameError, preserving original frozen evidence."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import traceback

from flatland_benchmark import BASE, read
from lazagna_common import ROOT, sha256, utc, write_json
import continue_strict_study as original

SCRIPTS = Path(__file__).resolve().parent
FIX = SCRIPTS / 'run_flatland_evaluation_import_fix_v1.py'
OLD = SCRIPTS / 'run_flatland_evaluation.py'
DIRECTORY = BASE / 'strict_continuation_import_fix_v1'


def main():
    lock = (BASE / 'strict_continuation.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    previous = read(BASE / 'strict_continuation/state.json')
    assert previous['status'] == 'needs_diagnosis'
    assert previous['completed_stages'] == [x[0] for x in original.STAGES[:5]]
    assert "returned non-zero exit status 1" in previous['error']
    log = (BASE / 'strict_continuation/heldout.log').read_text()
    assert "NameError: name 'Path' is not defined" in log
    assert FIX.read_text() == OLD.read_text().replace('import argparse\n', 'import argparse\nfrom pathlib import Path\n', 1)
    assert not (BASE / 'evaluation_jobs.json').exists()
    assert not (BASE / 'evaluation_cases').exists()
    assert not (BASE / 'evaluation_invocations').exists()
    old_registration = BASE / 'strict_continuation/registration.json'
    bindings = read(old_registration)['source_and_protocol_sha256']
    original.verify(bindings); original.training_gate(); original.quiescent()
    proof = BASE / 'seccomp_full_workload_validation.json'
    pilot = read(proof)
    assert pilot['status'] == 'passed'
    original.verify(pilot['evidence_sha256'])
    assert read(BASE/'training_analysis/summary.json')['status']=='all_registered_training_attempts_accounted'
    assert read(BASE/'selected_configs.json')['status']=='frozen_before_heldout'
    stages = [(label, ([FIX.name] + args[1:] if label in ('heldout','width300') else args))
              for label, args in original.STAGES[5:]]
    DIRECTORY.mkdir(exist_ok=False)
    own_bindings = {str(FIX): sha256(FIX), str(Path(__file__)): sha256(__file__),
                    str(old_registration): sha256(old_registration),
                    str(BASE/'strict_continuation/state.json'): sha256(BASE/'strict_continuation/state.json'),
                    str(BASE/'strict_continuation/heldout.log'): sha256(BASE/'strict_continuation/heldout.log'),
                    str(proof): sha256(proof)}
    write_json(DIRECTORY/'registration.json', dict(utc=utc(), amendment='Add missing pathlib.Path import only; failure occurred before evaluation registration or case execution.', source_and_evidence_sha256=own_bindings, original_binding_count=len(bindings), stages=stages, seccomp_qualification=pilot['qualification']))
    completed=[]
    def state(status, **fields):
        write_json(DIRECTORY/'state.json', dict(utc=utc(), supervisor_pid=os.getpid(),status=status,completed_stages=completed,**fields))
    env=os.environ.copy();env['PYTHONPATH']=str(SCRIPTS)+os.pathsep+str(ROOT/'scripts');env['PYTHONUNBUFFERED']='1'
    try:
        for label,args in stages:
            original.verify(bindings);original.verify(own_bindings);original.quiescent()
            cmd=[sys.executable,str(SCRIPTS/args[0]),*args[1:]]
            state('running_stage',stage=label,command=cmd)
            with (DIRECTORY/(label+'.log')).open('x') as out:
                subprocess.run(cmd,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT,check=True)
            completed.append(label);state('stage_completed',stage=label)
        state('awaiting_scientific_and_integrity_closure', report=str(BASE/'report.html'))
    except BaseException as error:
        state('needs_diagnosis',error=str(error),traceback=traceback.format_exc())
        raise

if __name__=='__main__': main()
