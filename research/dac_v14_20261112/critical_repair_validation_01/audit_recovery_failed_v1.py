#!/usr/bin/env python3
"""Complete post-run audits after a context-path error; never rerun VPR."""
import os
from pathlib import Path
import sys
from retained_prefix_workflow import D,read,write,sha
ROOT=D.parents[1];OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_benchmark as study
import flatland_timing_io_candidate as io

b=D/'critical_repair_validation_01';reg=read(b/'registration.json')
proc=Path('/proc')/str(reg['pid'])/'stat'
assert not (proc.exists() and proc.read_text().split(') ',1)[1].split()[19]==reg['start_ticks'])
assert not (b/'completion.json').exists()
write(b/'audit_recovery_registration.json',dict(native_calls=0,
    cause='Original runner assigned study.BASE to the new analysis batch before study.context(), which requires frozen benchmark_protocol.json at OLD. Both native analysis roles already completed and passed local FULL/load/CPD/input gates. Missing pair_check files are also prepared from already sealed input identities.',
    original_runner_sha256=sha(D/'run_critical_repair_validation.py'),recovery_sha256=sha(__file__),
    action='Build context at original frozen BASE, then redirect only audit output BASE; rehash all registered/shared/private inputs and outputs, audit existing route copies, seal. No VPR rerun.'))
source=D/'actual_search_tree_eltwise_dev_01/runs/eltwise_layer_T2'
receipts=[];gates={}
for path,digest in reg['source_sha256'].items():io.frozen_hash(path,digest)
io.frozen_hash(b/'registration.json',sha(b/'registration.json'))
for arm in ['C','R']:
    directory=b/'runs'/('eltwise_layer_'+arm);m=read(directory/'manifest.json');receipts.append(m)
    assert m['status']=='completed' and read(directory/'analysis_gate.json')['passed']
    for path,v in m['shared_inputs'].items():io.frozen_hash(path,v['sha256'])
    for path,digest in m['private_input_sha256'].items():assert sha(path)==digest
    for name,v in m['outputs'].items():assert sha(directory/name)==v['sha256']
    checks={name:sha(directory/name)==sha(source/name) for name in ['packed.net','placed.place']}
    write(directory/'pair_check.json',dict(passed=all(checks.values()),checks=checks,
        scope='Same original packing/placement; candidate route difference is separately registered and preserved.'))
    gates[arm]=read(directory/'analysis_gate.json')['checks']
study.BASE=OLD;ctx=study.context('eltwise_layer','hybrid_o',11,100);study.BASE=b
assert ctx['fixture']['original_graph']==receipts[0]['command'][receipts[0]['command'].index('--read_rr_graph')+1]
audit=study.audit_batch(ctx,receipts,b/'independent_native_analysis_audit.json');assert audit['passed']
io.seal_inputs(b/'input_seal.json')
observations=[dict(arm=m['tags']['arm'],status='legal',metrics=m['metrics'],process_seconds=m['wall_seconds'],
    physical_metrics=read(b/'runs'/m['name']/'independent_audit.json')['physical_metrics']) for m in receipts]
write(b/'completion.json',dict(status='native_analysis_terminal',passed=True,gates=gates,missing_arms=[],
    native_analysis_calls=2,route_search_calls=0,recovery_native_calls=0,observations=observations))
print(dict(passed=True,CPD=[m['metrics']['critical_path_ns'] for m in receipts],recovery_native_calls=0),flush=True)
