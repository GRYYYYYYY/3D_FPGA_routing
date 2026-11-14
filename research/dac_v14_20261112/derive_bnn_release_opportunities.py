#!/usr/bin/env python3
"""Map audited capacity gaps to actual owner branches and current STA slack."""
import collections,json,resource,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,downstream_pins
from immutable_rr_audit_cache import GraphAuditCache
sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace

start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3))
b=D/'bnn_slack_release_screen_01';out=b/'owner_slack';out.mkdir(exist_ok=False)
capacity=read(b/'Tf_capacity/analysis.json');relaxed=read(b/'Tf_relaxed/analysis.json')
for r in [capacity,relaxed]:assert r['passed'] and all(sha(p)==h for p,h in r['source_sha256'].items())
caps={(r['net'],r['pin']):r for r in capacity['results']}
selected=[r for r in relaxed['results'] if r['physical_seconds']<caps[r['net'],r['pin']]['physical_seconds']]
reg=read(b/'Tf_capacity/execution_registration.json');source=Path(reg['input_run']);state=D/'timing_cone_bnn_dev_01/Tf';v=read(state/'endpoint_vector.json');m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
files=[Path(__file__).resolve(),b/'Tf_capacity/analysis.json',b/'Tf_relaxed/analysis.json',source/'routed.route',source/'native_sta_frontier.jsonl',state/'endpoint_vector.json',D/'coordinated_repair_tree.py',D/'rr_audit_cache_bnn_01/completion.json']
write(out/'registration.json',dict(status='registered_before_owner_analysis',question='Which currently occupying branches explain the measured BNN capacity gaps, and what full-precision pin slack do they have relative to the original fixed timing cap?',source_sha256={str(p):sha(p) for p in files},native_calls=0,new_queries=0,
 qualification='Pin-slack margin is a screening proxy, not a guarantee that a physical detour meets endpoint timing. Final native FULL/STA and fixed batch budgets remain mandatory.'))
g=GraphAuditCache(graph,D/'rr_audit_cache_bnn_01');traces=read_trace(source/'routed.route');affected={}
for r in selected:
 for node,c in r['capacity_conflicts'].items():
  for net in c['other_nets']:affected.setdefault(net,set()).add(int(node))
trees={net:from_trace(traces[net]['trace'],g.switches) for net in affected};sta={}
for line in (source/'native_sta_frontier.jsonl').open():
 p=json.loads(line)
 if p.get('type')=='pin' and not p['driver'] and p['net'] in affected:sta[p['net'],p['pin']]=p
rows=[];baseline_worst=v['metrics']['least_slack_s']
for r in sorted(selected,key=lambda r:(-(caps[r['net'],r['pin']]['physical_seconds']-r['physical_seconds']),r['net'],r['pin'])):
 owners=collections.defaultdict(set)
 for node,c in r['capacity_conflicts'].items():
  for net in c['other_nets']:owners[net].add(int(node))
 releases=[]
 for net,nodes in sorted(owners.items()):
  pins=set().union(*(downstream_pins(trees[net],node) for node in nodes));assert pins
  pins_rows=[]
  for pin in sorted(pins):
   p=sta[net,pin];slack=p['setup_slack_s'];known=isinstance(slack,(int,float))
   pins_rows.append(dict(pin=pin,slack_s=slack,raw_criticality=p['setup_criticality_raw'],ignored=p['ignored'],global_net=p['global'],
    slack_margin_to_current_worst_s=slack-baseline_worst if known else None,
    screening_margin_at_fixed_1pct_CPD_cap_s=slack-baseline_worst+.01*v['cpd_s'] if known else None,native_delay_s=p['native_net_delay_s']))
  releases.append(dict(net=net,scarce_nodes=sorted(nodes),affected_sink_pins=pins_rows,
   all_current_slack_margins_positive=all(p['slack_margin_to_current_worst_s'] is not None and p['slack_margin_to_current_worst_s']>0 for p in pins_rows)))
 rows.append(dict(target=[r['net'],r['pin']],current_delay_s=r['current_physical_seconds'],capacity_delay_s=caps[r['net'],r['pin']]['physical_seconds'],
  relaxed_delay_s=r['physical_seconds'],capacity_gap_ns=(caps[r['net'],r['pin']]['physical_seconds']-r['physical_seconds'])*1e9,
  blocked_resources=r['capacity_conflicts'],owner_release_scope=releases,relaxed_suffix_nodes=r['suffix_nodes'],relaxed_suffix_switches=r['suffix_switches']))
write(out/'completion.json',dict(passed=True,rows=rows,input_state=str(state),current_cpd_s=v['cpd_s'],constraints_sha256=v['constraints_sha256'],
 graph_sha256=g.receipt['graph_sha256'],source_sha256={str(p):sha(p) for p in files},native_calls=0,new_queries=0,
 complete_analysis_seconds=time.monotonic()-start,qualification='Actual blocked resources and all descendant owner pins. Source is pristine Tf, not any later accepted state. Revalidate identities/current occupancy after a state change; no owner replacement or combined feasibility proved.'))
print([dict(target=r['target'],gap_ns=r['capacity_gap_ns'],owners=[(x['net'],len(x['affected_sink_pins']),x['all_current_slack_margins_positive']) for x in r['owner_release_scope']]) for r in rows],flush=True)
