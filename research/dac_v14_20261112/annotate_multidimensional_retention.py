#!/usr/bin/env python3
"""Separate quality projection, matched full-time frontier and unresolved retention."""
import collections,copy,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

start=time.monotonic();parent=D/'multiobjective_archive_02';out=D/'multiobjective_archive_03';out.mkdir(exist_ok=False)
c=read(parent/'completion.json');assert c['passed'] and all(sha(parent/n)==h for n,h in c['artifact_sha256'].items())
points=read(parent/'points.json');byid={p['id']:p for p in points}
for p in points:
 # Preserve prior exact quality labels, but remove ambiguity of a generic
 # archive_retained flag which previously described only four quality axes.
 p['quality_projection_retained']=p['archive_retained']
 matched=[q for q in points if q['id']!=p['id'] and p['timing_cohort'] and q['timing_cohort']==p['timing_cohort'] and q['quality_cohort']==p['quality_cohort'] and q['convergence']==p['convergence'] and p['complete_single_configuration_seconds'] is not None and q['complete_single_configuration_seconds'] is not None]
 if p['matched_time_dominated_by']:
  assert matched
  for ident in p['matched_time_dominated_by']:
   a=byid[ident];assert a in matched and a['complete_single_configuration_seconds']<=p['complete_single_configuration_seconds']
   assert all(a[k]<=p[k] for k in ['wirelength','SB_pairs','CB_sources'])
  p['candidate_retention']='dominated_in_matched_five_dimensions'
  p['archive_retained']=False
 elif not matched:
  p['candidate_retention']='retained_pending_comparable_complete_runtime'
  p['archive_retained']=True
 else:
  p['candidate_retention']='retained_on_matched_five_dimensional_frontier'
  p['archive_retained']=True
 p['five_dimensional_comparison_count']=len(matched)
 p['record_preserved']=True
 p['retention_qualification']='Four quality axes exclude endpoint-vector differences. Full-time dominance requires the same measured timing cohort, physical inputs and convergence. Missing standalone repair time is unknown, not zero or an automatic loss. All evidence remains available even for dominated points.'
summary=dict(passed=True,records=len(points),parent=str(parent),counts=dict(collections.Counter(p['candidate_retention'] for p in points)),
 quality_dominated_but_retained=[p['id'] for p in points if p['quality_dominated_by'] and p['archive_retained']],
 exact_four_dimensional_counts=dict(collections.Counter(p['quality_status'] for p in points)),
 semantics='Development archive. Final candidates retained when quality/runtime tradeoff or missing comparability prevents matched five-dimensional rejection. Retained pending runtime is not a proved Pareto optimum. No actual experiment or historical decision rewritten.',
 native_calls=0,complete_process_seconds=time.monotonic()-start,source_sha256={str(Path(__file__).resolve()):sha(__file__),str(parent/'completion.json'):sha(parent/'completion.json'),str(parent/'points.json'):sha(parent/'points.json')})
write(out/'points.json',points)
# Mechanism guard: the physical-capacity point is quality-dominated, but its
# complete algorithm runtime is unknown and must not be rejected on five axes.
physical=next(p for p in points if p['arm']=='Tf_repair_physical_capacity')
assert physical['quality_status']=='dominated' and physical['archive_retained'] and physical['candidate_retention']=='retained_pending_comparable_complete_runtime'
summary['artifact_sha256']={'points.json':sha(out/'points.json')};write(out/'completion.json',summary)
print({k:summary[k] for k in ['records','counts','exact_four_dimensional_counts']},flush=True)
