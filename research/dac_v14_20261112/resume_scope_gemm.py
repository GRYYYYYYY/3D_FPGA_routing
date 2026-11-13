#!/usr/bin/env python3
"""Finish post-route audits after an off-mode A3 guide-file requirement error; no routing."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import resource
import shutil
import signal
import socket
import sys
import time

D=Path(__file__).resolve().parent
R=D.parents[1]
B=D/'scope_gemm_dev_01'
OLD=R/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(R/'scripts'),str(D)]
import flatland_timing_io_candidate as io
from lazagna_common import sha256,write_json,utc
from audit_final_guides import audit as audit_guides

lock=(D/'scope_gemm_runner.lock').open('w')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not (B/'completion.json').exists() and not (B/'recovery_identity.json').exists()
resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
signal.alarm(1800)
assert shutil.disk_usage(B).free>=80*1024**3
reg=json.loads((B/'registration.json').read_text())
assert not (Path('/proc')/str(reg['pid'])).exists(), 'Original owner must be terminal'
shutil.copy2(__file__,B/'recovery_runner.py')
write_json(B/'recovery_identity.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],host=socket.gethostname(),utc=utc(),native_calls=0,runner_sha256=sha256(__file__),reason='Original runner skipped final-guide audit only for A1, then requested nonexistent guide CSV for native off-mode A3. All seven native runs and independent route audits already passed. Preserve original runner/logs; gate guide audit by actual recorded mode.',memory_bytes=64*1024**3,timeout=1800))
io.BASE=B
assert sha256(B/'runner.py')==reg['runner_sha256']
for relative,expected in reg['source_sha256'].items():
    assert sha256(B/'source'/Path(relative).name)==expected
summary=json.loads((B/'gemm_layer_audit.json').read_text())
assert summary['passed'] and summary['registered_route_count']==summary['legal_count']==7
rows=[]
for c in reg['circuits']:
    refs=json.loads((B/f'{c}_references.json').read_text())
    for arm,ref in refs.items():
        rd=Path(ref['path']);io.frozen_hash(rd/'manifest.json',ref['manifest_sha256'])
        m=json.loads((rd/'manifest.json').read_text())
        for path,expected in m['shared_inputs'].items(): io.frozen_hash(path,expected['sha256'])
        for fn,expected in m['outputs'].items(): io.frozen_hash(rd/fn,expected['sha256'])
        rows.append(dict(circuit=c,arm=arm,**ref))
    for arm in reg['arms']:
        rd=B/'runs'/f'{c}_{arm}';m=json.loads((rd/'manifest.json').read_text())
        assert m['status']=='completed' and m['metrics']['native_full_check_passed']
        for path,expected in m['shared_inputs'].items():
            assert list(io.identity(path))==expected['stat_identity'], path
            io.frozen_hash(path,expected['sha256'])
        for fn,expected in m['outputs'].items(): io.frozen_hash(rd/fn,expected['sha256'])
        a=json.loads((rd/'independent_audit.json').read_text());assert a['audit']['passed']
        mode=m['environment'].get('VPR_H3D_MODE','off')
        if mode!='off':
            assert (rd/'h3d_final_guides.csv').exists()
            existing=rd/'final_guide_audit.json'
            if existing.exists(): assert json.loads(existing.read_text())['passed']
            else: audit_guides(rd)
        else:
            assert arm in ['A1','A3']
            write_json(rd/'guide_audit_not_applicable.json',dict(reason='Recorded VPR_H3D_MODE=off native control has no planner guide output',mode=mode,manifest_sha256=sha256(rd/'manifest.json')))
        if arm=='F':assert json.loads((rd/'default_off_equivalence.json').read_text())['passed']
        rows.append(dict(circuit=c,arm=arm,status='legal',metrics=m['metrics'],physical_metrics=a['physical_metrics'],process_seconds=m['wall_seconds'],h3d=[line for line in (rd/'stdout.log').read_text().splitlines() if line.startswith('H3D_')],path=str(rd)))
        print('reused native and route audit; final guide status checked',rd.name,flush=True)
write_json(B/'observations.json',rows)
io.frozen_hash(B/'recovery_runner.py')
io.frozen_hash(B/'runner.py',reg['runner_sha256'])
io.seal_inputs(B/'input_seal.json')
write_json(B/'completion.json',dict(utc=utc(),status='recovered_post_route_audit_batch_complete_not_research_complete',native_calls=0,reused_native=7,observations=len(rows),recovery_identity_sha256=sha256(B/'recovery_identity.json')))
print('Seven existing native routes reused; all final audits and input seal complete',flush=True)
