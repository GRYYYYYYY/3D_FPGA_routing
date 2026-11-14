#!/usr/bin/env python3
"""Summarize observed joint quality tradeoffs without choosing configurations."""
import collections
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from pareto_archive_dimensions import dominates

archive=D/'multiobjective_archive_30'
completion=read(archive/'completion.json');assert completion['passed']
assert all(sha(archive/n)==h for n,h in completion['artifact_sha256'].items())
points=read(archive/'points.json');by_id={p['id']:p for p in points}
rows=[]
for p in points:
    baselines=[a for a in points if a['circuit']==p['circuit'] and a['quality_cohort']==p['quality_cohort'] and a['arm'] in ['A0','R1'] and a['id']!=p['id']]
    strong=[a['id'] for a in baselines if dominates(a,p)]
    rows.append(dict(id=p['id'],circuit=p['circuit'],arm=p['arm'],batch=p['batch'],convergence=p['convergence'],opportunity=p['opportunity'],
                     CPD_ns=p['CPD_ns'],CPD_interval_ns=p['CPD_interval_ns'],wirelength=p['wirelength'],SB_pairs=p['SB_pairs'],CB_sources=p['CB_sources'],
                     quality_status=p['quality_status'],strong_baseline_quality_dominated_by=strong,quality_dominated_by=p['quality_dominated_by'],
                     candidate_retention=p['candidate_retention'],complete_single_configuration_seconds=p['complete_single_configuration_seconds'],
                     timing_cohort=p['timing_cohort'],state=p['state']))
# List all equal-quality groups on the BNN observed frontier. This is an
# exhaustive descriptive projection, never a per-circuit configuration policy.
groups=collections.defaultdict(list)
for p in points:
    if p['circuit']=='bnn' and not p['quality_dominated_by']:
        groups[(p['CPD_ns'],tuple(p['CPD_interval_ns']),p['wirelength'],p['SB_pairs'],p['CB_sources'])].append(p['id'])
frontier=[dict(CPD_ns=k[0],CPD_interval_ns=list(k[1]),wirelength=k[2],SB_pairs=k[3],CB_sources=k[4],records=v) for k,v in sorted(groups.items())]
counts=collections.Counter(r['circuit'] for r in rows if r['strong_baseline_quality_dominated_by'] and r['arm'] not in ['A0','R1'])
write(D/'multiobjective_tradeoff_summary_10.json',dict(passed=True,archive=str(archive),records=len(rows),rows=rows,bnn_observed_quality_frontier=frontier,
    nonbaseline_records_quality_dominated_by_strong_baseline=dict(counts),
    qualification='Observed legal quality projection. Same input identity is required; convergence and repair opportunity remain separate row fields. This descriptive comparison is not a matched algorithm superiority claim. Missing complete time is never substituted by core, analysis, shared workflow or historical U time; such candidates remain provisionally retained. Rounded CPD overlaps stay uncertain. Duplicate repeats/states are not independent configurations. Fixed architecture occupancy is not silicon area or power.',
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'pareto_archive_dimensions.py',archive/'points.json',archive/'completion.json']}))
print(dict(records=len(rows),strong_baseline_dominated_nonbaseline_records=dict(counts),bnn_frontier_groups=len(frontier)))
