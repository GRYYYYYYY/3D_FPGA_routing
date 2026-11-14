#!/usr/bin/env python3
"""Load a repaired route into unchanged VPR for FULL legality and complete STA.

These are analysis-only feasibility interventions, not online routing runs.
"""
import fcntl
import os
from pathlib import Path
import shutil
import sys
from retained_prefix_workflow import D,read,write,sha,require_formal_terminal
ROOT=D.parents[1];OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study

require_formal_terminal();lock=(D/'critical_scope_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
source=D/'actual_search_tree_eltwise_dev_01/runs/eltwise_layer_T2'
pm=read(source/'manifest.json');a=read(D/'critical_capacity_potential_01/analysis.json');assert a['passed']
assert all(sha(p)==h for p,h in a['source_sha256'].items())
proposals=[r for r in a['results'] if 'candidate_route' in r];assert len(proposals)==1
proposal=proposals[0];candidate=Path(proposal['candidate_route']);assert sha(candidate)==proposal['candidate_route_sha256']
b=D/'critical_repair_validation_01';b.mkdir(exist_ok=False);(b/'bin').mkdir()
shutil.copy2(pm['command'][0],b/'bin/vpr')
shutil.copy2(OLD/'runtime_dependency_binding.json',b/'runtime_dependency_binding.json')
files=[Path(__file__),D/'critical_capacity_potential_01/analysis.json',candidate,source/'manifest.json',source/'routed.route',source/'independent_audit.json',
       source/'packed.net',source/'placed.place',D/'src/vpr/src/base/vpr_api.cpp',D/'src/vpr/src/base/read_route.cpp']
bindings={str(p):sha(p) for p in files}
reg=dict(status='registered_before_native_analysis',question='Does the capacity-feasible retained-tree extension pass unchanged native FULL legality and lower complete STA CPD?',
    hypothesis='A current final critical connection outside guided population has a strictly shorter local path even with other-net RR occupancy fixed.',
    arms=['C:load original currentTf route','R:load separate route with only net5479 pin36 target-exclusive chain replaced'],
    actual_changes='No router search or C++ modification. Remove --route, retain --analysis, use same binary/graph/net/place; request ten timing report paths for both roles; verify route switch IDs explicitly.',
    source_sha256=bindings,binary_sha256=sha(b/'bin/vpr'),pid=os.getpid(),
    start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
    limits=dict(timeout_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='Retrospective one-connection feasibility intervention, not a deployable online method or new full-router timing sample. Prior route/guide evidence and frozen public snapshot remain unchanged.',
    route_search_calls=0,native_analysis_calls_planned=2)
write(b/'registration.json',reg);io.BASE=b;io.ADDRESS_SPACE_BYTES=reg['limits']['memory_bytes']
for p,h in bindings.items():io.frozen_hash(p,h)
receipts=[];gates={}
for arm,route in [('C',source/'routed.route'),('R',candidate)]:
    assert shutil.disk_usage(D).free>=reg['limits']['disk_reserve_bytes']
    directory=b/'runs'/('eltwise_layer_'+arm);directory.mkdir(parents=True)
    for name in ['packed.net','placed.place']:shutil.copy2(source/name,directory/name)
    shutil.copy2(route,directory/'routed.route')
    before={name:sha(directory/name) for name in ['packed.net','placed.place','routed.route']}
    cmd=list(pm['command']);cmd[0]=str(b/'bin/vpr');cmd.remove('--route')
    cmd[cmd.index('--timing_report_npaths')+1]='10'
    cmd.extend(['--verify_route_file_switch_id','on'])
    for opt,name in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(directory/name)
    result=io.run(directory.name,cmd,environment={'VPR_H3D_MODE':'off'},timeout=1800,
        frozen=[cmd[0],cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],b/'registration.json'],
        private_inputs=[directory/name for name in before],
        tags=dict(circuit='eltwise_layer',arm=arm,phase='retrospective_native_analysis',hypothesis='fixed_other_net_capacity_feasible_critical_repair',route_search_calls=0))
    receipts.append(result)
    log=(directory/'stdout.log').read_text()
    gate=dict(process_completed=result['status']=='completed',native_FULL=result['metrics'].get('native_full_check_passed',False),
        route_load_observed='Finished loading route file' in log,
        inputs_unchanged=all(sha(directory/name)==h for name,h in before.items()),
        cpd_present=result['metrics'].get('critical_path_ns') is not None)
    if arm=='C':gate['control_CPD_exact']=result['metrics'].get('critical_path_ns')==pm['metrics']['critical_path_ns']
    gates[arm]=gate;write(directory/'analysis_gate.json',dict(passed=all(gate.values()),checks=gate))
    if not all(gate.values()):break
study.BASE=b;ctx=study.context('eltwise_layer','hybrid_o',11,100)
study.audit_batch(ctx,receipts,b/'independent_native_analysis_audit.json')
io.seal_inputs(b/'input_seal.json')
write(b/'completion.json',dict(status='native_analysis_terminal',gates=gates,
    passed=len(receipts)==2 and all(all(v.values()) for v in gates.values()),
    missing_arms=[arm for arm in ['C','R'] if arm not in gates],
    native_analysis_calls=len(receipts),route_search_calls=0,
    observations=[dict(arm=m['tags']['arm'],status=m['status'],metrics=m['metrics'],process_seconds=m['wall_seconds']) for m in receipts]))
print('Native load/STA gates',gates,flush=True)
