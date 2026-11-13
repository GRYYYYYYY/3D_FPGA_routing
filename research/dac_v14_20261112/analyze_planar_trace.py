#!/usr/bin/env python3
"""Reconcile pre-prune overuse evidence and independently recompute existing/proposed refresh gates."""
from pathlib import Path
import collections,hashlib,json,sys
B=Path(sys.argv[1]);assert json.loads((B/'input_seal.json').read_text())['passed'];reg=json.loads((B/'registration.json').read_text());results={}
for c in reg['circuits']:
 for a in ['V','T']:
  p=B/'runs'/f'{c}_{a}';m=json.loads((p/'manifest.json').read_text());assert m['status']=='completed' and m['metrics']['native_full_check_passed']
  assert json.loads((p/'independent_audit.json').read_text())['audit']['passed'] and json.loads((p/'final_guide_audit.json').read_text())['passed']
  assert json.loads((p/'optimization_equivalence.json').read_text())['passed']
  assert m['environment']['VPR_H3D_TRACE_PLANAR_FEEDBACK']==('1' if a=='T' else '0')
  if a=='V':assert 'H3D_PLANAR_' not in (p/'stdout.log').read_text()
 p=B/'runs'/f'{c}_T';pending=[];latest={};contexts=[];captures=0;path_records=0
 for line in (p/'stdout.log').read_text().splitlines():
  if not line.startswith('H3D_PLANAR_'):continue
  tag=line.split()[0];r=dict(x.split('=',1) for x in line.split()[1:]);net=int(r['net'])
  if tag=='H3D_PLANAR_PATH':
   ids=[int(x) for x in r['overused'].split(';') if x];assert ids and len(ids)==len(set(ids));pending.append((net,int(r['pin']),set(ids)));path_records+=1
  elif tag=='H3D_PLANAR_CAPTURE':
   resources={}
   for item in r['overused'].split(';'):
    if not item:continue
    node,occ,cap=map(int,item.split(':'));assert node not in resources and occ>cap>=0;resources[node]=(occ,cap)
   assert len(resources)==int(r['nodes'])
   assert len(pending)==int(r['affected_paths'])<=int(r['guided_paths'])
   assert len({pin for n,pin,_ in pending})==len(pending)
   for n,pin,ids in pending:assert n==net and ids<=resources.keys()
   latest[net]=dict(nodes=int(r['nodes']),guided_paths=int(r['guided_paths']),affected_paths=int(r['affected_paths']),resources=resources)
   pending=[];captures+=1
  elif tag=='H3D_PLANAR_CONTEXT':
   assert not pending
   it,last,cool=map(int,[r['iter'],r['last_attempt'],r['cooldown']]);cross=int(r['crossing_overuse']);drift=float(r['drift']);change=float(r['change'])
   assert drift>=0 and 0<=change<=1 and cross in [0,1]
   due=it-last>=cool and (cross or drift>=.15 or change>=.25)
   assert bool(int(r['original_due']))==bool(int(r['due']))==bool(due)
   observed={k:int(r[k]) for k in ['planar_nodes','guided_paths','affected_paths']}
   capture=latest.pop(net,None)
   if capture:
    assert observed==dict(planar_nodes=capture['nodes'],guided_paths=capture['guided_paths'],affected_paths=capture['affected_paths'])
   else:assert all(v==0 for v in observed.values())
   alternative_due=it-last>=cool and (due or observed['affected_paths']>0)
   contexts.append(dict(net=net,iteration=it,last_attempt=last,cooldown=cool,crossing_overuse=bool(cross),drift=drift,change=change,original_due=bool(due),hypothetical_due=bool(alternative_due),extra_opportunity=bool(alternative_due and not due),**observed))
  else:raise AssertionError(tag)
 extra=[r for r in contexts if r['extra_opportunity']]
 results[c]=dict(captures=captures,guided_affected_path_records=path_records,refresh_contexts=len(contexts),contexts_with_any_planar_overuse=sum(r['planar_nodes']>0 for r in contexts),contexts_with_guided_planar_overuse=sum(r['affected_paths']>0 for r in contexts),contexts_with_crossing_overuse=sum(r['crossing_overuse'] for r in contexts),original_due=sum(r['original_due'] for r in contexts),extra_opportunities=len(extra),unique_extra_nets=len({r['net'] for r in extra}),extra_by_iteration=dict(collections.Counter(r['iteration'] for r in extra)),extra=extra,contexts=contexts)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=dict(passed=True,circuits=results,scope='Decision-neutral observed pre-prune RR occupancy/capacity and guided-path subsets; independently reconciled log invariants and exact existing/hypothetical cooldown gates. V/T both reproduce sealed U route/table/refresh/guide. Occupancy observations are internal instrumented evidence, not independently reconstructed intermediate route snapshots. Repeated net/iteration opportunities are not independent samples. Added opportunities alone do not show candidate discrimination or QoR gain.',bindings={str(p):sha(p) for p in [Path(__file__),B/'input_seal.json',B/'registration.json']})
(B/'planar_feedback_mechanisms.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({c:{k:v for k,v in r.items() if k not in ['contexts','extra']} for c,r in results.items()},indent=2))
