#!/usr/bin/env python3
"""Exploratory physical-connection tails from matched, already audited routes."""
from pathlib import Path
import json,math
from inspect_paths import D,sha
from check_route import read_trace

def load(rd):
 rd=Path(rd);a=json.loads((rd/'independent_audit.json').read_text())['audit'];assert a['passed'] and a['routed_connection_delays']['available'];result={}
 for net,info in read_trace(rd/'routed.route').items():
  trace=info['trace']
  if not trace:continue
  source=trace[0];sinks=[n for n in trace if n.kind=='SINK'];remote=any(n.low[2]!=source.low[2] for n in sinks)
  for sink in sinks:
   key=(net,sink.pin);assert key not in result
   result[key]=dict(identity=(info['name'],source.inode,sink.inode),delay=a['nets'][str(net)]['routed_sink_delay_ns'][str(sink.pin)],group='cross_layer_pin' if sink.low[2]!=source.low[2] else 'same_layer_pin_in_mixed_net' if remote else 'entirely_planar_net')
 return result

def percentile(values,p):
 values=sorted(values);return values[min(len(values)-1,max(0,math.ceil(p*len(values))-1))] if values else None

def compare(left,right):
 left=Path(left);right=Path(right)
 assert all(sha(left/f)==sha(right/f) for f in ['packed.net','placed.place'])
 a,b=load(left),load(right);stats={};mismatched=[];union=set(a)|set(b);samples={}
 for key in sorted(union):
  if key not in a or key not in b or a[key]['identity']!=b[key]['identity'] or a[key]['group']!=b[key]['group']:
   mismatched.append(key);continue
  delta=b[key]['delay']-a[key]['delay'];group=a[key]['group'];samples.setdefault(group,[]).append((delta,key,a[key]['identity'],a[key]['delay'],b[key]['delay']))
 for group,items in samples.items():
  delta=[x[0] for x in items]
  stats[group]=dict(paired_connections=len(items),improved=sum(x < -1e-6 for x in delta),tied=sum(abs(x)<=1e-6 for x in delta),regressed=sum(x>1e-6 for x in delta),regressed_over_0p1_ns=sum(x>.1 for x in delta),mean_delta_ns=sum(delta)/len(delta),p95_delta_ns=percentile(delta,.95),p99_delta_ns=percentile(delta,.99),max_delta_ns=max(delta),min_delta_ns=min(delta),worst=sorted(items,reverse=True)[:10])
 return dict(reference=str(left),variant=str(right),reference_connections=len(a),variant_connections=len(b),unpaired_or_identity_mismatch=len(mismatched),mismatch_keys=mismatched,groups=stats,input_sha256={str(rd/f):sha(rd/f) for rd in [left,right] for f in ['packed.net','placed.place','routed.route','independent_audit.json']})
if __name__=='__main__':
 pairs=[('spmv_M','h1_dev_02/runs/spmv_F','h1_dev_02/runs/spmv_M'),('spmv_H','h1_dev_02/runs/spmv_F','h2_dp_dev_01/runs/spmv_H'),('eltwise_H','h2_expansion_01/runs/eltwise_layer_F','h2_expansion_01/runs/eltwise_layer_H'),('bnn_H','h2_expansion_01/runs/bnn_F','h2_expansion_01/runs/bnn_H')]
 result={'scope':'Post-hoc exploratory RR physical-delay tails, not STA CPD or criticality. Match net and pin plus identical SOURCE/SINK RR IDs and unchanged layer group; mismatches remain explicit. Equality tolerance 1e-6 ns, quantiles nearest-rank. Planar-net group has no eligible cross-layer pin and no direct guide.','pairs':{name:compare(D/a,D/b) for name,a,b in pairs}}
 out=D/'critical_path_diagnostics/paired_delay_tails.json';out.write_text(json.dumps(result,indent=2)+'\n')
 for name,pair in result['pairs'].items():
  print(name,'unpaired',pair['unpaired_or_identity_mismatch'])
  for group,x in pair['groups'].items():print(group,{k:v for k,v in x.items() if k!='worst'})
