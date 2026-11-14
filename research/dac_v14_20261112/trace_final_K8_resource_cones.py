#!/usr/bin/env python3
"""Trace current winning structures, distinguishing them from nonwinning fanin values."""
import resource,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_sta_arrival_cone_compact import select
resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));rows={};sources=[Path(__file__).resolve()]
for label,summary in [('A0_native_only_K8','strong_A0_native_only_K8_summary_01.json'),('A0_paired_K8','strong_A0_paired_K8_summary_01.json')]:
 s=read(D/summary);assert s['passed'];state=Path(s['final_state']);output=D/(label+'_final_cone_01.json');assert not output.exists();started=time.monotonic();r=select(state);r['complete_process_seconds']=time.monotonic()-started;write(output,r);assert r['passed'];old=D/'strong_A0_timing_trajectories_01/strict/round_003/feedback/cone.json';base=read(old);same=set(r['cones'])==set(base['cones'])and all(all(r['cones'][k][key]==base['cones'][k][key]for key in['nodes','edges','sources'])for k in r['cones']);rows[label]=dict(winning_structure_unchanged=same,full_fanin_and_value_records_equal=r['cones']==base['cones'],worst_endpoints_equal=r['selected_endpoints']==base['selected_endpoints'],critical_connections_equal=[(p['net'],p['pin'])for p in r['routed_connections']]==[(p['net'],p['pin'])for p in base['routed_connections']],selected_endpoints=len(r['selected_endpoints']),seconds=r['complete_process_seconds']);sources +=[D/summary,output,old]
write(D/'A0_K8_final_critical_structure_01.json',dict(passed=True,rows=rows,source_sha256={str(p):sha(p)for p in sources},native_calls=0,route_calls=0,qualification='Actual final native timing echoes, not inferred from flat CPD. Winning structure is separated from nonwinning fanin values; source clocks and full physical/STA remain those of each completed actor.'))
print(rows,flush=True)
