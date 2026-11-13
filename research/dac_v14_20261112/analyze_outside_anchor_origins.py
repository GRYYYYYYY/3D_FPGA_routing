#!/usr/bin/env python3
import collections
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import fields
b=D/'retained_outside_trace_eltwise_dev_01';r=read(b/'outside_trace_analysis.json');assert r['passed'];log=b/'runs/eltwise_layer_D/stdout.log';queries={}
for l in log.read_text().splitlines():
    if l.startswith('H3D_RESIDUAL_QUERY '):
        q=fields(l);queries[int(q['search'])]=q
counts=collections.Counter();byreason=collections.defaultdict(collections.Counter)
for w in r['rows']:
    q=queries[w['origin']];same=int(q['net'])==w['net'];seeds=set() if q['seeds']=='-' else {int(x.split(',')[0]) for x in q['seeds'].split(';')}
    category='other_origin_net' if not same else 'same_net_prior_actual_seed' if w['anchor'] in seeds else 'same_net_query_intermediate'
    counts[category]+=1;byreason[w['reason']][category]+=1
result=dict(passed=True,status='sealed_cached_anchor_origin_classification',source_sha256={str(p):sha(p) for p in [__file__,log,b/'outside_trace_analysis.json']},all_witnesses=dict(counts),by_exclusion_reason={k:dict(v) for k,v in byreason.items()},qualification='Cache is keyed by RR sink/source, not net. An absent anchor need never have belonged to this current net or have been an actual source: intermediate suffix vertices are also cached. Only same_net_prior_actual_seed supports that the anchor was once a real expandable source of this net. No inference that pruning alone caused absence.')
write(D/'outside_anchor_origin_diagnostic_01.json',result);print(result['by_exclusion_reason'])
