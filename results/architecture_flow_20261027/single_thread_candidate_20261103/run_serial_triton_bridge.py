#!/usr/bin/env python3
"""Private-cwd TritonPart bridge, preserving input/output and failure status."""
import math
import sys
sys.path.insert(0, '/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/scripts')
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from lazagna_common import ROOT, sha256, utc, write_json


def main():
    graph, parts, balance, seed = sys.argv[1:]
    # The published engine uses this fixed basename. Restrict Tcl interpolation.
    if Path(graph).name != graph or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-' for c in graph):
        raise ValueError('Expected a plain hypergraph filename')
    parts, seed, balance = int(parts), int(seed), float(balance)
    if parts < 2 or seed < 0 or not math.isfinite(balance) or balance < 0:
        raise ValueError('Invalid partition configuration')
    path = Path(graph)
    saved = Path('triton_evidence')
    saved.mkdir(exist_ok=False)
    shutil.copy2(path, saved / path.name)
    output = Path(graph + '.part.' + str(parts))
    if output.exists():
        raise FileExistsError(output)
    base = ROOT / 'vendor/openroad-local'
    binary = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/results/architecture_flow_20261027/single_thread_candidate_20261103/openroad_build_boost183/src/openroad')
    script = Path('run_triton_part.tcl')
    # catch ensures a Tcl failure cannot become a successful VPR partition.
    script.write_text('if {[catch {\n'
        f'  triton_part_hypergraph -hypergraph_file {{{graph}}} -num_parts {parts} '
        f'-balance_constraint {balance:.9g} -seed {seed}\n'
        '} message]} { puts stderr $message; exit 1 }\nexit 0\n')
    shutil.copy2(script, saved / script.name)
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = '/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/results/architecture_flow_20261027/single_thread_candidate_20261103/deps/root/usr/lib/x86_64-linux-gnu' + ':' + (base / 'library_dirs.txt').read_text().strip()
    env['OMP_NUM_THREADS'] = '1'
    command = [str(binary), '-no_init', '-no_splash', '-threads', '1', '-exit', str(script)]
    data = dict(start_utc=utc(), command=command, binary_sha256=sha256(binary),
                input_sha256=sha256(path), tcl_sha256=sha256(script),
                partition_seed=seed, parts=parts, balance=balance)
    start = time.monotonic()
    with open('run_triton_part.log', 'w') as log:
        result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    data.update(returncode=result.returncode, wall_seconds=time.monotonic()-start,
                finish_utc=utc())
    if result.returncode == 0 and output.exists():
        nvertices = int(path.read_text().splitlines()[0].split()[1])
        assignments = [int(x) for x in output.read_text().split()]
        data['output_valid'] = len(assignments) == nvertices and all(0 <= x < parts for x in assignments)
        data['part_sizes'] = [assignments.count(i) for i in range(parts)]
        data['output_sha256'] = sha256(output)
        shutil.copy2(output, saved / output.name)
    else:
        data['output_valid'] = False
    shutil.copy2('run_triton_part.log', saved / 'run_triton_part.log')
    write_json(saved / 'manifest.json', data)
    if result.returncode != 0 or not data['output_valid']:
        raise RuntimeError('TritonPart failed; see triton_evidence')


if __name__ == '__main__':
    main()
