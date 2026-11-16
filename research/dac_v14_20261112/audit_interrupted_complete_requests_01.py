"""Independently match all four old request files and actual native QUERY rows.

Bounded native request logs only: no graph, route-tree or full STA parsing.
This is one prerequisite component, never a complete-stage/candidate admission.
"""
import collections,math,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from recovery_prefix_v1 import live_identity

out=D/'interrupted_complete_request_audit_01';out.mkdir(exist_ok=False)
inventory=read(D/'interrupted_stage_reconciliation_01/inventory.json');rows=[];bound={};started=time.monotonic()
def bind(path):
    path=Path(path).resolve();s=path.stat();before=(s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    digest=sha(path);s=path.stat();assert before==(s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    bound[str(path)]=digest;return digest
bind(Path(__file__));bind(D/'interrupted_stage_reconciliation_01/inventory.json')
for item in inventory['rows']:
    tx=Path(item['transaction']);role_name=item['role'];worker=tx/role_name;run=worker/'runs/state'
    bind(tx/'registration.json');role=read(tx/'registration.json')['roles'][role_name]
    bind(worker/'registration.json');registration=read(worker/'registration.json')
    assert not live_identity(registration['pid'],registration['start_ticks'])
    bind(run/'manifest.json');manifest=read(run/'manifest.json');request=Path(role['request'])
    request_sha=bind(request);assert bind(manifest['environment']['VPR_JOINT_NATIVE_REQUEST'])==request_sha
    assert manifest['environment']['VPR_JOINT_NATIVE_OBJECTIVE']==role['objective']
    text=request.read_text().splitlines();cursor=1;nets=int(text[0]);pairs=[]
    for line in text[cursor:cursor+nets]:
        fields=list(map(int,line.split()));assert len(fields)==fields[1]+2
        pairs += [(fields[0],pin) for pin in fields[2:]]
    cursor+=nets;protected=int(text[cursor]);cursor+=1
    assert protected==0,'A fixed-target-path request needs its separate complete parser'
    count=int(text[cursor]);cursor+=1;raw=[]
    for line in text[cursor:cursor+count]:
        fields=line.split();assert len(fields)==3
        net,pin=int(fields[0]),int(fields[1]);criticality=float(fields[2]);assert math.isfinite(criticality) and 0<=criticality<=1
        raw.append((net,pin,criticality))
    cursor+=count;assert cursor==len(text),'Unparsed request bytes'
    expected=[(q['net'],q['pin'],q['raw_criticality']) for q in role['queries']]
    assert raw==expected,'Serialized raw criticalities or complete query order differ from registration'
    assert collections.Counter(pairs)==collections.Counter((net,pin) for net,pin,c in raw)
    assert len(set(pairs))==len(pairs)==count
    log=run/'joint_native.log';assert log.stat().st_size<16*1024**2;log_sha=bind(log)
    queries=[];attempts=[];complete=None;effective=[]
    allowed={'KEEP','NODE','FAIL_TARGET','FAIL_EDGE','OCC','MODE','DOMAIN_RELEASE'}
    with log.open() as stream:
        for line in stream:
            fields=line.split();assert fields and complete is None,'Rows after COMPLETE'
            kind=fields[0]
            if kind=='QUERY':
                assert len(fields)==8
                pair=(int(fields[1]),int(fields[2]));assert fields[3] in ['0','1']
                value=float(fields[4]);assert math.isfinite(value) and 0<=value<=1
                assert int(fields[5])>=0 and int(fields[6])>=0 and float(fields[7])>=0
                queries.append(pair);effective.append(value)
            elif kind=='ATTEMPT':
                assert len(fields)==6;pair=(int(fields[1]),int(fields[2]));assert pair in set(pairs)
                assert math.isfinite(float(fields[3])) and float(fields[3])>=1
                assert fields[4] in ['0','1'] and fields[5] in ['0','1'];attempts.append(pair)
            elif kind=='COMPLETE':
                assert len(fields)==6 and fields[1]=='1' and fields[-1]=='occupancy_restored'
                assert int(fields[2])==int(fields[3])==count and math.isfinite(float(fields[4]));complete=fields
            else:assert kind in allowed,kind
    assert complete is not None and queries==[(net,pin) for net,pin,c in expected]
    assert collections.Counter(queries)==collections.Counter(pairs)
    assert bind(log)==log_sha and bind(request)==request_sha
    result=dict(passed=True,pair=item['pair'],arm=item['arm'],transaction=str(tx),role=role_name,
        request_sha256=request_sha,native_log_sha256=log_sha,registered_and_serialized_queries=count,
        actual_QUERY_rows=len(queries),actual_ATTEMPT_rows=len(attempts),exact_ordered_net_pin_match=True,
        exact_serialized_raw_criticalities_match=True,query_pair_multiset_and_group_restore_scope_match=True,
        complete_native_marker_present=True,original_worker_completion_present=(worker/'completion.json').exists(),
        original_manifest_status=manifest['status'],full_stage_admission_passed=False,candidate_ready=False,new_native_calls=0,
        qualification='Complete request/provenance component only. Logged effective search criticality differs semantically from raw request criticality; neither is silently substituted for the other. Large source bytes, raw full STA, source endpoint/physical assurance and candidate audits remain separate registered gates. Original manifests/completions are untouched.')
    rows.append(result);write(out/(item['pair']+'_'+item['arm']+'.json'),result)
write(out/'completion.json',dict(passed=True,roles=rows,exactly_matched_registered_queries=sum(r['actual_QUERY_rows'] for r in rows),
    native_attempt_rows=sum(r['actual_ATTEMPT_rows'] for r in rows),complete_readonly_seconds=time.monotonic()-started,
    source_sha256=bound,new_native_calls=0,full_stage_admission_passed=False,new_independent_inputs=0,
    graph_route_or_STA_parsing=False,historical_receipts_changed=False,
    qualification='Independent bounded old-request/actual-query audit before any adapter runs. No native replay or reconstructed historical completion. This component does not replace pending serial source-byte/FULL/STA/endpoint/physical verification or justify a complete candidate/algorithm claim.'))
print(dict(passed=True,roles=len(rows),matched_queries=sum(r['actual_QUERY_rows'] for r in rows),native_calls=0))
