#!/usr/bin/env python3
"""Current-STA shared-sink IPIN potential with slack-offset bottleneck matching.

All entrance alternatives are queried in one graph-loading process. Matching
ignores conflicts before the IPIN and is only an optimistic routing reference.
"""
import argparse,array,collections,json,math,resource,shutil,signal,struct,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from current_sta_selector import select
from run_native_frontier_queries import make_case,write_cases,fingerprint,groups as output_groups
from coordinated_repair_tree import from_trace,prune_sinks,nodes,prefixes
from verify_path_witnesses_v2 import graph_records,f32
from timing_budget_matching import bottleneck,assignment_at
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);p.add_argument('--gain-reference',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);p.add_argument('--extra-prune-file',type=Path,required=True);p.add_argument('--reuse-reference',type=Path,required=True);a=p.parse_args()
started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800);assert shutil.disk_usage(D).free>=80*1024**3
state=a.state.resolve();g=a.gain_reference.resolve();b=a.batch.resolve();b.mkdir(exist_ok=False);source=Path(read(state/'completion.json')['run']);assert read(state/'completion.json')['passed']
gain=read(g/'analysis.json');assert gain['passed'] and all(sha(p)==h for p,h in gain['source_sha256'].items())
assert route_body(Path(read(g/'execution_registration.json')['input_run'])/'routed.route')==route_body(source/'routed.route')
base=select(source/'native_sta_frontier.jsonl');base_keys={(r['net'],r['pin']) for r in base['targets']};gc={(c['net'],c['pin']):c for c in read(g/'cases.json')}
positive=[r for r in gain['results'] if r['mode']==0 and r['improvement_ns']>1e-6 and (r['net'],r['pin']) in base_keys];assert positive
groups=collections.defaultdict(list)
for r in positive:groups[gc[r['net'],r['pin']]['sink']].append(r)
sink,focus=max(groups.items(),key=lambda p:(len(p[1]),max(r['improvement_ns'] for r in p[1]),-p[0]))
near_ns=max(r['improvement_ns'] for r in focus);selected=select(source/'native_sta_frontier.jsonl',near_ns)
selected['targets']=[r for r in selected['targets'] if r['sink']==sink];assert len(selected['targets'])>=2
assert len({r['net'] for r in selected['targets']})==len(selected['targets']),'Same-net multi-pin model requires another transaction representation'
manifest=read(source/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);assert sha(graph)==manifest['shared_inputs'][str(graph)]['sha256']
binary=D/'residual_query_offline_01/graph.bin';driver=D/'current_sta_queries_01/critical_capacity_driver';assert sha(binary)==read(binary.with_name('graph_binding.json'))['binary_graph_sha256'];assert sha(driver)==read(driver.parent/'execution.json')['output_sha256']['critical_capacity_driver']
extra=read(a.extra_prune_file);assert all(sha(p)==h for p,h in extra['source_sha256'].items());extra_pins={int(n):pins for n,pins in extra['extra_prune_by_net'].items()}
oldref=a.reuse_reference.resolve();oldcomplete=read(oldref/'completion.json');assert oldcomplete['passed'] and all(sha(p)==h for p,h in oldcomplete['source_sha256'].items())
assert oldcomplete['source_sha256'][str(driver)]==sha(driver) and oldcomplete['source_sha256'][str(binary)]==sha(binary)
files=[a.extra_prune_file,oldref/'completion.json',D/'coordinated_repair_tree.py',Path(__file__),D/'timing_budget_matching.py',D/'test_timing_budget_matching.py',D/'run_native_frontier_queries.py',D/'current_sta_selector.py',D/'native_timing_budget_scope_experiment_01.json',state/'completion.json',state/'endpoint_vector.json',source/'routed.route',source/'native_sta_frontier.jsonl',graph,binary,driver,g/'analysis.json',g/'cases.json']
bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(status='registered_before_queries',state=str(state),input_run=str(source),sink=sink,selection=selected,near_ns=near_ns,extra_prune_by_net=extra_pins,reuse_reference=str(oldref),focus=[(r['net'],r['pin']) for r in focus],
 question='Can current near-critical connections sharing the selected SINK choose distinct physical IPINs with a better slack-offset bottleneck when victim prefixes may move?',
 objective='min max_i (new_physical_delay_i - current_physical_delay_i + worst_current_slack - current_slack_i); proxy only, not endpoint STA.',
 relaxation='Each net retains its other branches. All other net occupancy is relaxed; matching enforces only actual IPIN and common SINK capacity, not shared preceding RR resources. No native calls.',
 query_aliases='Each (net, entrance_index) is a diagnostic output label; original net_pin and IPIN stored in query_map.json. Driver uses labels only for output.',
 limits=dict(query_process_seconds=900,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3),source_sha256=bindings))
caps=array.array('I');kinds=[];switches={}
for section,e in graph_records(graph):
 t=e.find('timing');v={} if t is None else t.attrib
 if section=='switches':
  assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal']);switches[int(e.attrib['id'])]=f32(v.get('Tdel',0))
 elif section=='rr_nodes':
  assert all(f32(v.get(k,0))==0 for k in ['R','C']);assert int(e.attrib['id'])==len(caps);caps.append(int(e.attrib['capacity']));kinds.append(e.attrib['type'])
 else:break
with binary.open('rb') as f:
 h=f.read(36);assert h[:8]==b'H3DRQ001';n=struct.unpack_from('<I',h,8)[0];m=struct.unpack_from('<Q',h,12)[0];assert n==len(caps);f.seek(36+20*n);edge_data=f.read();assert len(edge_data)==16*m
entrances={}
for u,v,w in struct.iter_unpack('<IId',edge_data):
 if v==sink:entrances[u]=min(w,entrances.get(u,math.inf))
del edge_data
assert entrances and all(kinds[u]=='IPIN' for u in entrances) and caps[sink]>=len(selected['targets'])
traces=read_trace(source/'routed.route');owners=collections.defaultdict(list)
for net,info in traces.items():
 for node in {r.inode for r in info['trace']}:owners[node].append(net)
original=[make_case(r,traces,kinds,switches,owners,caps) for r in selected['targets']]
assert set(extra_pins)<={c['net'] for c in original}
for c in original:
 if c['net'] not in extra_pins:continue
 tree=from_trace(traces[c['net']]['trace'],switches);released=set(extra_pins[c['net']])|{c['pin']};assert released<=tree['sinks'].keys()
 kept=prune_sinks(tree,released);retained=nodes(kept);prefix=prefixes(kept)
 c.update(retained=sorted(retained),removed=sorted(set(c['original_nodes'])-retained),anchors={str(n):prefix[n] for n in retained if kinds[n] not in ['SINK','IPIN']},other_sinks=sorted(set(kept['sinks'].values())),extra_removed_pins=sorted(released-{c['pin']}))
 assert c['root'] in retained and c['sink'] not in retained
write(b/'original_cases.json',original)
zero={i for i,c in enumerate(caps) if c==0};qcases=[];mapping={}
for c in original:
 for index,(ipin,tail) in enumerate(sorted(entrances.items()),1):
  item=dict(c,net=c['net'],pin=index,sink=ipin,blocked=sorted(zero));qcases.append(item)
  mapping[c['net'],index]=dict(net=c['net'],pin=c['pin'],ipin=ipin,tail_delay_s=tail,original_sink=sink)
write(b/'query_map.json',list(mapping.values()));write_cases(b/'queries.txt',qcases)
cache={};oldlogs=output_groups(oldref/'stdout.log');old_entrances=sorted(map(int,read(oldref/'capacity_and_selection.json')['entrances']))
for c in read(oldref/'original_cases.json'):
 for index,ipin in enumerate(old_entrances,1):
  item=dict(c,net=c['net'],pin=index,sink=ipin,blocked=sorted(zero));cache[fingerprint(item,1)]=oldlogs[c['net'],index,1]
answers={};missing=[];reuse=[]
for c in qcases:
 key=(c['net'],c['pin'],1);hit=cache.get(fingerprint(c,1))
 if hit:answers[key]=hit
 else:missing.append(c)
 reuse.append(dict(net=c['net'],query_alias=c['pin'],ipin=c['sink'],reused=bool(hit),fingerprint=fingerprint(c,1)))
newkeys={(c['net'],c['pin']) for c in missing};query_process_seconds=0.
if missing:
 write_cases(b/'missing.txt',missing);t=time.monotonic()
 with (b/'new.log').open('w') as out,(b/'stderr.log').open('w') as err:proc=subprocess.run([str(driver),str(binary),str(b/'missing.txt'),'capacity'],stdout=out,stderr=err,timeout=900)
 query_process_seconds=time.monotonic()-t;assert proc.returncode==0;answers.update(output_groups(b/'new.log'))
else:(b/'stderr.log').write_text('')
with (b/'stdout.log').open('w') as f:
 for key in sorted(answers):f.writelines(answers[key])
write(b/'reuse_receipts.json',dict(source=str(oldref),queries=reuse,source_sha256={str(oldref/n):sha(oldref/n) for n in ['completion.json','stdout.log','original_cases.json','capacity_and_selection.json']}))
rows={};paths=collections.defaultdict(list)
for line in (b/'stdout.log').open():
 v=line.split();key=tuple(map(int,v[1:3]));assert int(v[3])==1 and key in mapping
 if v[0]=='RESULT':
  assert key not in rows;rows[key]=dict(**mapping[key],stop=int(v[4]),expansions=int(v[5]),cost_to_ipin_s=float(v[8]),lower_to_ipin_s=float(v[9]),core_seconds=float(v[10]),edge_count=int(v[11]))
 else:assert v[0]=='EDGE' and int(v[4])==len(paths[key]);paths[key].append((int(v[5]),int(v[6]),float(v[7])))
assert rows.keys()==mapping.keys();by_net={c['net']:c for c in original};matrix={n:{} for n in by_net};wanted={(u,sink,w) for u,w in entrances.items()};all_options=[]
for key,r in rows.items():
 assert r['stop'] in [0,2],'Query limit is unknown, not infeasibility'
 if r['stop']==2:assert r['edge_count']==0;continue
 path=paths[key];c=by_net[r['net']];assert r['cost_to_ipin_s']==r['lower_to_ipin_s']
 assert path[0][0]==r['ipin'] and path[-1][1]==n and len(path)==r['edge_count']
 assert all(x[1]==y[0] for x,y in zip(path,path[1:])) and len({x[0] for x in path})==len(path)
 assert not {x[0] for x in path}&zero and all(x[0] not in set(c['retained']) for x in path[:-1])
 assert abs(sum(x[2] for x in path)-r['cost_to_ipin_s'])<1e-23
 assert abs(float(c['anchors'][str(path[-1][0])])-path[-1][2])<1e-23
 forward=[path[-1][0]]+[x[0] for x in reversed(path[:-1])]+[sink];weights=[x[2] for x in reversed(path[:-1])]+[r['tail_delay_s']]
 assert len(forward)==len(set(forward));cost=r['cost_to_ipin_s']+r['tail_delay_s'];matrix[r['net']][r['ipin']]=cost
 wanted.update((v,u,w) for u,v,w in path[:-1]);r.update(cost_s=cost,forward=forward,weights=weights,prefix_s=path[-1][2]);all_options.append(r)
# Audit all newly returned edges and all actual capacities against the XML once.
seen={};checked_caps=0
for section,e in graph_records(graph):
 at=e.attrib
 if section=='rr_nodes':assert caps[int(at['id'])]==int(at['capacity']);checked_caps+=1
 elif section=='rr_edges':
  sw=int(at['switch_id']);edge=int(at['src_node']),int(at['sink_node']),switches[sw]
  if edge in wanted:seen[edge]=min(sw,seen.get(edge,sw))
assert wanted==seen.keys() and checked_caps==len(caps)
for r in all_options:r['switches']=[seen[u,v,w] for u,v,w in zip(r['forward'],r['forward'][1:],r['weights'])]
sta={r['net']:r for r in selected['targets']};offset={net:base['worst_slack_s']-sta[net]['slack_s']-c['current_physical_seconds'] for net,c in by_net.items()};ipin_caps={i:int(caps[i]) for i in entrances}
result=bottleneck(matrix,ipin_caps,offset);assert result['status']=='optimal'
chosen=[next(r for r in all_options if r['net']==net and r['ipin']==ipin) for net,ipin in result['assignment'].items()]
path_owners=collections.defaultdict(set)
for r in chosen:
 for node in set(by_net[r['net']]['retained'])|set(r['forward']):path_owners[node].add(r['net'])
conflicts={str(node):dict(nets=sorted(nets),capacity=int(caps[node])) for node,nets in path_owners.items() if len(nets)>caps[node]}
write(b/'options.json',all_options);write(b/'matching.json',dict(**result,offsets_s=offset,chosen=chosen,selected_tree_conflicts=conflicts,initial_proxy=0.,sink_capacity=int(caps[sink])))
write(b/'capacity_and_selection.json',dict(sink=sink,entrances=entrances,capacities=ipin_caps,selection=selected))
for name in ['reuse_receipts.json','registration.json','original_cases.json','query_map.json','queries.txt','stdout.log','stderr.log','options.json','matching.json','capacity_and_selection.json']:bindings[str(b/name)]=sha(b/name)
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=True,status='current_STA_IPIN_matching_reference',agents=len(original),ipins=len(entrances),new_queries=len(missing),reused_queries=len(rows)-len(missing),total_queries=len(rows),extra_prune_by_net=extra_pins,exact_queries=sum(r['stop']==0 for r in rows.values()),unreachable_queries=sum(r['stop']==2 for r in rows.values()),query_process_seconds=query_process_seconds,query_core_seconds=sum(r['core_seconds'] for key,r in rows.items() if key in newkeys),historical_core_seconds=sum(r['core_seconds'] for key,r in rows.items() if key not in newkeys),complete_process_seconds=time.monotonic()-started,
 proxy_bottleneck_delta_s=result['objective'],matching_has_strict_proxy_gain=result['objective']<0,selected_tree_conflicts=len(conflicts),source_sha256=bindings,native_calls=0,
 qualification='Optimal assignment of exact fixed-own-tree per-IPIN distances for the selected shared-SINK group, with all other occupancy relaxed and only IPIN/SINK capacities imposed. Optimistic local proxy reference, not a complete routable solution or global CPD bound. Slack offsets do not account for additive changes on shared timing paths; native FULL/STA remains mandatory. No whole original routing runtime inferred.'))
print(dict(agents=len(original),ipins=len(entrances),proxy_delta_ps=result['objective']*1e12,selected_tree_conflicts=len(conflicts),seconds=time.monotonic()-started),flush=True)
