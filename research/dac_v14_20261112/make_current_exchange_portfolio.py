#!/usr/bin/env python3
"""Generate free native requests from current critical-owner dependency closures."""
import argparse,hashlib,json
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_proposal_portfolio import request_text
p=argparse.ArgumentParser()
for n in ['expansion','feedback','output']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();expansion=a.expansion.resolve();x=read(expansion);assert x['passed'] and all(sha(path)==h for path,h in x['source_sha256'].items());f=a.feedback.resolve();cone=read(f/'cone.json');op=read(f/'owners/completion.json');state=Path(x['input_state']);assert Path(op['input_state'])==Path(cone['source_state'])==state
source=Path(read(state/'completion.json')['run']);b=a.output.resolve();b.mkdir(exist_ok=False);wanted={(int(n),pin) for r in x['rows'] for n,ps in r['expanded_removed_pins'].items() for pin in ps};sta={}
if wanted:
 for line in (source/'native_sta_frontier.jsonl').open():
  row=json.loads(line)
  if row.get('type')=='pin' and (row['net'],row['pin']) in wanted:
   assert not row['driver'] and not row['global'] and not row['ignored'];sta[row['net'],row['pin']]=row
   if set(sta)==wanted:break
 assert set(sta)==wanted
bindings={str(p):sha(p) for p in [Path(__file__).resolve(),D/'current_proposal_portfolio.py',expansion,f/'cone.json',f/'owners/completion.json',state/'completion.json',state/'endpoint_vector.json',source/'native_sta_frontier.jsonl',source/'routed.route']};proposals=[];seen=set();current_path_pins={(r['net'],r['pin']) for r in cone['routed_connections']}
for i,row in enumerate(x['rows']):
 if not row['critical_core_paths_compatible']:continue
 target=tuple(row['target']);repair={(int(n),pin) for n,ps in row['expanded_removed_pins'].items() for pin in ps};critical={c['net'] for c in row['conditional_distance_certificates']};owners=sorted(k for k in repair if k[0] in critical);others=sorted(repair-{target}-set(owners));ordered=[target]+owners+others;assert set(ordered)==repair and len(ordered)==len(repair)
 plan=dict(passed=True,source_state=str(state),actions=[],selection=dict(status='current_critical_owner_dependency_closure',targets=[list(target)]+[list(k) for k in owners if k in current_path_pins],fraction=1.,exchange_target=list(target)),repair_pins=sorted(repair),ordered_queries=[dict(net=n,pin=pin,raw_criticality=sta[n,pin]['setup_criticality_raw']) for n,pin in ordered],source_sha256=bindings,native_calls=0,accepted=False,
  qualification='Expanded current dependency closure; native freely chooses every path under its original objective/domain. No preset path or new kernel. Conditional core model does not guarantee complete legal donor restoration or final CPD. Original budgets and native FULLSTA decide acceptance.')
 path=b/f'exchange_{i:03d}.plan.json';write(path,plan);digest=hashlib.sha256(request_text(plan).encode()).hexdigest()
 if digest in seen:continue
 seen.add(digest);proposals.append(dict(name=f'critical_owner_exchange_{i:03d}',plan=str(path),request_sha256=digest,repair_connections=len(repair)))
write(b/'portfolio.json',dict(passed=True,source_state=str(state),expansion=str(expansion),feedback=str(f),proposals=proposals,source_sha256=bindings,native_calls=0,qualification='Fixed free target-first native schedule after action-derived proposals are exhausted. No per-circuit historical best or forced witness. A partial closure certificate is not final routing quality.'))
print(dict(proposals=len(proposals),connections=[p['repair_connections'] for p in proposals]),flush=True)
