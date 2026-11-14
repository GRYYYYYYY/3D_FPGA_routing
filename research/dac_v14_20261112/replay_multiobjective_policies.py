#!/usr/bin/env python3
"""Independent fixed-budget policy replay of existing legal state observations.

This evaluates retention eligibility, not a newly executed routing trajectory.
"""
import math,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from multiobjective_acceptance_v2 import decide,RESOURCE_KEYS

start=time.monotonic();b=D/'multiobjective_policy_replay_01';b.mkdir(exist_ok=False)
archive=D/'multiobjective_archive_01';proof=read(archive/'completion.json');assert proof['passed']
assert all(sha(archive/n)==h for n,h in proof['artifact_sha256'].items())
points=read(archive/'points.json');anchors={'spmv':D/'native_endpoint_spmv_dev_01/A0','eltwise_layer':D/'native_endpoint_vector_dev_01/A0'}
files=[Path(__file__).resolve(),D/'multiobjective_acceptance_v2.py',archive/'completion.json',archive/'points.json']
write(b/'registration.json',dict(status='registered_before_policy_replay',question='Which previously rejected legal states meet explicit timing/resource tradeoffs without changing their historical acceptance?',
 anchor_states={k:str(v) for k,v in anchors.items()},policies=['timing_under_resources','resources_under_timing'],
 grid=dict(CPD_multiplier=[1.,1.01,1.03,1.05],extra_SB_pairs=[0,1,2,4,16],extra_CB_sources=[0,4,16],wire_limit_multiplier=1.05,resource_objectives=['wirelength','SB_pairs','CB_sources']),
 qualification='Uniform exploratory grid across both existing exact-vector cohorts, not per-circuit selected confirmation parameters. All points remain independently sourced. No native calls or state transitions; budget checks use fixed original anchors with no cumulative epsilon.',source_sha256={str(p):sha(p) for p in files}))
rows=[]
for circuit,state in anchors.items():
 before=read(state/'endpoint_vector.json');run=Path(read(state/'completion.json')['run']);anchor=next(p for p in points if p['run_manifest']==str(run/'manifest.json'))
 resources={k:anchor[k] for k in RESOURCE_KEYS};files.extend([state/'endpoint_vector.json',state/'completion.json'])
 for p in points:
  if p['quality_cohort']!=anchor['quality_cohort'] or not p['state']:continue
  after_path=Path(p['state'])/'endpoint_vector.json';after=read(after_path);files.append(after_path);other={k:p[k] for k in RESOURCE_KEYS}
  for cpdm in [1.,1.01,1.03,1.05]:
   for extra_sb in [0,1,2,4,16]:
    for extra_cb in [0,4,16]:
     caps=dict(wirelength=math.ceil(resources['wirelength']*1.05),SB_pairs=resources['SB_pairs']+extra_sb,CB_sources=resources['CB_sources']+extra_cb)
     for objective in RESOURCE_KEYS:
      decision=decide('resources_under_timing',before,after,resources,other,cpd_limit_s=before['cpd_s']*cpdm,resource_limits=caps,native_valid=p['status']=='legal',transaction_complete=True,resource_objectives=(objective,))
      rows.append(dict(circuit=circuit,point=p['id'],mode='resources_under_timing',objective=objective,CPD_multiplier=cpdm,extra_SB=extra_sb,extra_CB=extra_cb,accepted=decision['accepted'],reason=decision['reason']))
     decision=decide('timing_under_resources',before,after,resources,other,cpd_limit_s=before['cpd_s']*cpdm,resource_limits=caps,native_valid=True,transaction_complete=True)
     rows.append(dict(circuit=circuit,point=p['id'],mode='timing_under_resources',objective='CPD',CPD_multiplier=cpdm,extra_SB=extra_sb,extra_CB=extra_cb,accepted=decision['accepted'],reason=decision['reason']))
write(b/'decisions.json',rows)
write(b/'completion.json',dict(passed=True,decisions=len(rows),eligible_checks=sum(r['accepted'] for r in rows),
 eligible_distinct_points=sorted({r['point'] for r in rows if r['accepted']}),native_calls=0,accepted_state_transitions=0,
 source_sha256={str(p):sha(p) for p in set(files)},artifact_sha256={'decisions.json':sha(b/'decisions.json'),'registration.json':sha(b/'registration.json')},
 complete_process_seconds=time.monotonic()-start,qualification='Exact policy replay only. An eligible historical state is not a new repair result, search-success result or algorithm-runtime sample. New native intervention still required.'))
print(dict(decisions=len(rows),eligible_distinct_points=len({r['point'] for r in rows if r['accepted']})),flush=True)
