#!/usr/bin/env python3
"""Run serial-partition diagnostic cases against preserved hypergraphs."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[3]
base = root/'results/architecture_flow_20261027'
candidate = Path(__file__).parent
sys.path.insert(0, str(root/'scripts'))
from check_flatland_partition_balance import audit

cases = [
    'balance_relative3_conv_layer_hls_s21_hybrid_o_n80_w300_p1_place',
    'balance_relative3_robot_rl_s21_hybrid_o_n60_w100_p1_place',
    'balance_literal_spmv_s11_sb_n40_w100_p1_place',
]
binary = candidate/'openroad_build_boost183/src/openroad'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
out = candidate/'partition_validation_set_20261103'
out.mkdir(exist_ok=False)
registration = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), cases=cases,
    binary_sha256=sha(binary), script_sha256=sha(__file__), sample_interval_seconds=0.01,
    input_manifest_sha256={n:sha(base/'runs'/n/'triton_evidence/manifest.json') for n in cases},
    scope='Diagnostic only; polling may miss transient threads; literal and relative3 are separate.')
(out/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
env = dict(os.environ)
env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
    LD_LIBRARY_PATH=str(candidate/'deps/root/usr/lib/x86_64-linux-gnu')+':' +
                    (root/'vendor/openroad-local/library_dirs.txt').read_text().strip())
rows=[]
for name in cases:
    source = base/'runs'/name/'triton_evidence'; dest = out/name; dest.mkdir()
    for filename in ('triton_hypergraph.hgr','run_triton_part.tcl'):
        shutil.copyfile(source/filename,dest/filename)
    command=[str(binary),'-no_init','-no_splash','-threads','1','-exit','run_triton_part.tcl']
    peak=0;samples=0;start=time.monotonic();timed_out=False
    with (dest/'stdout.log').open('w') as log:
        proc=subprocess.Popen(command,cwd=dest,env=env,stdout=log,stderr=subprocess.STDOUT)
        while proc.poll() is None:
            try:
                peak=max(peak,len(list((Path('/proc')/str(proc.pid)/'task').iterdir())));samples+=1
            except OSError: pass
            if time.monotonic()-start>600:
                proc.kill();timed_out=True;break
            time.sleep(.01)
        code=proc.wait()
    original=json.loads((source/'manifest.json').read_text());part=dest/'triton_hypergraph.hgr.part.2'
    row=dict(case=name,returncode=code,timeout=timed_out,peak_sampled_threads=peak,
             samples=samples,wall_seconds=time.monotonic()-start,assignment_exists=part.exists())
    if part.exists():
        row['assignment_sha256']=sha(part)
        row['original_assignment_sha256']=sha(source/part.name)
        row['assignment_identical']=row['assignment_sha256']==row['original_assignment_sha256']
        row['balance_audit']=audit(dest/'triton_hypergraph.hgr',part,2,original['balance'])
    rows.append(row); (dest/'result.json').write_text(json.dumps(row,indent=2)+'\n')
    print(name,'rc',code,'peak',peak,'identical',row.get('assignment_identical'),flush=True)
(out/'summary.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    registration_sha256=sha(out/'registration.json'),results=rows,
    qualification='Diagnostic only; nonexclusive shared host; not general equivalence or thread proof.'),indent=2)+'\n')
