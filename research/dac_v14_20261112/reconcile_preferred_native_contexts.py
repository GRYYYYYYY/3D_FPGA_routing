#!/usr/bin/env python3
"""Separate sparse offline cache state from the real native Qs trajectory."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import fields
b=D/'preferred_query_certificate_offline_03';report=read(b/'analysis.json');assert report['passed']
rd=D/'residual_native_eltwise_dev_01/runs/eltwise_layer_Qs';m=read(rd/'manifest.json');assert read(rd.parent.parent/'input_seal.json')['passed'] and read(rd.parent.parent/'residual_native_analysis.json')['passed'];assert sha(rd/'stdout.log')==m['outputs']['stdout.log']['sha256']
qs={};domains={}
for l in (rd/'stdout.log').read_text().splitlines():
 if l.startswith('H3D_SEARCH_DOMAIN '):r=fields(l);domains[int(r['search'])]=r
 elif l.startswith('H3D_RESIDUAL_QUERY '):r=fields(l);qs[int(r['search'])]=r
cases={int(c['domain']['search']):c for c in read(b/'cases.json')};offline={r['search']:r for r in read(D/'residual_path_reuse_offline_01/analysis.json')['rows']};preferred={r['search']:r for r in report['rows'] if r['mode']==4};rows=[]
for search,c in cases.items():
 assert domains[search]==c['domain'],search
 r=qs[search];assert r['sources']==r['source_rows']
 seeds={}
 for s in c['seeds']:
  if s['layer']==int(c['domain']['sink_layer']):seeds[s['node']]=min(seeds.get(s['node'],float('inf')),s['delay'])
 recorded={int(x.split(',')[0]):float(x.split(',')[1]) for x in r['seeds'].split(';')};assert recorded==seeds
 old=offline[search];p=preferred[search]
 rows.append(dict(search=search,native_hit=bool(int(r['hit'])),native_no_cross_query_expansions=int(r['expansions']),native_no_cross_has_path=bool(int(r['has_path'])),native_no_cross_upper_seconds=float(r['upper_seconds']) if int(r['has_path']) else None,sparse_offline_prior_hit=old['S_prior'] is not None,sparse_offline_query_expansions=old['S_query_expansions'],preferred_targeted_upper_seconds=p['upper_seconds'],preferred_expansions=p['expansions'],native_hit_only_reallocation_exercised=bool(int(r['hit']))))
result=dict(passed=True,native_route_calls=0,rows=rows,native_cache_hits=sum(r['native_hit'] for r in rows),sparse_offline_prior_cache_hits=sum(r['sparse_offline_prior_hit'] for r in rows),native_query_work=sum(r['native_no_cross_query_expansions'] for r in rows),same_actual_domains_and_complete_sink_layer_seed_sets=True,source_sha256={str(p):sha(p) for p in [Path(__file__),b/'analysis.json',b/'cases.json',rd/'manifest.json',rd/'stdout.log',rd.parent.parent/'residual_native_analysis.json',D/'residual_path_reuse_offline_01/analysis.json']},qualification='Sparse offline cache replay previously queried all31focus groups, including unguided groups. Native Qs queried only actual guided searches throughout the full trajectory. Cache hit/state cannot be transferred across these different histories even when actual search domains and source sets match. A native hit-only budget-reallocation pilot would not exercise on these10focus contexts. Do not infer native free work from the three sparse-offline hits; broader actual-seed coverage is required before selecting that policy.')
write(D/'preferred_native_context_reconciliation_01.json',result)
print({k:v for k,v in result.items() if k not in ['rows','source_sha256','qualification']})
