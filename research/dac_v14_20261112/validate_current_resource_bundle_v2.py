#!/usr/bin/env python3
"""Bind the actual controller's helper to frozen independently generated requests."""
from retained_prefix_workflow import D,read,write,sha
from current_resource_bundle_v2 import select_cuts,serialize_request
candidates=read(D/'pooled_resource_repair_dev_01/R1_fast/round_000/selection/candidates.json');rows=[]
for size in [1,4,8]:
 selected=select_cuts(candidates,size);request,domain,queries=serialize_request(selected);old=D/f'current_resource_bundle_validation_01/K{size}';assert request==(old/'request.txt').read_text() and domain==(old/'domain.txt').read_text();rows.append(dict(size=size,nets=[r['net'] for r in selected],exact_frozen_request=True))
for start in [0,1,2]:
 selected=select_cuts(candidates,8,start);assert len(selected)==8 and len({r['net'] for r in selected})==8;assert selected[0]==candidates[start]
assert select_cuts(candidates,4,len(candidates))==[]
write(D/'current_resource_bundle_validation_02.json',dict(passed=True,rows=rows,rank_windows_checked=[0,1,2],empty_window_checked=True,source_sha256={str(p):sha(p) for p in [__file__,D/'current_resource_bundle_v2.py',D/'current_resource_bundle_validation_01/completion.json',D/'pooled_resource_repair_dev_01/R1_fast/round_000/selection/candidates.json']},native_calls=0,qualification='Controller helper exactly reproduces independent registered K1/4/8 request/domain fixtures and excludes same-net overlap within windows. No whole candidate feasibility or quality inferred.'))
print(rows,flush=True)
