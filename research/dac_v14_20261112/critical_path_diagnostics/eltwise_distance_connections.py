#!/usr/bin/env python3
"""Cross-evaluate the union of reported worst-path connections without new routing."""
from pathlib import Path
import csv,json
from inspect_paths import D,sha
from check_route import read_trace
from compare_connections import extract
reports=json.loads((D/'critical_path_diagnostics/eltwise_distance_paths.json').read_text())
connections={}
for report in reports:
 for c in report['connections']:
  if c['inter_cluster']:connections[c['net'],tuple(c['sink_location'])]=c
rows=[];bindings={};private_hashes=[]
for report in reports:
 rd=Path(report['path']);arm=rd.name.rsplit('_',1)[1]
 m=json.loads((rd/'manifest.json').read_text());audit=json.loads((rd/'independent_audit.json').read_text())
 assert m['status']=='completed' and m['metrics']['native_full_check_passed'] and audit['audit']['passed']
 private_hashes.append([sha(rd/f) for f in ['packed.net','placed.place']])
 traces=read_trace(rd/'routed.route');by_name={v['name']:(k,v) for k,v in traces.items()}
 guides={}
 if (rd/'h3d_final_guides.csv').exists():
  guides={(int(r['net']),int(r['pin'])):r for r in csv.DictReader((rd/'h3d_final_guides.csv').open())}
 for (name,location),c in connections.items():
  net,info=by_name[name];paths=extract(info,location);assert len(paths)==1
  p=paths[0];pins={n.pin for n in info['trace'] if n.inode==p['sink'] and n.pin is not None};assert len(pins)==1
  pin=next(iter(pins));ns=audit['audit']['nets'][str(net)]['routed_sink_delay_ns'][str(pin)]
  g=guides.get((net,pin))
  rows.append(dict(arm=arm,net=name,cluster_net=net,pin=pin,sink_location=location,source_rr=info['trace'][0].inode,sink_rr=p['sink'],physical_connection_ns=ns,crossings=p['crossings'],direct_guide=g,any_guide_on_net=any(n==net for n,_ in guides)))
 bindings[str(rd)]={f:sha(rd/f) for f in ['manifest.json','routed.route','independent_audit.json','report_timing.setup.rpt','packed.net','placed.place']}
assert all(p==private_hashes[0] for p in private_hashes)
bykey={}
for r in rows:bykey.setdefault((r['net'],tuple(r['sink_location'])),[]).append(r)
for group in bykey.values():assert len({(r['source_rr'],r['sink_rr']) for r in group})==1
out=dict(batch_sealed_by_run={r['path']:r['batch_sealed'] for r in reports},scope='Exact same source/sink RR connection identities for union of worst setup reports. Physical audited RR delay, not full atom STA delay; path startpoints can differ. Direct guide and any-guide-on-net distinguish indirect effects. No single-event causality claim. Unsealed runs are exploratory diagnostics only, excluded from quality aggregates.',rows=rows,bindings=bindings,script_sha256=sha(Path(__file__)))
(D/'critical_path_diagnostics/eltwise_distance_connections.json').write_text(json.dumps(out,indent=2)+'\n')
for r in rows:print(r['arm'],r['net'],r['physical_connection_ns'],'directguide',bool(r['direct_guide']),'netguide',r['any_guide_on_net'])
