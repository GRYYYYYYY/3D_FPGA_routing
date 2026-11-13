#!/usr/bin/env python3
"""Standalone invariants; end-to-end same-table paired fixtures live in the research workspace."""
from pathlib import Path
import argparse,subprocess,json,hashlib
VTR=Path(__file__).resolve().parents[5]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);o=p.parse_args().output;o.mkdir(exist_ok=False,parents=True)
s=Path(__file__).with_name('test_regret.cpp');h=VTR/'vpr/src/route/h3d_timing_regret.h';binary=o/'test_regret'
cmd=['g++','-std=c++20','-O2','-Wall','-Wextra','-I',str(h.parent),str(s),'-o',str(binary)]
with (o/'test.log').open('w') as f:
 subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 subprocess.run([str(binary.resolve())],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=30)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(o/'validation.json').write_text(json.dumps(dict(passed=True,command=cmd,source_sha256=sha(s),header_sha256=sha(h),binary_sha256=sha(binary),log_sha256=sha(o/'test.log')),indent=2)+'\n')
print((o/'test.log').read_text())
