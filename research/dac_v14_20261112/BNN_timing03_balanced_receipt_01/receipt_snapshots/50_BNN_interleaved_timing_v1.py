"""Accounting for balanced complete-run timing, without filling missing results."""
import os, platform, time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from run_native_scope_policy_v4 import run_dir
from complete_resource_timing_equivalence_v1 import compare
from endpoint_timing_policy_streaming_v2 import compare as endpoints

ORDER = ['native_0', 'domain_0', 'domain_1', 'native_1']

def validate_configs(native, domain):
    assert set(native) == set(domain)
    assert {k for k in native if native[k] != domain[k]} == {'domain_mode','domain_feedback'}
    assert (native['domain_mode'],native['domain_feedback']) == ('unrestricted',False)
    assert (domain['domain_mode'],domain['domain_feedback']) == ('paired',True)
    assert not native['external_history_allowed'] and not native['initial_route_imported']
    assert native['cache_mode'] == 'joint_build_inside_flow'
    assert 'terminal_resource_policy' not in native

def environment():
    return dict(observed_unix=time.time(),host=platform.node(),kernel=platform.release(),
        platform=platform.platform(),cpu_affinity=sorted(os.sched_getaffinity(0)),
        loadavg=Path('/proc/loadavg').read_text().strip(),
        memory=[line for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:','MemAvailable:'))],
        fixed_environment={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','PYTHONDONTWRITEBYTECODE']},
        qualification='Shared-host observation, not exclusive allocation or proof of no external activity; OS caches not flushed.')

def aggregate(rows, pairs):
    """No incomplete, failed or divergent run is silently removed from timing."""
    assert list(rows) == ORDER
    assert len(pairs) == 2
    valid = all(r.get('complete_verified') and r.get('same_role_exact') and r.get('measurement_complete') and r.get('environment_signature_consistent') for r in rows.values())
    valid = valid and all(p.get('matched_initial_state') and p.get('endpoint_comparison_available') for p in pairs)
    out = dict(all_registered_attempts_retained=True,registered_attempts=4,
        independent_new_inputs=0,paired_cost_observation_available=bool(valid),
        statistical_speedup_established=False,causal_environment_control_established=False,
        research_complete=False)
    if valid:
        times={k:float(v['complete_seconds']) for k,v in rows.items()}
        assert all(v>0 for v in times.values())
        ratios=[times['domain_'+str(i)]/times['native_'+str(i)] for i in range(2)]
        out.update(pair_domain_over_native_ratios=ratios,
            domain_mean_seconds=(times['domain_0']+times['domain_1'])/2,
            native_mean_seconds=(times['native_0']+times['native_1'])/2,
            native_observed_range_seconds=[min(times['native_0'],times['native_1']),max(times['native_0'],times['native_1'])],
            domain_observed_range_seconds=[min(times['domain_0'],times['domain_1']),max(times['domain_0'],times['domain_1'])])
    else:
        out.update(pair_domain_over_native_ratios=None,domain_mean_seconds=None,native_mean_seconds=None)
    return out

def finish(root):
    plan=read(root/'plan.json');rows=read(root/'queue/results.json');assert list(rows)==ORDER
    comparison_files=[]
    for name,row in rows.items():
        expected=read(root/'admission.json')['environment']
        observed=[read(root/name/f'environment_{x}.json') for x in ['before','after']]
        row['environment_signature_consistent']=all(all(x[k]==expected[k] for k in ['host','kernel','platform','cpu_affinity','fixed_environment']) for x in observed)
        row['same_role_exact']=False
        if not row['complete_verified']: continue
        case=root/name; done=read(case/'completion.json')
        ref=Path(plan['references'][name.split('_')[0]])
        equivalence=compare(case,ref)
        write(case/'same_role_equivalence.json',equivalence)
        graphs=[]
        for component,names in [('resource_flow/graph_audit_cache',['nodes.npy','edges.npy','switches.npy']),('resource_flow/full_graph_cache',['extra.npy','metadata.json']),('physical_query_graph',['graph.bin'])]:
            for n in names:
                graphs.append(dict(component=component,file=n,byte_exact=sha(case/'flow'/component/n)==sha(ref/'flow'/component/n)))
        row['same_role_exact']=bool(equivalence['downstream_actual_states_requests_and_native_work_exact'] and all(g['byte_exact'] for g in graphs))
        row['graph_payloads']=graphs
        initial=Path(done['initial_state']);final=Path(done['final_state'])
        own=endpoints(read(initial/'endpoint_vector.json'),read(final/'endpoint_vector.json'))
        write(case/'own_root_endpoints.json',own)
        row['own_root_endpoints']={k:v for k,v in own.items() if k!='changes'}
        row['quality']=dict(done['resources'],CPD_ns=done['CPD_ns'])
        comparison_files.extend([case/'completion.json',case/'same_role_equivalence.json',case/'own_root_endpoints.json'])
    pairs=[]
    for i in range(2):
        n,d=[root/(x+'_'+str(i)) for x in ['native','domain']]
        pair=dict(index=i,matched_initial_state=False,endpoint_comparison_available=False)
        if all(rows[p.name]['complete_verified'] for p in [n,d]):
            nc,dc=[read(p/'completion.json') for p in [n,d]]
            roots=[Path(c['initial_state']) for c in [nc,dc]]
            vectors=[read(p/'endpoint_vector.json') for p in roots]
            pair['matched_initial_state']=all(vectors[0][k]==vectors[1][k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']) and route_body(run_dir(roots[0])/'routed.route')==route_body(run_dir(roots[1])/'routed.route')
            diff=endpoints(*[read(Path(c['final_state'])/'endpoint_vector.json') for c in [nc,dc]])
            write(root/f'pair_{i}_final_endpoints.json',diff)
            pair.update(endpoint_comparison_available=bool(diff['compatible']),final_endpoint_summary={k:v for k,v in diff.items() if k!='changes'},
                final_resource_delta={k:dc['resources'][k]-nc['resources'][k] for k in nc['resources']},CPD_ns_delta=dc['CPD_ns']-nc['CPD_ns'])
            comparison_files.append(root/f'pair_{i}_final_endpoints.json')
        pairs.append(pair)
    out=aggregate(rows,pairs)
    out.update(passed=True,rows=rows,pairs=pairs,source_sha256={str(f):sha(f) for f in [root/'plan.json',root/'queue/results.json',*comparison_files]},
        qualification='Four new complete measurement attempts, order native/domain then domain/native, all retained. Same known BNN input, zero new independent inputs. Both arms use identical stable engineering, source seals, input interpretation, observer, environment and complete-command boundaries; only domain treatment differs. Actual equivalence and identical new roots gate descriptive paired ratios. Two observations per arm do not establish statistical acceleration; shared-host activity and OS cache remain uncontrolled. Original historical22.95% result is not overwritten, and this batch cannot terminate the research goal.')
    write(root/'comparison.json',out)
    return out
