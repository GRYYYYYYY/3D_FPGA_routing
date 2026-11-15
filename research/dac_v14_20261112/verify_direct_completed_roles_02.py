"""Check every actual legal candidate of the four completed direct-audit roles."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir

root=D/'direct_completed_roles_validation_02';root.mkdir(exist_ok=False)
queue=D/'direct_scope_resource_equivalence_recovery_02/queue'
snapshot=root/'observed_results.json';snapshot.write_bytes((queue/'results.json').read_bytes())
observed=read(snapshot);closed=read(queue/'completion.json');assert closed['passed'] and len(closed['results'])==4
assert all(sha(p)==h for p,h in closed['source_sha256'].items())
results={};files=[queue/'completion.json',Path(__file__).resolve(),snapshot,queue/'registration.json']
for name in ['eltwise_A0_native','eltwise_A0_paired','bnn_A0_native','bnn_A0_paired']:
    row=observed[name];assert row['passed'] and row['comparison']['passed']
    old=D/'stable_seed_transfer_dev_01'/name;new=queue.parent/name
    oa,na=[read(p/'attempts.json') for p in [old,new]];assert len(oa)==len(na)
    for actor in [old,new]:
        closed=read(actor/'completion.json');assert closed['passed']
        assert all(sha(f)==h for f,h in closed['source_sha256'].items())
        files += [actor/'completion.json',actor/'attempts.json',actor/'registration.json']
    legal=failed=0
    for a,b in zip(oa,na):
        assert all(a[k]==b[k] for k in ['round','candidate_rank','bundle_removed_pins'])
        assert a['pair'].keys()==b['pair'].keys()
        txa=old/f"round_{a['round']:03d}"/f"candidate_{a['candidate_rank']:02d}"
        txb=new/f"round_{b['round']:03d}"/f"candidate_{b['candidate_rank']:02d}"
        for filename in ['request.txt','domain.txt']:
            assert sha(txa/filename)==sha(txb/filename)
            files += [txa/filename,txb/filename]
        for role in a['pair']:
            x,y=a['pair'][role],b['pair'][role]
            assert all(x.get(k)==y.get(k) for k in ['status','accepted','CPD_s','resources'])
            if x['status']!='legal_evaluated':failed+=1;continue
            sx,sy=Path(x['evaluation']),Path(y['evaluation'])
            vx,vy=read(sx/'endpoint_vector.json'),read(sy/'endpoint_vector.json')
            assert all(vx[k]==vy[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
            assert route_body(run_dir(sx)/'routed.route')==route_body(run_dir(sy)/'routed.route')
            files += [sx/'endpoint_vector.json',sy/'endpoint_vector.json',run_dir(sx)/'routed.route',run_dir(sy)/'routed.route']
            legal+=1
    comp=row['comparison']
    results[name]=dict(passed=True,legal_candidates_with_exact_full_vectors_and_ordered_bodies=legal,
        other_matched_outcomes=failed,all_requests_and_domains_exact=True,
        reference_imported_seconds=comp['reference_imported_workflow_seconds'],
        direct_imported_seconds=comp['direct_imported_workflow_seconds'],
        observed_seconds_difference=comp['direct_imported_workflow_seconds']-comp['reference_imported_workflow_seconds'])
write(root/'completion.json',dict(passed=True,roles=results,native_calls=0,engineering_cohort_complete=True,
    source_sha256={str(f):sha(f) for f in files},
    qualification='Four completed roles on two circuits, not four independent circuits. Every actual legal candidate, including rejections, has exact full-vector and ordered-route equivalence; requests and domain lists match. All four registered roles are terminal and verified. Imported workflow costs include each own execution, not cold full route-plus-repair timing, repetitions or a statistical speedup.'))
print(dict(passed=True,roles=results,native_calls=0),flush=True)
