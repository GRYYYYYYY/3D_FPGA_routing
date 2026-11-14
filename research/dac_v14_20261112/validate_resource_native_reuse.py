#!/usr/bin/env python3
"""Reuse a completed physical native transaction, rejecting changed semantic controls."""
import copy
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_native_reuse_resource import match
b=D/'strong_A0_native_reuse_validation_01';tx=b/'transaction';role=read(tx/'registration.json')['roles']['current_group'];pilot=D/'strong_native_A0_timing_pilot_01';hit=match(role,[pilot]);assert hit and Path(hit['evaluation'])==pilot/'joint_current_scope_evaluation';bad_pressure=copy.deepcopy(role);bad_pressure['pressure_start']=2.;assert match(bad_pressure,[pilot]) is None
fake=b/'domain_mismatch';fake.mkdir();r=read(pilot/'registration.json');r['roles']={k:dict(v,crossing_reuse_enabled=True) for k,v in r['roles'].items()};write(fake/'registration.json',r);assert match(role,[fake]) is None;write(b/'completion.json',dict(passed=True,exact_existing_request_native_result_reused=True,actual_native_binary='resource_domain_stage_01',changed_pressure_rejected=True,domain_restriction_mismatch_rejected=True,native_calls=0,route_calls=0,source_sha256={str(p):sha(p) for p in [__file__,D/'current_native_reuse_resource.py',tx/'registration.json',pilot/'registration.json',pilot/'joint_current_scope_decisions.json',pilot/'joint_current_scope_evaluation/completion.json']},qualification='Completed same-state/query/objective/resource-stage binary result reused exactly with new policy decisions. Different pressure or crossing-domain semantics not silently treated as equivalent. No repeated native experiment or borrowed creation time.'))
print(dict(passed=True,evaluation=hit['evaluation']),flush=True)
