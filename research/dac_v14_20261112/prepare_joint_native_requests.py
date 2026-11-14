#!/usr/bin/env python3
"""Bind matched joint-native scope and deterministic recovery schedules."""
import argparse,json
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
p=argparse.ArgumentParser();p.add_argument('--batch',type=Path,required=True);a=p.parse_args();b=a.batch.resolve();b.mkdir(exist_ok=False)
roles={'R1_fixed_id':('native_frontier_transaction_R1_01','native_endpoint_vector_dev_01/R1',True,'id'),
       'R1_sequential_id':('native_frontier_transaction_R1_01','native_endpoint_vector_dev_01/R1',False,'id'),
       'Tf_fixed_id':('current_sta_Tf_transaction_02','current_sta_policy_Tf_01/evaluation_002',True,'id'),
       'Tf_fixed_slack':('current_sta_Tf_transaction_02','current_sta_policy_Tf_01/evaluation_002',True,'slack')}
registrations={}
for role,(transaction_name,state_name,fixed,order) in roles.items():
    tx=D/transaction_name;state=D/state_name;r=read(tx/'analysis.json');assert r['passed'] and r['all_sinks_restored']
    assert all(sha(p)==h for p,h in r['source_sha256'].items())
    source=Path(read(state/'completion.json')['run']);original=Path(r['input_run'])
    assert route_body(source/'routed.route')==route_body(original/'routed.route')
    assert all(sha(source/n)==sha(original/n) for n in ['packed.net','placed.place'])
    first=read(tx/'initial_transaction.json');trees=read(tx/'final_transaction_trees.json')
    removed={int(n):[int(p) for p,s in pairs] for n,pairs in first['pending'].items()}
    for t in r['targets']:removed.setdefault(t['net'],[]).append(t['pin'])
    sta={}
    for line in (source/'native_sta_frontier.jsonl').open():
        x=json.loads(line)
        if x['type']=='pin' and not x['driver']:sta[x['net'],x['pin']]=x
    blockers=[(int(n),int(pin)) for n,pairs in first['pending'].items() for pin,sink in pairs]
    if order=='slack':blockers.sort(key=lambda k:(sta[k]['setup_slack_s'] if isinstance(sta[k]['setup_slack_s'],(float,int)) else float('inf'),k))
    else:blockers.sort()
    targets=[(t['net'],t['pin']) for t in r['targets']]
    targets.sort(key=lambda k:(sta[k]['setup_slack_s'],k))
    queries=blockers if fixed else targets+blockers
    request=b/(role+'.txt')
    with request.open('w') as f:
        f.write(str(len(removed))+'\n')
        for net,pins in sorted(removed.items()):f.write(' '.join(map(str,[net,len(pins),*sorted(pins)]))+'\n')
        f.write(str(len(targets) if fixed else 0)+'\n')
        if fixed:
            for net,pin in targets:
                path=first['target_reserved_nodes'][str(net)];edges=trees[str(net)]['edges']
                f.write(f'{net} {pin} {len(path)-1}\n')
                for u,v in zip(path,path[1:]):
                    parent,sw,w=edges[str(v)];assert parent==u;f.write(f'{u} {v} {sw}\n')
        f.write(str(len(queries))+'\n')
        for net,pin in queries:f.write(f"{net} {pin} {sta[net,pin]['setup_criticality_raw']:.17g}\n")
    registrations[role]=dict(transaction=str(tx),state=str(state),source=str(source),request=str(request),fixed_target_paths=fixed,order=order,
         removed_pins=removed,targets=targets,queries=[dict(net=n,pin=p,slack_s=sta[n,p]['setup_slack_s'],raw_criticality=sta[n,p]['setup_criticality_raw']) for n,p in queries],
         source_sha256={str(p):sha(p) for p in [tx/'analysis.json',tx/'initial_transaction.json',tx/'final_transaction_trees.json',source/'routed.route',source/'native_sta_frontier.jsonl',request]})
write(b/'registration.json',dict(status='registered_before_native',roles=registrations,source_sha256={str(p):sha(p) for p in [Path(__file__),D/'current_sta_joint_native_experiment_01.json',D/'src/vpr/src/route/h3d_joint_native_repair.h']},
 hypothesis='Matched-scope native recovery may reproduce joint quality; timing urgency may prevent victim-endpoint losses.',
 qualification='Same affected sink/tree set is supplied to native controls; this isolates repair/scheduling, not independent discovery of blocker scope. Native global trees unchanged; external serialized candidate gets fresh FULL/STA.',
 limits=dict(native_process_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3)))
print({k:len(v['queries']) for k,v in registrations.items()})
