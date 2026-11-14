#!/usr/bin/env python3
"""Which actual queued seeds already inherit the planned crossing from their tree prefix?"""
import collections,json,mmap,resource,signal,struct
from retained_prefix_workflow import D,read,write,sha
from analyze_search_domain_v2 import inside
resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
b=D/'actual_search_tree_eltwise_dev_01';a=read(b/'actual_tree_analysis.json');assert a['passed'];assert sha(b/'actual_cases.jsonl')==a['cases_jsonl_sha256']
g=D/'residual_query_offline_01/graph.bin';binding=read(g.with_name('graph_binding.json'));assert sha(g)==binding['binary_graph_sha256']
rows=[];totals=collections.Counter()
with g.open('rb') as gf,mmap.mmap(gf.fileno(),0,access=mmap.ACCESS_READ) as graph,(b/'actual_cases.jsonl').open() as f:
 n,edges,unit,span=struct.unpack_from('<IQdd',graph,8)
 def info(node):
  x,y,dx,dy,l=struct.unpack_from('<iiiii',graph,36+20*node);return dict(xlow=x,ylow=y,dx=dx,dy=dy,layer=l)
 def in_box(node,dom):
  x=info(node);return int(dom['xmin'])<=x['dx']<=int(dom['xmax']) and int(dom['ymin'])<=x['dy']<=int(dom['ymax']) and int(dom['layer_min'])<=x['layer']<=int(dom['layer_max'])
 for line in f:
  c=json.loads(line);dom=c['domain'];pref=set(map(int,dom['preferred'].split(',')));sink=int(dom['sink']);sl=info(sink)['layer'];used={}
  for node,expand,td,parent,sw,pin in c['tree']:
   used[node]=False if parent<0 else used[parent] or parent in pref and info(parent)['layer']!=info(node)['layer']
  seeds={}
  for node,l,td in c['seeds']:seeds[node]=(l,td)
  retained=[node for node,(l,td) in seeds.items() if l==sl and used[node] and in_box(node,dom)]
  sink_seeds=[node for node,(l,td) in seeds.items() if l==sl and in_box(node,dom)];source_seeds=[node for node,(l,td) in seeds.items() if l!=sl and in_box(node,dom)]
  q=c['native_query'];ps=c['native_reverse_path'];native_anchor=ps[-1][0] if q['has_path']=='1' else None
  row=dict(search=int(dom['search']),net=int(dom['net']),pin=int(dom['pin']),iter=int(dom['iter']),criticality=float(dom['criticality']),source_seeds=len(source_seeds),sink_seeds=len(sink_seeds),retained_preferred_seeds=len(retained),native_cache_hit=q['hit']=='1',native_has_path=q['has_path']=='1',native_path_inherits_preferred=native_anchor is not None and used[native_anchor],retained_seed_ids=retained)
  rows.append(row);totals['contexts']+=1;totals['with_retained_preferred_seed']+=bool(retained);totals['with_retained_preferred_seed_c09']+=bool(retained) and float(dom['criticality'])>=.9;totals['native_path_inherits_preferred']+=row['native_path_inherits_preferred'];totals['native_cache_hits_with_retained_preferred_seed']+=row['native_cache_hit'] and bool(retained);totals['no_opposite_layer_seed']+=not source_seeds
write(b/'preferred_prefix_analysis.json',dict(passed=True,native_route_calls=0,totals=dict(totals),rows=rows,source_sha256={str(p):sha(p) for p in [__import__('pathlib').Path(__file__),b/'actual_tree_analysis.json',b/'actual_cases.jsonl',g,g.with_name('graph_binding.json')]},qualification='Actual full current-tree ancestry determines whether a queued sink-layer seed already inherits a recommended crossing. This is not merely ownership of that RR node: the exact parent-child edge must cross layers at a preferred source. BB-filtered seeds and the existing physical one-additional-cross model remain narrower than all native search paths. This diagnostic does not change guide behavior or certify global congestion/STA.'))
print(dict(totals))
