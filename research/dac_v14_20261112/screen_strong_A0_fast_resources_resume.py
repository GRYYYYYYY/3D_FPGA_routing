#!/usr/bin/env python3
"""Reuse the completed current selector after a report-field naming failure."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_resource_bundle_v2 import select_cuts,serialize_request
b=D/'strong_A0_fast_resource_screen_01';reg=read(b/'registration.json');selection=read(b/'selection/completion.json');assert selection['passed'] and all(sha(p)==h for p,h in reg['source_sha256'].items()) and all(sha(p)==h for p,h in selection['source_sha256'].items());cuts=read(b/'selection/candidates.json');assert not (b/'completion.json').exists();bundles={}
for k in[1,4,8]:
 selected=select_cuts(cuts,k);text,domain,queries=serialize_request(selected)if selected else('','',[]);(b/f'K{k}.txt').write_text(text);(b/f'K{k}_domain.txt').write_text(domain);bundles[str(k)]=dict(actual_nets=len(selected),queries=queries,removed_pins={str(x['net']):x['pins']for x in selected},screened_removed_crossings=sum(x['removed_crossing_resources']for x in selected),minimum_margin_ns=min(x['minimum_margin_s']for x in selected)*1e9 if selected else None)
write(b/'report_field_failure.json',dict(status='report_only_field_name_mismatch',field_requested='min_setup_margin_ns',actual_selector_field='minimum_margin_s',selector_completed_and_reused=True,repeated_selector_calls=0,new_native_calls=0))
write(b/'completion.json',dict(passed=True,source_state=reg['source_state'],candidate_scopes=len(cuts),bundles=bundles,source_sha256={str(p):sha(p)for p in[Path(__file__).resolve(),b/'registration.json',b/'selection/completion.json',b/'selection/candidates.json',b/'report_field_failure.json',*[b/f'K{k}{suffix}.txt'for k in[1,4,8]for suffix in['','_domain']]]},native_calls=0,route_calls=0,qualification='Read-only potential screen; failed report assembly fixed without repeating completed selection or any native experiment. Margin is current worst-slack distance, not proof of candidate final timing.'))
print(dict(scopes=len(cuts),bundles=bundles),flush=True)
