#!/usr/bin/env python3
"""Independent actual queued-seed/current-tree physics and witness-intersection audit."""
import collections,json,math,resource,signal,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import fields,graph_records,f32
from analyze_search_domain_v2 import inside
from audit_residual_query_offline import near
ROOT=D.parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from check_route import read_trace
resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
b=D/'actual_search_tree_eltwise_dev_01';rd=b/'runs/eltwise_layer_T2';assert read(b/'input_seal.json')['passed'];assert read(b/'completion.json')['gate_passed'] and not read(b/'completion.json')['missing_arms'];assert read(rd/'trace_reproduction.json')['passed'];m=read(rd/'manifest.json');assert sha(rd/'stdout.log')==m['outputs']['stdout.log']['sha256']
graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);assert sha(graph)==m['shared_inputs'][str(graph)]['sha256']
contexts={};seeds=collections.defaultdict(list);trees=collections.defaultdict(list);domains={};queries={};paths=collections.defaultdict(list);summ=None;old_seeds=collections.defaultdict(list)
with (rd/'stdout.log').open() as f:
 for line in f:
  if not line.startswith(('H3D_ACTUAL_','H3D_SEARCH_DOMAIN','H3D_RESIDUAL_QUERY ','H3D_RESIDUAL_EDGE ')):continue
  tag=line.split(' ',1)[0];r=fields(line)
  if tag=='H3D_ACTUAL_SEARCH':k=int(r['search']);assert k not in contexts;contexts[k]=r
  elif tag=='H3D_ACTUAL_SEED':
   k=int(r['search']);assert int(r['seq'])==len(seeds[k]);seeds[k].append((int(r['node']),int(r['layer']),float(r['delay'])))
  elif tag=='H3D_ACTUAL_TREE':
   k=int(r['search']);assert int(r['seq'])==len(trees[k]);trees[k].append((int(r['node']),int(r['expand']),float(r['delay']),int(r['parent']),int(r['switch']),int(r['pin'])))
  elif tag=='H3D_SEARCH_DOMAIN':k=int(r['search']);assert k not in domains;domains[k]=r
  elif tag=='H3D_SEARCH_DOMAIN_SEED':old_seeds[int(r['search'])].append((int(r['node']),int(r['layer']),float(r['delay_seconds'])))
  elif tag=='H3D_RESIDUAL_QUERY':k=int(r['search']);assert k not in queries;queries[k]=r
  elif tag=='H3D_RESIDUAL_EDGE':
   k=int(r['search']);assert int(r['index'])==len(paths[k]);paths[k].append((int(r['from']),int(r['to']),float(r['physical_seconds']),float(r['toll_seconds'])))
  elif tag=='H3D_ACTUAL_SUMMARY':summ=r
assert contexts.keys()==queries.keys()=={k for k,v in domains.items() if v['guide']=='1'}
assert summ and int(summ['contexts'])==int(summ['complete'])==len(contexts) and int(summ['seed_omitted'])==int(summ['tree_omitted'])==0
assert int(summ['seed_rows'])==sum(map(len,seeds.values())) and int(summ['tree_rows'])==sum(map(len,trees.values()))
wanted_nodes={t[0] for rows in trees.values() for t in rows};wanted_nodes.update(int(c['sink']) for c in contexts.values());wanted_edges={(t[3],t[0],t[4]) for rows in trees.values() for t in rows if t[3]>=0}
nreal=read(D/'residual_query_offline_01/graph_binding.json')['nodes'];wanted_weights={(v,u,w) for rows in paths.values() for u,v,w,t in rows if v!=nreal};wanted_nodes.update(n for u,v,w in wanted_weights for n in [u,v]);wanted_nodes.update(n for rows in seeds.values() for n,l,t in rows);wanted_pairs={(u,v) for u,v,s in wanted_edges}|{(u,v) for u,v,w in wanted_weights}
nodes={};switch={};found=set();weights=set();layer_count=0;node_count=0
for section,e in graph_records(graph):
 a=e.attrib
 if section=='switches':
  t=e.find('timing');v={} if t is None else t.attrib;assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal']);switch[int(a['id'])]=f32(v.get('Tdel',0))
 elif section=='rr_nodes':
  n=int(a['id']);node_count+=1;v=e.find('loc').attrib;l=int(v.get('layer_low',v.get('layer',0)));layer_count=max(layer_count,l+1)
  if n in wanted_nodes:
   t=e.find('timing');assert t is None or all(float(t.attrib.get(k,0))==0 for k in ['R','C']);assert l==int(v.get('layer_high',v.get('layer',0)));nodes[n]=dict(kind=a['type'],layer=l,direction=a.get('direction','NONE'),**{k:int(v[k]) for k in ['xlow','xhigh','ylow','yhigh']})
 elif section=='rr_edges':
  u,v,s=int(a['src_node']),int(a['sink_node']),int(a['switch_id'])
  if (u,v) in wanted_pairs:found.add((u,v,s));weights.add((u,v,switch[s]))
assert node_count==nreal and wanted_edges<=found and wanted_weights<=weights
route=read_trace(rd/'routed.route');terminals={}
for net,data in route.items():
 for t in data['trace']:
  if t.kind=='SINK' and t.pin is not None:terminals[net,t.pin]=t.inode
stats=collections.Counter();path_states=collections.Counter();class_by_hit=collections.defaultdict(collections.Counter);observations=[]
case_path=b/'actual_cases.jsonl';assert not case_path.exists()
with case_path.open('w') as out:
 for k,c in contexts.items():
  dom=domains[k];q=queries[k];tree=trees[k];ss=seeds[k];net=int(c['net']);sink=int(c['sink'])
  for name in ['iter','attempt','search','net','pin','sink','criticality','preferred','rcv']:assert c[name]==dom[name]
  for name in ['iter','attempt','search','net','pin','sink','criticality']:assert c[name]==q[name]
  assert c['complete']=='1' and c['tree_present']=='1' and c['rcv']=='0'
  assert len(ss)==int(c['seeds'])==int(c['seed_rows']) and len(tree)==int(c['tree_nodes'])==int(c['tree_rows'])
  assert terminals[net,int(c['pin'])]==sink
  bynode={};roots=[];duplicates=0
  for n,expand,delay,parent,sw,pin in tree:
   assert f32(delay)==delay and math.isfinite(delay) and delay>=0
   if n in bynode:assert nodes[n]['kind']=='SINK';duplicates+=1
   if parent<0:assert sw==-1 and delay==0.;roots.append(n)
   else:
    assert parent in bynode and (parent,n,sw) in found
    assert f32(f32(bynode[parent][2])+f32(switch[sw]))==delay,(k,n,delay,bynode[parent][2],switch[sw]);stats['native_float_prefix_checks']+=1
   bynode[n]=(n,expand,delay,parent,sw,pin);stats['tree_rows']+=1
  assert len(roots)==1 and roots[0]==route[net]['trace'][0].inode;stats['duplicate_sink_rows']+=duplicates
  unique={};layers=collections.defaultdict(list)
  for n,l,delay in ss:
   assert n in bynode and bynode[n][1] and bynode[n][2]==delay and nodes[n]['layer']==l
   unique[n]=min(unique.get(n,math.inf),delay);layers[l].append(delay);stats['seed_rows']+=1
  for part in dom['layers'].split(';'):
   layer,pushes,minimum,*rest=part.split(',');vals=layers[int(layer)];assert len(vals)==int(pushes);assert min(vals,default=math.inf)==float(minimum)
  if k in old_seeds:assert ss[:len(old_seeds[k])]==old_seeds[k];stats['old_focus_seed_rows']+=len(old_seeds[k])
  sink_seeds={n:d for n,d in unique.items() if nodes[n]['layer']==nodes[sink]['layer']}
  recorded={} if q['seeds']=='-' else {int(a):float(t) for a,t in (part.split(',') for part in q['seeds'].split(';'))}
  assert int(q['sources'])==int(q['source_rows'])==len(sink_seeds) and sink_seeds==recorded
  ps=paths[k];assert len(ps)==int(q['path_edges'])==int(q['edge_rows']);state='missing';splice=None
  if q['has_path']=='1':
   assert ps and ps[0][0]==sink and ps[-1][1]==nreal and all(a[1]==z[0] for a,z in zip(ps,ps[1:]));anchor=ps[-1][0];assert anchor in sink_seeds and ps[-1][2]==sink_seeds[anchor]
   assert all(t==0. for u,v,w,t in ps) and near(sum(w for u,v,w,t in ps),float(q['upper_seconds']))
   sequence=[sink]+[v for u,v,w,t in ps[:-1]];assert sequence[-1]==anchor and len(sequence)==len(set(sequence))
   for u,v,w,t in ps[:-1]:assert (v,u,w) in weights and nodes[u]['layer']==nodes[v]['layer']==nodes[sink]['layer'] and inside(nodes[u],dom,layer_count) and inside(nodes[v],dom,layer_count)
   hits=[(i,n) for i,n in enumerate(sequence[:-1]) if n in bynode]
   state='valid_extension' if not hits else 'target_already_in_tree' if hits[0][0]==0 else 'tree_intersection'
   if hits:
    i,n=hits[0]
    if i>0 and n in unique and bynode[n][1] and inside(nodes[n],dom,layer_count):
     value=unique[n]+sum(e[2] for e in ps[:i]);splice=dict(anchor=n,edges=i,upper_seconds=value,change_seconds=value-float(q['upper_seconds']));stats['splice_to_actual_seed']+=1
   path_states[state]+=1;class_by_hit[q['hit']][state]+=1
  else:assert not ps;path_states['missing']+=1
  obs=dict(search=k,iter=int(c['iter']),net=net,pin=int(c['pin']),criticality=float(c['criticality']),raw_seeds=len(ss),unique_seeds=len(unique),tree_nodes=len(tree),cached=bool(int(q['hit'])),no_cross_status=state,splice=splice)
  observations.append(obs)
  out.write(json.dumps(dict(context=c,domain=dom,seeds=ss,tree=tree,native_query={name:value for name,value in q.items() if name!='seeds'},native_reverse_path=ps),separators=(',',':'))+'\n')
result=dict(passed=True,status='complete_actual_guided_seed_tree_physics_audit',contexts=len(contexts),stats=dict(stats),native_no_cross_paths=dict(path_states),path_states_by_cache_hit={k:dict(v) for k,v in class_by_hit.items()},real_directed_tree_edges_checked=len(wanted_edges),real_directed_path_edges_checked=len(wanted_weights),observations=observations,cases_jsonl_sha256=sha(case_path),source_sha256={str(p):sha(p) for p in [Path(__file__),graph,rd/'stdout.log',rd/'manifest.json',rd/'trace_reproduction.json',b/'input_seal.json',rd/'independent_audit.json',rd/'final_guide_audit.json']},qualification='All actual guided search contexts, complete current tree membership and successful queued seed pushes reconciled with original layer counts and native query source sets. Zero-RC physical directed edges and native float Tdel recurrence checked. Duplicate SINK RR ids may represent distinct pins. A simple suffix from an actually queued anchor with no other current-tree intersection is a sufficient local extension witness, not a global capacity or final STA certificate. Current congestion prices were not captured. Truncating at the closest other queued tree node is an independently derived candidate, not an implemented routing change.')
write(b/'actual_tree_analysis.json',result);print({k:v for k,v in result.items() if k not in ['source_sha256','observations','qualification']})
