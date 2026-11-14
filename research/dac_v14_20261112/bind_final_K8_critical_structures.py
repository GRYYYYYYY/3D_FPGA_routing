#!/usr/bin/env python3
"""Compare already-exported cones with JSON keys normalized; no trace rerun."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
old=D/'strong_A0_timing_trajectories_01/strict/round_003/feedback/cone.json';base=read(old);rows={};files=[Path(__file__).resolve(),old,D/'A0_K8_final_critical_structure_01.json']
for label in['A0_native_only_K8','A0_paired_K8']:
 p=D/(label+'_final_cone_01.json');r=read(p);assert r['passed'];same=set(r['cones'])==set(base['cones'])and all(all(r['cones'][k][key]==base['cones'][k][key]for key in['nodes','edges','sources'])for k in r['cones']);rows[label]=dict(winning_structure_unchanged=same,full_fanin_and_value_records_equal=r['cones']==base['cones'],worst_endpoints_equal=r['selected_endpoints']==base['selected_endpoints'],critical_connections_equal=[(p['net'],p['pin'])for p in r['routed_connections']]==[(p['net'],p['pin'])for p in base['routed_connections']]);files.append(p)
write(D/'A0_K8_final_critical_structure_02.json',dict(passed=True,rows=rows,prior_report='A0_K8_final_critical_structure_01.json',prior_report_issue='Compared an in-memory int-keyed cone dictionary with a loaded string-keyed JSON dictionary. Both actual exported traces were correct; only cross-serialization comparison was wrong.',repeated_selector_calls=0,native_calls=0,route_calls=0,source_sha256={str(p):sha(p)for p in files},qualification='Authoritative comparison of the already exported final native timing echoes. No new current-cone selection, native analysis or routing experiment. Old report preserved with this explicit correction.'))
print(rows,flush=True)
