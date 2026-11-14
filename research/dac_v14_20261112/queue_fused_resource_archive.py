#!/usr/bin/env python3
"""Single downstream owner admits only sealed BNN actors, preserving all prior points."""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from export_policy_analysis_pool import process_identity
from pareto_archive_dimensions import dominates

q = D / 'fused_resource_archive_queue_01'
q.mkdir(exist_ok=False)
lock = (q / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
prior = D / 'fused_resource_development_01/queue'
owner = read(prior / 'registration.json')
parent = D / 'multiobjective_archive_52'
output = D / 'multiobjective_fused_resource_final_01'
files = [Path(__file__).resolve(), D / 'append_fused_resource_observations.py',
    D / 'pareto_archive_dimensions.py', parent / 'completion.json', parent / 'points.json', prior / 'registration.json']
bound = {str(path): sha(path) for path in files}
write(q / 'registration.json', dict(pid=os.getpid(), start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bound, prerequisite_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),
    parent_archive=str(parent), output_archive=str(output), native_calls=0,
    question='After actual cohort completion, admit every legal BNN candidate/rejection from passed sealed actors and refresh the joint population with strong baselines.',
    qualification='Read-only extraction/reconciliation, no rerouting or repeated experiments. Already archived eltwise actors are not duplicated. Partial passed actors may be retained even if another branch failed; no overall research stop. Shared continuation and manuscript are not edited by this background extractor.'))
write(q / 'status.json', dict(status='waiting_for_registered_fused_cohort_terminal',observed_at=time.time()))
while True:
    actual = process_identity(owner['pid'])
    if not actual or actual['state']=='Z' or actual['start_ticks']!=owner['start_ticks']:
        break
    time.sleep(15)
assert (prior/'completion.json').exists(), 'Prior owner ended without terminal receipt; reconcile, do not blindly rerun'
assert all(sha(path)==digest for path,digest in bound.items())
actors = []
unavailable = []
for name in ['bnn_A0_native_only_K8','bnn_A0_feedback_K8']:
    actor = prior.parent/name
    receipt = actor/'completion.json'
    if receipt.exists() and read(receipt).get('passed'):
        actors.append(actor)
    else:
        unavailable.append(name)
if not actors:
    write(q/'completion.json',dict(passed=False,status='no_new_passed_sealed_BNN_actor',unavailable=unavailable,source_sha256=bound))
    sys.exit(1)
command = [sys.executable,str(D/'append_fused_resource_observations.py'),'--parent',str(parent),'--output',str(output)]
for actor in actors:
    command += ['--actor',str(actor)]
started = time.monotonic()
with (q/'archive.log').open('w') as log:
    child = subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    write(q/'status.json',dict(status='extracting_sealed_observations',pid=child.pid,start_ticks=process_identity(child.pid)['start_ticks']))
    code = child.wait()
assert code==0 and read(output/'completion.json')['passed']
points = read(output/'points.json')
front = [p for p in points if p['circuit']=='bnn' and not p['quality_dominated_by']]
groups = {}
for point in front:
    key = (point['CPD_ns'],point['wirelength'],point['SB_pairs'],point['CB_sources'])
    groups.setdefault(key,[]).append(point['id'])
counts = {}
for point in points:
    if point['arm'] in ['A0','R1']:
        continue
    if any(base['arm'] in ['A0','R1'] and base['quality_cohort']==point['quality_cohort'] and dominates(base,point) for base in points):
        counts[point['circuit']]=counts.get(point['circuit'],0)+1
report = D/'multiobjective_fused_resource_summary_01.json'
write(report,dict(passed=True,archive=str(output),records=len(points),
    BNN_observed_quality_groups=[dict(CPD_ns=key[0],wirelength=key[1],SB_pairs=key[2],CB_sources=key[3],records=value) for key,value in sorted(groups.items())],
    nonbaseline_records_quality_dominated_by_strong_baselines=counts,
    completed_actors={actor.name:read(actor/'completion.json') for actor in actors},
    unavailable_actors=unavailable,source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),output/'completion.json',output/'points.json']},
    qualification='Descriptive quality projection over actual same-input points, not a per-circuit history-best method score. Complete cold times remain unknown. Root, policy, implementation, traversal representation, convergence and repair opportunity remain explicit; a new own-current native control may strengthen the joint frontier too. No fixed matrix completion ends research.'))
write(q/'completion.json',dict(passed=True,output_archive=str(output),summary=str(report),actors=[str(actor) for actor in actors],
    unavailable_actors=unavailable,source_sha256=bound,complete_extraction_seconds=time.monotonic()-started,native_calls=0))
