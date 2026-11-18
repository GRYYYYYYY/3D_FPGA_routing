"""Summarize final paired endpoint components and changes in physical BNN occupancy."""
import collections
import math
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import compare
from resource_opportunity_census import stream_trace

out=D/'submission_narrative_20/data'
base=D/'BNN_interleaved_timing_03'
states=[Path(read(base/r/'completion.json')['final_state']) for r in ('native_0','domain_0')]
lstm=read(D/'LSTM_domain_whole_admission_03/pair/completion.json')
lpaths=[Path(p).parent for p in lstm['source_sha256'] if p.endswith('/timing_initial/endpoint_vector.json')]
assert len(lpaths)==2 and '/native/' in str(lpaths[0])
result={}
def distribution(a):
    loss=-a[a<0]
    return dict(n=len(a),improved=int(sum(a>0)),tied=int(sum(a==0)),worse=len(loss),
                loss_quantiles_ps=dict(zip(['median','p90','p95','p99','max'],map(float,np.quantile(loss,[.5,.9,.95,.99,1])))) if len(loss) else {})
for label,dirs,expected in [('BNN',states,(534,803)),('LSTM',lpaths,(51,23))]:
    left,right=[read(s/'endpoint_vector.json') for s in dirs]
    comp=compare(left,right)
    assert comp['compatible'] and (comp['setup_improved'],comp['setup_regressed'])==expected
    row={}
    for kind in ['setup','hold']:
        finite=[];nonfinite=collections.Counter()
        for key,v in left[kind].items():
            w=right[kind][key]
            if all(isinstance(q,(int,float)) and math.isfinite(q) for q in (v,w)):
                finite.append((v,w))
            else:nonfinite[str((v,w))]+=1
        a,b=np.array(finite).T
        delta=(b-a)*1e12
        row[kind]=dict(all=distribution(delta),nonfinite_pairs=dict(nonfinite),missing_tag_endpoints=len(left['endpoint_ids'])-len({__import__('json').loads(k)[0] for k in left[kind]}),
                       within_1ns_of_native_worst=distribution(delta[a<=a.min()+1e-9]),
                       negative_component_counts=[int(sum(z<0)) for z in (a,b)],
                       worst_ns=[float(z.min()*1e9) for z in (a,b)])
    row['native_metrics']=[v['metrics'] for v in (left,right)]
    row['source_sha256']={arm:sha(state/'endpoint_vector.json') for arm,state in zip(('native','domain'),dirs,strict=True)}
    result[label]=row
write(out/'endpoint_distributions.json',result)
cache=base/'native_0/flow/resource_flow/graph_audit_cache'
nodes=np.load(cache/'nodes.npy',mmap_mode='r')
maps=[]
for state in states:
    m={}
    for net in stream_trace(state/'runs/state/routed.route'):
        tr=net['trace']
        for a,b in zip(tr,tr[1:]):
            if a.switch==-1 or nodes[a.inode,4]==nodes[b.inode,4]:continue
            key=('CB',a.inode) if a.kind=='OPIN' else ('SB',*sorted((a.inode,b.inode)))
            m[key]=net['net']
    maps.append(m)
counts=[collections.Counter(k[0] for k in m) for m in maps]
assert counts==[{'SB':82,'CB':5062},{'SB':43,'CB':5060}]
from csv import writer
with (out/'bnn_changed_sites.csv').open('w') as f:
    w=writer(f);w.writerow(['change','type','node_or_pair','x','y','layer_at_first_id','native_net','domain_net'])
    for key in sorted(maps[0].keys()|maps[1].keys()):
        n,d=(m.get(key) for m in maps)
        if n==d:continue
        w.writerow(['freed' if d is None else 'new' if n is None else 'reassigned',key[0],'/'.join(map(str,key[1:])),*nodes[key[1],2:5],n,d])
print(result['BNN']['setup'],result['LSTM']['setup'])
