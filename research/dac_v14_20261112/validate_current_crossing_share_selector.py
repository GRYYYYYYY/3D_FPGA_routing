#!/usr/bin/env python3
"""Compare the new reusable current selector against all old frozen scope rows."""
import resource,time
from retained_prefix_workflow import D,read,write,sha
from full_route_graph_cache import FullRouteGraphCache
from current_crossing_share_selector import select
from run_native_scope_policy_v4 import run_dir
b=D/'current_crossing_share_selector_validation_01';b.mkdir(exist_ok=False);started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));old=D/'shared_crossing_scopes_01';r=read(old/'registration.json');rd=run_dir(__import__('pathlib').Path(r['states']['A0']));cmd=read(rd/'manifest.json')['command'];cache=FullRouteGraphCache(cmd[cmd.index('--read_rr_graph')+1],D/'full_route_graph_cache_bnn_01');results={}
write(b/'registration.json',dict(question='Does the algorithm-facing fresh-current selector reproduce the independent frozen derivation for every ranked scope on all three pristine states, with exact current resources?',source_sha256={str(p):sha(p) for p in [__file__,D/'current_crossing_share_selector.py',old/'completion.json']},native_calls=0,route_calls=0))
for name in ['A0','R1','Tf']:
 rows=select(r['states'][name],cache,b/name);ref=read(old/name/'candidates.json');keys=['net','pins','released_SB','released_CB','released_wire','released_nodes','retained_crossing_sources','removed_crossing_resources','minimum_margin_s','resource_per_sink','ordered_queries'];assert [{k:x[k] for k in keys} for x in rows]==[{k:x[k] for k in keys} for x in ref];results[name]=dict(scopes=len(rows),all_ranked_scopes_exact=True,first=[rows[0]['net'],rows[0]['pins']])
write(b/'completion.json',dict(passed=True,states=results,complete_process_seconds=time.monotonic()-started,source_sha256={str(p):sha(p) for p in [b/'registration.json',D/'current_crossing_share_selector.py',*[b/n/'completion.json' for n in results]]},native_calls=0,route_calls=0,qualification='Necessary selector refactor equivalence before integration; no repeated native experiment or new quality result.'))
print(results,flush=True)
