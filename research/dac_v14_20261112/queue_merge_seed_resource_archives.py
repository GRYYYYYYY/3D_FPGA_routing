#!/usr/bin/env python3
"""Merge two real archive branches after the registered resource extraction owner ends."""
import collections
import csv
import fcntl
import os
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from export_policy_analysis_pool import process_identity
from pareto_archive_dimensions import annotate

q=D/'merge_seed_resource_archive_queue_01'
q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
prior=D/'fused_resource_archive_queue_01'
owner=read(prior/'registration.json')
seed=D/'multiobjective_seed_order_diag_01'
assert read(seed/'completion.json')['passed']
bound={str(path):sha(path) for path in [Path(__file__).resolve(),D/'pareto_archive_dimensions.py',prior/'registration.json',seed/'completion.json',seed/'points.json']}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bound,prerequisite_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),
    output_archive=str(D/'multiobjective_merged_seed_resource_01'),native_calls=0,
    question='Merge all legal seed-policy diagnostics and extended native/domain resource trajectories into one strong-baseline population without duplicating common ancestors or combining times.',
    qualification='Single writer for a new merged artifact only. Previous archives, source cohorts, manuscript and shared handoff remain unchanged. Derived dominance annotations are recomputed; conflicting core provenance fails instead of silently choosing a row.'))
write(q/'status.json',dict(status='waiting_for_registered_resource_archive_owner'))
while True:
    actual=process_identity(owner['pid'])
    if not actual or actual['state']=='Z' or actual['start_ticks']!=owner['start_ticks']:break
    time.sleep(15)
assert (prior/'completion.json').exists(),'Missing terminal archive receipt: reconcile, do not duplicate extraction'
assert read(prior/'completion.json')['passed']
assert all(sha(path)==digest for path,digest in bound.items())
resource=Path(read(prior/'completion.json')['output_archive'])
derived={'quality_dominated_by','nominal_quality_dominated_by','matched_time_dominated_by','quality_projection_retained',
    'quality_status','candidate_retention','archive_retained','record_preserved','five_dimensional_comparison_count','retention_qualification'}
points={};duplicates=[]
for archive in [seed,resource]:
    receipt=read(archive/'completion.json')
    assert receipt['passed'] and all(sha(archive/name)==digest for name,digest in receipt['artifact_sha256'].items())
    for point in read(archive/'points.json'):
        ident=point['id'];core={key:value for key,value in point.items() if key not in derived}
        if ident in points:
            assert core=={key:value for key,value in points[ident].items() if key not in derived},'Conflicting physical/configuration provenance for '+ident
            duplicates.append(ident)
        else:points[ident]=point
out=D/'multiobjective_merged_seed_resource_01'
out.mkdir(exist_ok=False)
values=annotate(list(points.values()))
write(out/'points.json',values)
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','convergence','opportunity','quality_status','candidate_retention','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as stream:
    writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows({key:point.get(key) for key in fields} for point in values)
write(out/'merge_provenance.json',dict(parents=[str(seed),str(resource)],duplicate_common_observations=len(duplicates),common_ids=duplicates,
    core_provenance_strictly_equal=True,derived_annotations_recomputed=sorted(derived),no_time_values_combined=True))
write(out/'completion.json',dict(passed=True,records=len(values),parents=[str(seed),str(resource)],
    quality_counts=dict(collections.Counter(point['quality_status'] for point in values)),retention_counts=dict(collections.Counter(point['candidate_retention'] for point in values)),
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),D/'pareto_archive_dimensions.py',seed/'completion.json',seed/'points.json',resource/'completion.json',resource/'points.json']},
    artifact_sha256={name:sha(out/name) for name in ['points.json','points.csv','merge_provenance.json']},native_calls=0,
    qualification='Legal state archive across explicit versions/roots/opportunities. Includes stronger native controls and single-transaction diagnostics; no per-circuit history-best configuration, mathematical resource bound, cold timing or algorithm-superiority claim. Missing whole runtime remains unknown.'))
groups=collections.defaultdict(list)
for point in values:
    if point['circuit']=='bnn' and not point['quality_dominated_by']:
        groups[(point['CPD_ns'],point['wirelength'],point['SB_pairs'],point['CB_sources'])].append(point['id'])
summary=D/'multiobjective_merged_seed_resource_summary_01.json'
write(summary,dict(passed=True,archive=str(out),records=len(values),
    BNN_observed_quality_groups=[dict(CPD_ns=key[0],wirelength=key[1],SB_pairs=key[2],CB_sources=key[3],records=ids) for key,ids in sorted(groups.items())],
    root_A0_R1_records=[point['id'] for point in values if point['arm'] in ['A0','R1']],
    own_current_native_control_records=[point['id'] for point in values if 'native_only' in point.get('batch','')],
    source_sha256={str(path):sha(path) for path in [out/'completion.json',out/'points.json']},
    qualification='Union population with external roots and own-current native controls. Single-transaction seed diagnostics remain separate from automatic pristine-root method configurations. Candidate quality dominance omits unknown comparable full runtime.'))
write(q/'completion.json',dict(passed=True,output_archive=str(out),summary=str(summary),records=len(values),source_sha256=bound,native_calls=0))
