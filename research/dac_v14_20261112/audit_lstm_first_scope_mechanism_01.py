"""Bounded read-only request/event audit of existing first-scope transactions.

No graph/route/full-vector read, full-result admission, experiment or retry.
"""
import collections
import json
import math
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

def parse_request(data,role):
    lines=data.decode().splitlines();n=int(lines[0]);cursor=1;pairs=[]
    for line in lines[cursor:cursor+n]:
        fields=list(map(int,line.split()));assert len(fields)==fields[1]+2
        pairs.extend((fields[0],pin) for pin in fields[2:])
    cursor+=n;assert lines[cursor]=='0';cursor+=1;count=int(lines[cursor]);cursor+=1
    raw=[]
    for line in lines[cursor:cursor+count]:
        fields=line.split();assert len(fields)==3
        raw.append((int(fields[0]),int(fields[1]),float(fields[2])))
    assert cursor+count==len(lines) and len(raw)==count
    assert all(math.isfinite(c) and 0<=c<=1 for _,_,c in raw)
    assert raw==[(q['net'],q['pin'],q['raw_criticality']) for q in role['queries']]
    assert collections.Counter(pairs)==collections.Counter((n,p) for n,p,c in raw)
    assert len(set(pairs))==len(pairs)
    return raw

def main():
    out=D/'LSTM_first_scope_mechanism_audit_01';assert not out.exists()
    started=time.monotonic();base=Path(read(D/'cp1r3_distinct_input_cohort_01/plan.json')['inputs'][0]['workspace'])
    bound={};rows={};requests={};roles={};initials={};decisions={}
    def bind(path):
        path=Path(path);assert path.stat().st_size<4*1024**2
        before=path.stat();h=sha(path);after=path.stat()
        assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
        bound[str(path)]=h;return h
    bind(Path(__file__).resolve())
    for arm,name in [('native','reuse_off'),('domain','reuse_on')]:
        tx=base/arm/'flow/resource_flow/repair/round_000/candidate_00';worker=tx/name;run=worker/'runs/state'
        for p in [tx/'registration.json',tx/'completion.json',tx/(name+'_decisions.json'),worker/'registration.json',worker/'completion.json',run/'manifest.json']:
            bind(p)
        role=read(tx/'registration.json')['roles'][name];roles[arm]=role
        registration=read(worker/'registration.json');identity=process_identity(registration['pid'])
        assert not identity or identity['state']=='Z' or identity['start_ticks']!=registration['start_ticks']
        done=read(tx/'completion.json');closed=read(worker/'completion.json');manifest=read(run/'manifest.json')
        assert done['passed'] and closed['passed'] and all(closed['checks'].values())
        assert manifest['status']=='completed' and manifest['returncode']==0
        request=Path(role['request']);bind(request);requests[arm]=request.read_bytes();expected=parse_request(requests[arm],role)
        assert bind(manifest['environment']['VPR_JOINT_NATIVE_REQUEST'])==bind(request)
        assert manifest['environment']['VPR_JOINT_NATIVE_OBJECTIVE']==role['objective']
        assert manifest['environment']['VPR_JOINT_NATIVE_SEED_ORDER']==role['seed_order']
        assert manifest['environment']['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE']==('1' if role['domain_failure_release'] else '0')
        domain_path=Path(role['crossing_domain']);bind(domain_path)
        if role['crossing_reuse_enabled']:
            assert bind(manifest['environment']['VPR_JOINT_NATIVE_REUSE_CROSSINGS'])==bind(domain_path)
        else:assert manifest['environment']['VPR_JOINT_NATIVE_REUSE_CROSSINGS']==''
        log=run/'joint_native.log';bind(log);queries=[];events=[];attempts=0;terminal=None
        for line in log.read_text().splitlines():
            fields=line.split();assert fields and terminal is None
            if fields[0]=='QUERY':
                assert len(fields)==8;queries.append((int(fields[1]),int(fields[2])))
            elif fields[0]=='DOMAIN_RELEASE':events.append(line)
            elif fields[0]=='ATTEMPT':attempts+=1
            elif fields[0]=='COMPLETE':
                assert len(fields)==6 and fields[1]=='1' and fields[-1]=='occupancy_restored'
                assert int(fields[2])==int(fields[3])==len(expected);terminal=fields
            else:assert fields[0] in {'KEEP','NODE','FAIL_TARGET','FAIL_EDGE','OCC','MODE'}
        assert terminal and queries==[(n,p) for n,p,c in expected]
        source=Path(role['state']);bind(source/'completion.json');initials[arm]=read(source/'completion.json')
        decision=read(tx/(name+'_decisions.json'));decisions[arm]=decision
        result=done['roles'][name];assert decision['resources_under_timing']['accepted']
        evaluation=Path(result['evaluation']);bind(evaluation/'completion.json');evaluated=read(evaluation/'completion.json')
        assert evaluated['passed'] and all(evaluated['checks'].values())
        domain_audit=None
        if arm=='domain':
            path=tx/(name+'_domain_audit.json');bind(path);domain_audit=read(path)
            assert domain_audit['passed'] and domain_audit['released_queries']==[] and events==[]
            for p,h in domain_audit['source_sha256'].items():
                if Path(p).stat().st_size<4*1024**2:assert bind(p)==h
        comparison=decision['strict']['comparison']
        rows[arm]=dict(transaction=str(tx),role=name,request_sha256=bind(request),domain_bytes_sha256=bind(domain_path),
            registered_queries=len(expected),actual_QUERY_rows=len(queries),actual_ATTEMPT_rows=attempts,
            complete_request_order_matches=True,domain_enabled=role['crossing_reuse_enabled'],
            failure_release_enabled=role['domain_failure_release'],observed_release_events=events,
            owner_coordination=False,original_candidate_checks=evaluated['checks'],
            original_candidate_CPD_s=result['cpd_s'],original_candidate_resources=result['resources'],
            original_endpoint_delta_summary={k:v for k,v in comparison.items() if k!='changes'},
            complete_transaction_seconds=done['complete_orchestrator_seconds'],native_core_seconds=result['native_core_seconds'],
            declared_source_vector_sha256=role['source_sha256'][str(source/'endpoint_vector.json')],
            declared_initial_route_body_sha256=initials[arm]['route_body_sha256'])
    assert requests['native']==requests['domain']
    operational=['queries','removed_pins','objective','fixed_target_paths','seed_order','original_budget','fixed_resource_limits','scope','baseline']
    assert all(roles['native'][k]==roles['domain'][k] for k in operational)
    assert rows['native']['domain_bytes_sha256']==rows['domain']['domain_bytes_sha256']
    assert rows['native']['declared_source_vector_sha256']==rows['domain']['declared_source_vector_sha256']
    assert rows['native']['declared_initial_route_body_sha256']==rows['domain']['declared_initial_route_body_sha256']
    assert decisions['native']['strict']['comparison']==decisions['domain']['strict']['comparison']
    assert all(sha(p)==h for p,h in bound.items())
    out.mkdir();write(out/'completion.json',dict(passed=True,kind='bounded_existing_request_and_event_audit',
        is_experiment_completion=False,rows=rows,complete_readonly_seconds=time.monotonic()-started,
        actual_request_and_domain_bytes_equal=True,operational_role_fields_equal=operational,
        declared_initial_route_body_and_vector_hashes_equal=True,raw_large_source_bytes_reverified=False,
        original_endpoint_change_records_equal=True,raw_full_vectors_reverified=False,
        local_domain_minus_native={k:rows['domain']['original_candidate_resources'][k]-rows['native']['original_candidate_resources'][k] for k in ['wirelength','SB_pairs','CB_sources']},
        no_release_event_or_owner_coordination_in_this_scope=True,
        original_native_whole_verification_status='execution_or_verification_failed',
        whole_method_quality_admitted=False,complete_paired_ratio=None,paper_benefit_claims_authorized=False,
        new_native_or_STA_calls=0,new_independent_verified_pairs=0,source_sha256=bound,
        qualification='Existing first-scope logs and receipts only; exact request bytes/order and zero failure-release events are audited. Source route-body/full-vector identity here relies on original declared digests, pending serial full-byte confirmation. The local +72wire/-2SB observation is consistent with domain restriction changing the tradeoff; neither release nor owner coordination executed in this scope. Later trajectories may diverge. Transaction/core times are nested costs, not complete algorithm times. Native whole verification remains failed and domain is ongoing. No new experiment, complete confirmation, universal gain or manuscript benefit.'))
    print(dict(passed=True,local_delta={k:rows['domain']['original_candidate_resources'][k]-rows['native']['original_candidate_resources'][k] for k in ['wirelength','SB_pairs','CB_sources']},queries_per_arm=8,release_events=0,whole_quality_admitted=False))

if __name__=='__main__':main()
