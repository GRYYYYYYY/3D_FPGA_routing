#!/usr/bin/env python3
"""Pair final inter-cluster connection delays from saved audits and route terminals."""
from pathlib import Path
import collections,hashlib,json,re,statistics,sys,datetime
P=Path(__file__).resolve().parent;ROOT=P.parents[1];B=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path.insert(0,str(ROOT/'scripts'))
from check_route import NET_RE,NODE_RE,coordinates
bindings={}
def read(p):
 data=p.read_bytes();bindings[str(p.relative_to(ROOT))]=hashlib.sha256(data).hexdigest();return data.decode()
def terminal_ids(path):
 text=read(path);net=None;source=None;result={}
 for line in text.splitlines():
  m=NET_RE.match(line)
  if m:
   net=m[1] if 'global net' not in m[3] else None;source=None
  elif line.startswith('Node:') and net is not None:
   # Record only terminal identities; channel paths remain in the archived route.
   if 'SOURCE' not in line and 'SINK' not in line:continue
   m=NODE_RE.match(line)
   if not m:raise ValueError(line)
   node=int(m[1]);low=coordinates(m[3])
   if m[2]=='SOURCE':source=(node,low)
   if m[2]=='SINK':
    key=(net,str(int(m[6])));assert key not in result and source is not None
    result[key]=dict(source=source,sink=(node,low),remote=source[1][2]!=low[2])
 return result
cases=[]
for circuit,size in [('clstm_like.small',60),('clstm_like.large',80)]:
 arms=[]
 for suffix in ['a0','delay_critical_c6']:
  name=f'heldout_{circuit}_s23_hybrid_o_n{size}_w100_p0_{suffix}';d=B/'runs'/name
  audit=json.loads(read(d/'independent_audit.json'))['audit'];assert audit['passed'] and audit['routed_connection_delays']['available']
  terminals=terminal_ids(d/'routed.route');assert bindings[str((d/'routed.route').relative_to(ROOT))]==audit['inputs']['route_sha256']
  records={}
  for nid,n in audit['nets'].items():
   for pin,delay in n['routed_sink_delay_ns'].items():
    key=(nid,pin);records[key]=dict(name=n['name'],delay_ns=delay,**terminals[key])
  assert set(records)==set(terminals)
  arms.append(dict(run=name,records=records))
 assert set(arms[0]['records'])==set(arms[1]['records'])
 changes=[]
 for key,a in arms[0]['records'].items():
  r=arms[1]['records'][key]
  assert (a['name'],a['source'],a['sink'])==(r['name'],r['source'],r['sink'])
  changes.append(dict(net_id=key[0],net_pin_index=key[1],net_name=a['name'],remote=a['remote'],a0_ns=a['delay_ns'],r1_ns=r['delay_ns'],delta_ns=r['delay_ns']-a['delay_ns']))
 groups={}
 for name,rows in [('all',changes),('remote',[x for x in changes if x['remote']])]:
  groups[name]=dict(count=len(rows),improved=sum(x['delta_ns'] < -1e-9 for x in rows),tied=sum(abs(x['delta_ns']) <= 1e-9 for x in rows),regressed=sum(x['delta_ns'] > 1e-9 for x in rows),a0_mean_ns=statistics.mean(x['a0_ns'] for x in rows),r1_mean_ns=statistics.mean(x['r1_ns'] for x in rows),mean_delta_ns=statistics.mean(x['delta_ns'] for x in rows),largest_improvements=sorted(rows,key=lambda x:x['delta_ns'])[:3],largest_regressions=sorted(rows,key=lambda x:x['delta_ns'],reverse=True)[:3])
 cases.append(dict(circuit=circuit,seed=23,family='hybrid_o',flow='p0',width=100,arms=[a['run'] for a in arms],terminal_identity_equal=True,groups=groups))
read(ROOT/'scripts/check_route.py')
result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='paired_terminals_verified',scope='Same net IDs/names and Net_pin_index, same SOURCE/SINK RR IDs and coordinates verified in saved routes; actual switch-delay sums from independent zero-RC audits. Excludes local/logic timing and is not a native STA critical-path decomposition, final-guide adoption measurement or isolated DP causal effect.',cases=cases,source_sha256=bindings)
(P/'data/connection_changes.json').write_text(json.dumps(result,indent=2)+'\n')
for c in cases:
 print(c['circuit'],{k:{kk:vv for kk,vv in v.items() if not kk.startswith('largest')} for k,v in c['groups'].items()})
