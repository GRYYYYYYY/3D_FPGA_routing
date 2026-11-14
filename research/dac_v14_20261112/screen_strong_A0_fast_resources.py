#!/usr/bin/env python3
"""Measure current structural/slack scope after the completed strong-A0 timing path."""
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from full_route_graph_cache import FullRouteGraphCache
from current_crossing_share_selector_v2 import select
from current_resource_bundle_v2 import select_cuts,serialize_request
from run_native_scope_policy_v4 import run_dir
b=D/'strong_A0_fast_resource_screen_01';b.mkdir(exist_ok=False);started=time.monotonic();proof=D/'strong_A0_policy_equivalence_01.json';assert read(proof)['passed'];terminal=D/'strong_A0_timing_trajectories_01/strict/completion.json';c=read(terminal);assert c['passed'];source=Path(c['final_state']);r=run_dir(source);m=read(r/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);cache=D/'full_route_graph_cache_bnn_01';files=[Path(__file__).resolve(),proof,terminal,source/'completion.json',source/'endpoint_vector.json',r/'manifest.json',r/'routed.route',r/'independent_audit.json',D/'current_crossing_share_selector_v2.py',D/'current_resource_bundle_v2.py',cache/'completion.json'];bound={str(p):sha(p)for p in files};write(b/'registration.json',dict(source_state=str(source),question='After the lowest-wire strong-A0 three-step timing trajectory, do the unchanged slack-bearing sharing scopes still offer resource targets, and can timing repair followed by current-state resource repair improve the joint frontier?',source_sha256=bound,native_calls=0,route_calls=0,qualification='Read-only current selector screening. Structural cut resources are not feasible savings; no quality or timing-runtime improvement inferred. Existing running/queued experiments remain unchanged.'))
g=FullRouteGraphCache(graph,cache);cuts=select(source,g,b/'selection');bundles={}
for k in [1,4,8]:
 selected=select_cuts(cuts,k);text,domain,queries=serialize_request(selected)if selected else('','',[]);(b/f'K{k}.txt').write_text(text);(b/f'K{k}_domain.txt').write_text(domain);bundles[str(k)]=dict(actual_nets=len(selected),queries=queries,removed_pins={str(x['net']):x['pins']for x in selected},screened_removed_crossings=sum(x['removed_crossing_resources']for x in selected),min_setup_margin_ns=min(x['min_setup_margin_ns']for x in selected)if selected else None)
assert all(sha(p)==h for p,h in bound.items());write(b/'completion.json',dict(passed=True,source_state=str(source),CPD_ns=c['final_CPD_s']*1e9,resources=c['final_resources'],candidate_scopes=len(cuts),bundles=bundles,source_sha256=bound,complete_screen_seconds=time.monotonic()-started,native_calls=0,route_calls=0,qualification='Potential current resource scope on a sealed algorithmically obtained timing state, not a new feasible candidate or a full cold algorithm result. All frozen controls preserved.'))
print(dict(scopes=len(cuts),bundles=bundles),flush=True)
