#!/usr/bin/env python3
"""Preserve endpoint-tail differences omitted by the four-axis Pareto projection."""
import math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import compare
s=read(D/'bnn_selected_group_summary_01.json');rows=[];bound={str(p):sha(p) for p in [Path(__file__).resolve(),D/'bnn_selected_group_summary_01.json',D/'endpoint_timing_policy.py']}
for row in s['rows']:
 old=Path(row['old_evaluation'])/'endpoint_vector.json';new=Path(row['evaluation'])/'endpoint_vector.json';v=read(new);o=read(old);x=compare(o,v);assert x['compatible']
 finite={k:z for k,z in v['setup'].items() if isinstance(z,(int,float)) and math.isfinite(z)};oldfinite={k:z for k,z in o['setup'].items() if isinstance(z,(int,float)) and math.isfinite(z)};worst=min(finite.values());oldworst=min(oldfinite.values());reg=[c for c in x['changes'] if c['kind']=='setup' and c['delta_s']<0]
 near={}
 for ns in [.01,.05,.1,.2]:
  before={k for k,z in oldfinite.items() if z-oldworst<=ns*1e-9};after={k for k,z in finite.items() if z-worst<=ns*1e-9};near[str(ns)]=dict(before_count=len(before),after_count=len(after),entered=len(after-before),left=len(before-after),regressed_in_after=sum(c['endpoint_domain'] in after for c in reg))
 rows.append(dict(baseline=row['baseline'],old_evaluation=row['old_evaluation'],selected_evaluation=row['evaluation'],selected_vs_all_positive_setup_improved=x['setup_improved'],selected_vs_all_positive_setup_regressed=x['setup_regressed'],hold_violation_regressions=x['hold_violation_regressions'],worst_regression_ps=max([-c['delta_s']*1e12 for c in reg],default=0),closest_regressed_to_selected_worst_ns=min([(c['after_s']-worst)*1e9 for c in reg],default=None),near_endpoints=near,changes=x['changes']))
 for p in [old,new]:bound[str(p)]=sha(p)
write(D/'bnn_selected_group_vector_analysis_01.json',dict(passed=True,rows=rows,source_sha256=bound,native_calls=0,qualification='Exact same-endpoint/domain/constraint comparison. Four quality archive axes omit these vector differences; equal CPD and lower wire do not imply every endpoint improves. No new route/STA processes.'))
print([{k:v for k,v in r.items() if k!='changes'} for r in rows])
